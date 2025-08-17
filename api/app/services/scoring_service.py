from typing import List, Dict, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime, timedelta
from app.models.application import Application
from app.models.opportunity import Opportunity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class ScoringService:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        
    async def calculate_fit_score(
        self, 
        user_skills: List[str],
        user_experience: str,
        opportunity: Opportunity,
        user_applications_history: List[Application],
        db: AsyncSession
    ) -> float:
        """Calculate fit score (0-100) for an opportunity"""
        
        # Component scores
        skill_score = self._calculate_skill_match(user_skills, opportunity.skills_required or [])
        experience_score = self._calculate_experience_match(user_experience, opportunity.jd_text or "")
        urgency_score = self._calculate_urgency_score(opportunity.deadline_at)
        conversion_score = await self._calculate_conversion_likelihood(
            user_applications_history, opportunity, db
        )
        
        # Weighted combination
        weights = {
            'skills': 0.35,
            'experience': 0.25, 
            'urgency': 0.15,
            'conversion': 0.25
        }
        
        final_score = (
            skill_score * weights['skills'] +
            experience_score * weights['experience'] +
            urgency_score * weights['urgency'] +
            conversion_score * weights['conversion']
        )
        
        return min(100.0, max(0.0, final_score))
    
    def _calculate_skill_match(self, user_skills: List[str], required_skills: List[str]) -> float:
        """Calculate skill overlap score using Jaccard similarity"""
        if not required_skills:
            return 50.0  # Neutral score when no skills specified
            
        user_skills_set = set(skill.lower() for skill in user_skills)
        required_skills_set = set(skill.lower() for skill in required_skills)
        
        if not user_skills_set:
            return 0.0
            
        intersection = user_skills_set.intersection(required_skills_set)
        union = user_skills_set.union(required_skills_set)
        
        jaccard_score = len(intersection) / len(union) if union else 0.0
        return jaccard_score * 100.0
    
    def _calculate_experience_match(self, user_experience: str, job_description: str) -> float:
        """Calculate experience match using TF-IDF cosine similarity"""
        if not user_experience or not job_description:
            return 50.0
            
        try:
            # Preprocess texts
            texts = [user_experience.lower(), job_description.lower()]
            
            # Calculate TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return similarity * 100.0
        except:
            return 50.0
    
    def _calculate_urgency_score(self, deadline: Optional[datetime]) -> float:
        """Calculate urgency score based on deadline"""
        if not deadline:
            return 50.0  # Neutral score for no deadline
            
        now = datetime.utcnow()
        days_until_deadline = (deadline - now).days
        
        if days_until_deadline < 0:
            return 0.0  # Deadline passed
        elif days_until_deadline <= 2:
            return 100.0  # Very urgent
        elif days_until_deadline <= 7:
            return 80.0  # Urgent
        elif days_until_deadline <= 30:
            return 60.0  # Moderate urgency
        else:
            return 40.0  # Low urgency
    
    async def _calculate_conversion_likelihood(
        self, 
        user_applications: List[Application],
        opportunity: Opportunity,
        db: AsyncSession
    ) -> float:
        """Calculate likelihood of success based on historical data"""
        if not user_applications:
            return 50.0  # Neutral score for new users
            
        # Analyze similar applications
        similar_apps = [
            app for app in user_applications 
            if app.opportunity.kind == opportunity.kind
        ]
        
        if not similar_apps:
            return 50.0
            
        # Calculate success rate
        successful_apps = [
            app for app in similar_apps 
            if app.status in ['offer', 'accepted']
        ]
        
        success_rate = len(successful_apps) / len(similar_apps)
        
        # Boost score based on recent positive outcomes
        recent_apps = [
            app for app in similar_apps 
            if app.created_at > datetime.utcnow() - timedelta(days=90)
        ]
        
        if recent_apps:
            recent_success_rate = len([
                app for app in recent_apps 
                if app.status in ['offer', 'accepted']
            ]) / len(recent_apps)
            
            # Weight recent performance more heavily
            final_rate = (success_rate * 0.4) + (recent_success_rate * 0.6)
        else:
            final_rate = success_rate
            
        return final_rate * 100.0

    async def generate_recommendations(
        self, 
        user_id: int,
        limit: int = 10,
        db: AsyncSession
    ) -> List[Dict]:
        """Generate personalized opportunity recommendations"""
        from app.models.user import User, UserSkill
        from app.models.application import Application
        
        # Get user data
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return []
            
        # Get user skills
        skills_result = await db.execute(
            select(UserSkill).where(UserSkill.user_id == user_id)
        )
        user_skills = [skill.skill.name for skill in skills_result.scalars().all()]
        
        # Get user applications history
        apps_result = await db.execute(
            select(Application).where(Application.user_id == user_id)
        )
        user_applications = apps_result.scalars().all()
        
        # Get available opportunities (not applied to)
        applied_opportunity_ids = [app.opportunity_id for app in user_applications]
        
        opportunities_query = select(Opportunity).where(
            Opportunity.status == 'active'
        )
        if applied_opportunity_ids:
            opportunities_query = opportunities_query.where(
                ~Opportunity.id.in_(applied_opportunity_ids)
            )
            
        opportunities_result = await db.execute(opportunities_query)
        opportunities = opportunities_result.scalars().all()
        
        # Score each opportunity
        scored_opportunities = []
        for opp in opportunities:
            score = await self.calculate_fit_score(
                user_skills,
                user.profile_data.get('experience', ''),
                opp,
                user_applications,
                db
            )
            
            scored_opportunities.append({
                'opportunity': opp,
                'fit_score': score,
                'organization': opp.organization
            })
        
        # Sort by score and apply diversity
        scored_opportunities.sort(key=lambda x: x['fit_score'], reverse=True)
        
        # Add diversity (don't recommend too many from same company)
        diverse_recommendations = []
        company_counts = {}
        
        for item in scored_opportunities:
            company = item['organization'].name
            if company_counts.get(company, 0) < 2:  # Max 2 per company
                diverse_recommendations.append(item)
                company_counts[company] = company_counts.get(company, 0) + 1
                
                if len(diverse_recommendations) >= limit:
                    break
        
        return diverse_recommendations[:limit]
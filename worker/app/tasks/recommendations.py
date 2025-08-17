from celery import shared_task
import asyncio
from app.services.database import get_async_session
from app.services.scoring_service import ScoringService
import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_daily_recommendations(user_id: int = None):
    """Generate daily recommendations for users"""
    return asyncio.run(_generate_daily_recommendations_async(user_id))

async def _generate_daily_recommendations_async(user_id: Optional[int] = None):
    try:
        from app.models.user import User
        from sqlalchemy import select
        
        async with get_async_session() as db:
            # Get users to generate recommendations for
            if user_id:
                users_result = await db.execute(
                    select(User).where(User.id == user_id, User.is_active == True)
                )
            else:
                users_result = await db.execute(
                    select(User).where(User.is_active == True)
                )
            
            users = users_result.scalars().all()
            
            scoring_service = ScoringService()
            results = []
            
            for user in users:
                try:
                    recommendations = await scoring_service.generate_recommendations(
                        user.id, limit=10, db=db
                    )
                    
                    # Cache recommendations (could store in Redis)
                    # For now, just log
                    logger.info(f"Generated {len(recommendations)} recommendations for user {user.id}")
                    
                    results.append({
                        'user_id': user.id,
                        'recommendations_count': len(recommendations),
                        'success': True
                    })
                    
                    # Optionally send email with recommendations
                    if recommendations:
                        from app.tasks.notifications import send_recommendations_email
                        send_recommendations_email.delay(user.id, recommendations[:5])
                        
                except Exception as e:
                    logger.error(f"Error generating recommendations for user {user.id}: {str(e)}")
                    results.append({
                        'user_id': user.id,
                        'success': False,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'processed_users': len(results),
                'results': results
            }
            
    except Exception as e:
        logger.error(f"Error in daily recommendations: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@shared_task
def update_opportunity_scores():
    """Update fit scores for all user applications"""
    return asyncio.run(_update_opportunity_scores_async())

async def _update_opportunity_scores_async():
    try:
        from app.models.application import Application
        from app.models.user import User, UserSkill
        from sqlalchemy import select
        
        async with get_async_session() as db:
            # Get all applications without scores or with old scores
            apps_result = await db.execute(
                select(Application).where(
                    (Application.score_fit == None) | 
                    (Application.updated_at < datetime.utcnow() - timedelta(days=7))
                )
            )
            applications = apps_result.scalars().all()
            
            scoring_service = ScoringService()
            updated_count = 0
            
            for app in applications:
                try:
                    # Get user skills
                    skills_result = await db.execute(
                        select(UserSkill).where(UserSkill.user_id == app.user_id)
                    )
                    user_skills = [skill.skill.name for skill in skills_result.scalars().all()]
                    
                    # Get user applications history
                    history_result = await db.execute(
                        select(Application).where(
                            Application.user_id == app.user_id,
                            Application.id != app.id
                        )
                    )
                    user_history = history_result.scalars().all()
                    
                    # Calculate new score
                    score = await scoring_service.calculate_fit_score(
                        user_skills,
                        app.user.profile_data.get('experience', ''),
                        app.opportunity,
                        user_history,
                        db
                    )
                    
                    app.score_fit = score
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error updating score for application {app.id}: {str(e)}")
            
            await db.commit()
            
            logger.info(f"Updated scores for {updated_count} applications")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_processed': len(applications)
            }
            
    except Exception as e:
        logger.error(f"Error updating opportunity scores: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
from celery import shared_task
import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
import asyncio
from app.services.database import get_async_session
from app.models.opportunity import Opportunity, Organization
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

@shared_task
def scrape_opportunity(url: str, user_id: int) -> Dict:
    """Scrape job/internship opportunity from URL"""
    return asyncio.run(_scrape_opportunity_async(url, user_id))

async def _scrape_opportunity_async(url: str, user_id: int) -> Dict:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract job details (LinkedIn-style)
        if 'linkedin.com' in url:
            data = await _scrape_linkedin_job(soup, url)
        elif 'indeed.com' in url:
            data = await _scrape_indeed_job(soup, url)
        elif 'glassdoor.com' in url:
            data = await _scrape_glassdoor_job(soup, url)
        else:
            data = await _scrape_generic_job(soup, url)
            
        # Save to database
        async with get_async_session() as db:
            # Find or create organization
            org_result = await db.execute(
                select(Organization).where(Organization.name == data['company'])
            )
            organization = org_result.scalar_one_or_none()
            
            if not organization:
                organization = Organization(
                    name=data['company'],
                    website=data.get('company_website', ''),
                    location=data.get('location', ''),
                )
                db.add(organization)
                await db.flush()
            
            # Create opportunity
            opportunity = Opportunity(
                organization_id=organization.id,
                title=data['title'],
                kind=data.get('type', 'job'),
                location=data.get('location', ''),
                mode=data.get('work_mode', 'onsite'),
                url=url,
                jd_text=data.get('description', ''),
                skills_required=data.get('skills', []),
                salary_min=data.get('salary_min'),
                salary_max=data.get('salary_max'),
                source='scraped'
            )
            
            db.add(opportunity)
            await db.commit()
            
            logger.info(f"Successfully scraped opportunity: {data['title']} at {data['company']}")
            
            return {
                'success': True,
                'opportunity_id': opportunity.id,
                'title': data['title'],
                'company': data['company']
            }
            
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'url': url
        }

async def _scrape_linkedin_job(soup: BeautifulSoup, url: str) -> Dict:
    """LinkedIn-specific scraping logic"""
    data = {}
    
    # Title
    title_elem = soup.find('h1', class_='top-card-layout__title')
    data['title'] = title_elem.get_text(strip=True) if title_elem else 'Unknown Title'
    
    # Company
    company_elem = soup.find('a', class_='topcard__org-name-link')
    data['company'] = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
    
    # Location
    location_elem = soup.find('span', class_='topcard__flavor--bullet')
    data['location'] = location_elem.get_text(strip=True) if location_elem else ''
    
    # Description
    desc_elem = soup.find('div', class_='show-more-less-html__markup')
    data['description'] = desc_elem.get_text(separator=' ', strip=True) if desc_elem else ''
    
    # Skills extraction from description
    data['skills'] = _extract_skills_from_text(data['description'])
    
    # Work mode detection
    desc_lower = data['description'].lower()
    if 'remote' in desc_lower:
        data['work_mode'] = 'remote'
    elif 'hybrid' in desc_lower:
        data['work_mode'] = 'hybrid'
    else:
        data['work_mode'] = 'onsite'
    
    return data

async def _scrape_generic_job(soup: BeautifulSoup, url: str) -> Dict:
    """Generic scraping for unknown job sites"""
    data = {}
    
    # Try common selectors for title
    title_selectors = ['h1', '.job-title', '.title', '[class*="title"]']
    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem:
            data['title'] = elem.get_text(strip=True)
            break
    else:
        data['title'] = 'Unknown Title'
    
    # Try to find company
    company_selectors = ['.company', '.employer', '[class*="company"]', '[class*="employer"]']
    for selector in company_selectors:
        elem = soup.select_one(selector)
        if elem:
            data['company'] = elem.get_text(strip=True)
            break
    else:
        data['company'] = 'Unknown Company'
    
    # Get all text for description
    data['description'] = soup.get_text(separator=' ', strip=True)
    data['skills'] = _extract_skills_from_text(data['description'])
    
    return data

def _extract_skills_from_text(text: str) -> List[str]:
    """Extract technical skills from job description text"""
    # Common technical skills
    skill_patterns = [
        r'\b(?:Python|Java|JavaScript|C\+\+|C#|Ruby|Go|Rust|Swift|Kotlin|PHP|TypeScript)\b',
        r'\b(?:React|Angular|Vue|Django|Flask|Spring|Express|Laravel|Rails)\b',
        r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|PostgreSQL|MongoDB|Redis)\b',
        r'\b(?:Machine Learning|Data Science|AI|Deep Learning|TensorFlow|PyTorch)\b',
        r'\b(?:SQL|NoSQL|REST|GraphQL|Microservices|DevOps|CI/CD)\b'
    ]
    
    skills = set()
    text_upper = text.upper()
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        skills.update(match.upper() for match in matches)
    
    return list(skills)

@shared_task
def scrape_multiple_opportunities(urls: List[str], user_id: int) -> Dict:
    """Scrape multiple opportunities in parallel"""
    results = []
    for url in urls:
        result = scrape_opportunity.delay(url, user_id)
        results.append(result.get())
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    return {
        'total': len(urls),
        'successful': len(successful),
        'failed': len(failed),
        'results': results
    }
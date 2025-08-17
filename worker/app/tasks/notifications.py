from celery import shared_task
import asyncio
from app.services.email_service import EmailService
from app.services.database import get_async_session
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_email(to_email: str, subject: str, body: str, user_id: int = None):
    """Send email notification"""
    return asyncio.run(_send_email_async(to_email, subject, body, user_id))

async def _send_email_async(to_email: str, subject: str, body: str, user_id: int = None):
    try:
        email_service = EmailService()
        result = await email_service.send_email(to_email, subject, body)
        
        logger.info(f"Email sent to {to_email}: {subject}")
        
        return {
            'success': True,
            'to_email': to_email,
            'subject': subject
        }
        
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'to_email': to_email
        }

@shared_task
def send_recommendations_email(user_id: int, recommendations: List[Dict]):
    """Send daily recommendations email"""
    return asyncio.run(_send_recommendations_email_async(user_id, recommendations))

async def _send_recommendations_email_async(user_id: int, recommendations: List[Dict]):
    try:
        from app.models.user import User
        
        async with get_async_session() as db:
            user = await db.get(User, user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Generate email content
            subject = f"🎯 Daily Job Recommendations - {len(recommendations)} New Opportunities"
            
            body = f"""
            Hi {user.full_name},
            
            Here are your personalized job recommendations for today:
            
            """
            
            for i, rec in enumerate(recommendations, 1):
                opp = rec['opportunity']
                org = rec['organization']
                score = rec['fit_score']
                
                body += f"""
                {i}. {opp.title} at {org.name}
                   📍 {opp.location or 'Location not specified'}
                   💰 {f"${opp.salary_min:,}" if opp.salary_min else "Salary not specified"}
                   🎯 Fit Score: {score:.0f}/100
                   🔗 {opp.url}
                   
                """
            
            body += """
            
            Ready to apply? Log in to your Student CRM to manage these opportunities.
            
            Best of luck with your applications!
            Student CRM Team
            """
            
            email_service = EmailService()
            await email_service.send_email(user.email, subject, body)
            
            logger.info(f"Sent recommendations email to user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'recommendations_count': len(recommendations)
            }
            
    except Exception as e:
        logger.error(f"Error sending recommendations email to user {user_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'user_id': user_id
        }

@shared_task
def send_deadline_reminders():
    """Send reminders for approaching deadlines"""
    return asyncio.run(_send_deadline_reminders_async())

async def _send_deadline_reminders_async():
    try:
        from app.models.application import Application
        from app.models.user import User
        from datetime import datetime, timedelta
        from sqlalchemy import select
        
        # Find applications with deadlines in next 24-48 hours
        tomorrow = datetime.utcnow() + timedelta(days=1)
        day_after = datetime.utcnow() + timedelta(days=2)
        
        async with get_async_session() as db:
            apps_result = await db.execute(
                select(Application, User).join(User).where(
                    Application.status.in_(['to_apply', 'applied']),
                    Application.opportunity.has(deadline_at__between=[tomorrow, day_after])
                )
            )
            
            urgent_applications = apps_result.all()
            sent_count = 0
            
            for app, user in urgent_applications:
                try:
                    deadline = app.opportunity.deadline_at
                    hours_remaining = (deadline - datetime.utcnow()).total_seconds() / 3600
                    
                    subject = f"⏰ Deadline Alert: {app.opportunity.title} - {hours_remaining:.0f} hours left"
                    
                    body = f"""
                    Hi {user.full_name},
                    
                    This is a reminder that the deadline for "{app.opportunity.title}" at {app.opportunity.organization.name} is approaching:
                    
                    ⏰ Deadline: {deadline.strftime('%B %d, %Y at %I:%M %p')}
                    ⏳ Time Remaining: {hours_remaining:.0f} hours
                    📍 Status: {app.status.replace('_', ' ').title()}
                    
                    {'🚀 Time to submit your application!' if app.status == 'to_apply' else '📞 Consider following up on your application.'}
                    
                    Good luck!
                    Student CRM Team
                    """
                    
                    email_service = EmailService()
                    await email_service.send_email(user.email, subject, body)
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Error sending deadline reminder for application {app.id}: {str(e)}")
            
            logger.info(f"Sent {sent_count} deadline reminder emails")
            
            return {
                'success': True,
                'reminders_sent': sent_count,
                'total_urgent': len(urgent_applications)
            }
            
    except Exception as e:
        logger.error(f"Error sending deadline reminders: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
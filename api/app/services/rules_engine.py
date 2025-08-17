from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.rule import Rule
from app.models.application import Application
from app.models.task import Task
import logging

logger = logging.getLogger(__name__)

class RulesEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def process_user_rules(self, user_id: int):
        """Process all active rules for a user"""
        # Get user's active rules
        rules_result = await self.db.execute(
            select(Rule).where(
                Rule.owner_id == user_id,
                Rule.enabled == True
            )
        )
        rules = rules_result.scalars().all()
        
        results = []
        for rule in rules:
            try:
                result = await self._process_rule(rule)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing rule {rule.id}: {str(e)}")
                results.append({
                    'rule_id': rule.id,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    async def _process_rule(self, rule: Rule) -> Dict[str, Any]:
        """Process a single rule"""
        # Parse rule configuration
        trigger = rule.trigger
        condition = json.loads(rule.condition_json) if rule.condition_json else {}
        action = json.loads(rule.action_json) if rule.action_json else {}
        
        # Check if rule should be triggered
        should_trigger = await self._evaluate_trigger(rule.owner_id, trigger, condition)
        
        if not should_trigger:
            return {
                'rule_id': rule.id,
                'triggered': False,
                'message': 'Conditions not met'
            }
        
        # Execute action
        action_result = await self._execute_action(rule.owner_id, action)
        
        # Update rule's last run time
        rule.last_run_at = datetime.utcnow()
        await self.db.commit()
        
        return {
            'rule_id': rule.id,
            'triggered': True,
            'action_result': action_result
        }
    
    async def _evaluate_trigger(self, user_id: int, trigger: str, condition: Dict) -> bool:
        """Evaluate if a rule trigger condition is met"""
        
        if trigger == "application_no_response":
            return await self._check_application_no_response(user_id, condition)
        elif trigger == "deadline_approaching":
            return await self._check_deadline_approaching(user_id, condition)
        elif trigger == "status_unchanged":
            return await self._check_status_unchanged(user_id, condition)
        elif trigger == "daily_recommendations":
            return await self._check_daily_recommendations(user_id, condition)
        else:
            logger.warning(f"Unknown trigger type: {trigger}")
            return False
    
    async def _check_application_no_response(self, user_id: int, condition: Dict) -> bool:
        """Check for applications with no response after specified days"""
        days = condition.get('days', 7)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find applications that were applied to but haven't progressed
        apps_result = await self.db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.status == 'applied',
                Application.applied_at <= cutoff_date
            )
        )
        
        stale_applications = apps_result.scalars().all()
        return len(stale_applications) > 0
    
    async def _check_deadline_approaching(self, user_id: int, condition: Dict) -> bool:
        """Check for opportunities with approaching deadlines"""
        hours = condition.get('hours', 48)
        cutoff_date = datetime.utcnow() + timedelta(hours=hours)
        
        # Find applications with approaching deadlines
        apps_result = await self.db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.status.in_(['to_apply', 'applied']),
                Application.opportunity.has(deadline_at__lte=cutoff_date)
            )
        )
        
        urgent_applications = apps_result.scalars().all()
        return len(urgent_applications) > 0
    
    async def _check_status_unchanged(self, user_id: int, condition: Dict) -> bool:
        """Check for applications stuck in same status"""
        days = condition.get('days', 14)
        status = condition.get('status', 'applied')
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        apps_result = await self.db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.status == status,
                Application.updated_at <= cutoff_date
            )
        )
        
        stuck_applications = apps_result.scalars().all()
        return len(stuck_applications) > 0
    
    async def _check_daily_recommendations(self, user_id: int, condition: Dict) -> bool:
        """Always trigger for daily recommendations"""
        return True
    
    async def _execute_action(self, user_id: int, action: Dict) -> Dict[str, Any]:
        """Execute a rule action"""
        action_type = action.get('type')
        
        if action_type == "create_task":
            return await self._create_task_action(user_id, action)
        elif action_type == "send_email":
            return await self._send_email_action(user_id, action)
        elif action_type == "send_notification":
            return await self._send_notification_action(user_id, action)
        elif action_type == "update_priority":
            return await self._update_priority_action(user_id, action)
        else:
            return {'success': False, 'error': f'Unknown action type: {action_type}'}
    
    async def _create_task_action(self, user_id: int, action: Dict) -> Dict[str, Any]:
        """Create a task"""
        try:
            task = Task(
                user_id=user_id,
                title=action.get('title', 'Automated Task'),
                description=action.get('description', ''),
                due_at=datetime.utcnow() + timedelta(days=action.get('due_days', 1)),
                priority=action.get('priority', 'medium'),
                source='rule_engine'
            )
            
            self.db.add(task)
            await self.db.commit()
            
            return {
                'success': True,
                'task_id': task.id,
                'message': 'Task created successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_email_action(self, user_id: int, action: Dict) -> Dict[str, Any]:
        """Queue email for sending"""
        try:
            from worker.app.tasks.notifications import send_email
            
            # Queue email task
            send_email.delay(
                to_email=action.get('to'),
                subject=action.get('subject', 'Student CRM Notification'),
                body=action.get('body', ''),
                user_id=user_id
            )
            
            return {
                'success': True,
                'message': 'Email queued for sending'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_notification_action(self, user_id: int, action: Dict) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            # This would integrate with your notification system
            # For now, we'll just log it
            logger.info(f"Notification for user {user_id}: {action.get('message')}")
            
            return {
                'success': True,
                'message': 'Notification sent'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _update_priority_action(self, user_id: int, action: Dict) -> Dict[str, Any]:
        """Update application priority"""
        try:
            application_id = action.get('application_id')
            new_priority = action.get('priority', 1)
            
            if application_id:
                app_result = await self.db.execute(
                    select(Application).where(
                        Application.id == application_id,
                        Application.user_id == user_id
                    )
                )
                application = app_result.scalar_one_or_none()
                
                if application:
                    application.priority = new_priority
                    await self.db.commit()
                    
                    return {
                        'success': True,
                        'message': f'Updated priority to {new_priority}'
                    }
            
            return {'success': False, 'error': 'Application not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
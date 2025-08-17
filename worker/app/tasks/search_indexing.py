from celery import shared_task
import asyncio
from app.services.database import get_async_session
from meilisearch import Client
import os
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

# Meilisearch client
meili_client = Client(
    os.getenv("MEILISEARCH_URL", "http://localhost:7700"),
    os.getenv("MEILI_MASTER_KEY", "")
)

@shared_task
def index_document(document_id: int):
    """Index document in Meilisearch"""
    return asyncio.run(_index_document_async(document_id))

async def _index_document_async(document_id: int):
    try:
        from app.models.document import Document
        
        async with get_async_session() as db:
            document = await db.get(Document, document_id)
            if not document:
                return {'success': False, 'error': 'Document not found'}
            
            # Prepare document for indexing
            doc_data = {
                'id': f"doc_{document.id}",
                'entity_type': 'document',
                'entity_id': document.id,
                'title': document.title,
                'content': document.content_text or "",
                'kind': document.kind,
                'owner_id': document.owner_id,
                'created_at': document.created_at.isoformat(),
                'tags': document.tags or []
            }
            
            # Index in documents collection
            index = meili_client.index('documents')
            task = index.add_documents([doc_data])
            
            logger.info(f"Indexed document {document_id} in Meilisearch")
            
            return {
                'success': True,
                'document_id': document_id,
                'meili_task_id': task.task_uid
            }
            
    except Exception as e:
        logger.error(f"Error indexing document {document_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'document_id': document_id
        }

@shared_task
def index_opportunity(opportunity_id: int):
    """Index opportunity in Meilisearch"""
    return asyncio.run(_index_opportunity_async(opportunity_id))

async def _index_opportunity_async(opportunity_id: int):
    try:
        from app.models.opportunity import Opportunity, Organization
        
        async with get_async_session() as db:
            # Get opportunity with organization
            result = await db.execute(
                select(Opportunity, Organization)
                .join(Organization)
                .where(Opportunity.id == opportunity_id)
            )
            opportunity, organization = result.first()
            
            if not opportunity:
                return {'success': False, 'error': 'Opportunity not found'}
            
            # Prepare for indexing
            opp_data = {
                'id': f"opp_{opportunity.id}",
                'entity_type': 'opportunity',
                'entity_id': opportunity.id,
                'title': opportunity.title,
                'company': organization.name,
                'location': opportunity.location or "",
                'description': opportunity.jd_text or "",
                'kind': opportunity.kind,
                'mode': opportunity.mode,
                'skills': opportunity.skills_required or [],
                'salary_min': opportunity.salary_min,
                'salary_max': opportunity.salary_max,
                'deadline_at': opportunity.deadline_at.isoformat() if opportunity.deadline_at else None,
                'created_at': opportunity.created_at.isoformat()
            }
            
            # Index in opportunities collection
            index = meili_client.index('opportunities')
            task = index.add_documents([opp_data])
            
            logger.info(f"Indexed opportunity {opportunity_id} in Meilisearch")
            
            return {
                'success': True,
                'opportunity_id': opportunity_id,
                'meili_task_id': task.task_uid
            }
            
    except Exception as e:
        logger.error(f"Error indexing opportunity {opportunity_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'opportunity_id': opportunity_id
        }

@shared_task
def setup_search_indexes():
    """Setup Meilisearch indexes with proper configuration"""
    try:
        # Documents index
        docs_index = meili_client.index('documents')
        docs_index.update_searchable_attributes(['title', 'content', 'tags'])
        docs_index.update_filterable_attributes(['kind', 'owner_id', 'created_at'])
        docs_index.update_sortable_attributes(['created_at'])
        
        # Opportunities index
        opps_index = meili_client.index('opportunities')
        opps_index.update_searchable_attributes(['title', 'company', 'description', 'skills'])
        opps_index.update_filterable_attributes(['kind', 'mode', 'location', 'company', 'created_at'])
        opps_index.update_sortable_attributes(['created_at', 'deadline_at', 'salary_min'])
        
        # Contacts index
        contacts_index = meili_client.index('contacts')
        contacts_index.update_searchable_attributes(['name', 'email', 'notes', 'role'])
        contacts_index.update_filterable_attributes(['organization', 'strength', 'last_contacted_at'])
        contacts_index.update_sortable_attributes(['last_contacted_at', 'strength'])
        
        logger.info("Successfully setup Meilisearch indexes")
        
        return {'success': True, 'message': 'Search indexes configured'}
        
    except Exception as e:
        logger.error(f"Error setting up search indexes: {str(e)}")
        return {'success': False, 'error': str(e)}

@shared_task
def reindex_all():
    """Re-index all entities"""
    return asyncio.run(_reindex_all_async())

async def _reindex_all_async():
    try:
        from app.models.document import Document
        from app.models.opportunity import Opportunity
        from app.models.contact import Contact
        
        async with get_async_session() as db:
            # Get all documents
            docs_result = await db.execute(select(Document))
            documents = docs_result.scalars().all()
            
            # Get all opportunities
            opps_result = await db.execute(select(Opportunity))
            opportunities = opps_result.scalars().all()
            
            # Get all contacts
            contacts_result = await db.execute(select(Contact))
            contacts = contacts_result.scalars().all()
            
            # Index documents
            for doc in documents:
                index_document.delay(doc.id)
            
            # Index opportunities
            for opp in opportunities:
                index_opportunity.delay(opp.id)
            
            # Index contacts
            for contact in contacts:
                index_contact.delay(contact.id)
            
            total = len(documents) + len(opportunities) + len(contacts)
            
            logger.info(f"Queued {total} items for re-indexing")
            
            return {
                'success': True,
                'total_queued': total,
                'documents': len(documents),
                'opportunities': len(opportunities),
                'contacts': len(contacts)
            }
            
    except Exception as e:
        logger.error(f"Error during re-indexing: {str(e)}")
        return {'success': False, 'error': str(e)}
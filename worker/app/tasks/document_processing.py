from celery import shared_task
import pytesseract
from PIL import Image
import PyPDF2
from docx import Document
import os
import asyncio
from app.services.database import get_async_session
from app.models.document import Document as DocModel
from app.services.embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_document(document_id: int):
    """Process uploaded document: extract text, generate embeddings"""
    return asyncio.run(_process_document_async(document_id))

async def _process_document_async(document_id: int):
    try:
        async with get_async_session() as db:
            # Get document
            document = await db.get(DocModel, document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            file_path = document.file_path
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Extract text based on file type
            text_content = ""
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                text_content = _extract_pdf_text(file_path)
            elif file_ext in ['.docx', '.doc']:
                text_content = _extract_docx_text(file_path)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                text_content = _extract_image_text(file_path)
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            # Update document with extracted text
            document.content_text = text_content
            document.word_count = len(text_content.split())
            
            # Generate embeddings
            embedding_service = EmbeddingService()
            embeddings = await embedding_service.generate_embeddings(text_content)
            document.embeddings = embeddings.tolist()
            
            # Index in search
            from app.tasks.search_indexing import index_document
            index_document.delay(document_id)
            
            await db.commit()
            
            logger.info(f"Successfully processed document {document_id}")
            
            return {
                'success': True,
                'document_id': document_id,
                'word_count': document.word_count,
                'has_embeddings': len(embeddings) > 0
            }
            
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'document_id': document_id
        }

def _extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF using PyPDF2"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        logger.warning(f"Error extracting PDF text: {e}")
    return text.strip()

def _extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.warning(f"Error extracting DOCX text: {e}")
        return ""

def _extract_image_text(file_path: str) -> str:
    """Extract text from image using OCR"""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        logger.warning(f"Error extracting image text: {e}")
        return ""

@shared_task
def bulk_process_documents(document_ids: List[int]):
    """Process multiple documents"""
    results = []
    for doc_id in document_ids:
        result = process_document(doc_id)
        results.append(result)
    
    successful = sum(1 for r in results if r.get('success'))
    return {
        'total': len(document_ids),
        'successful': successful,
        'failed': len(document_ids) - successful,
        'results': results
    }
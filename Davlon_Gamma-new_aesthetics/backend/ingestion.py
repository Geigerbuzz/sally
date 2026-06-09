import google.generativeai as genai
from .config import settings
from .database import db
import logging
import uuid
import io
import fitz  # PyMuPDF
import pdfplumber
import csv
import PIL.Image
import docx # python-docx
import openpyxl
from pptx import Presentation
from .graph_service import graph_service
from .csv_service import CsvIngestionService
from .category_agent import CategoryManager
from .document_lifecycle import get_lifecycle_manager, DocumentLifecycle, DocumentStatus
from .semantic_chunker import chunk_document_semantically

logger = logging.getLogger("davlon-ingestion")

class HighFidelityIngestor:
    """
    Self-Adapting Document Ingestor.
    
    Uses AI-driven category discovery instead of hardcoded categories.
    Categories evolve with each document uploaded, learning the company's
    domain and terminology automatically.
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.csv_service = CsvIngestionService()
        # Dynamic category manager (replaces hardcoded CATEGORIES)
        self.category_manager = CategoryManager(db)
        # Document lifecycle manager for permanence scoring
        self.lifecycle_manager = get_lifecycle_manager(db)

    async def _classify_document(self, text_sample: str, filename: str) -> list:
        """
        Dynamic document classification using AI-driven category discovery.
        
        Now returns MULTIPLE categories (e.g., ["real_estate", "legal"] for a deed).
        
        Instead of fixed categories, this method:
        1. Analyzes the document content
        2. Assigns to all relevant categories (1-3)
        3. Creates new categories if needed
        4. Updates the Company Profile with learned categories
        
        Returns list of category names.
        """
        try:
            categories = await self.category_manager.classify_document(text_sample, filename)
            logger.info(f"Document '{filename}' classified as: {categories}")
            return categories
        except Exception as e:
            logger.error(f"Dynamic classification failed: {e}")
            return ["general"]

    def extract_tables_to_markdown(self, pdf_bytes):
        """
        Layer 2: Extracts tables using pdfplumber and converts them to Markdown.
        Returns a dictionary of {page_index: [list of markdown tables]}.
        """
        table_map = {}
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    md_tables = []
                    for table in tables:
                        # Convert list of lists to Markdown Table
                        if not table: continue
                        
                        # Clean None values
                        clean_table = [[str(cell) if cell is not None else "" for cell in row] for row in table]
                        
                        # Header
                        header = "| " + " | ".join(clean_table[0]) + " |"
                        separator = "| " + " | ".join(["---"] * len(clean_table[0])) + " |"
                        
                        # Body
                        body = ""
                        for row in clean_table[1:]:
                            body += "\n| " + " | ".join(row) + " |"
                            
                        md_table = f"\n{header}\n{separator}{body}\n"
                        md_tables.append(md_table)
                    
                    if md_tables:
                        table_map[i] = md_tables
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
        return table_map

    async def _generate_caption(self, image_bytes, mime_type="image/jpeg"):
        """Helper to call Gemini for a single image."""
        try:
           model = genai.GenerativeModel('gemini-2.5-flash-lite')
           
           # Skip small icons
           if len(image_bytes) < 4096:
               return None

           response = await model.generate_content_async([
               "Describe this image in detail. If it's a chart, describe the data trends.",
               {"mime_type": mime_type, "data": image_bytes}
           ])
           return response.text.strip()
        except Exception as e:
            logger.warning(f"Caption generation failed: {e}")
            return None

    async def caption_pdf_images(self, pdf_bytes):
        """Extracts and captions images from PDF."""
        caption_map = {}
        try:
           doc = fitz.open(stream=pdf_bytes, filetype="pdf")
           for i, page in enumerate(doc):
               images = page.get_images()
               captions = []
               for img_index, img in enumerate(images):
                   xref = img[0]
                   base_image = doc.extract_image(xref)
                   image_bytes = base_image["image"]
                   mime = base_image["ext"] # usually 'jpeg', 'png'
                   
                   # Map fitz ext to mime
                   if mime == 'jpg': mime = 'image/jpeg'
                   elif mime == 'png': mime = 'image/png'
                   else: mime = f'image/{mime}'

                   caption = await self._generate_caption(image_bytes, mime)
                   if caption:
                       captions.append(f"![Image-{i}-{img_index}](placeholder) *AI Caption: {caption}*")
                       logger.info(f"Generated caption for PDF P{i+1}")
               
               if captions:
                   caption_map[i] = captions
        except Exception as e:
            logger.error(f"PDF Image extraction failed: {e}")
        return caption_map

    async def extract_docx(self, file_contents: bytes, filename: str) -> str:
        """Extracts text from DOCX."""
        # Note: Image extraction from DOCX via python-docx is complex without unzipping.
        # For this iteration, we focus on high-fidelity TEXT.
        # If image extraction is strictly required, we would need to unzip the docx and find media folder.
        full_text = f"# Document: {filename}\n\n"
        try:
            doc = docx.Document(io.BytesIO(file_contents))
            for para in doc.paragraphs:
                full_text += para.text + "\n\n"
            
            # Simple Table Extraction for DOCX
            for table in doc.tables:
                full_text += "\n### Table\n"
                for row in table.rows:
                    row_text = [cell.text for cell in row.cells]
                    full_text += "| " + " | ".join(row_text) + " |\n"
                full_text += "\n"
                
        except Exception as e:
            logger.error(f"DOCX Extraction failed: {e}")
            return ""
            
        return full_text

    async def extract_csv(self, file_contents: bytes, filename: str) -> str:
        """
        Extracts content from CSV files using the Hybrid CsvIngestionService.
        """
        text_content = file_contents.decode('utf-8', errors='ignore')
        
        # In newer Python async/await patterns, simple sync functions can be blocked.
        # However, CsvIngestionService.ingest_csv IS async.
        return await self.csv_service.ingest_csv(text_content, filename)

    async def extract_xlsx(self, file_contents: bytes, filename: str) -> str:
        """Extracts data from Excel."""
        full_text = f"# Spreadsheet: {filename}\n\n"
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_contents), data_only=True)
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                full_text += f"## Sheet: {sheet}\n\n"
                
                rows = list(ws.rows)
                if not rows: continue
                
                # Simple Markdown Table
                # Header
                headers = [str(cell.value or "") for cell in rows[0]]
                full_text += "| " + " | ".join(headers) + " |\n"
                full_text += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                
                for row in rows[1:]:
                    values = [str(cell.value or "") for cell in row]
                    full_text += "| " + " | ".join(values) + " |\n"
                
                full_text += "\n---\n"
        except Exception as e:
            logger.error(f"XLSX Extraction failed: {e}")
            return ""
        return full_text

    async def extract_pptx(self, file_contents: bytes, filename: str) -> str:
        """Extracts text and images from PowerPoint."""
        full_text = f"# Presentation: {filename}\n\n"
        try:
            prs = Presentation(io.BytesIO(file_contents))
            for i, slide in enumerate(prs.slides):
                full_text += f"## Slide {i+1}\n\n"
                
                # Text
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        full_text += shape.text + "\n"
                
                # Images
                # Note: Extracting images from shapes in python-pptx is possible if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
                # Simplified check:
                for shape in slide.shapes:
                    if hasattr(shape, "image"):
                        image_bytes = shape.image.blob
                        mime = shape.image.content_type
                        
                        caption = await self._generate_caption(image_bytes, mime)
                        if caption:
                            full_text += f"\n![Slide-Img](placeholder) *AI Caption: {caption}*\n"
                
                full_text += "\n---\n"
        except Exception as e:
            logger.error(f"PPTX Extraction failed: {e}")
            return ""
        return full_text

    async def extract_markdown(self, file_contents: bytes, filename: str) -> str:
        """
        Stitches Text (PyMuPDF) and Tables (pdfplumber) into a single Markdown string.
        """
        full_text = f"# Document: {filename}\n\n"
        
        # 1. Get Tables (The Skeleton)
        tables_by_page = self.extract_tables_to_markdown(file_contents)
        
        # 1.5 Get Images (The Eyes)
        captions_by_page = await self.caption_pdf_images(file_contents)
        
        # 2. Get Text (The Meat)
        doc = fitz.open(stream=file_contents, filetype="pdf")
        
        for i, page in enumerate(doc):
            # Extract text blocks
            text = page.get_text()
            
            full_text += f"## Page {i+1}\n\n"
            full_text += text
            
            # Append tables found on this page
            if i in tables_by_page:
                full_text += "\n\n### Data Tables\n"
                for table in tables_by_page[i]:
                    full_text += table + "\n"
            
            # Append images found on this page
            if i in captions_by_page:
                full_text += "\n\n### Figures & Charts\n"
                for caption in captions_by_page[i]:
                    full_text += caption + "\n"
            
            full_text += "\n---\n"
            
        return full_text

    def chunk_markdown(self, text, chunk_size=1000, overlap=100):
        """
        Recursive chunker respectful of Markdown headers.
        Now also detects content type for each chunk.
        
        Returns list of dicts: [{"text": "...", "content_type": "text|image|table|graph"}, ...]
        """
        chunks = []
        start = 0
        
        def detect_content_type(chunk_text: str) -> str:
            """Detect the primary content type of a chunk."""
            chunk_lower = chunk_text.lower()
            
            # Check for graph/chart indicators (graphs take precedence over images)
            graph_markers = ['chart', 'graph', 'plot', 'data visualization', 'bar chart', 
                           'pie chart', 'line graph', 'histogram', 'trend', 'x-axis', 'y-axis']
            if any(marker in chunk_lower for marker in graph_markers):
                return "graph"
            
            # Check for image captions (AI Caption marker from our extraction)
            image_markers = ['![image', 'ai caption:', '![slide-img', '### figures', 
                           'photo', 'picture', 'illustration', 'diagram', 'screenshot']
            if any(marker in chunk_lower for marker in image_markers):
                return "image"
            
            # Check for table content
            table_markers = ['### data tables', '| ---', '|---|', '### table']
            if any(marker in chunk_lower for marker in table_markers):
                return "table"
            
            # Default to text
            return "text"
        
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                # Try to break at a newline to avoid splitting words
                break_point = text.rfind('\n', start, end)
                if break_point != -1:
                    end = break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                content_type = detect_content_type(chunk)
                chunks.append({
                    "text": chunk,
                    "content_type": content_type
                })
            start = end - overlap
        return chunks

    async def ingest(self, file_contents: bytes, filename: str, doc_id: str):
        try:
            logger.info(f"Starting High-Fidelity Ingestion for {filename}...")
            
            # 0. Create Document Node (Persistence)
            await graph_service.create_document_node(doc_id, filename)
            
            # 1. Hybrid Extraction
            if filename.lower().endswith(".csv"):
                    # Use Hybrid Service (Schema + AI Fallback)
                    markdown_text = await self.extract_csv(file_contents, filename)

            elif filename.lower().endswith(".pdf"):
                markdown_text = await self.extract_markdown(file_contents, filename)
            elif filename.lower().endswith(".docx"):
                markdown_text = await self.extract_docx(file_contents, filename)
            elif filename.lower().endswith(".xlsx"):
                markdown_text = await self.extract_xlsx(file_contents, filename)
            elif filename.lower().endswith(".pptx"):
                markdown_text = await self.extract_pptx(file_contents, filename)
            else:
                markdown_text = file_contents.decode("utf-8") # Plain text/MD support
                
            if not markdown_text.strip():
                return False

            # 1.5 Classify Document (now returns multiple categories)
            categories = await self._classify_document(markdown_text, filename)
            
            # 1.6 Analyze Document Lifecycle (Permanence + Version Detection)
            permanence = await self.lifecycle_manager.analyze_permanence(markdown_text, filename)
            logger.info(f"Permanence analysis: score={permanence.permanence_score:.2f}, type={permanence.document_type}")
            
            # 1.7 Calculate confidence using rule-based approach
            confidence = self.lifecycle_manager.calculate_confidence(
                filename=filename,
                content=markdown_text,
                ai_analysis=permanence
            )
            logger.info(f"Confidence calculation: {confidence:.2f}")
            
            if confidence < 0.6:
                logger.warning(f"Low confidence ({confidence:.2f}) for '{filename}' - user notification recommended")
            
            # Check for version supersession
            superseded_doc_id = await self.lifecycle_manager.detect_supersession(filename, doc_id)
            if superseded_doc_id:
                await self.lifecycle_manager.mark_as_superseded(superseded_doc_id, doc_id)
                logger.info(f"Document supersedes: {superseded_doc_id}")
            
            # Create lifecycle record with calculated confidence
            lifecycle = DocumentLifecycle(
                doc_id=doc_id,
                status=DocumentStatus.ACTIVE,
                permanence_score=permanence.permanence_score,
                document_type=permanence.document_type,
                supersedes=superseded_doc_id,
                legacy_confidence=confidence  # Now calculated, not defaulted!
            )
            success = await self.lifecycle_manager.save_lifecycle(lifecycle)
            if not success:
                logger.warning(f"Failed to save lifecycle for {doc_id}, proceeding with defaults")
            
            # 1.8 Send inbox notification if confidence is low
            if await self.lifecycle_manager.should_notify_for_legacy(doc_id):
                await db.create_inbox_message(
                    subject="📄 Document Review Needed",
                    body=f"I'm not sure whether \"{filename}\" should remain active or be moved to legacy.\n\nPermanence score: {permanence.permanence_score:.0%}\nDocument type: {permanence.document_type}\n\nWould you like to keep it active or archive it?",
                    msg_type="legacy_archival",
                    metadata={"doc_id": doc_id, "filename": filename, "permanence": permanence.permanence_score},
                    actions=[
                        {"id": "keep_active", "label": "Keep Active"},
                        {"id": "archive", "label": "Move to Legacy"}
                    ]
                )
                logger.info(f"Sent inbox notification for low-confidence doc: {filename}")

            # 2. Semantic Chunking (embedding-based topic detection)
            # Check if any category is special for overlap decision
            special_categories = await db.get_special_categories()
            is_special = any(cat in special_categories for cat in categories)
            
            # Use semantic chunking if enabled (default), no fallback - quality over speed
            if settings.SEMANTIC_CHUNKING_ENABLED:
                try:
                    chunks = await chunk_document_semantically(
                        markdown_text,
                        overlap_ratio=0.5 if is_special else 0.3,
                        is_special_category=is_special
                    )
                    logger.info(f"Semantic chunking: {len(chunks)} chunks for '{filename}' (special={is_special})")
                except Exception as chunk_error:
                    logger.error(f"Semantic chunking failed for '{filename}': {chunk_error}")
                    # No fallback - return error to user
                    raise ValueError(f"Document chunking failed: {chunk_error}. Please try again or contact support.")
            else:
                # Explicitly disabled via config - only for debugging/testing
                chunks = self.chunk_markdown(markdown_text)
                logger.warning(f"Character chunking used for '{filename}' (semantic disabled via config)")
            
            # Count content types for logging
            type_counts = {}
            for c in chunks:
                ct = c['content_type']
                type_counts[ct] = type_counts.get(ct, 0) + 1
            logger.info(f"Content types: {type_counts}")

            # 3. Embedding (Gemini-001) with position tracking for chunk linking
            batch_size = 5
            prev_chunk_id = None  # Track previous chunk for NEXT/PREV linking
            global_position = 0   # Track position across all batches
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                
                # Extract just the text for embedding
                batch_texts = [c['text'] for c in batch]
                
                response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=batch_texts,
                    task_type="RETRIEVAL_DOCUMENT",
                    title=filename,
                    output_dimensionality=768
                )
                
                embeddings = response['embedding']
                
                # 4. Save to Neo4j with category, content_type, position, and chunk links
                for j, emb in enumerate(embeddings):
                    chunk_data = batch[j]
                    chunk_text = chunk_data['text']
                    content_type = chunk_data['content_type']
                    chunk_id = str(uuid.uuid4())
                    
                    await db.insert_chunk(
                        doc_id=doc_id, 
                        chunk_id=chunk_id, 
                        text=chunk_text, 
                        embedding=emb, 
                        source=filename,
                        category=categories,
                        content_type=content_type,
                        position=global_position,
                        prev_chunk_id=prev_chunk_id  # Links to previous chunk
                    )
                    
                    # Track for next iteration
                    prev_chunk_id = chunk_id
                    global_position += 1
            
            logger.info(f"Ingestion Complete: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Ingestion Error: {e}")
            import traceback
            traceback.print_exc()
            return False

# Global Instance
ingestor = HighFidelityIngestor()

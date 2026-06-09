
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from .config import settings
from .database import db
from .rag import rag
from .ingestion import ingestor
from .graph_service import graph_service
from .learning_engine import learning_engine
from .document_lifecycle import get_lifecycle_manager
import shutil
import os
import logging
import uuid
import asyncio
import time

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("davlon-backend")
ai_client = rag

app = FastAPI()

# CORS - Allow all for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background scheduler for daily maintenance jobs
scheduler = None

# Startup/Shutdown
@app.on_event("startup")
async def startup_db_client():
    global scheduler
    await db.connect()
    
    # Initialize APScheduler for background jobs
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = AsyncIOScheduler()
        
        # Daily at 3 AM: Re-evaluate stale documents
        scheduler.add_job(
            daily_maintenance_job,
            CronTrigger(hour=3, minute=0),
            id="daily_maintenance",
            replace_existing=True
        )
        
        # Weekly on Monday at 9 AM: Category relationship analysis
        scheduler.add_job(
            weekly_category_analysis_job,
            CronTrigger(day_of_week='mon', hour=9, minute=0),
            id="weekly_category_analysis",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Background scheduler started (daily maintenance at 3 AM, category analysis Mondays 9 AM)")
    except ImportError:
        logger.warning("APScheduler not installed - scheduled jobs disabled")

@app.on_event("shutdown")
async def shutdown_db_client():
    global scheduler
    if scheduler:
        scheduler.shutdown()
    await db.close()


async def daily_maintenance_job():
    """
    Runs daily at 3 AM:
    1. Re-evaluate stale documents for legacy status
    2. Prune low-performing query expansions
    """
    logger.info("Starting daily maintenance job...")
    
    try:
        # 1. Document lifecycle check
        lifecycle_manager = get_lifecycle_manager(db)
        lifecycle_result = await lifecycle_manager.reevaluate_stale_documents()
        logger.info(f"Lifecycle check: evaluated={lifecycle_result['evaluated']}, marked_legacy={lifecycle_result['marked_legacy']}")
        
        # 2. Prune low-performing expansions (after 10+ uses)
        pruned = await db.prune_low_performing_expansions(min_uses=10, max_miss_rate=0.8)
        logger.info(f"Expansion pruning: removed {len(pruned)} low-hit terms")
        
    except Exception as e:
        logger.error(f"Daily maintenance job failed: {e}")


async def weekly_category_analysis_job():
    """
    Runs weekly on Monday at 9 AM:
    Analyzes category relationships and sends merge suggestions to Inbox.
    """
    logger.info("Starting weekly category analysis job...")
    
    try:
        from .category_intelligence import get_category_intelligence
        
        cat_intel = get_category_intelligence(db)
        suggestions_sent = await cat_intel.generate_merge_suggestions()
        
        logger.info(f"Category analysis complete: {suggestions_sent} merge suggestions sent to Inbox")
    except Exception as e:
        logger.error(f"Weekly category analysis job failed: {e}")


# Models
class QueryRequest(BaseModel):
    prompt: str
    file_ids: List[str] = [] # Legacy field, kept for compatibility
    
class QueryResponse(BaseModel):
    text: str
    citations: List[str]
    confidence: float

# Endpoints

@app.get("/health")
def read_root():
    return {"status": "ok", "service": "Davlon Backend"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Ingests a file using the High-Fidelity Pipeline (Text/Markdown/Vector).
    """
    try:
        contents = await file.read()
        doc_id = str(uuid.uuid4())
        
        # New Ingestion Logic
        success = await ingestor.ingest(contents, file.filename, doc_id)
        
        if success:
            return {"status": "success", "filename": file.filename, "file_id": doc_id}
        else:
            raise HTTPException(status_code=500, detail="Ingestion failed internally.")
            
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    True RAG Query: Hybrid Search + Verification.
    """
    response = await rag.query_hybrid(request.prompt, request.file_ids)
    return QueryResponse(
        text=response["text"],
        citations=response.get("citations", []),
        confidence=response.get("confidence", 0.0)
    )

# --- Middleware: Request Logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# --- Global Exception Handlers ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )

# Endpoints

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Davlon Backend"}

# --- API Endpoints ---

@app.post("/api/ingest/doc")
async def ingest_document(file: UploadFile = File(...)):
    """
    1. Saves file to disk (temp in /tmp).
    2. Uploads to Gemini File API.
    3. Stores Metadata in Neo4j.
    """
    import tempfile
    
    # Create a temp file in the system temp directory (always writable)
    # delete=False because we need to close it before Gemini reads it (Cross-platform safety)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
            
        # 2. Upload to Gemini
        logger.info(f"Uploading {file.filename} to Gemini from {temp_path}...")
        file_ref = await ai_client.upload_file(temp_path, display_name=file.filename)
        logger.info(f"Gemini File ID: {file_ref.name}")
        
        # 3. Store in Neo4j
        query = """
        MERGE (d:Document {id: $id})
        SET d.name = $name,
            d.uri = $uri,
            d.mimeType = $mime,
            d.uploadedAt = datetime()
        RETURN d
        """
        async with db.get_session() as session:
            await session.run(query, {
                "id": file_ref.name,  # unique 'files/xxxx' ID
                "name": file.filename,
                "uri": file_ref.uri,
                "mime": file_ref.mime_type
            })
            
        return {"status": "success", "file_id": file_ref.name, "message": "Indexed in Brain & Graph"}

    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        # Return the actual error message to the frontend for better debugging
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Cleanup
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup temp file: {cleanup_error}")

@app.post("/api/query/rag")
async def query_documents(payload: dict):
    """
    Payload: { "prompt": "Who is Alice?", "UseAllDocs": true }
    """
    prompt = payload.get("prompt")
    use_all = payload.get("UseAllDocs", True)
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt required")
        
    try:
        # 1. Get File IDs from Neo4j
        # In a real scenario, we might filter by Project or User
        file_ids = []
        if use_all:
            async with db.get_session() as session:
                result = await session.run("MATCH (d:Document) RETURN d.id as id")
                file_ids = [record["id"] async for record in result]
        
        if not file_ids:
            return {"answer": "I don't have any documents to read yet.", "citations": []}

        # 2. Ask Gemini (Hybrid RAG)
        logger.info(f"Querying Gemini with {len(file_ids)} documents...")
        result = await rag.query_hybrid(prompt, file_ids)
        
        # 3. Collect learning signals (async, non-blocking)
        categories_used = result.get("categories_used", [])
        if categories_used:
            asyncio.create_task(
                learning_engine.collect_query_signals(categories_used)
            )
        
        # 4. Format Response
        return {
            "answer": result["text"],
            "citations": result.get("citations", []), 
            "source_count": len(file_ids),
            "uses_special_sources": result.get("uses_special_sources", False),
            "legacy_warning": result.get("legacy_warning")
        }
        
    except Exception as e:
        logger.error(f"Query Error: {e}")
        # Return error as answer so it appears in chat
        return {
            "answer": f"**System Error**: {str(e)}",
            "citations": [],
            "source_count": 0
        }

@app.get("/api/widgets/data")
async def get_widget_data():
    """
    Live data for dashboard widgets.
    Fetches real data from Neo4j when available, otherwise returns simulated data.
    """
    import random
    
    data = {
        "listings": {"active": 0, "pending": 0},
        "revenue": {"current": 0, "unit": "M", "trend": "+0%"},
        "leads": {"new": 0, "trend": "+0%"},
        "avgDOM": {"days": 0},
        "recentSales": [],
        "pipeline": {"stages": []},
        "revenueChart": {"labels": [], "values": []}
    }
    
    try:
        # 1. Listings Count (Real from Neo4j)
        async with db.get_session() as session:
            result = await session.run("MATCH (l:Listing) RETURN count(l) as count")
            record = await result.single()
            listings_count = record["count"] if record else 0
            data["listings"]["active"] = listings_count
            data["listings"]["pending"] = max(0, listings_count // 3)  # Estimate
            
        # 2. Documents Count (for activity metric)
        async with db.get_session() as session:
            result = await session.run("MATCH (d:Document) RETURN count(d) as count")
            record = await result.single()
            doc_count = record["count"] if record else 0
        
        # 3. Simulated but varying data (when real data would need CRM integration)
        # Using time-based randomization for "live" feel
        import time
        seed = int(time.time() / 5)  # Changes every 5 seconds
        random.seed(seed)
        
        # Revenue (simulated with slight variation)
        base_revenue = 1.2 + (listings_count * 0.15) + random.uniform(-0.1, 0.1)
        trend_pct = random.randint(5, 18)
        data["revenue"]["current"] = round(base_revenue, 1)
        data["revenue"]["unit"] = "M"
        data["revenue"]["trend"] = f"+{trend_pct}%"
        
        # Leads (simulated)
        data["leads"]["new"] = max(3, listings_count * 2 + random.randint(-2, 5))
        data["leads"]["trend"] = f"+{random.randint(8, 25)}%"
        
        # Avg Days on Market (simulated)
        data["avgDOM"]["days"] = random.randint(28, 45)
        
        # Recent Sales (simulated list)
        sample_addresses = [
            "123 Oak Street", "456 Pine Avenue", "789 Maple Drive",
            "321 Elm Court", "654 Cedar Lane", "987 Birch Road"
        ]
        recent_sales = []
        for i in range(min(3, listings_count or 2)):
            recent_sales.append({
                "address": sample_addresses[i % len(sample_addresses)],
                "price": f"${random.randint(350, 850)}k",
                "daysAgo": random.randint(1, 14)
            })
        data["recentSales"] = recent_sales
        
        # Pipeline Stages (simulated)
        total = max(10, listings_count * 3)
        data["pipeline"]["stages"] = [
            {"name": "Prospecting", "count": int(total * 0.35), "color": "#ff9f0a"},
            {"name": "Showings", "count": int(total * 0.25), "color": "#0a84ff"},
            {"name": "Negotiation", "count": int(total * 0.20), "color": "#30d158"},
            {"name": "Closing", "count": int(total * 0.20), "color": "#bf5af2"}
        ]
        
        # Revenue Chart (last 6 months, simulated)
        months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [random.randint(65, 95) for _ in range(6)]
        values[-1] = int(base_revenue * 100 / 1.5)  # Make current month match revenue
        data["revenueChart"]["labels"] = months
        data["revenueChart"]["values"] = values
        
    except Exception as e:
        logger.warning(f"Widget data fetch error (using fallbacks): {e}")
        # Return complete simulated data on error
        import time
        seed = int(time.time() / 5)
        random.seed(seed)
        
        data["listings"]["active"] = random.randint(8, 25)
        data["listings"]["pending"] = random.randint(2, 8)
        data["leads"]["new"] = random.randint(5, 20)
        data["leads"]["trend"] = f"+{random.randint(8, 25)}%"
        data["revenue"]["current"] = round(random.uniform(1.5, 4.5), 1)
        data["revenue"]["trend"] = f"+{random.randint(5, 18)}%"
        data["avgDOM"]["days"] = random.randint(25, 50)
        data["pipeline"]["stages"] = [
            {"name": "Prospecting", "count": random.randint(3, 8), "color": "#ff9f0a"},
            {"name": "Showings", "count": random.randint(2, 6), "color": "#0a84ff"},
            {"name": "Negotiation", "count": random.randint(1, 4), "color": "#30d158"},
            {"name": "Closing", "count": random.randint(1, 3), "color": "#bf5af2"}
        ]
        data["recentSales"] = [
            {"address": "123 Oak Street", "price": f"${random.randint(350, 850)}k", "daysAgo": random.randint(1, 14)},
            {"address": "456 Pine Avenue", "price": f"${random.randint(350, 850)}k", "daysAgo": random.randint(1, 14)}
        ]
        data["revenueChart"]["labels"] = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        data["revenueChart"]["values"] = [random.randint(65, 95) for _ in range(6)]
    
    return data

@app.post("/api/ingest/data")
async def ingest_structured_data(
    file: UploadFile = File(...), 
    label: str = "Entity"
):
    """
    Ingests a CSV file into Neo4j.
    - label: The Node Label to apply (e.g., 'Agent', 'Property').
    """
    try:
        content = await file.read()
        count = await graph_ingestor.ingest_csv_content(content, label)
        return {"status": "success", "nodes_created": count, "label": label}
    except Exception as e:
        logger.error(f"Structured Ingest Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents():
    """Fetch list of processed documents from Neo4j"""
    query = """
    MATCH (d:Document)
    RETURN d.name as name, d.id as id, d.uploadedAt as date
    ORDER BY d.uploadedAt DESC
    """
    try:
        async with db.get_session() as session:
            result = await session.run(query)
            # Neo4j DateTime objects need to be converted to strings
            documents = [
                {
                    "name": record["name"], 
                    "id": record["id"], 
                    "date": str(record["date"])
                } 
                async for record in result
            ]
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Failed to fetch docs: {e}")
        return {"documents": []} # Fail gracefully


@app.get("/api/listings")
async def get_listings():
    """Fetch all listings from Neo4j for the Workspace page."""
    try:
        results = await graph_service.get_all_listings()
        listings = []
        for row in results:
            listing = row.get('l', {})
            agents = row.get('agents', [])
            
            # Calculate data completeness for traffic light
            required_fields = ['beds', 'baths', 'sqft', 'price']
            filled = sum(1 for f in required_fields if listing.get(f, 0) not in [0, None, ''])
            completeness = filled / len(required_fields)
            
            # Traffic light status: red < 50%, yellow 50-99%, green = 100%
            if completeness < 0.5:
                status = 'red'
            elif completeness < 1.0:
                status = 'yellow'
            else:
                status = 'green'
            
            listings.append({
                "id": listing.get('id'),
                "address": listing.get('address', 'Unknown Address'),
                "beds": listing.get('beds', 0),
                "baths": listing.get('baths', 0),
                "sqft": listing.get('sqft', 0),
                "price": listing.get('price', 0),
                "status": status,
                "agents": agents,
                "bonuses": listing.get('bonuses', []),
                "source": listing.get('source_file', '')
            })
        
        return {"listings": listings}
    except Exception as e:
        logger.error(f"Failed to fetch listings: {e}")
        return {"listings": []}


# --- Widget Generation Endpoint ---

@app.post("/api/generate-widget")
async def generate_widget(payload: dict):
    """
    Uses AI + RAG to generate a widget payload from uploaded documents.
    1. Query RAG for relevant context
    2. Generate widget JSON using that data
    """
    import google.generativeai as genai
    from .config import settings
    import json
    import re
    
    prompt = payload.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt required")
    
    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # --- RAG: Retrieve relevant context ---
        query_emb = await rag.get_embedding(prompt, task_type="RETRIEVAL_QUERY")
        results = await db.vector_search(query_emb, limit=5)
        
        # Build context from retrieved chunks
        context_text = ""
        if results:
            for i, res in enumerate(results):
                context_text += f"\n[Source: {res['source']}]\n{res['text']}\n"
        
        # --- Prompt with RAG context ---
        system_prompt = f"""You are a widget JSON generator for a dashboard. 
You MUST use the DATA PROVIDED below to populate the widget. Do NOT make up data.

=== RETRIEVED DATA FROM USER'S DOCUMENTS ===
{context_text if context_text else "(No relevant documents found - generate sample data)"}
=== END DATA ===

TEMPLATES (pick one):
1. "kpi-card" for single numbers:
   {{"id":"w-1","title":"Revenue","template":"kpi-card","dimension":"1x1","data":{{"value":"$45k","trend":"up","trendValue":"+12%"}}}}

2. "bar-chart" for comparisons:
   {{"id":"w-2","title":"Sales by Region","template":"bar-chart","dimension":"2x1","data":{{"labels":["North","South"],"datasets":[{{"label":"Revenue","values":[45,32]}}]}}}}

3. "line-chart" for trends:
   {{"id":"w-3","title":"Monthly Traffic","template":"line-chart","dimension":"2x1","data":{{"labels":["Jan","Feb","Mar"],"datasets":[{{"label":"Visitors","values":[120,150,180]}}]}}}}

4. "data-table" for lists:
   {{"id":"w-4","title":"Top Agents","template":"data-table","dimension":"2x2","data":{{"headers":["Name","Sales"],"rows":[["Alice","$500k"],["Bob","$320k"]]}}}}

RULES:
- Output ONLY the JSON object, no markdown, no explanation
- EXTRACT real values from the retrieved data above
- Keep titles under 25 characters
- Include "dimension" field ("1x1", "2x1", "1x2", or "2x2")

USER REQUEST: {prompt}"""

        response = await model.generate_content_async(system_prompt)
        raw_text = response.text.strip()
        
        # Clean JSON from markdown code blocks if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r'^```(?:json)?\n?', '', raw_text)
            raw_text = re.sub(r'\n?```$', '', raw_text)
        
        # Parse and validate JSON
        widget_payload = json.loads(raw_text)
        
        # Ensure required fields
        if "id" not in widget_payload:
            widget_payload["id"] = f"w-{int(time.time()*1000)}"
        if "template" not in widget_payload:
            raise HTTPException(status_code=422, detail="AI did not return a valid template")
        
        logger.info(f"Generated widget: {widget_payload.get('title')} ({widget_payload.get('template')}) from {len(results)} chunks")
        
        return {"status": "success", "widget": widget_payload}
        
    except json.JSONDecodeError as e:
        logger.error(f"Widget JSON Parse Error: {e}")
        return {"status": "error", "message": "AI returned invalid JSON", "raw": raw_text[:500]}
    except Exception as e:
        logger.error(f"Widget Generation Error: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/generate-title")
async def generate_title(payload: dict):
    """
    Generates a short topic title for a chat session using Gemini.
    Tries multiple model versions to maximize compatibility.
    """
    import google.generativeai as genai
    from .config import settings
    import re
    
    prompt = payload.get("prompt")
    if not prompt:
        return {"title": "New Session"}
        
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    
    # List of models to try in order of preference
    models_to_try = ['gemini-2.0-flash-lite', 'gemini-2.0-flash-exp', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
    
    system_prompt = f"Summarize the following user query into a concise, 3-5 word topic title. Output ONLY the title. Do NOT use quotes. User Query: {prompt}"
    
    last_error = None

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(system_prompt)
            title = response.text.strip()
            
            # Cleanup
            title = title.replace('"', '').replace("'", "")
            title = re.sub(r'^Title:\s*', '', title, flags=re.IGNORECASE)
            title = title.strip()
            
            if title:
                return {"title": title}
                
        except Exception as e:
            last_error = e
            continue
            
    # If all models failed
    logger.error(f"Title Generation Failed (All models). Last Error: {last_error}")
    # Fallback to truncation
    return {"title": prompt[:30] + "..." if len(prompt) > 30 else prompt}


@app.post("/api/agent/check")
async def trigger_agent_check(payload: dict):
    """
    Manually triggers the 'Data Missing Agent' for a specific listing or all.
    """
    listing_id = payload.get("listing_id")
    if not listing_id:
        return {"status": "error", "message": "listing_id required"}
        
    await graph_service.generate_data_request(listing_id)
    return {"status": "success", "message": f"Agent check complete for {listing_id}"}


@app.get("/api/inbox")
async def get_inbox_messages(email: Optional[str] = None):
    """
    Fetches messages for the Inbox UI.
    """
    messages = await graph_service.get_inbox_messages(email)
    return {"messages": messages}


@app.post("/api/inbox/action")
async def handle_inbox_action(payload: dict):
    """
    Handle actions on inbox items.
    
    Payload: {"message_id": "gap_market_analysis", "action": "remind" | "ignore"}
    """
    message_id = payload.get("message_id", "")
    action = payload.get("action")
    category = payload.get("category")  # For promotion suggestions
    metadata = payload.get("metadata", {})  # For category merge suggestions
    
    if not message_id or not action:
        raise HTTPException(status_code=400, detail="message_id and action required")
    
    # Handle knowledge gap actions
    if message_id.startswith("gap_"):
        topic = message_id[4:]  # Remove "gap_" prefix
        result = await graph_service.handle_knowledge_gap_action(topic, action)
        return result
    
    # Handle promotion suggestions from learning engine
    if category and action in ["approve", "reject", "remind"]:
        result = await learning_engine.handle_promotion_action(category, action)
        return result
    
    # Handle category merge suggestions
    if action in ["merge", "link", "ignore"] and metadata.get("category_a") and metadata.get("category_b"):
        from .category_intelligence import get_category_intelligence
        cat_intel = get_category_intelligence(db)
        
        cat_a = metadata["category_a"]
        cat_b = metadata["category_b"]
        
        if action == "merge":
            success = await cat_intel.merge_categories(cat_a, cat_b)
            if success:
                # Mark message as processed
                await db.run_query(
                    "MATCH (m:Message {id: $id}) SET m.processed = true, m.action_taken = 'merged'",
                    {"id": message_id}
                )
            return {"status": "success" if success else "error", "action": "merged", "categories": [cat_a, cat_b]}
        
        elif action == "link":
            success = await cat_intel.link_categories(cat_a, cat_b)
            if success:
                await db.run_query(
                    "MATCH (m:Message {id: $id}) SET m.processed = true, m.action_taken = 'linked'",
                    {"id": message_id}
                )
            return {"status": "success" if success else "error", "action": "linked", "categories": [cat_a, cat_b]}
        
        elif action == "ignore":
            await db.run_query(
                "MATCH (m:Message {id: $id}) SET m.processed = true, m.action_taken = 'ignored'",
                {"id": message_id}
            )
            return {"status": "success", "action": "ignored"}
    
    return {"status": "error", "message": "Unknown message type"}


@app.post("/api/admin/prune-expansions")
async def prune_expansions(payload: dict = {}):
    """
    Admin endpoint to prune low-performing query expansion terms.
    
    Payload (optional):
        min_uses: int - Minimum uses before considering for pruning (default 10)
        max_miss_rate: float - Terms with hit rate below this are pruned (default 0.8)
    """
    min_uses = payload.get("min_uses", 10)
    max_miss_rate = payload.get("max_miss_rate", 0.8)
    
    try:
        pruned = await db.prune_low_performing_expansions(
            min_uses=min_uses,
            max_miss_rate=max_miss_rate
        )
        
        return {
            "status": "success",
            "pruned_count": len(pruned),
            "pruned_terms": pruned
        }
    except Exception as e:
        logger.error(f"Expansion pruning error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/admin/expansion-metrics")
async def get_expansion_metrics():
    """
    Admin endpoint to view quality metrics for query expansion caching.
    
    Returns:
        - total_expansions: Cached term count
        - avg_hit_rate: How often expansions appear in results
        - best/worst_performers: Terms ranked by effectiveness
    """
    try:
        metrics = await db.get_expansion_metrics()
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        logger.error(f"Expansion metrics error: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/admin/analyze-categories")
async def analyze_categories():
    """
    Admin endpoint to manually trigger category relationship analysis.
    Sends merge suggestions to Inbox.
    """
    try:
        from .category_intelligence import get_category_intelligence
        
        cat_intel = get_category_intelligence(db)
        relationships = await cat_intel.analyze_all_relationships()
        suggestions = await cat_intel.generate_merge_suggestions()
        
        return {
            "status": "success",
            "total_relationships_found": len(relationships),
            "merge_suggestions_sent": suggestions,
            "top_relationships": [
                {
                    "categories": [r.category_a, r.category_b],
                    "composite_score": round(r.composite_score, 3),
                    "relationship_type": r.relationship_type,
                    "signals": {
                        "document_overlap": round(r.document_overlap, 3),
                        "semantic_similarity": round(r.semantic_similarity, 3),
                        "query_cooccurrence": round(r.query_cooccurrence, 3),
                        "cross_citation": round(r.cross_citation, 3)
                    }
                }
                for r in relationships[:10]  # Top 10
            ]
        }
    except Exception as e:
        logger.error(f"Category analysis error: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/error-report")
async def submit_error_report(payload: dict):
    """
    Receives error reports from frontend and sends to Discord + Email.
    """
    import aiohttp
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    timestamp = payload.get("timestamp", "")
    user_description = payload.get("userDescription", "")
    error_message = payload.get("errorMessage", "")
    context = payload.get("context", "")
    user_agent = payload.get("userAgent", "")
    url = payload.get("url", "")
    
    # Format the report
    report_text = f"""
🚨 **Error Report** 🚨

**Time**: {timestamp}
**Context**: {context}
**URL**: {url}

**Error**: {error_message}

**User Description**:
{user_description}

**User Agent**: {user_agent}
""".strip()

    sent_to = []
    
    # Send to Discord
    if settings.DISCORD_WEBHOOK_URL:
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    settings.DISCORD_WEBHOOK_URL,
                    json={"content": report_text},
                    headers={"Content-Type": "application/json"}
                )
            sent_to.append("Discord")
        except Exception as e:
            logger.error(f"Discord webhook failed: {e}")
    
    # Send Email
    if settings.ERROR_REPORT_EMAIL and settings.SMTP_USER:
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_USER
            msg["To"] = settings.ERROR_REPORT_EMAIL
            msg["Subject"] = f"🚨 Davlon Error Report: {context or 'Unknown'}"
            
            # Plain text version
            msg.attach(MIMEText(report_text.replace("**", ""), "plain"))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            sent_to.append("Email")
        except Exception as e:
            logger.error(f"Email send failed: {e}")
    
    if not sent_to:
        logger.warning(f"Error report not sent (no channels configured): {error_message[:100]}")
    else:
        logger.info(f"Error report sent to: {', '.join(sent_to)}")
    
    return {"status": "success", "sent_to": sent_to}


# --- Static File Serving (Frontend) ---

# Mount 'public' directory to root '/'
# html=True allows '/sources' to serve 'sources.html' automatically if it existed, 
# but for specific files like 'sources.html' we usually access them directly.
# Placing this LAST ensures API routes take precedence.
app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

import google.generativeai as genai
from .config import settings
from .database import db
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .company_profile import get_profile_service, CompanyProfile

logger = logging.getLogger("davlon-rag")


@dataclass
class QueryClassification:
    """Result of multi-category query classification."""
    detected_categories: List[str]  # Categories found relevant to the query
    has_special: bool               # Whether any category is special (e.g., legal)
    unknown_topics: List[str]       # Topics mentioned but not in our categories
    query: str                      # Original query for reference


from enum import Enum

class QueryIntent(Enum):
    """
    Intent classification for adaptive retrieval strategy.
    Different intents need different amounts and types of context.
    """
    FACTUAL = "factual"           # "What is X?" → Need 1-5 precise chunks
    COMPREHENSIVE = "comprehensive" # "List all X" → Need many chunks (10-20)
    ANALYTICAL = "analytical"     # "Why did X?" → Need context + reasoning (8-12)
    COMPARATIVE = "comparative"   # "Compare X and Y" → Need multiple topics (10-15)
    TEMPORAL = "temporal"         # "When did X?" → Need time-aware search (5-8)
    DEFINITION = "definition"     # "What does X mean?" → Need 1-3 definition chunks
    SUMMARY = "summary"           # "Summarize X" → Need broad coverage (15-20)


@dataclass
class RetrievalStrategy:
    """Configuration for how to retrieve chunks based on query intent."""
    base_k: int                  # Base number of chunks to retrieve
    score_floor: float           # Minimum similarity score to include
    expand_context: bool         # Whether to fetch surrounding chunks
    prefer_recent: bool          # Prioritize newer documents
    prefer_definitions: bool     # Boost definition-type chunks


# Retrieval strategies for each intent type
RETRIEVAL_STRATEGIES = {
    QueryIntent.FACTUAL: RetrievalStrategy(
        base_k=5, score_floor=0.5, expand_context=False, 
        prefer_recent=False, prefer_definitions=False
    ),
    QueryIntent.COMPREHENSIVE: RetrievalStrategy(
        base_k=15, score_floor=0.35, expand_context=True, 
        prefer_recent=False, prefer_definitions=False
    ),
    QueryIntent.ANALYTICAL: RetrievalStrategy(
        base_k=10, score_floor=0.4, expand_context=True, 
        prefer_recent=False, prefer_definitions=False
    ),
    QueryIntent.COMPARATIVE: RetrievalStrategy(
        base_k=12, score_floor=0.4, expand_context=True, 
        prefer_recent=False, prefer_definitions=False
    ),
    QueryIntent.TEMPORAL: RetrievalStrategy(
        base_k=8, score_floor=0.4, expand_context=False, 
        prefer_recent=True, prefer_definitions=False
    ),
    QueryIntent.DEFINITION: RetrievalStrategy(
        base_k=3, score_floor=0.55, expand_context=False, 
        prefer_recent=False, prefer_definitions=True
    ),
    QueryIntent.SUMMARY: RetrievalStrategy(
        base_k=18, score_floor=0.3, expand_context=True, 
        prefer_recent=False, prefer_definitions=False
    ),
}


def classify_query_intent(query: str) -> QueryIntent:
    """
    Rule-based classification of query intent for adaptive retrieval.
    Fast and deterministic - no AI needed.
    """
    query_lower = query.lower().strip()
    
    # COMPREHENSIVE: Wants everything
    if any(phrase in query_lower for phrase in [
        "list all", "show all", "what are all", "every", "enumerate",
        "give me all", "all the", "complete list", "full list"
    ]):
        return QueryIntent.COMPREHENSIVE
    
    # SUMMARY: Wants overview
    if any(phrase in query_lower for phrase in [
        "summarize", "summary", "overview", "recap", "key points",
        "main points", "highlights", "brief", "tldr", "tl;dr"
    ]):
        return QueryIntent.SUMMARY
    
    # COMPARATIVE: Comparing things
    if any(phrase in query_lower for phrase in [
        "compare", "comparison", "difference between", "vs", "versus",
        "differ", "differences", "similarities", "better", "worse"
    ]):
        return QueryIntent.COMPARATIVE
    
    # ANALYTICAL: Wants reasoning
    if any(phrase in query_lower for phrase in [
        "why", "explain why", "how does", "reason", "cause",
        "because", "analyze", "analysis", "implications"
    ]):
        return QueryIntent.ANALYTICAL
    
    # TEMPORAL: Time-related
    if any(phrase in query_lower for phrase in [
        "when", "what date", "what time", "timeline", "history",
        "latest", "recent", "last", "newest", "oldest", "first"
    ]):
        return QueryIntent.TEMPORAL
    
    # DEFINITION: Wants meaning
    if any(phrase in query_lower for phrase in [
        "what is", "what are", "define", "definition", "meaning of",
        "what does", "means", "stands for", "refers to"
    ]):
        return QueryIntent.DEFINITION
    
    # Default to FACTUAL
    return QueryIntent.FACTUAL


# Confidence thresholds for verification
# Images (photos, diagrams, non-graph visuals) have lower threshold 
# because visual interpretation is inherently more ambiguous
CONFIDENCE_THRESHOLD_TEXT = 0.90      # Standard text content
CONFIDENCE_THRESHOLD_IMAGE = 0.75     # Images only (NOT graphs)
CONFIDENCE_THRESHOLD_TABLE = 0.90     # Tabular data
CONFIDENCE_THRESHOLD_GRAPH = 0.90     # Charts, graphs, data visualizations


# Model configurations for adaptive selection
# Models are selected based on corpus size and query complexity
@dataclass
class ModelConfig:
    """Configuration for a Gemini model."""
    name: str
    max_input_tokens: int
    max_output_tokens: int
    max_chunks: int          # Practical limit for RAG (tokens / avg_chunk_size)
    cost_per_1m_input: float # USD
    latency_tier: str        # "fast", "medium", "slow"


# Available models (ordered by capability)
GEMINI_MODELS = {
    "lite": ModelConfig(
        name="gemini-2.5-flash-lite",
        max_input_tokens=1_000_000,
        max_output_tokens=8_192,
        max_chunks=1500,      # Conservative for fast responses
        cost_per_1m_input=0.075,
        latency_tier="fast"
    ),
    "flash": ModelConfig(
        name="gemini-2.5-flash",
        max_input_tokens=1_048_576,
        max_output_tokens=65_536,
        max_chunks=1500,
        cost_per_1m_input=0.15,
        latency_tier="fast"
    ),
    "pro": ModelConfig(
        name="gemini-2.5-pro",
        max_input_tokens=1_048_576,
        max_output_tokens=65_536,
        max_chunks=1500,
        cost_per_1m_input=1.25,
        latency_tier="medium"
    ),
}


def select_model_for_corpus(total_chunks: int, query_intent: QueryIntent) -> ModelConfig:
    """
    Select the appropriate model based on corpus size and query complexity.
    
    Strategy:
    - Small corpus (<500 chunks): Use lite for speed
    - Medium corpus (500-5000): Use flash for balance
    - Large corpus (5000+): Use flash with higher K
    - Complex queries (summary, comprehensive): Consider pro
    """
    # Heavy queries might need Pro for better reasoning
    is_complex_query = query_intent in [
        QueryIntent.COMPREHENSIVE, 
        QueryIntent.SUMMARY, 
        QueryIntent.ANALYTICAL
    ]
    
    if total_chunks < 500:
        # Small corpus - lite is fine
        return GEMINI_MODELS["lite"] if not is_complex_query else GEMINI_MODELS["flash"]
    elif total_chunks < 5000:
        # Medium corpus - flash is the sweet spot
        return GEMINI_MODELS["flash"]
    else:
        # Large corpus - flash handles it, pro for complex
        return GEMINI_MODELS["flash"] if not is_complex_query else GEMINI_MODELS["pro"]


def calculate_adaptive_k(
    base_k: int, 
    total_chunks: int, 
    has_special: bool,
    model: ModelConfig
) -> int:
    """
    Calculate dynamic K based on corpus size and model capacity.
    
    Scales K with corpus to prevent information loss at scale.
    """
    # Scale factor based on corpus size
    if total_chunks < 500:
        scale = 1.0      # Small corpus - base K is fine
    elif total_chunks < 2000:
        scale = 1.5      # Medium - 50% more
    elif total_chunks < 10000:
        scale = 2.0      # Large - double
    else:
        scale = 3.0      # Very large - triple
    
    # Apply scale
    scaled_k = int(base_k * scale)
    
    # Special category boost
    if has_special:
        scaled_k = int(scaled_k * 1.5)
    
    # Clamp to model's practical limit
    max_k = min(model.max_chunks // 2, 200)  # Leave room for other context
    
    return max(3, min(scaled_k, max_k))


# Score floor for filtering low-relevance chunks
SCORE_FLOOR = 0.35  # Chunks below this are filtered out

class GeminiClient:
    """
    Self-Adapting RAG Client.
    
    Uses dynamically learned categories and company context instead of
    hardcoded domain assumptions. The system prompt adapts to the company's
    industry and terminology.
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            # Base system instruction - will be enhanced with company context
            system_instruction="You are a rigorous data auditor. For every factual claim you make, you MUST append a citation tag in the exact format: [[Source: <filename> (Page <X>)]]. If specific page info is unavailable, use [[Source: <filename>]]. Do not create a bibliography; use inline tags only."
        )
        self.embedding_model = "models/gemini-embedding-001"
        # Lite model for fast query classification
        self.classifier_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        # Profile service for company context
        self.profile_service = get_profile_service(db)

    async def _get_company_profile(self) -> Optional[CompanyProfile]:
        """Retrieves the current company profile for context-aware responses."""
        try:
            return await self.profile_service.get_or_create_profile()
        except Exception as e:
            logger.error(f"Failed to get company profile: {e}")
            return None

    async def _classify_query(self, user_query: str) -> str:
        """
        Uses AI to determine which document category is most relevant.
        
        Categories are dynamically learned from uploaded documents,
        not hardcoded. This enables the system to adapt to any industry.
        
        DEPRECATED: Use classify_query_multi() for better results.
        """
        try:
            # Get available categories from DB (learned categories)
            available_categories = await db.get_unique_categories()
            
            if len(available_categories) <= 1:
                return None  # No filtering needed if only one category
            
            # Get company context for smarter classification
            profile = await self._get_company_profile()
            industry_hint = ""
            if profile and profile.industry:
                industry_hint = f"\nNote: This is a {profile.industry} company."
            
            prompt = f"""Given this user question, which document category is MOST relevant?

Available categories: {', '.join(available_categories)}{industry_hint}

User question: "{user_query}"

Respond with ONLY the category name. If the question could apply to multiple or is unclear, respond with "general"."""

            response = await self.classifier_model.generate_content_async(prompt)
            category = response.text.strip().lower()
            
            if category in available_categories:
                logger.info(f"Query classified as: {category}")
                return category
            else:
                logger.info(f"Query classification unclear, using no filter")
                return None
        except Exception as e:
            logger.error(f"Query classification failed: {e}")
            return None

    async def expand_query_for_retrieval(self, query: str) -> tuple[str, list[str]]:
        """
        Expand query with synonyms and related terms for better retrieval.
        
        Uses Neo4j cache first, falls back to LLM on cache miss.
        Returns (expanded_query, list_of_expansion_terms) for hit tracking.
        """
        # Extract key terms from query for caching (simple approach: use whole query)
        cache_key = query.lower().strip()
        
        # Try cache first
        cached = await db.get_cached_expansion(cache_key)
        if cached:
            expansion_terms = cached["expansions"]
            expanded_query = f"{query} {', '.join(expansion_terms)}"
            logger.info(f"Cache HIT for '{cache_key[:30]}...' ({len(expansion_terms)} terms)")
            return expanded_query, expansion_terms
        
        # Cache miss - call LLM
        try:
            prompt = f"""Given this search query, generate 3-5 synonyms or related terms that might appear in business documents.

Query: "{query}"

Rules:
- Return ONLY the terms, comma-separated
- Include acronyms and their expansions (APR, ROI, etc.)
- Include formal and informal variants
- NO explanations, just terms

Example:
Query: "What is the interest rate?"
Terms: APR, annual percentage rate, lending rate, finance charge, rate of interest"""

            response = await self.classifier_model.generate_content_async(prompt)
            expanded_terms_str = response.text.strip()
            
            # Parse comma-separated terms
            expansion_terms = [t.strip() for t in expanded_terms_str.split(',') if t.strip()]
            
            # Save to cache
            if expansion_terms:
                await db.save_expansion(cache_key, expansion_terms)
                logger.info(f"Cache MISS for '{cache_key[:30]}...' - saved {len(expansion_terms)} terms")
            
            expanded_query = f"{query} {expanded_terms_str}"
            return expanded_query, expansion_terms
            
        except Exception as e:
            logger.warning(f"Query expansion failed, using original: {e}")
            return query, []


    async def classify_query_multi(self, user_query: str) -> 'QueryClassification':
        """
        Detects ALL relevant categories in a query, plus any unknown topics.
        
        Returns:
            QueryClassification with:
            - detected_categories: List of categories found in query
            - has_special: Whether any detected category is special
            - unknown_topics: Topics mentioned that don't match any category
        """
        try:
            # Get available categories from DB
            available_categories = await db.get_unique_categories()
            special_categories = await db.get_special_categories()
            
            # Get company context
            profile = await self._get_company_profile()
            industry_hint = ""
            if profile and profile.industry:
                industry_hint = f"\nNote: This is a {profile.industry} company."
            
            prompt = f"""Analyze this user question and identify:

1. ALL document categories that are relevant (from the available list)
2. Any topics mentioned that DON'T match available categories

Available categories: {', '.join(available_categories)}{industry_hint}

User question: "{user_query}"

Respond ONLY in JSON format:
{{"categories": ["category1", "category2"], "unknown_topics": ["topic_not_in_list"]}}

If no unknown topics, use empty array. If no matching categories, use ["general"]."""

            response = await self.classifier_model.generate_content_async(prompt)
            
            # Parse JSON response
            import json
            text = response.text.strip()
            # Clean potential markdown code blocks
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            
            result = json.loads(text)
            
            # Validate and filter categories
            detected = [c.lower() for c in result.get('categories', []) if c.lower() in available_categories]
            if not detected:
                detected = ['general'] if 'general' in available_categories else []
            
            unknown = result.get('unknown_topics', [])
            has_special = any(c in special_categories for c in detected)
            
            classification = QueryClassification(
                detected_categories=detected,
                has_special=has_special,
                unknown_topics=unknown,
                query=user_query
            )
            
            logger.info(f"Multi-category classification: {detected}, unknown: {unknown}, special: {has_special}")
            return classification
            
        except Exception as e:
            logger.error(f"Multi-category classification failed: {e}")
            # Fallback to empty classification
            return QueryClassification(
                detected_categories=[],
                has_special=False,
                unknown_topics=[],
                query=user_query
            )

    def _apply_special_category_tiebreaker(
        self, 
        results: List[dict], 
        detected_categories: List[str],
        special_categories: List[str]
    ) -> List[dict]:
        """
        Re-sort results using relevance-first with special category as tiebreaker.
        
        At similar relevance scores, chunks from special categories that were
        detected in the query get priority. This ensures context allocation
        favors important documents without overriding pure relevance.
        
        Approach: Relevance-First, Category-Tiebreaker
        - Primary sort: relevance score (rounded to 1 decimal for grouping)
        - Secondary sort: is this chunk from a detected special category?
        """
        # Find which categories are both detected AND special
        priority_categories = set(detected_categories) & set(special_categories)
        
        if not priority_categories:
            return results  # No special categories in query, keep original order
        
        def sort_key(result):
            score = result.get('score', 0)
            # Round score to group similar scores together
            score_bucket = round(score, 1)
            
            # Check if chunk belongs to a priority category
            chunk_category = result.get('category', '')
            is_priority = chunk_category in priority_categories
            
            # Sort by: score_bucket DESC, then is_priority DESC (True before False)
            return (-score_bucket, -int(is_priority))
        
        sorted_results = sorted(results, key=sort_key)
        logger.info(f"Applied special category tiebreaker for: {priority_categories}")
        return sorted_results

    async def _log_special_category_query(
        self, 
        query: str, 
        sources: List[str], 
        answer: str,
        categories: List[str]
    ):
        """
        Audit logging for queries that use special category sources.
        
        Creates an AuditLog node in Neo4j for compliance and accountability.
        This helps track:
        - Who asked about legal/important documents
        - What answer was generated
        - Which sources were cited
        """
        try:
            cypher = """
            CREATE (a:AuditLog {
                id: randomUUID(),
                query: $query,
                answer: $answer,
                sources: $sources,
                categories: $categories,
                timestamp: datetime(),
                type: 'special_category_query'
            })
            """
            await db.run_query(cypher, {
                "query": query,
                "answer": answer,
                "sources": sources,
                "categories": list(set(categories))  # Remove duplicates
            })
            logger.info(f"Audit log created for special category query: {categories}")
        except Exception as e:
            # Don't fail the query if audit logging fails
            logger.error(f"Failed to create audit log: {e}")

    async def upload_file(self, path: str, display_name: str):
        """Uploads a file to Gemini File API."""
        # Note: genai.upload_file is synchronous, but we wrap it in async for the interface
        # In a high-load system, offload this to a thread pool.
        file = genai.upload_file(path=path, display_name=display_name)
        return file

    async def query_with_files(self, prompt: str, file_ids: List[str]):
        """Queries Gemini with specific documents in context."""
        files = []
        for fid in file_ids:
            try:
                # Retrieve the file resource object using the ID (files/xxx)
                # This ensures we have the handle to pass to generate_content
                f = genai.get_file(fid)
                files.append(f)
            except Exception as e:
                logger.warning(f"Could not retrieve file {fid}: {e}")
        
        if not files:
            # Fallback to pure text query if files are missing?
            # Or return error. Let's try to answer without files but warn.
            pass

        # Construct request: Prompt + File Objects
        request_content = [prompt] + files
        
        response = await self.model.generate_content_async(request_content)
        
        # Parse citations (if any) - The File API doesn't structure them automatically 
        # like the notebookLM logic, but we can extract them if the prompt asks.
        # For now, return raw text.
        return {
            "text": response.text,
            "citations": [], # Future: Extract these
            "confidence": 1.0 # Trust the model for now
        }

    async def get_embedding(self, text: str, task_type="RETRIEVAL_QUERY"):
        """Generates embedding for a single string."""
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type=task_type,
            output_dimensionality=768 # Matches DB index
        )
        return result['embedding']

    def _split_by_structure(self, text: str) -> List[str]:
        """
        Splits text into verifiable atomic units:
        - Table Rows
        - List Items
        - Sentences (for paragraphs)
        """
        import re
        chunks = []
        lines = text.split('\n')
        
        current_paragraph = []
        
        def flush_paragraph():
            if current_paragraph:
                para_text = " ".join(current_paragraph).strip()
                if para_text:
                    # Split paragraph into sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para_text)
                    for s in sentences:
                        if s.strip(): chunks.append(s.strip())
                current_paragraph.clear()

        for line in lines:
            line = line.strip()
            if not line:
                flush_paragraph()
                continue
                
            # Check for Table Row (| col | col |)
            if line.startswith('|') and line.endswith('|'):
                flush_paragraph()
                # Skip separator lines
                if '---' in line: continue 
                chunks.append(line)
                continue
                
            # Check for List Item (- item, * item, 1. item)
            # Regex: Start of line, optional space, bullet (*,-,+) or digit+dot, space, content
            if re.match(r'^[\*\-\+]\s+', line) or re.match(r'^\d+\.\s+', line):
                flush_paragraph()
                chunks.append(line)
                continue
                
            # Headers
            if line.startswith('#'):
                flush_paragraph()
                # Headers are structural, usually don't need verification, but let's keep them if they contain claims
                chunks.append(line)
                continue
                
            # Otherwise, it's part of a paragraph
            current_paragraph.append(line)
            
        flush_paragraph()
        return chunks

    # ... (Rest of class) ...

    # Removed incomplete query_hybrid definition

    async def _verify_mathematically(self, answer: str, context_chunks: List[str]):
        """
        The 'Vector Judge'.
        Calculates max cosine similarity between the Answer and any of the Context Chunks.
        Returns (max_score, list_of_all_scores).
        """
        if not answer or not context_chunks:
            return 0.0, []
            
        try:
            # Embed Answer
            ans_emb = await self.get_embedding(answer, task_type="SEMANTIC_SIMILARITY")
            
            # Embed Contexts (Serial Fallback for Stability)
            ctx_embs = []
            for chunk in context_chunks:
                try:
                    c_res = genai.embed_content(
                        model=self.embedding_model,
                        content=chunk,
                        task_type="SEMANTIC_SIMILARITY",
                        output_dimensionality=768
                    )
                    if 'embedding' in c_res:
                        ctx_embs.append(c_res['embedding'])
                    else:
                        logger.warning(f"Embedding failed for chunk: {chunk[:20]}...")
                        # Append zero vector or skip?
                        # If we skip, indices won't match. 
                        # Let's append a zero vector of size 768 to maintain index alignment
                        ctx_embs.append([0.0] * 768)
                except Exception as ex:
                    logger.error(f"Embedding chunk error: {ex}")
                    ctx_embs.append([0.0] * 768)
            
            if not ctx_embs:
                return 0.0, []

            # Calculate Similarity
            # Reshape for sklearn
            A = np.array(ans_emb).reshape(1, -1)
            C = np.array(ctx_embs)
            
            # Compute similarities between Answer and ALL chunks
            # C is (N_chunks, 768)
            similarities = cosine_similarity(A, C)[0] # Flatten -> (N_chunks,)
            
            confidence_score = float(np.max(similarities))
            all_scores = [float(s) for s in similarities]
            
            return confidence_score, all_scores
            
        except Exception as e:
            logger.error(f"Vector Judge Failed: {e}")
            return 0.0, []

    async def _rewrite_sentence(self, sentence: str, context_chunks: List[str]) -> str:
        """
        Asks Gemini to rewrite a specific sentence to be strictly supported by the context.
        """
        rewrite_prompt = f"""
        TASK: Rewrite the following sentence to be 100% supported by the provided Context.
        If the sentence is completely unsupported, output "REMOVE".
        Do not add new information. Keep it concise.
        
        SENTENCE: "{sentence}"
        
        CONTEXT:
        {chr(10).join(context_chunks)}
        """
        response = await self.model.generate_content_async(rewrite_prompt)
        return response.text.strip()

    async def query_hybrid(self, user_query: str, doc_ids: list[str] = None, use_graph_expansion: bool = True):
        """
        True RAG Pipeline with Hybrid Search:
        0. Query Intent Classification (for adaptive K)
        0.5. Multi-Category Classification (detect all relevant categories + unknown topics)
        1. Hybrid Search: Vector + Graph Traversal (Neo4j)
        2. Context Injection & Generative Step
        3. Atomic Verification (Sentence-by-Sentence) with Rewrite Loop
        
        The hybrid search combines:
        - Vector similarity (semantic matching)
        - Graph traversal (structural relationships)
        
        Adaptive K selection based on query intent:
        - "What is X?" → 5 chunks (factual)
        - "List all X" → 15 chunks (comprehensive)
        - "Why did X?" → 10 chunks (analytical)
        """
        import re
        try:
            # 0. Query Intent Classification (for adaptive K)
            query_intent = classify_query_intent(user_query)
            strategy = RETRIEVAL_STRATEGIES[query_intent]
            
            # 0.5. Multi-Category Classification
            classification = await self.classify_query_multi(user_query)
            
            # Log any unknown topics detected
            if classification.unknown_topics:
                for topic in classification.unknown_topics:
                    await db.log_unknown_topic(topic, user_query)
                logger.info(f"Logged unknown topics: {classification.unknown_topics}")
            
            # Use primary category for filtering (first detected, or None)
            target_category = classification.detected_categories[0] if classification.detected_categories else None
            
            # 1. Corpus-Aware Model and K Selection
            # Count total chunks to determine corpus size
            total_chunks = await db.count_chunks()
            
            # Select model based on corpus size and query complexity
            selected_model = select_model_for_corpus(total_chunks, query_intent)
            
            # Calculate adaptive K (scales with corpus size)
            search_limit = calculate_adaptive_k(
                base_k=strategy.base_k,
                total_chunks=total_chunks,
                has_special=classification.has_special,
                model=selected_model
            )
            
            logger.info(
                f"Adaptive retrieval: intent={query_intent.value}, "
                f"corpus={total_chunks} chunks, model={selected_model.name}, "
                f"k={search_limit}"
            )
            
            # 2. Query Expansion (add synonyms for better vocabulary matching)
            expanded_query, expansion_terms = await self.expand_query_for_retrieval(user_query)
            
            # 3. Hybrid Search: Embed expanded query & Search with Graph Expansion
            query_emb = await self.get_embedding(expanded_query, task_type="RETRIEVAL_QUERY")
            
            # Use hybrid graph search for better precision
            results = await db.hybrid_graph_search(
                embedding=query_emb, 
                limit=search_limit, 
                category=target_category,
                expand_graph=use_graph_expansion and strategy.expand_context,
                temporal_boost=strategy.prefer_recent
            )
            
            # 2.5. Score Floor Filtering (remove low-relevance noise)
            original_count = len(results)
            results = [r for r in results if r.get('score', 0) >= SCORE_FLOOR]
            
            if len(results) < original_count:
                logger.info(f"Score floor filtered: {original_count} → {len(results)} chunks (floor={SCORE_FLOOR})")
            
            if not results:
                return {
                    "text": "I couldn't find any relevant information in the uploaded documents.",
                    "citations": [],
                    "confidence": 0.0
                }
            
            # Apply special category boost if detected in query
            if classification.has_special and len(results) > 1:
                special_categories = await db.get_special_categories()
                results = self._apply_special_category_tiebreaker(
                    results, 
                    classification.detected_categories, 
                    special_categories
                )

            context_text = ""
            context_chunks = []
            chunk_ids = []  # Track IDs for surrounding context lookup
            chunk_content_types = []  # Track content type for each chunk
            graph_enhanced_count = 0
            temporal_boosted_count = 0
            
            for i, res in enumerate(results):
                chunk_txt = res['text']
                src = res['source']
                content_type = res.get('content_type', 'text')
                chunk_id = res.get('chunk_id')  # For context expansion
                
                chunk_content_types.append(content_type)
                chunk_ids.append(chunk_id)
                
                # Indicate if this result was boosted by graph relationships
                graph_marker = ""
                if res.get('graph_enhanced'):
                    graph_marker = " [Graph-Enhanced]"
                    graph_enhanced_count += 1
                
                # Indicate if this result was boosted by recency
                temporal_marker = ""
                if res.get('temporal_boosted'):
                    temporal_marker = " [Recent]"
                    temporal_boosted_count += 1
                
                # Include related entity info if available
                entity_info = ""
                if res.get('related_entities') and len(res['related_entities']) > 0:
                    entity_info = f" (Related: {', '.join(res['related_entities'][:3])})"
                
                # Content type marker for transparency
                type_marker = ""
                if content_type == "image":
                    type_marker = " [Image]"
                elif content_type == "table":
                    type_marker = " [Table]"
                elif content_type == "graph":
                    type_marker = " [Graph/Chart]"
                
                context_text += f"\n[CHUNK {i+1}] (Source: {src}{type_marker}{graph_marker}{temporal_marker}{entity_info})\n{chunk_txt}\n"
                context_chunks.append(chunk_txt)
            
            # Log search quality
            if graph_enhanced_count > 0 or temporal_boosted_count > 0:
                logger.info(f"Hybrid search: {graph_enhanced_count}/{len(results)} graph-enhanced, {temporal_boosted_count}/{len(results)} temporal-boosted")
            
            # Track expansion hits for learning (which synonyms appeared in results)
            if expansion_terms:
                all_result_text = " ".join(context_chunks).lower()
                expansion_hits = {
                    term: term.lower() in all_result_text 
                    for term in expansion_terms
                }
                await db.record_expansion_hits(user_query, expansion_hits)
                hit_count = sum(1 for h in expansion_hits.values() if h)
                logger.info(f"Expansion hit tracking: {hit_count}/{len(expansion_terms)} terms found in results")
            
            # 2. Initial Generation with Company-Aware Context
            profile = await self._get_company_profile()
            
            # Build industry-aware system prompt
            company_context = ""
            if profile:
                if profile.name:
                    company_context += f"You are assisting {profile.name}"
                    if profile.industry:
                        company_context += f", a {profile.industry} company"
                    company_context += ". "
                
                # Add domain vocabulary if available
                if profile.domain_terms:
                    terms_str = ", ".join([f"{k}={v}" for k, v in list(profile.domain_terms.items())[:10]])
                    company_context += f"\n\nDomain terminology: {terms_str}"
            
            # SPECIAL CATEGORY TONE MODIFIER
            # If answering with special (e.g., legal) sources, use careful language
            special_tone_modifier = ""
            uses_special_sources = False
            if classification.has_special:
                special_categories = await db.get_special_categories()
                for res in results:
                    if res.get('category') in special_categories:
                        uses_special_sources = True
                        break
            
            if uses_special_sources:
                special_tone_modifier = """

IMPORTANT TONE GUIDANCE:
Some of your sources are from important/legal documents. When citing these:
- Use precise, verified language (avoid "might", "probably", "I think")
- Reference specific document names and dates where available
- Include verification advice: "Please verify this against the original document for critical decisions."
- Do NOT paraphrase legal/contractual terms loosely
"""
            
            system_prompt = f"""
            SYSTEM: You are a strict analyst.{' ' + company_context if company_context else ''}{special_tone_modifier}
            Use ONLY the provided Context Chunks to answer.
            If the answer is not in the context, say "I don't know".
            Always cite your sources using the format [[Source: filename]].
            
            CONTEXT:
            {context_text}
            """
            response = await self.model.generate_content_async([system_prompt, user_query])
            full_answer = response.text
            
            # 3. ATOMIC VERIFICATION (Sentence Level) with Content-Type Aware Thresholds
            # Split into sentences (simple heuristics for now)
            sentences = re.split(r'(?<=[.!?])\s+', full_answer)
            verified_sentences = []
            min_confidence = 1.0 # Track lowest score
            
            # Helper to determine confidence threshold based on content types in context
            def get_confidence_threshold(sentence: str, content_types: list) -> float:
                """
                Determine confidence threshold based on:
                1. If sentence references an image explicitly
                2. If source chunks are image-type (not graphs)
                
                Images get 75% threshold, everything else gets 90%
                """
                # Check if sentence seems to reference an image
                image_keywords = ['image', 'photo', 'picture', 'diagram', 'illustration', 
                                  'figure', 'screenshot', 'visual', 'shown in']
                sentence_lower = sentence.lower()
                references_image = any(kw in sentence_lower for kw in image_keywords)
                
                # Check if any source chunk is image type (NOT graph)
                has_image_source = 'image' in content_types
                
                # Use lower threshold only if explicitly referencing image content
                if references_image or has_image_source:
                    # But NOT if it's actually a graph/chart
                    graph_keywords = ['graph', 'chart', 'plot', 'data visualization', 'bar chart', 'pie chart', 'line graph']
                    if any(kw in sentence_lower for kw in graph_keywords):
                        return CONFIDENCE_THRESHOLD_GRAPH  # 90% for graphs
                    return CONFIDENCE_THRESHOLD_IMAGE  # 75% for images
                
                return CONFIDENCE_THRESHOLD_TEXT  # 90% for standard text
            
            for sent in sentences:
                if not sent.strip(): continue
                
                # Determine appropriate threshold for this sentence
                threshold = get_confidence_threshold(sent, chunk_content_types)
                threshold_label = "75%" if threshold == CONFIDENCE_THRESHOLD_IMAGE else "90%"
                
                # Verify
                score, scores_list = await self._verify_mathematically(sent, context_chunks)
                
                if score < threshold:
                    logger.warning(f"Sentence failed verif ({score:.2f} < {threshold_label}): '{sent}' -> Expanding context...")
                    
                    # CONTEXT EXPANSION: Try to get surrounding chunks for more context
                    expanded_chunks = list(context_chunks)  # Copy current chunks
                    context_expanded = False
                    
                    for cid in chunk_ids:
                        if cid:
                            try:
                                surrounding = await db.get_surrounding_context(cid, window=1)
                                for before_txt in surrounding.get('before', []):
                                    if before_txt and before_txt not in expanded_chunks:
                                        expanded_chunks.append(before_txt)
                                        context_expanded = True
                                for after_txt in surrounding.get('after', []):
                                    if after_txt and after_txt not in expanded_chunks:
                                        expanded_chunks.append(after_txt)
                                        context_expanded = True
                            except Exception as e:
                                logger.debug(f"Context expansion failed for {cid}: {e}")
                    
                    if context_expanded:
                        logger.info(f"Context expanded: {len(context_chunks)} -> {len(expanded_chunks)} chunks")
                        # Re-verify with expanded context
                        score, scores_list = await self._verify_mathematically(sent, expanded_chunks)
                        
                        if score >= threshold:
                            # Success with expanded context!
                            logger.info(f"Expanded context verification passed: {score:.2f}")
                            verified_sentences.append(sent)
                            continue
                    
                    # Still below threshold - try rewrite
                    logger.warning(f"Retrying with rewrite...")
                    
                    # RETRY LOOP (use expanded context if available)
                    retry_context = expanded_chunks if context_expanded else context_chunks
                    new_sent = await self._rewrite_sentence(sent, retry_context)
                    
                    if new_sent == "REMOVE":
                        continue # Skip this sentence
                        
                    # Verify Retry
                    new_score, new_scores_list = await self._verify_mathematically(new_sent, retry_context)
                    
                    if new_score < threshold:
                        logger.error(f"Retry failed ({new_score:.2f} < {threshold_label}): '{new_sent}'. Aborting message.")
                        
                        # Construct detailed failure message
                        threshold_pct = int(threshold * 100)
                        debug_lines = [
                            f"**I found relevant documents, but I could not verify the answer with >{threshold_pct}% certainty. I will not guess.**",
                            "\n**Debug Info:**",
                            f"- **Failed Sentence:** \"{sent}\"",
                        ]
                        if new_sent != sent:
                            debug_lines.append(f"- **Retried As:** \"{new_sent}\"")
                        
                        debug_lines.append(f"- **Max Confidence:** {new_score:.2f}")
                        debug_lines.append(f"- **Required Threshold:** {threshold_pct}%")
                        debug_lines.append("\n**Source Scores:**")
                        
                        # results matches context_chunks index-wise
                        for i, s_score in enumerate(new_scores_list):
                            # Handle case where results might be fewer than chunks (though loops above sync them)
                            if i < len(results):
                                src_name = results[i]['source']
                                src_type = results[i].get('content_type', 'text')
                                type_label = f" [{src_type}]" if src_type != 'text' else ""
                                debug_lines.append(f"- {s_score:.2f} vs {src_name}{type_label}")
                        
                        final_error_text = "\n".join(debug_lines)
                        
                        return {
                            "text": final_error_text,
                            "citations": [],
                            "confidence": new_score,
                            "sources_used": []
                        }
                    else:
                        logger.info(f"Retry succeeded ({new_score:.2f})")
                        verified_sentences.append(new_sent)
                        min_confidence = min(min_confidence, new_score)
                else:
                    verified_sentences.append(sent)
                    min_confidence = min(min_confidence, score)
            
            final_text = " ".join(verified_sentences)
            
            # Build legacy source warnings for footer
            # ENHANCED: Stronger warnings for special category legacy documents
            legacy_sources = []
            special_legacy_count = 0
            special_categories = await db.get_special_categories() if classification.has_special else []
            
            for r in results:
                if r.get('is_legacy'):
                    is_special_legacy = r.get('category') in special_categories
                    if is_special_legacy:
                        special_legacy_count += 1
                    
                    legacy_info = {
                        'source': r['source'],
                        'reason': r.get('status_reason', 'age_decay'),
                        'superseded_by': r.get('superseded_by'),
                        'is_special': is_special_legacy
                    }
                    legacy_sources.append(legacy_info)
            
            # Append footer warning if any legacy sources cited
            legacy_warning = None
            if legacy_sources:
                legacy_count = len(legacy_sources)
                
                # ENHANCED: Stronger message for special category legacy docs
                if special_legacy_count > 0:
                    legacy_warning = {
                        'count': legacy_count,
                        'message': f"⚠️ IMPORTANT: {special_legacy_count} source{'s' if special_legacy_count > 1 else ''} from legacy legal/important documents. Please verify this information is current before relying on it for critical decisions.",
                        'severity': 'high',
                        'details': legacy_sources
                    }
                else:
                    legacy_warning = {
                        'count': legacy_count,
                        'message': f"Note: {legacy_count} source{'s' if legacy_count > 1 else ''} from older documents.",
                        'severity': 'low',
                        'details': legacy_sources
                    }
            
            # AUDIT LOGGING: Log queries involving special category sources
            if uses_special_sources:
                await self._log_special_category_query(
                    query=user_query,
                    sources=[r['source'] for r in results],
                    answer=final_text[:500],  # Truncate for storage
                    categories=[r.get('category') for r in results if r.get('category') in special_categories]
                )
            
            # Collect categories used for learning engine
            categories_used = list(set(r.get('category') for r in results if r.get('category')))
            
            return {
                "text": final_text,
                "citations": [], 
                "confidence": min_confidence,
                "sources_used": [r['source'] for r in results],
                "categories_used": categories_used,  # NEW: for learning engine
                "legacy_warning": legacy_warning,
                "uses_special_sources": uses_special_sources
            }

        except Exception as e:
            logger.error(f"RAG Error: {e}")
            return {"text": f"Error: {str(e)}", "confidence": 0.0}

rag = GeminiClient()

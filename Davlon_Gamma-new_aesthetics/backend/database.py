from neo4j import AsyncGraphDatabase
from .config import settings
from datetime import datetime, timedelta
import math

# Temporal decay configuration
TEMPORAL_DECAY_DAYS = 365  # Documents older than this get maximum decay
TEMPORAL_DECAY_FACTOR = 0.3  # Maximum decay (30% reduction for oldest docs)

class Neo4jDriver:
    def __init__(self):
        self.driver = None
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD

    async def connect(self):
        if not self.uri or not self.password:
            print("Warning: Neo4j credentials not present. Database features will fail.")
            return

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            await self.driver.verify_connectivity()
            print("Neo4j Connected (Async)")
            await self.create_vector_index()
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")

    async def close(self):
        if self.driver:
            await self.driver.close()
            print("Neo4j Disconnected")

    async def create_vector_index(self):
        """Creates the vector index for Document Chunks if it doesn't exist."""
        # Using 768 dimensions for gemini-embedding-001 (can be scaled, but 768 is efficient)
        # Note: If we use the full 3072, we change this. Let's stick to 768 for efficiency unless requested.
        # Actually user showed doc saying 001 is "up to 3072". Let's use 768 for compatibility with standard text-embedding-004 fallback if needed, or stick to 768.
        # Wait, for gemini-embedding-001 the default is often 768. Let's check ingestion code for dimension param.
        # Database Reset/Healing: Ensure Index is fresh and correct (768 dims)
        drop_query = "DROP INDEX chunk_embeddings IF EXISTS"
        
        index_query = """
        CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
        FOR (c:Chunk)
        ON (c.embedding)
        OPTIONS {indexConfig: {
         `vector.dimensions`: 768,
         `vector.similarity_function`: 'cosine'
        }}
        """
        if not self.driver:
            print("Error: Neo4j driver not connected. Cannot create vector index.")
            return

        async with self.driver.session() as session:
            try:
                # 1. Drop old index (fixes dimension mismatches)
                await session.run(drop_query)
                print("Old Vector Index dropped (if existed).")
                
                # 2. Create new index
                await session.run(index_query)
                print("Vector Index 'chunk_embeddings' (768d) created.")
            except Exception as e:
                # Fallback or explicit error if index creation fails (e.g. community edition limitations?)
                print(f"Warning: Could not create Vector Index: {e}")

    async def run_query(self, query: str, parameters: dict = None):
        if not self.driver:
            print("Error: Neo4j driver not connected. Cannot run query.")
            return []
        async with self.driver.session() as session:
            result = await session.run(query, parameters)
            return [record.data() async for record in result]

    async def insert_chunk(
        self, 
        doc_id: str, 
        chunk_id: str, 
        text: str, 
        embedding: list, 
        source: str, 
        category: str | list = "general",  # Now accepts string OR list
        content_type: str = "text",
        position: int = 0,                  # Position within document
        prev_chunk_id: str = None           # Previous chunk for linking
    ):
        """
        Saves a text chunk with its vector embedding, categories, and content type.
        
        category can be:
        - A single string: "legal" (will be stored as ["legal"])
        - A list: ["real_estate", "legal"] 
        
        content_type options:
        - "text": Standard text content
        - "image": Image descriptions (photos, diagrams, etc.)
        - "table": Tabular data
        - "graph": Charts, graphs, data visualizations
        
        position: Chunk position within the document (0-indexed)
        prev_chunk_id: ID of previous chunk for :NEXT/:PREV linking
        """
        if not self.driver:
            print("Error: Neo4j driver not connected. Cannot insert chunk.")
            return
        
        # Normalize categories to list
        if isinstance(category, str):
            categories = [category]
        else:
            categories = list(category) if category else ["general"]
        
        # Insert chunk with position
        query = """
        MERGE (d:Document {id: $doc_id})
        MERGE (c:Chunk {id: $chunk_id})
        SET c.text = $text,
            c.embedding = $embedding,
            c.source = $source,
            c.categories = $categories,
            c.category = $categories[0],
            c.content_type = $content_type,
            c.position = $position,
            c.createdAt = datetime()
        MERGE (d)-[:HAS_CHUNK]->(c)
        """
        async with self.driver.session() as session:
            await session.run(
                query, 
                doc_id=doc_id, 
                chunk_id=chunk_id, 
                text=text, 
                embedding=embedding, 
                source=source, 
                categories=categories,
                content_type=content_type,
                position=position
            )
            
            # Create NEXT/PREV relationship if there's a previous chunk
            if prev_chunk_id:
                link_query = """
                MATCH (prev:Chunk {id: $prev_id})
                MATCH (curr:Chunk {id: $curr_id})
                MERGE (prev)-[:NEXT]->(curr)
                MERGE (curr)-[:PREV]->(prev)
                """
                await session.run(link_query, prev_id=prev_chunk_id, curr_id=chunk_id)

    async def count_chunks(self) -> int:
        """Returns total number of chunks in the database (for corpus size detection)."""
        if not self.driver:
            return 0
        query = "MATCH (c:Chunk) RETURN count(c) as total"
        async with self.driver.session() as session:
            result = await session.run(query)
            record = await result.single()
            return record["total"] if record else 0

    async def get_surrounding_context(
        self, 
        chunk_id: str, 
        window: int = 1
    ) -> dict:
        """
        Fetch chunks before and after the matched chunk for expanded context.
        
        Uses :NEXT/:PREV relationships created during ingestion.
        
        Args:
            chunk_id: The ID of the chunk to get context for
            window: How many chunks before/after to fetch (default 1)
            
        Returns:
            dict with 'before', 'main', 'after' text arrays
        """
        if not self.driver:
            return {"before": [], "main": "", "after": []}
        
        query = """
        MATCH (main:Chunk {id: $chunk_id})
        OPTIONAL MATCH (prev:Chunk)-[:NEXT*1..$window]->(main)
        OPTIONAL MATCH (main)-[:NEXT*1..$window]->(next:Chunk)
        WITH main, 
             collect(DISTINCT prev.text) as before_texts,
             collect(DISTINCT next.text) as after_texts
        RETURN before_texts, main.text as main_text, after_texts
        ORDER BY main.position
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, chunk_id=chunk_id, window=window)
                record = await result.single()
                
                if record:
                    return {
                        "before": record["before_texts"] or [],
                        "main": record["main_text"] or "",
                        "after": record["after_texts"] or []
                    }
                return {"before": [], "main": "", "after": []}
        except Exception as e:
            logger.warning(f"Failed to get surrounding context: {e}")
            return {"before": [], "main": "", "after": []}

    async def get_unique_categories(self):
        """Returns list of unique document categories in the database."""
        if not self.driver:
            return []
        query = "MATCH (c:Chunk) RETURN DISTINCT c.category as category"
        async with self.driver.session() as session:
            result = await session.run(query)
            categories = [record["category"] async for record in result if record["category"]]
            return categories if categories else ["general"]

    async def get_special_categories(self) -> list:
        """
        Returns list of categories marked as 'special' (e.g., legal).
        
        Special categories get enhanced treatment:
        - 50% chunk overlap
        - 95% citation threshold
        - Enhanced audit logging
        """
        if not self.driver:
            return ["legal"]  # Default fallback
        
        query = """
        MATCH (c:CategoryConfig)
        WHERE c.is_special = true
        RETURN c.name as name
        """
        async with self.driver.session() as session:
            result = await session.run(query)
            categories = [record["name"] async for record in result]
            # Always include 'legal' as hardcoded special
            if "legal" not in categories:
                categories.append("legal")
            return categories

    async def log_unknown_topic(self, topic: str, query: str):
        """
        Log when a user asks about a topic not in our categories.
        
        Uses LLM-based normalization to detect aliases:
        - "MVP" → "minimum_viable_product"
        - "ROI" → "return_on_investment"
        
        Tracks aliases for future quick lookup.
        """
        if not self.driver:
            return
        
        # Normalize the topic (may detect aliases)
        normalized = await self._normalize_topic(topic)
        
        cypher = """
        MERGE (t:UnknownTopic {name: $topic})
        ON CREATE SET 
            t.first_seen = datetime(), 
            t.count = 1,
            t.notified = false,
            t.aliases = []
        ON MATCH SET 
            t.count = t.count + 1, 
            t.last_seen = datetime()
        
        CREATE (q:QueryLog {
            text: $query, 
            timestamp: datetime()
        })
        MERGE (q)-[:MENTIONED]->(t)
        """
        
        async with self.driver.session() as session:
            await session.run(cypher, topic=normalized, query=query)

    async def _normalize_topic(self, topic: str) -> str:
        """
        Normalize a topic name, detecting if it's an alias of an existing topic.
        
        Uses LLM to detect acronyms and synonyms:
        - "MVP" → matches existing "minimum_viable_product"
        - "Minimum Viable Product" → normalized to "minimum_viable_product"
        """
        import google.generativeai as genai
        
        # First, get existing unknown topics
        existing_topics = await self._get_existing_unknown_topics()
        
        if not existing_topics:
            # No existing topics, just normalize the string
            return topic.lower().replace(" ", "_").replace("-", "_")
        
        # Check quick alias lookup first
        for existing in existing_topics:
            aliases = existing.get('aliases', []) or []
            if topic.lower() in [a.lower() for a in aliases]:
                return existing['name']
        
        # Use LLM to check for semantic match
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            prompt = f"""Is "{topic}" an acronym, abbreviation, or synonym for any of these existing topics?

Existing topics: {[t['name'] for t in existing_topics]}

Rules:
- "MVP" matches "minimum_viable_product"
- "ROI" matches "return_on_investment"  
- "Customer Feedback" matches "customer_feedback"
- Be generous with matching - if there's a reasonable connection, match it

If there's a match, respond with ONLY the matching topic name.
If no match, respond with "NEW".
"""
            
            response = await model.generate_content_async(prompt)
            result = response.text.strip().lower()
            
            existing_names = [t['name'].lower() for t in existing_topics]
            
            if result != "new" and result in existing_names:
                # Store this as an alias for future quick lookup
                await self._add_topic_alias(result, topic)
                return result
            
        except Exception as e:
            # Log but don't fail - fall back to basic normalization
            print(f"LLM normalization failed: {e}")
        
        # No match found - normalize and return as new topic
        return topic.lower().replace(" ", "_").replace("-", "_")

    async def _get_existing_unknown_topics(self) -> list:
        """Get all existing unknown topics with their aliases."""
        if not self.driver:
            return []
        
        query = """
        MATCH (t:UnknownTopic)
        RETURN t.name as name, t.aliases as aliases
        """
        
        async with self.driver.session() as session:
            result = await session.run(query)
            return [record.data() async for record in result]

    async def _add_topic_alias(self, topic_name: str, alias: str):
        """Add an alias to an existing unknown topic."""
        if not self.driver:
            return
        
        query = """
        MATCH (t:UnknownTopic {name: $topic})
        SET t.aliases = COALESCE(t.aliases, []) + $alias
        """
        
        async with self.driver.session() as session:
            await session.run(query, topic=topic_name, alias=alias)

    async def check_knowledge_gaps(self, threshold: int = 3, days: int = 7) -> list:
        """
        Find unknown topics that have been mentioned frequently.
        
        Args:
            threshold: Minimum mentions to trigger alert
            days: Look back period
            
        Returns:
            List of dicts with topic name, count, and example queries
        """
        if not self.driver:
            return []
        
        query = """
        MATCH (t:UnknownTopic)
        WHERE t.count >= $threshold 
        AND t.last_seen > datetime() - duration({days: $days})
        AND (NOT t.notified OR t.notified = false)
        OPTIONAL MATCH (q:QueryLog)-[:MENTIONED]->(t)
        WITH t, COLLECT(q.text)[0..3] as examples
        RETURN t.name as topic, t.count as mentions, examples
        ORDER BY t.count DESC
        LIMIT 5
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, threshold=threshold, days=days)
            return [record.data() async for record in result]

    async def mark_topic_notified(self, topic: str):
        """Mark an unknown topic as having been notified to admin."""
        if not self.driver:
            return
        
        query = """
        MATCH (t:UnknownTopic {name: $topic})
        SET t.notified = true, t.notified_at = datetime()
        """
        
        async with self.driver.session() as session:
            await session.run(query, topic=topic)

    async def vector_search(self, embedding: list, limit: int = 5, category: str = None):
        """Finds chunks similar to the query embedding, optionally filtered by category."""
        if not self.driver:
            print("Error: Neo4j driver not connected. Cannot perform vector search.")
            return []
        
        if category:
            # Filtered search: get more results, then filter, then limit
            query = """
            CALL db.index.vector.queryNodes('chunk_embeddings', $search_limit, $embedding)
            YIELD node, score
            WHERE node.category = $category
            RETURN node.text as text, node.source as source, node.category as category, score
            LIMIT $limit
            """
            async with self.driver.session() as session:
                result = await session.run(query, search_limit=limit*4, limit=limit, embedding=embedding, category=category)
                return [record.data() async for record in result]
        else:
            # Unfiltered search
            query = """
            CALL db.index.vector.queryNodes('chunk_embeddings', $limit, $embedding)
            YIELD node, score
            RETURN node.text as text, node.source as source, node.category as category, score
            """
            async with self.driver.session() as session:
                result = await session.run(query, limit=limit, embedding=embedding)
                return [record.data() async for record in result]

    async def hybrid_graph_search(
        self, 
        embedding: list, 
        limit: int = 5, 
        category: str = None,
        expand_graph: bool = True,
        temporal_boost: bool = True  # NEW: Prioritize recent documents
    ):
        """
        Hybrid Search: Combines vector similarity with graph traversal + temporal awareness.
        
        1. Vector search finds semantically similar chunks (candidates)
        2. Graph traversal expands to related entities and sibling chunks
        3. Temporal decay applied to older documents (configurable)
        4. Re-ranking based on combined vector + graph + temporal relevance
        
        This provides more precise retrieval by leveraging structural relationships
        and document recency, not just semantic similarity.
        """
        if not self.driver:
            print("Error: Neo4j driver not connected. Cannot perform hybrid search.")
            return []
        
        if not expand_graph:
            # Fallback to standard vector search
            return await self.vector_search(embedding, limit, category)
        
        # Phase 1: Vector search for candidate chunks (get more than needed)
        # Include content_type, createdAt, and document status for lifecycle-aware processing
        candidate_limit = limit * 4
        
        if category:
            vector_query = """
            CALL db.index.vector.queryNodes('chunk_embeddings', $search_limit, $embedding)
            YIELD node, score
            WHERE node.category = $category
            OPTIONAL MATCH (d:Document)-[:HAS_CHUNK]->(node)
            WITH node, score, d
            WHERE d.status IS NULL OR d.status <> 'archived'
            RETURN node as chunk, score, node.id as chunk_id, node.text as text, node.source as source, 
                   node.category as category, node.content_type as content_type,
                   node.createdAt as created_at,
                   COALESCE(d.status, 'active') as doc_status,
                   COALESCE(d.permanence_score, 0.5) as permanence_score,
                   d.superseded_by as superseded_by,
                   d.status_reason as status_reason
            LIMIT $candidate_limit
            """
        else:
            vector_query = """
            CALL db.index.vector.queryNodes('chunk_embeddings', $candidate_limit, $embedding)
            YIELD node, score
            OPTIONAL MATCH (d:Document)-[:HAS_CHUNK]->(node)
            WITH node, score, d
            WHERE d.status IS NULL OR d.status <> 'archived'
            RETURN node as chunk, score, node.id as chunk_id, node.text as text, node.source as source, 
                   node.category as category, node.content_type as content_type,
                   node.createdAt as created_at,
                   COALESCE(d.status, 'active') as doc_status,
                   COALESCE(d.permanence_score, 0.5) as permanence_score,
                   d.superseded_by as superseded_by,
                   d.status_reason as status_reason
            """
        
        async with self.driver.session() as session:
            # Get vector candidates
            if category:
                result = await session.run(
                    vector_query, 
                    search_limit=candidate_limit * 2, 
                    candidate_limit=candidate_limit, 
                    embedding=embedding, 
                    category=category
                )
            else:
                result = await session.run(
                    vector_query, 
                    candidate_limit=candidate_limit, 
                    embedding=embedding
                )
            
            candidates = [record.data() async for record in result]
            
            if not candidates:
                return []
            
            # Phase 2: Graph expansion - find related chunks through shared entities/documents
            # Get the sources from top candidates for expansion
            top_sources = list(set([c['source'] for c in candidates[:limit]]))
            
            expansion_query = """
            // Find chunks from same documents as our top candidates
            // Now includes document status for lifecycle-aware processing
            MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
            WHERE d.name IN $sources
            WITH c, d, 0.7 as graph_boost
            
            // Also find chunks linked to same entities as our candidates
            OPTIONAL MATCH (e)-[r]->(c) WHERE NOT e:Document
            
            RETURN DISTINCT 
                c.text as text, 
                c.source as source, 
                c.category as category,
                c.content_type as content_type,
                graph_boost,
                COALESCE(d.status, 'active') as doc_status,
                COALESCE(d.permanence_score, 0.5) as permanence_score,
                d.superseded_by as superseded_by,
                d.status_reason as status_reason,
                labels(e)[0] as related_entity_type
            LIMIT $expansion_limit
            """
            
            try:
                expansion_result = await session.run(
                    expansion_query, 
                    sources=top_sources,
                    expansion_limit=limit * 2
                )
                expanded_chunks = [record.data() async for record in expansion_result]
            except Exception as e:
                # Graph expansion failed, continue with vector results only
                print(f"Graph expansion warning: {e}")
                expanded_chunks = []
            
            # Phase 3: Merge and re-rank results with temporal decay
            # Create a map of text -> result for deduplication
            result_map = {}
            
            def calculate_temporal_boost(created_at_str):
                """Calculate temporal boost based on document age."""
                if not created_at_str or not temporal_boost:
                    return 0.0
                try:
                    # Neo4j datetime comes as string or datetime object
                    if hasattr(created_at_str, 'to_native'):
                        created_at = created_at_str.to_native()
                    else:
                        created_at = datetime.fromisoformat(str(created_at_str).replace('Z', '+00:00'))
                    
                    now = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
                    age_days = (now - created_at).days
                    
                    # Linear decay: 0 days = 0.3 boost, 365+ days = 0 boost
                    if age_days <= 0:
                        return TEMPORAL_DECAY_FACTOR
                    elif age_days >= TEMPORAL_DECAY_DAYS:
                        return 0.0
                    else:
                        return TEMPORAL_DECAY_FACTOR * (1 - age_days / TEMPORAL_DECAY_DAYS)
                except Exception:
                    return 0.0
            
            # Add vector candidates with their scores
            for c in candidates:
                text = c['text']
                if text not in result_map:
                    temporal = calculate_temporal_boost(c.get('created_at'))
                    doc_status = c.get('doc_status', 'active')
                    
                    # Apply legacy decay (90% reduction for legacy docs)
                    legacy_decay = 0.9 if doc_status == 'legacy' else 0.0
                    
                    result_map[text] = {
                        'text': text,
                        'source': c['source'],
                        'category': c['category'],
                        'content_type': c.get('content_type', 'text'),
                        'score': c['score'],
                        'vector_score': c['score'],
                        'graph_boost': 0.0,
                        'temporal_boost': temporal,
                        'legacy_decay': legacy_decay,
                        'doc_status': doc_status,
                        'superseded_by': c.get('superseded_by'),
                        'status_reason': c.get('status_reason'),
                        'related_entities': []
                    }
            
            # Add graph-expanded chunks with boost (now includes status fields)
            for ec in expanded_chunks:
                text = ec['text']
                doc_status = ec.get('doc_status', 'active')
                legacy_decay = 0.9 if doc_status == 'legacy' else 0.0
                
                if text in result_map:
                    # Boost existing result
                    result_map[text]['graph_boost'] = ec.get('graph_boost', 0.5)
                    if ec.get('related_entity_type'):
                        result_map[text]['related_entities'].append(ec['related_entity_type'])
                else:
                    # Add new result from graph expansion with full status info
                    result_map[text] = {
                        'text': text,
                        'source': ec['source'],
                        'category': ec['category'],
                        'content_type': ec.get('content_type', 'text'),
                        'score': 0.5,  # Base score for graph-found results
                        'vector_score': 0.0,
                        'graph_boost': ec.get('graph_boost', 0.5),
                        'temporal_boost': 0.0,
                        'legacy_decay': legacy_decay,
                        'doc_status': doc_status,
                        'superseded_by': ec.get('superseded_by'),
                        'status_reason': ec.get('status_reason'),
                        'related_entities': [ec.get('related_entity_type')] if ec.get('related_entity_type') else []
                    }
            
            # Calculate final scores: vector_score + graph_boost + temporal_boost - legacy_decay
            for key in result_map:
                r = result_map[key]
                legacy_decay = r.get('legacy_decay', 0.0)
                r['final_score'] = r['vector_score'] + r['graph_boost'] + r['temporal_boost'] - legacy_decay
            
            # Sort by final score and return top results
            sorted_results = sorted(
                result_map.values(), 
                key=lambda x: x['final_score'], 
                reverse=True
            )[:limit]
            
            # Clean up internal fields and include legacy status for warnings
            final_results = []
            for r in sorted_results:
                final_results.append({
                    'text': r['text'],
                    'source': r['source'],
                    'category': r['category'],
                    'content_type': r.get('content_type', 'text'),
                    'score': r['final_score'],
                    'graph_enhanced': r['graph_boost'] > 0,
                    'temporal_boosted': r['temporal_boost'] > 0,
                    'related_entities': list(set(r['related_entities'])),
                    # Legacy info for citation warnings
                    'is_legacy': r.get('doc_status') == 'legacy',
                    'legacy_reason': r.get('status_reason'),
                    'superseded_by': r.get('superseded_by')
                })
            
            return final_results

    def get_session(self):
        # Returns an async session context manager
        if not self.driver:
            raise Exception("Neo4j Driver is not connected. Check your NEO4J_URI/PASSWORD credentials.")
        return self.driver.session()

    # =========================================================================
    # ADAPTIVE LEARNING SYSTEM
    # =========================================================================

    async def create_signal(
        self, 
        category: str, 
        signal_type: str, 
        value: float,
        decay_rate: float = 0.05,
        metadata: dict = None
    ):
        """
        Create a learning signal for a category.
        
        Signal types: query, citation_trust, correction, followup_required, admin_rejection
        """
        if not self.driver:
            return
        
        query = """
        MERGE (c:CategoryConfig {name: $category})
        ON CREATE SET c.observation_start = datetime()
        
        CREATE (s:Signal {
            id: randomUUID(),
            type: $type,
            value: $value,
            decay_rate: $decay_rate,
            timestamp: datetime(),
            metadata: $metadata
        })
        MERGE (c)-[:HAS_SIGNAL]->(s)
        """
        
        async with self.driver.session() as session:
            await session.run(query, {
                "category": category,
                "type": signal_type,
                "value": value,
                "decay_rate": decay_rate,
                "metadata": metadata or {}
            })

    async def get_category_signals(self, category: str, days: int = 30) -> list:
        """Get recent signals for a category."""
        if not self.driver:
            return []
        
        query = """
        MATCH (c:CategoryConfig {name: $category})-[:HAS_SIGNAL]->(s:Signal)
        WHERE s.timestamp > datetime() - duration({days: $days})
        RETURN s.type as type, s.value as value, s.decay_rate as decay_rate, 
               s.timestamp as timestamp
        ORDER BY s.timestamp DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"category": category, "days": days})
            return [record.data() async for record in result]

    async def calculate_importance_score(self, category: str) -> float:
        """
        Calculate time-decayed importance score for a category.
        Uses exponential decay: signal_weight * e^(-λ * days_old)
        """
        if not self.driver:
            return 0.0
        
        signals = await self.get_category_signals(category, days=30)
        
        if not signals:
            return 0.0
        
        score = 0.0
        now = datetime.now()
        
        # Signal type weights
        weights = {
            "query": 0.1,
            "citation_trust": 0.3,
            "correction": -0.4,
            "followup_required": -0.2,
            "admin_rejection": -0.3
        }
        
        for signal in signals:
            signal_type = signal['type']
            base_weight = weights.get(signal_type, 0.1)
            
            # Calculate age in days
            timestamp = signal['timestamp']
            if hasattr(timestamp, 'to_native'):
                timestamp = timestamp.to_native()
            age_days = (now - timestamp.replace(tzinfo=None)).days if timestamp else 0
            
            # Apply exponential decay
            decay_rate = signal.get('decay_rate', 0.05)
            decay = math.exp(-decay_rate * age_days)
            
            contribution = base_weight * signal['value'] * decay
            score += contribution
        
        return min(max(score, 0.0), 1.0)  # Clamp to [0, 1]

    async def get_all_categories(self) -> list:
        """Get all category configs for promotion checking."""
        if not self.driver:
            return []
        
        query = """
        MATCH (c:CategoryConfig)
        RETURN c.name as name, c.is_special as is_special, 
               c.observation_start as observation_start,
               c.rejection_cooldown as rejection_cooldown
        """
        
        async with self.driver.session() as session:
            result = await session.run(query)
            categories = []
            async for record in result:
                data = record.data()
                # Convert Neo4j datetime if needed
                obs_start = data.get('observation_start')
                if obs_start and hasattr(obs_start, 'to_native'):
                    data['observation_start'] = obs_start.to_native()
                cooldown = data.get('rejection_cooldown')
                if cooldown and hasattr(cooldown, 'to_native'):
                    data['rejection_cooldown'] = cooldown.to_native()
                categories.append(data)
            return categories

    async def promote_category(self, category: str):
        """Promote a category to special status."""
        if not self.driver:
            return
        
        query = """
        MERGE (c:CategoryConfig {name: $category})
        SET c.is_special = true,
            c.promoted_at = datetime()
        """
        
        async with self.driver.session() as session:
            await session.run(query, {"category": category})
        
        print(f"Category '{category}' promoted to special status")

    async def create_inbox_message(
        self,
        subject: str,
        body: str,
        msg_type: str,
        metadata: dict = None,
        actions: list = None
    ):
        """Create an inbox message for admin notification."""
        if not self.driver:
            return
        
        query = """
        CREATE (m:Message {
            id: randomUUID(),
            subject: $subject,
            body: $body,
            type: $type,
            metadata: $metadata,
            actions: $actions,
            timestamp: datetime(),
            read: false
        })
        """
        
        import json
        async with self.driver.session() as session:
            await session.run(query, {
                "subject": subject,
                "body": body,
                "type": msg_type,
                "metadata": json.dumps(metadata or {}),
                "actions": json.dumps(actions or [])
            })

    async def count_category_signals(self, category: str) -> int:
        """Count total signals for confidence calculation."""
        if not self.driver:
            return 0
        
        query = """
        MATCH (c:CategoryConfig {name: $category})-[:HAS_SIGNAL]->(s:Signal)
        RETURN count(s) as count
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"category": category})
            record = await result.single()
            return record["count"] if record else 0

    # =========================================================================
    # TERM EXPANSION CACHING
    # =========================================================================

    async def get_cached_expansion(self, term: str) -> dict | None:
        """
        Retrieve cached expansion for a query term.
        
        Returns:
            dict with 'expansions' list and 'stats', or None if not cached
        """
        if not self.driver:
            return None
        
        # Normalize term for lookup
        normalized_term = term.lower().strip()
        
        query = """
        MATCH (te:TermExpansion {term: $term})
        SET te.times_used = COALESCE(te.times_used, 0) + 1,
            te.last_used = datetime()
        RETURN te.expansions as expansions, 
               te.expansion_stats as stats,
               te.times_used as times_used
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, term=normalized_term)
            record = await result.single()
            
            if record and record["expansions"]:
                import json
                stats = {}
                if record["stats"]:
                    try:
                        stats = json.loads(record["stats"])
                    except:
                        pass
                
                return {
                    "expansions": record["expansions"],
                    "stats": stats,
                    "times_used": record["times_used"]
                }
        
        return None

    async def save_expansion(self, term: str, expansions: list[str]):
        """
        Store a new term expansion in Neo4j.
        
        Args:
            term: The normalized query term
            expansions: List of synonym/related terms
        """
        if not self.driver or not expansions:
            return
        
        normalized_term = term.lower().strip()
        
        # Initialize stats for each expansion term
        import json
        initial_stats = {exp: {"hits": 0, "uses": 0} for exp in expansions}
        
        query = """
        MERGE (te:TermExpansion {term: $term})
        ON CREATE SET 
            te.expansions = $expansions,
            te.expansion_stats = $stats,
            te.created_at = datetime(),
            te.times_used = 1,
            te.last_used = datetime()
        ON MATCH SET
            te.expansions = $expansions,
            te.expansion_stats = $stats,
            te.updated_at = datetime()
        """
        
        async with self.driver.session() as session:
            await session.run(
                query, 
                term=normalized_term, 
                expansions=expansions,
                stats=json.dumps(initial_stats)
            )

    async def record_expansion_hits(
        self, 
        term: str, 
        expansion_hits: dict[str, bool]
    ):
        """
        Track which expansion terms appeared in retrieved results.
        
        Args:
            term: The original query term
            expansion_hits: Dict of {expansion_term: was_found_in_results}
        """
        if not self.driver:
            return
        
        normalized_term = term.lower().strip()
        
        # Get current stats
        query_get = """
        MATCH (te:TermExpansion {term: $term})
        RETURN te.expansion_stats as stats
        """
        
        async with self.driver.session() as session:
            result = await session.run(query_get, term=normalized_term)
            record = await result.single()
            
            if not record or not record["stats"]:
                return
            
            import json
            try:
                stats = json.loads(record["stats"])
            except:
                return
            
            # Update stats for each expansion term
            for exp_term, was_hit in expansion_hits.items():
                if exp_term in stats:
                    stats[exp_term]["uses"] += 1
                    if was_hit:
                        stats[exp_term]["hits"] += 1
            
            # Save updated stats
            query_update = """
            MATCH (te:TermExpansion {term: $term})
            SET te.expansion_stats = $stats
            """
            await session.run(query_update, term=normalized_term, stats=json.dumps(stats))

    async def prune_low_performing_expansions(
        self, 
        min_uses: int = 10, 
        max_miss_rate: float = 0.8
    ) -> list[dict]:
        """
        Remove expansion terms that rarely appear in results.
        
        Args:
            min_uses: Minimum times an expansion must be used before pruning
            max_miss_rate: If hit_rate < (1 - max_miss_rate), prune it
        
        Returns:
            List of pruned terms with their stats
        """
        if not self.driver:
            return []
        
        pruned = []
        
        query = """
        MATCH (te:TermExpansion)
        WHERE te.times_used >= $min_uses
        RETURN te.term as term, te.expansions as expansions, te.expansion_stats as stats
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, min_uses=min_uses)
            records = [record.data() async for record in result]
            
            import json
            
            for record in records:
                term = record["term"]
                expansions = record["expansions"] or []
                stats_str = record["stats"]
                
                if not stats_str:
                    continue
                
                try:
                    stats = json.loads(stats_str)
                except:
                    continue
                
                # Find terms to prune
                new_expansions = []
                for exp in expansions:
                    exp_stats = stats.get(exp, {})
                    uses = exp_stats.get("uses", 0)
                    hits = exp_stats.get("hits", 0)
                    
                    if uses >= min_uses:
                        hit_rate = hits / uses if uses > 0 else 0
                        if hit_rate < (1 - max_miss_rate):
                            # Prune this term
                            pruned.append({
                                "parent_term": term,
                                "expansion": exp,
                                "hit_rate": hit_rate,
                                "uses": uses
                            })
                            del stats[exp]
                            continue
                    
                    new_expansions.append(exp)
                
                # Update if anything was pruned
                if len(new_expansions) < len(expansions):
                    update_query = """
                    MATCH (te:TermExpansion {term: $term})
                    SET te.expansions = $expansions,
                        te.expansion_stats = $stats,
                        te.last_pruned = datetime()
                    """
                    await session.run(
                        update_query, 
                        term=term, 
                        expansions=new_expansions,
                        stats=json.dumps(stats)
                    )
        
        return pruned

    async def get_expansion_metrics(self) -> dict:
        """
        Calculate aggregate quality metrics for query expansions.
        
        Returns:
            dict with:
            - total_expansions: Total cached term expansions
            - total_uses: Sum of all uses
            - avg_hit_rate: Average hit rate across all terms
            - best_performers: Top 5 terms by hit rate
            - worst_performers: Bottom 5 terms by hit rate (candidates for pruning)
            - cache_hit_rate: % of queries that hit cache vs LLM
        """
        if not self.driver:
            return {}
        
        query = """
        MATCH (te:TermExpansion)
        RETURN te.term as term, 
               te.times_used as uses, 
               te.expansion_stats as stats,
               te.created_at as created
        ORDER BY te.times_used DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query)
            records = [record.data() async for record in result]
        
        if not records:
            return {
                "total_expansions": 0,
                "total_uses": 0,
                "avg_hit_rate": 0,
                "best_performers": [],
                "worst_performers": [],
                "cache_hit_rate": 0
            }
        
        import json
        
        total_uses = 0
        all_hit_rates = []
        term_metrics = []
        
        for record in records:
            term = record["term"]
            uses = record["uses"] or 0
            total_uses += uses
            
            stats_str = record["stats"]
            if not stats_str:
                continue
            
            try:
                stats = json.loads(stats_str)
            except:
                continue
            
            # Calculate hit rate for this term
            term_hits = 0
            term_uses = 0
            for exp_term, exp_stats in stats.items():
                term_hits += exp_stats.get("hits", 0)
                term_uses += exp_stats.get("uses", 0)
            
            hit_rate = term_hits / term_uses if term_uses > 0 else 0
            all_hit_rates.append(hit_rate)
            
            term_metrics.append({
                "term": term[:50],  # Truncate long terms
                "uses": uses,
                "hit_rate": round(hit_rate, 3),
                "expansion_count": len(stats)
            })
        
        # Sort for best/worst
        sorted_by_rate = sorted(term_metrics, key=lambda x: x["hit_rate"], reverse=True)
        
        avg_hit_rate = sum(all_hit_rates) / len(all_hit_rates) if all_hit_rates else 0
        
        return {
            "total_expansions": len(records),
            "total_uses": total_uses,
            "avg_hit_rate": round(avg_hit_rate, 3),
            "best_performers": sorted_by_rate[:5],
            "worst_performers": sorted_by_rate[-5:][::-1] if len(sorted_by_rate) > 5 else [],
            "cache_hit_rate": round((total_uses - len(records)) / total_uses, 3) if total_uses > 0 else 0
        }

# Global instance
db = Neo4jDriver()


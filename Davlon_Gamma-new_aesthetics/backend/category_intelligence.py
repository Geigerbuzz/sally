"""
Category Intelligence Module

Comprehensive category relationship analysis using multiple signals:
1. Document co-occurrence (which categories appear together)
2. Centroid embeddings (semantic similarity of category contents)
3. Query co-reference (categories queried in same sessions)
4. Cross-citation (documents in one category reference another)

All signals feed into a composite similarity score, with merge suggestions
sent to Inbox for human approval.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json

logger = logging.getLogger("davlon-category-intelligence")


@dataclass
class CategoryRelationship:
    """Represents a relationship between two categories."""
    category_a: str
    category_b: str
    
    # Individual signal scores (0-1)
    document_overlap: float      # How often they co-tag documents
    semantic_similarity: float   # Cosine similarity of centroids
    query_cooccurrence: float    # How often queried together
    cross_citation: float        # Documents reference each other
    
    # Composite
    composite_score: float
    relationship_type: str  # "merge_candidate", "parent_child", "sibling", "unrelated"
    confidence: float
    evidence_count: int


class CategoryIntelligence:
    """
    Analyzes category relationships using multi-signal fusion.
    
    Design Principles:
    - No hard-coded relationships - all discovered from data
    - Human-in-the-loop - suggestions require approval
    - Time-aware - recent signals weighted more
    - Explainable - every suggestion includes evidence
    """
    
    def __init__(self, db):
        self.db = db
    
    # ==================== SIGNAL 1: Document Co-occurrence ====================
    
    async def calculate_document_overlap(self) -> Dict[Tuple[str, str], float]:
        """
        Find category pairs that frequently appear on the same documents.
        
        Returns dict of (cat_a, cat_b) -> overlap_score (0-1)
        """
        query = """
        // Get all documents with their categories
        MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
        WHERE c.category IS NOT NULL
        WITH d, collect(DISTINCT c.category) as categories
        WHERE size(categories) > 1
        
        // Generate pairs
        UNWIND range(0, size(categories)-2) as i
        UNWIND range(i+1, size(categories)-1) as j
        WITH categories[i] as cat_a, categories[j] as cat_b, d
        
        // Count co-occurrences
        WITH cat_a, cat_b, count(d) as overlap_count
        
        // Get total docs per category for normalization
        OPTIONAL MATCH (d1:Document)-[:HAS_CHUNK]->(c1:Chunk {category: cat_a})
        WITH cat_a, cat_b, overlap_count, count(DISTINCT d1) as total_a
        
        OPTIONAL MATCH (d2:Document)-[:HAS_CHUNK]->(c2:Chunk {category: cat_b})
        WITH cat_a, cat_b, overlap_count, total_a, count(DISTINCT d2) as total_b
        
        // Jaccard-style similarity: overlap / (a + b - overlap)
        WITH cat_a, cat_b, overlap_count, total_a, total_b,
             toFloat(overlap_count) / (total_a + total_b - overlap_count) as jaccard
        WHERE jaccard > 0.1  // Filter noise
        
        RETURN cat_a, cat_b, overlap_count, jaccard
        ORDER BY jaccard DESC
        LIMIT 50
        """
        
        try:
            results = await self.db.run_query(query)
            overlaps = {}
            for r in results:
                key = tuple(sorted([r['cat_a'], r['cat_b']]))
                overlaps[key] = r['jaccard']
            return overlaps
        except Exception as e:
            logger.error(f"Document overlap calculation failed: {e}")
            return {}
    
    # ==================== SIGNAL 2: Semantic Similarity (Centroids) ====================
    
    async def calculate_category_centroids(self) -> Dict[str, List[float]]:
        """
        Calculate the centroid (average embedding) for each category.
        """
        query = """
        MATCH (c:Chunk)
        WHERE c.category IS NOT NULL AND c.embedding IS NOT NULL
        WITH c.category as category, c.embedding as embedding
        WITH category, collect(embedding) as embeddings
        WHERE size(embeddings) >= 3  // Need minimum docs
        
        // Calculate centroid (average of all embeddings)
        WITH category, embeddings,
             [i IN range(0, size(embeddings[0])-1) | 
              reduce(sum = 0.0, e IN embeddings | sum + e[i]) / size(embeddings)
             ] as centroid
        
        RETURN category, centroid
        """
        
        try:
            results = await self.db.run_query(query)
            return {r['category']: r['centroid'] for r in results}
        except Exception as e:
            logger.error(f"Centroid calculation failed: {e}")
            return {}
    
    async def calculate_semantic_similarity(self, centroids: Dict[str, List[float]]) -> Dict[Tuple[str, str], float]:
        """
        Calculate pairwise cosine similarity between category centroids.
        """
        import math
        
        def cosine_sim(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)
        
        categories = list(centroids.keys())
        similarities = {}
        
        for i, cat_a in enumerate(categories):
            for cat_b in categories[i+1:]:
                sim = cosine_sim(centroids[cat_a], centroids[cat_b])
                if sim > 0.5:  # Only track significant similarity
                    key = tuple(sorted([cat_a, cat_b]))
                    similarities[key] = sim
        
        return similarities
    
    # ==================== SIGNAL 3: Query Co-occurrence ====================
    
    async def calculate_query_cooccurrence(self) -> Dict[Tuple[str, str], float]:
        """
        Find categories that are frequently queried together in the same session.
        """
        query = """
        // Get queries with their detected categories
        MATCH (q:Query)
        WHERE q.detected_categories IS NOT NULL
        WITH q, apoc.convert.fromJsonList(q.detected_categories) as categories
        WHERE size(categories) > 1
        
        // Generate pairs
        UNWIND range(0, size(categories)-2) as i
        UNWIND range(i+1, size(categories)-1) as j
        WITH categories[i] as cat_a, categories[j] as cat_b
        
        // Count co-queries
        WITH cat_a, cat_b, count(*) as coquery_count
        WHERE coquery_count >= 3  // Minimum threshold
        
        // Normalize by total queries
        MATCH (q2:Query)
        WITH cat_a, cat_b, coquery_count, count(q2) as total_queries
        
        RETURN cat_a, cat_b, coquery_count, 
               toFloat(coquery_count) / total_queries as normalized_score
        ORDER BY normalized_score DESC
        LIMIT 30
        """
        
        try:
            results = await self.db.run_query(query)
            return {
                tuple(sorted([r['cat_a'], r['cat_b']])): r['normalized_score']
                for r in results
            }
        except Exception as e:
            logger.warning(f"Query cooccurrence failed (APOC may not be available): {e}")
            return {}
    
    # ==================== SIGNAL 4: Cross-Citation ====================
    
    async def calculate_cross_citation(self) -> Dict[Tuple[str, str], float]:
        """
        Find categories whose documents frequently reference each other.
        (Requires entity/relationship extraction to work well - placeholder for now)
        """
        # This becomes more powerful with entity extraction
        # For now, use chunk proximity as a proxy
        query = """
        // Find chunks that are semantically similar but from different categories
        MATCH (c1:Chunk), (c2:Chunk)
        WHERE c1.category <> c2.category
          AND c1.source <> c2.source  // Different documents
          AND c1.embedding IS NOT NULL
          AND c2.embedding IS NOT NULL
        WITH c1, c2, 
             gds.similarity.cosine(c1.embedding, c2.embedding) as sim
        WHERE sim > 0.85  // High similarity = likely related content
        
        WITH c1.category as cat_a, c2.category as cat_b, count(*) as citation_count
        WHERE citation_count >= 5
        
        RETURN cat_a, cat_b, citation_count,
               toFloat(citation_count) / 100 as normalized_score  // Rough normalization
        ORDER BY citation_count DESC
        LIMIT 20
        """
        
        try:
            results = await self.db.run_query(query)
            return {
                tuple(sorted([r['cat_a'], r['cat_b']])): min(r['normalized_score'], 1.0)
                for r in results
            }
        except Exception as e:
            logger.warning(f"Cross-citation failed (GDS may not be available): {e}")
            return {}
    
    # ==================== COMPOSITE ANALYSIS ====================
    
    async def analyze_all_relationships(self) -> List[CategoryRelationship]:
        """
        Master analysis combining all signals into comprehensive relationships.
        """
        logger.info("Starting comprehensive category relationship analysis...")
        
        # Gather all signals
        doc_overlaps = await self.calculate_document_overlap()
        centroids = await self.calculate_category_centroids()
        semantic_sims = await self.calculate_semantic_similarity(centroids)
        query_cooc = await self.calculate_query_cooccurrence()
        cross_cite = await self.calculate_cross_citation()
        
        # Collect all unique category pairs
        all_pairs = set()
        all_pairs.update(doc_overlaps.keys())
        all_pairs.update(semantic_sims.keys())
        all_pairs.update(query_cooc.keys())
        all_pairs.update(cross_cite.keys())
        
        relationships = []
        
        for cat_a, cat_b in all_pairs:
            key = (cat_a, cat_b)
            
            # Get individual signals (default 0 if not present)
            doc_score = doc_overlaps.get(key, 0.0)
            sem_score = semantic_sims.get(key, 0.0)
            query_score = query_cooc.get(key, 0.0)
            cite_score = cross_cite.get(key, 0.0)
            
            # Count how many signals we have
            evidence_count = sum([
                1 if doc_score > 0 else 0,
                1 if sem_score > 0 else 0,
                1 if query_score > 0 else 0,
                1 if cite_score > 0 else 0
            ])
            
            # Weighted composite score
            # Document overlap is most reliable, semantic is rich, query is behavioral
            composite = (
                0.35 * doc_score +
                0.30 * sem_score +
                0.20 * query_score +
                0.15 * cite_score
            )
            
            # Confidence based on evidence diversity
            confidence = min(evidence_count / 3.0, 1.0)
            
            # Determine relationship type
            if composite > 0.7 and evidence_count >= 3:
                rel_type = "merge_candidate"
            elif composite > 0.5:
                rel_type = "sibling"
            elif sem_score > 0.7 and doc_score < 0.3:
                rel_type = "parent_child"  # Similar content but rarely co-occur
            else:
                rel_type = "related"
            
            relationships.append(CategoryRelationship(
                category_a=cat_a,
                category_b=cat_b,
                document_overlap=doc_score,
                semantic_similarity=sem_score,
                query_cooccurrence=query_score,
                cross_citation=cite_score,
                composite_score=composite,
                relationship_type=rel_type,
                confidence=confidence,
                evidence_count=evidence_count
            ))
        
        # Sort by composite score
        relationships.sort(key=lambda r: r.composite_score, reverse=True)
        
        logger.info(f"Analyzed {len(relationships)} category relationships")
        return relationships
    
    # ==================== INBOX INTEGRATION ====================
    
    async def generate_merge_suggestions(self) -> int:
        """
        Analyze categories and send merge suggestions to Inbox.
        Returns number of suggestions generated.
        """
        relationships = await self.analyze_all_relationships()
        suggestions_sent = 0
        
        for rel in relationships:
            if rel.relationship_type == "merge_candidate" and rel.confidence >= 0.6:
                await self._send_merge_suggestion(rel)
                suggestions_sent += 1
            
            if suggestions_sent >= 3:  # Limit to avoid inbox spam
                break
        
        return suggestions_sent
    
    async def _send_merge_suggestion(self, rel: CategoryRelationship):
        """Create an inbox message suggesting a category merge."""
        
        # Build human-readable evidence
        evidence_parts = []
        if rel.document_overlap > 0.3:
            evidence_parts.append(f"appear together in {int(rel.document_overlap * 100)}% of documents")
        if rel.semantic_similarity > 0.6:
            evidence_parts.append("contain very similar content")
        if rel.query_cooccurrence > 0.2:
            evidence_parts.append("are often searched together")
        if rel.cross_citation > 0.3:
            evidence_parts.append("frequently reference each other")
        
        evidence_text = ", and ".join(evidence_parts) if evidence_parts else "seem related"
        
        body = f"""I've noticed that "{rel.category_a}" and "{rel.category_b}" {evidence_text}.

Would you like me to:
• **Merge** them into a single category
• **Link** them as related categories (keeps both, shows connection)
• **Ignore** this suggestion

Merging won't delete any documents — it just combines how they're organized."""
        
        await self.db.create_inbox_message(
            subject=f"📊 Category similarity: {rel.category_a} ↔ {rel.category_b}",
            body=body,
            msg_type="category_merge_suggestion",
            metadata={
                "category_a": rel.category_a,
                "category_b": rel.category_b,
                "composite_score": rel.composite_score,
                "relationship_type": rel.relationship_type,
                "evidence": {
                    "document_overlap": rel.document_overlap,
                    "semantic_similarity": rel.semantic_similarity,
                    "query_cooccurrence": rel.query_cooccurrence,
                    "cross_citation": rel.cross_citation
                }
            },
            actions=[
                {"id": "merge", "label": "Merge categories"},
                {"id": "link", "label": "Link as related"},
                {"id": "ignore", "label": "Ignore"}
            ]
        )
        
        logger.info(f"Sent merge suggestion: {rel.category_a} ↔ {rel.category_b} (score: {rel.composite_score:.2f})")
    
    # ==================== MERGE EXECUTION ====================
    
    async def merge_categories(self, source_category: str, target_category: str) -> bool:
        """
        Merge source_category INTO target_category.
        All chunks with source_category get re-tagged to target_category.
        """
        query = """
        MATCH (c:Chunk {category: $source})
        SET c.category = $target,
            c.previous_category = $source,
            c.merged_at = datetime()
        RETURN count(c) as updated_count
        """
        
        try:
            result = await self.db.run_query(query, {
                "source": source_category,
                "target": target_category
            })
            count = result[0]['updated_count'] if result else 0
            logger.info(f"Merged {count} chunks from '{source_category}' into '{target_category}'")
            return True
        except Exception as e:
            logger.error(f"Category merge failed: {e}")
            return False
    
    async def link_categories(self, cat_a: str, cat_b: str, relationship: str = "RELATED_TO") -> bool:
        """
        Create a relationship between two categories without merging.
        """
        query = f"""
        MERGE (a:Category {{name: $cat_a}})
        MERGE (b:Category {{name: $cat_b}})
        MERGE (a)-[r:{relationship}]->(b)
        SET r.created_at = datetime(),
            r.discovered_by = 'category_intelligence'
        RETURN a, b
        """
        
        try:
            await self.db.run_query(query, {"cat_a": cat_a, "cat_b": cat_b})
            logger.info(f"Linked categories: {cat_a} -[{relationship}]-> {cat_b}")
            return True
        except Exception as e:
            logger.error(f"Category linking failed: {e}")
            return False


# Singleton instance
_category_intelligence = None

def get_category_intelligence(db) -> CategoryIntelligence:
    global _category_intelligence
    if _category_intelligence is None:
        _category_intelligence = CategoryIntelligence(db)
    return _category_intelligence

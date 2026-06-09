"""
Document Lifecycle Management Module.

Implements:
- AI-inferred permanence scores
- Document status tracking (Active, Legacy, Archived)
- Version detection and supersession
- Learning from user recovery actions

This module is the core of the intelligent document aging system that
differentiates between perpetual documents (deeds) and ephemeral ones (drafts).
"""

import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime
import logging
import json
import re

from .config import settings
from .database import db

logger = logging.getLogger("davlon-lifecycle")

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)


class DocumentStatus(str, Enum):
    """Document lifecycle status."""
    ACTIVE = "active"
    LEGACY = "legacy"
    ARCHIVED = "archived"


class LegacyReason(str, Enum):
    """Why a document was moved to legacy."""
    SUPERSEDED = "superseded"
    AGE_DECAY = "age_decay"
    LOW_PERMANENCE = "low_permanence"
    USER_ARCHIVED = "user_archived"


class PermanenceAnalysis(BaseModel):
    """Result of AI permanence analysis."""
    permanence_score: float = Field(ge=0.0, le=1.0)
    document_type: str
    reasoning: str
    is_versioned: bool = False
    version_info: Optional[str] = None
    time_sensitive: bool = False


class DocumentLifecycle(BaseModel):
    """Document lifecycle metadata."""
    doc_id: str
    status: DocumentStatus = DocumentStatus.ACTIVE
    status_reason: Optional[LegacyReason] = None
    status_changed_at: Optional[datetime] = None
    permanence_score: float = 0.5
    document_type: str = "general"
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None
    legacy_confidence: float = 1.0
    recovery_count: int = 0


class LifecycleManager:
    """
    Manages document lifecycle with AI-inferred permanence.
    
    Key responsibilities:
    1. Analyze documents for permanence score during ingestion
    2. Detect version supersession
    3. Track document status changes
    4. Learn from user recovery actions
    """
    
    def __init__(self, db_driver):
        self.db = db_driver
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    async def analyze_permanence(
        self, 
        content: str, 
        filename: str
    ) -> PermanenceAnalysis:
        """
        Use AI to analyze document permanence.
        
        High permanence (0.8-1.0): Deeds, certificates, signed contracts
        Medium permanence (0.4-0.7): Reports, policies, procedures
        Low permanence (0.0-0.3): Drafts, meeting notes, temporary docs
        """
        # Take first 3000 chars for analysis (cost effective)
        content_preview = content[:3000] if len(content) > 3000 else content
        
        prompt = f"""Analyze this document and determine its permanence score.

Filename: {filename}
Content Preview:
---
{content_preview}
---

Permanence Score Guidelines:
- 0.9-1.0: Legally binding, perpetual documents (property deeds, certificates, signed contracts, official records)
- 0.7-0.8: Important but may need updates (policies, procedures, employee handbooks)
- 0.5-0.6: Standard documents (reports, proposals, standard communications)
- 0.3-0.4: Time-sensitive documents (quarterly reports, meeting notes, project updates)
- 0.0-0.2: Ephemeral documents (drafts, working copies, temporary notes)

Look for these indicators:
- PERMANENT: Legal language, signatures, notarization, "deed", "certificate", "official"
- MEDIUM: Policy language, "procedure", "handbook", version numbers
- EPHEMERAL: "draft", "v0.", "working", "temp", "WIP", "for review", specific dates like "this week"

Respond ONLY in JSON format:
{{
  "permanence_score": 0.X,
  "document_type": "legal_deed|contract|policy|report|draft|meeting_notes|general",
  "reasoning": "Brief explanation",
  "is_versioned": true/false,
  "version_info": "v2" or null,
  "time_sensitive": true/false
}}"""

        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return PermanenceAnalysis(
                    permanence_score=float(data.get('permanence_score', 0.5)),
                    document_type=data.get('document_type', 'general'),
                    reasoning=data.get('reasoning', 'Unable to determine'),
                    is_versioned=data.get('is_versioned', False),
                    version_info=data.get('version_info'),
                    time_sensitive=data.get('time_sensitive', False)
                )
        except Exception as e:
            logger.error(f"Permanence analysis failed: {e}")
        
        # Default fallback
        return PermanenceAnalysis(
            permanence_score=0.5,
            document_type="general",
            reasoning="Analysis unavailable, using default"
        )
    
    def calculate_confidence(
        self, 
        filename: str, 
        content: str, 
        ai_analysis: PermanenceAnalysis
    ) -> float:
        """
        Calculate confidence using rule-based approach with AI fallback.
        
        High confidence (0.8+): Deterministic rules matched
        Medium confidence (0.5-0.7): AI had to guess, some signals present
        Low confidence (<0.5): Ambiguous, should notify user for confirmation
        
        Returns:
            float: Confidence score between 0 and 1
        """
        filename_lower = filename.lower()
        content_lower = content[:5000].lower()  # Check first 5000 chars
        
        # RULE 1: Strong filename indicators = HIGH confidence
        high_permanence_indicators = [
            "deed", "certificate", "official", "signed", "notarized", 
            "contract", "agreement", "license", "permit", "title"
        ]
        low_permanence_indicators = [
            "draft", "wip", "temp", "v0", "working", "notes", 
            "scratch", "todo", "brainstorm", "rough"
        ]
        
        # Check filename for clear indicators
        for indicator in high_permanence_indicators:
            if indicator in filename_lower:
                if ai_analysis.permanence_score >= 0.7:
                    logger.debug(f"High confidence: filename '{indicator}' + AI agrees")
                    return 0.95  # Filename + AI agree
                else:
                    logger.debug(f"Conflict: filename '{indicator}' but AI says low permanence")
                    return 0.4  # Conflict - ask user
        
        for indicator in low_permanence_indicators:
            if indicator in filename_lower:
                if ai_analysis.permanence_score <= 0.4:
                    logger.debug(f"High confidence: filename '{indicator}' + AI agrees")
                    return 0.95  # Filename + AI agree
                else:
                    logger.debug(f"Conflict: filename '{indicator}' but AI says high permanence")
                    return 0.4  # Conflict - ask user
        
        # RULE 2: Legal language in content = HIGH confidence for legal docs
        legal_phrases = [
            "hereby", "witnesseth", "notary", "seal", "executed",
            "undersigned", "legally binding", "whereas", "hereinafter"
        ]
        legal_count = sum(1 for phrase in legal_phrases if phrase in content_lower)
        
        if legal_count >= 2:  # Strong legal language
            if ai_analysis.permanence_score >= 0.7:
                logger.debug(f"High confidence: legal language ({legal_count} phrases) + AI agrees")
                return 0.95
            else:
                logger.debug(f"Conflict: legal language but AI disagrees")
                return 0.4  # Content looks legal but AI disagrees - ask user
        
        # RULE 3: Clear versioning = HIGH confidence
        if ai_analysis.is_versioned and ai_analysis.version_info:
            logger.debug(f"High confidence: clear version detected ({ai_analysis.version_info})")
            return 0.9
        
        # RULE 4: AI hedging language = LOWER confidence
        hedging_phrases = [
            "may be", "could be", "possibly", "likely", "seems", 
            "appears to", "might", "uncertain", "unclear", "not sure"
        ]
        hedging_count = sum(1 for h in hedging_phrases if h in ai_analysis.reasoning.lower())
        
        if hedging_count >= 2:
            logger.debug(f"Low confidence: AI hedging ({hedging_count} phrases)")
            return 0.4  # AI is uncertain - ask user
        elif hedging_count == 1:
            logger.debug(f"Medium confidence: some AI hedging")
            return 0.6
        
        # RULE 5: Very short reasoning = suspect
        if len(ai_analysis.reasoning) < 20:
            logger.debug(f"Medium confidence: reasoning too short")
            return 0.5
        
        # RULE 6: Extreme permanence scores with good reasoning = higher confidence
        if ai_analysis.permanence_score >= 0.9 or ai_analysis.permanence_score <= 0.1:
            logger.debug(f"Higher confidence: extreme score with reasoning")
            return 0.8  # Extreme scores are usually more certain
        
        # Default: moderate confidence
        logger.debug(f"Default moderate confidence")
        return 0.7

    
    async def detect_supersession(
        self, 
        filename: str, 
        doc_id: str
    ) -> Optional[str]:
        """
        Detect if this document supersedes an existing one.
        
        Returns the doc_id of the superseded document, if any.
        """
        # Extract base name and version
        version_patterns = [
            r'(.+?)_v(\d+)',      # file_v2.pdf
            r'(.+?)_V(\d+)',      # file_V2.pdf
            r'(.+?)\s+v(\d+)',    # file v2.pdf
            r'(.+?)_rev(\d+)',    # file_rev2.pdf
            r'(.+?)_r(\d+)',      # file_r2.pdf
        ]
        
        base_name = None
        version_num = None
        
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        for pattern in version_patterns:
            match = re.match(pattern, name_without_ext, re.IGNORECASE)
            if match:
                base_name = match.group(1)
                version_num = int(match.group(2))
                break
        
        if not base_name or version_num is None:
            return None
        
        if version_num <= 1:
            return None  # v1 doesn't supersede anything
        
        # Look for previous version
        previous_version = version_num - 1
        
        query = """
        MATCH (d:Document)
        WHERE d.name =~ $pattern AND d.id <> $current_id
        RETURN d.id as doc_id, d.name as name
        ORDER BY d.createdAt DESC
        LIMIT 1
        """
        
        # Build pattern to match previous versions
        pattern = f"(?i){re.escape(base_name)}[_\\s]?[vV]?{previous_version}.*"
        
        results = await self.db.run_query(query, {
            "pattern": pattern,
            "current_id": doc_id
        })
        
        if results:
            return results[0]['doc_id']
        
        return None
    
    async def save_lifecycle(self, lifecycle: DocumentLifecycle) -> bool:
        """
        Save document lifecycle metadata to Neo4j.
        
        Returns True if successful, False otherwise.
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        SET d.status = $status,
            d.status_reason = $status_reason,
            d.status_changed_at = datetime(),
            d.permanence_score = $permanence_score,
            d.document_type = $document_type,
            d.superseded_by = $superseded_by,
            d.supersedes = $supersedes,
            d.legacy_confidence = $legacy_confidence,
            d.recovery_count = $recovery_count
        RETURN d.id as id
        """
        
        try:
            results = await self.db.run_query(query, {
                "doc_id": lifecycle.doc_id,
                "status": lifecycle.status.value,
                "status_reason": lifecycle.status_reason.value if lifecycle.status_reason else None,
                "permanence_score": lifecycle.permanence_score,
                "document_type": lifecycle.document_type,
                "superseded_by": lifecycle.superseded_by,
                "supersedes": lifecycle.supersedes,
                "legacy_confidence": lifecycle.legacy_confidence,
                "recovery_count": lifecycle.recovery_count
            })
            return len(results) > 0
        except Exception as e:
            logger.error(f"Failed to save lifecycle for {lifecycle.doc_id}: {e}")
            return False
    
    async def mark_as_superseded(self, old_doc_id: str, new_doc_id: str):
        """Mark an old document as superseded by a newer one."""
        query = """
        MATCH (old:Document {id: $old_id})
        MATCH (new:Document {id: $new_id})
        SET old.status = 'legacy',
            old.status_reason = 'superseded',
            old.superseded_by = $new_id,
            old.status_changed_at = datetime()
        SET new.supersedes = $old_id
        MERGE (new)-[:SUPERSEDES]->(old)
        """
        
        await self.db.run_query(query, {
            "old_id": old_doc_id,
            "new_id": new_doc_id
        })
        
        logger.info(f"Document {old_doc_id} superseded by {new_doc_id}")
    
    async def recover_document(self, doc_id: str) -> bool:
        """
        Recover a document from Legacy status.
        Also learns from this action to improve future predictions.
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        SET d.status = 'active',
            d.status_reason = null,
            d.recovery_count = COALESCE(d.recovery_count, 0) + 1,
            d.permanence_score = CASE 
                WHEN d.permanence_score < 0.8 THEN d.permanence_score + 0.2
                ELSE 1.0
            END,
            d.status_changed_at = datetime()
        RETURN d.document_type as doc_type, d.category as category
        """
        
        results = await self.db.run_query(query, {"doc_id": doc_id})
        
        if results:
            doc_type = results[0].get('doc_type', 'general')
            category = results[0].get('category', 'general')
            
            # Learn: boost permanence for similar documents
            await self._boost_category_permanence(category, 0.05)
            logger.info(f"Document {doc_id} recovered. Boosted permanence for {category}")
            return True
        
        return False
    
    async def _boost_category_permanence(self, category: str, boost: float):
        """Boost permanence score for a category based on user feedback."""
        # This updates the CompanyProfile to remember this preference
        query = """
        MATCH (cp:CompanyProfile)
        WITH cp, COALESCE(cp.category_permanence_boosts, '{}') as boosts_str
        WITH cp, apoc.convert.fromJsonMap(boosts_str) as boosts
        SET cp.category_permanence_boosts = apoc.convert.toJson(
            apoc.map.setKey(boosts, $category, 
                COALESCE(boosts[$category], 0.0) + $boost
            )
        )
        """
        try:
            await self.db.run_query(query, {"category": category, "boost": boost})
        except Exception as e:
            # APOC may not be installed, log and continue
            logger.warning(f"Category boost failed (APOC not available?): {e}")
    
    async def archive_document(self, doc_id: str) -> bool:
        """Archive a document (removes from search entirely)."""
        query = """
        MATCH (d:Document {id: $doc_id})
        SET d.status = 'archived',
            d.status_reason = 'user_archived',
            d.status_changed_at = datetime()
        RETURN d.id as id
        """
        
        results = await self.db.run_query(query, {"doc_id": doc_id})
        return len(results) > 0
    
    async def get_legacy_documents(self) -> List[Dict]:
        """Get all legacy and archived documents for the Legacy tab."""
        query = """
        MATCH (d:Document)
        WHERE d.status IN ['legacy', 'archived']
        OPTIONAL MATCH (newer:Document)-[:SUPERSEDES]->(d)
        RETURN d.id as doc_id,
               d.name as filename,
               d.status as status,
               d.status_reason as reason,
               d.status_changed_at as changed_at,
               d.permanence_score as permanence,
               d.document_type as doc_type,
               newer.name as superseded_by_name,
               d.superseded_by as superseded_by_id,
               d.createdAt as created_at
        ORDER BY d.status_changed_at DESC
        """
        
        return await self.db.run_query(query)
    
    async def should_notify_for_legacy(self, doc_id: str) -> bool:
        """
        Check if we should send an inbox notification about this legacy decision.
        Only notify when confidence < 60%.
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        RETURN d.legacy_confidence as confidence
        """
        
        results = await self.db.run_query(query, {"doc_id": doc_id})
        if results:
            confidence = results[0].get('confidence', 1.0)
            return confidence < 0.6
        return False

    async def reevaluate_stale_documents(self, age_days: int = 90, min_permanence: float = 0.5) -> dict:
        """
        Daily job: Find and re-evaluate old documents that might be legacy.
        
        Args:
            age_days: Only check docs older than this
            min_permanence: Docs with score below this are candidates
            
        Returns:
            dict with counts of evaluated, marked_legacy
        """
        query = """
        MATCH (d:Document)
        WHERE d.status = 'active'
          AND d.createdAt < datetime() - duration({days: $age_days})
          AND d.permanence_score < $min_permanence
        RETURN d.id as doc_id, d.name as name, d.permanence_score as score, 
               d.legacy_confidence as confidence
        LIMIT 50
        """
        
        results = await self.db.run_query(query, {
            "age_days": age_days,
            "min_permanence": min_permanence
        })
        
        evaluated = 0
        marked_legacy = 0
        
        for record in results:
            doc_id = record.get("doc_id")
            name = record.get("name")
            score = record.get("score", 0.5)
            confidence = record.get("confidence", 1.0)
            
            # If low permanence AND low confidence, mark as legacy
            if score < 0.3 and confidence < 0.7:
                try:
                    update_query = """
                    MATCH (d:Document {id: $doc_id})
                    SET d.status = 'legacy',
                        d.status_reason = 'low_permanence',
                        d.status_changed_at = datetime()
                    """
                    await self.db.run_query(update_query, {"doc_id": doc_id})
                    marked_legacy += 1
                    logger.info(f"Auto-marked as legacy: {name} (score={score:.2f})")
                except Exception as e:
                    logger.error(f"Failed to mark {doc_id} as legacy: {e}")
            
            evaluated += 1
        
        return {
            "evaluated": evaluated,
            "marked_legacy": marked_legacy
        }


# Singleton instance
_lifecycle_manager = None

def get_lifecycle_manager(db_driver=None):
    """Get or create the lifecycle manager singleton."""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager(db_driver or db)
    return _lifecycle_manager

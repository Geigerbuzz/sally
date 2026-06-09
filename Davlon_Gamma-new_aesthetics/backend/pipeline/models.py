from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
import hashlib

# --- Core Primitive: The Verification Unit ---
class SourceType(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    LIVE_API = "live_api"
    WEBPAGE = "webpage"

class Citation(BaseModel):
    """
    A strict reference to a specific location in a source document.
    """
    source_id: str = Field(..., description="UUID of the parent document")
    page_number: Optional[int] = Field(None, description="Physical page number (for PDFs)")
    line_number: Optional[int] = Field(None, description="Line number range start")
    text_snippet: str = Field(..., description="The exact raw text used as evidence")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Ocular/Model confidence in this text")

class DataChunk(BaseModel):
    """
    A semantic unit of information extracted from a source.
    """
    chunk_id: str = Field(..., default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest())
    content: str
    metadata: Dict[str, Any]
    source_type: SourceType
    created_at: datetime = Field(default_factory=datetime.now)

    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Chunk content cannot be empty')
        return v

# --- The "Auditor" Protocol ---
class InsightDraft(BaseModel):
    """
    An intermediate answer drafted by the LLM before verification.
    """
    query: str
    draft_answer: str
    proposed_citations: List[Citation] = []

class VerifiedInsight(BaseModel):
    """
    The final output allowed to be shown to the user.
    """
    query: str
    verified_answer: str
    citations: List[Citation]
    verification_log: List[str] = Field(..., description="Audit trail of how the answer was verified")
    hallucination_score: float = Field(0.0, description="0.0 = Perfect, 1.0 = Pure Fabrication")

# --- Live Data Integrity ---
class LiveDataPacket(BaseModel):
    """
    Schema for incoming real-time data streams.
    """
    stream_id: str
    timestamp: datetime
    data_payload: Dict[str, Any]
    
    # Confidence Metrics
    latency_ms: int
    source_reliability_score: float = 1.0


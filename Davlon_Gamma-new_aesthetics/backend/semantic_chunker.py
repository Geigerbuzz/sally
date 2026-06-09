"""
Semantic Chunker: Embedding-Based Intelligent Document Splitting

Uses sentence-level embeddings to detect topic boundaries and create
semantically coherent chunks. Each chunk contains a complete "thought"
rather than arbitrary character boundaries.

Philosophy: Never cut a sentence in half. Group related sentences together.
"""

import google.generativeai as genai
import logging
import re
import math
from typing import List, Tuple
from dataclasses import dataclass

from .config import settings

logger = logging.getLogger("davlon-semantic-chunker")

# Configure the API
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)


@dataclass
class SemanticChunk:
    """A semantically coherent chunk of text."""
    text: str
    content_type: str  # "text", "table", "image", "graph"
    start_sentence: int
    end_sentence: int
    avg_similarity: float  # How cohesive is this chunk internally


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))
    
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    
    return dot_product / (magnitude_a * magnitude_b)


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences, preserving structure.
    
    ENHANCED: Keeps entire tables as single units, not just individual rows.
    
    Handles:
    - Standard sentence endings (. ! ?)
    - Abbreviations (Mr., Dr., etc.)
    - Decimal numbers (3.14)
    - Headers (kept as single units, marked for forced breaks)
    - Tables (ENTIRE table kept as single unit)
    - List items (kept as single units)
    """
    sentences = []
    lines = text.split('\n')
    
    current_sentence = ""
    table_buffer = []  # Collect table rows
    in_table = False
    
    def flush_sentence():
        nonlocal current_sentence
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    def flush_table():
        nonlocal table_buffer, in_table
        if table_buffer:
            # Keep entire table as one "sentence" (atomic unit)
            table_text = "\n".join(table_buffer)
            sentences.append(table_text)
            table_buffer = []
        in_table = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        if not line_stripped:
            # Empty line might end a table
            if in_table:
                flush_table()
            if current_sentence:
                flush_sentence()
            continue
        
        # Detect table row: starts with | and contains another |
        is_table_row = line_stripped.startswith('|') and '|' in line_stripped[1:]
        
        # Also detect markdown table separator: |---|---|
        is_table_separator = bool(re.match(r'^\|[\s\-:|]+\|$', line_stripped))
        
        if is_table_row or is_table_separator:
            # Starting or continuing a table
            if not in_table:
                flush_sentence()  # End any pending text
            in_table = True
            table_buffer.append(line_stripped)
            continue
        else:
            # Not a table row - flush any pending table
            if in_table:
                flush_table()
        
        # Headers - keep as single unit (marked for special handling)
        if line_stripped.startswith('#'):
            flush_sentence()
            sentences.append(line_stripped)
            continue
        
        # List items - keep as single unit
        if re.match(r'^[\*\-\+]\s+', line_stripped) or re.match(r'^\d+\.\s+', line_stripped):
            flush_sentence()
            sentences.append(line_stripped)
            continue
        
        # Regular text - split by sentence boundaries
        current_sentence += " " + line_stripped
        
        # Split on sentence endings, but be careful about abbreviations
        # Pattern: sentence ending followed by space and capital letter
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', current_sentence.strip())
        
        if len(parts) > 1:
            # All but last are complete sentences
            for part in parts[:-1]:
                if part.strip():
                    sentences.append(part.strip())
            current_sentence = parts[-1]
    
    # Flush any remaining content
    if in_table:
        flush_table()
    flush_sentence()
    
    return [s for s in sentences if s]


def is_table_content(text: str) -> bool:
    """Check if text is a complete table block."""
    lines = text.strip().split('\n')
    if len(lines) < 2:
        return False
    
    # All lines should be table rows
    table_lines = 0
    for line in lines:
        line = line.strip()
        if line.startswith('|') and '|' in line[1:]:
            table_lines += 1
        elif re.match(r'^[\s\-:|]+$', line):
            table_lines += 1  # Separator line
    
    return table_lines >= len(lines) * 0.8  # 80%+ table rows


def detect_content_type(text: str) -> str:
    """Detect the primary content type of text."""
    text_lower = text.lower()
    
    # Check for graph/chart indicators
    if any(word in text_lower for word in ['graph showing', 'chart:', 'plotted', 'x-axis', 'y-axis', 'bar chart', 'line graph', 'pie chart']):
        return "graph"
    
    # Check for image indicators (but not graphs)
    if any(word in text_lower for word in ['[image', 'figure:', 'photo of', 'picture of', 'screenshot', 'diagram']):
        return "image"
    
    # Check for table - use helper for multi-line tables
    if is_table_content(text) or ('|' in text and text.count('|') >= 4):
        return "table"
    
    return "text"


async def embed_sentences(sentences: List[str]) -> List[List[float]]:
    """
    Embed a batch of sentences using Gemini embedding model.
    
    Uses SEMANTIC_SIMILARITY task type for best sentence comparison.
    """
    if not sentences:
        return []
    
    try:
        # Batch embed for efficiency
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=sentences,
            task_type="SEMANTIC_SIMILARITY",
            output_dimensionality=768
        )
        
        embeddings = response['embedding']
        
        # Handle both single and batch responses
        if isinstance(embeddings[0], float):
            # Single embedding returned
            return [embeddings]
        
        return embeddings
        
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        # Return zero vectors as fallback
        return [[0.0] * 768 for _ in sentences]


async def semantic_chunk(
    text: str,
    min_chunk_size: int = 100,
    max_chunk_size: int = 1500,
    target_chunk_size: int = 600,
    lookahead_window: int = 4
) -> List[SemanticChunk]:
    """
    Split text into semantically coherent chunks using sentence embeddings.
    
    ENHANCED Algorithm:
    1. Split text into sentences
    2. Embed each sentence
    3. Calculate similarity between consecutive sentences
    4. Compute ADAPTIVE threshold based on document's similarity distribution
    5. Use LOOKAHEAD WINDOW to confirm topic breaks (check N+1 through N+4)
    6. Group sentences into chunks, respecting min/max sizes
    
    Args:
        text: Document text to chunk
        min_chunk_size: Minimum characters per chunk (avoid tiny chunks)
        max_chunk_size: Maximum characters per chunk (avoid context overflow)
        target_chunk_size: Ideal chunk size to aim for
        lookahead_window: How many sentences ahead to check for topic coherence
    
    Returns:
        List of SemanticChunk objects
    """
    # Step 1: Split into sentences
    sentences = split_into_sentences(text)
    
    if not sentences:
        return []
    
    if len(sentences) == 1:
        return [SemanticChunk(
            text=sentences[0],
            content_type=detect_content_type(sentences[0]),
            start_sentence=0,
            end_sentence=0,
            avg_similarity=1.0
        )]
    
    logger.info(f"Semantic chunking: {len(sentences)} sentences to process")
    
    # Step 2: Embed all sentences (batched)
    embeddings = await embed_sentences(sentences)
    
    if len(embeddings) != len(sentences):
        logger.warning(f"Embedding count mismatch: {len(embeddings)} vs {len(sentences)}")
        return _fallback_chunk(text)
    
    # Step 3: Calculate ALL pairwise similarities for lookahead
    # Build similarity matrix for efficient lookups
    def get_similarity(i: int, j: int) -> float:
        """Get similarity between sentences i and j."""
        if i < 0 or j < 0 or i >= len(embeddings) or j >= len(embeddings):
            return 0.0
        return cosine_similarity(embeddings[i], embeddings[j])
    
    # Calculate consecutive similarities
    consecutive_sims = []
    for i in range(len(embeddings) - 1):
        consecutive_sims.append(get_similarity(i, i + 1))
    
    # Step 4: ADAPTIVE THRESHOLD
    # Calculate document's natural similarity baseline
    if consecutive_sims:
        avg_sim = sum(consecutive_sims) / len(consecutive_sims)
        # Standard deviation
        variance = sum((s - avg_sim) ** 2 for s in consecutive_sims) / len(consecutive_sims)
        std_sim = math.sqrt(variance)
        
        # Adaptive threshold: average minus half standard deviation
        # This catches genuine dips below the document's normal pattern
        adaptive_threshold = avg_sim - (0.5 * std_sim)
        
        # Clamp to reasonable range
        adaptive_threshold = max(0.55, min(0.85, adaptive_threshold))
        
        logger.info(f"Similarity stats: avg={avg_sim:.3f}, std={std_sim:.3f}, adaptive_threshold={adaptive_threshold:.3f}")
    else:
        adaptive_threshold = 0.72  # Fallback
    
    # Step 5: Find topic boundaries with LOOKAHEAD WINDOW
    def is_topic_break(position: int) -> bool:
        """
        Determine if position is a topic break using lookahead.
        
        Returns True if:
        1. Similarity to next sentence is below threshold, AND
        2. The next few sentences form a coherent new topic together
        """
        if position >= len(consecutive_sims):
            return False
        
        current_to_next = consecutive_sims[position]
        
        # Not a break if similarity is high
        if current_to_next >= adaptive_threshold:
            return False
        
        # Check if next sentences form a coherent block
        # (confirming this is a real topic change, not just noise)
        lookahead_end = min(position + lookahead_window, len(embeddings) - 1)
        
        if lookahead_end <= position + 1:
            # Not enough lookahead, trust the low similarity
            return True
        
        # Calculate average similarity within the upcoming window
        upcoming_sims = []
        for j in range(position + 1, lookahead_end):
            upcoming_sims.append(get_similarity(j, j + 1))
        
        if not upcoming_sims:
            return True
        
        avg_upcoming = sum(upcoming_sims) / len(upcoming_sims)
        
        # Confirmed break if:
        # - Current-to-next is low
        # - Upcoming sentences are coherent together (high internal similarity)
        if avg_upcoming > adaptive_threshold:
            # Upcoming window is coherent = confirmed new topic
            logger.debug(f"Confirmed break at {position}: next_sim={current_to_next:.3f}, upcoming_coherence={avg_upcoming:.3f}")
            return True
        
        # Also check if current sentence is more similar to content before it
        # than to content after it (directional check)
        if position > 0:
            sim_to_previous = get_similarity(position, position - 1)
            sim_to_upcoming_avg = sum(get_similarity(position, position + k) for k in range(1, min(3, len(embeddings) - position))) / min(2, len(embeddings) - position - 1)
            
            if sim_to_previous > sim_to_upcoming_avg + 0.1:
                # Current belongs more with previous content
                return True
        
        return False
    
    # Step 6: Group sentences into chunks
    chunks = []
    current_chunk_sentences = [sentences[0]]
    current_chunk_start = 0
    current_chunk_sims = []
    
    for i in range(len(sentences) - 1):
        current_size = sum(len(s) for s in current_chunk_sentences)
        next_sentence = sentences[i + 1]
        would_be_size = current_size + len(next_sentence)
        
        # Check if current chunk or next sentence is a table (never split tables)
        current_is_table = is_table_content(current_chunk_sentences[-1])
        next_is_table = is_table_content(next_sentence)
        
        # Decision: Should we break here?
        should_break = False
        break_reason = ""
        
        # NEVER break in the middle of a table
        if current_is_table and next_is_table:
            # Both are tables - keep together (likely continuation)
            pass  # Don't break
        
        # Force break if too big (but only if not a table)
        elif would_be_size > max_chunk_size and not next_is_table:
            should_break = True
            break_reason = "max size"
        
        # Force break on headers (structural boundary)
        elif next_sentence.startswith('#'):
            should_break = True
            break_reason = "header"
        
        # Break BEFORE a table (table is its own chunk unless small)
        elif next_is_table and current_size >= min_chunk_size:
            should_break = True
            break_reason = "table boundary"
        
        # Topic break with lookahead confirmation (but not for tables)
        elif current_size >= min_chunk_size and is_topic_break(i) and not current_is_table:
            should_break = True
            break_reason = "topic shift"
        
        # Soft break at target size if similarity is weakening
        elif current_size >= target_chunk_size and i < len(consecutive_sims):
            if consecutive_sims[i] < adaptive_threshold + 0.08:
                should_break = True
                break_reason = "target size"
        
        if should_break:
            # Create chunk from accumulated sentences
            chunk_text = " ".join(current_chunk_sentences)
            avg_sim = sum(current_chunk_sims) / len(current_chunk_sims) if current_chunk_sims else 1.0
            
            chunks.append(SemanticChunk(
                text=chunk_text,
                content_type=detect_content_type(chunk_text),
                start_sentence=current_chunk_start,
                end_sentence=i,
                avg_similarity=avg_sim
            ))
            
            logger.debug(f"Chunk {len(chunks)}: sentences {current_chunk_start}-{i}, reason={break_reason}")
            
            # Start new chunk
            current_chunk_sentences = [next_sentence]
            current_chunk_start = i + 1
            current_chunk_sims = []
        else:
            # Continue accumulating
            current_chunk_sentences.append(next_sentence)
            if i < len(consecutive_sims):
                current_chunk_sims.append(consecutive_sims[i])
    
    # Don't forget the last chunk
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        avg_sim = sum(current_chunk_sims) / len(current_chunk_sims) if current_chunk_sims else 1.0
        
        chunks.append(SemanticChunk(
            text=chunk_text,
            content_type=detect_content_type(chunk_text),
            start_sentence=current_chunk_start,
            end_sentence=len(sentences) - 1,
            avg_similarity=avg_sim
        ))
    
    logger.info(f"Created {len(chunks)} semantic chunks from {len(sentences)} sentences (adaptive_threshold={adaptive_threshold:.3f})")
    
    return chunks


def _fallback_chunk(text: str, chunk_size: int = 800) -> List[SemanticChunk]:
    """Simple fallback chunking if embedding fails."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind('. ', start, end)
            if last_period > start + chunk_size * 0.5:
                end = last_period + 1
        
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(SemanticChunk(
                text=chunk_text,
                content_type=detect_content_type(chunk_text),
                start_sentence=0,
                end_sentence=0,
                avg_similarity=0.5
            ))
        
        start = end
    
    return chunks


async def apply_overlap(
    chunks: List[SemanticChunk],
    overlap_ratio: float = 0.3
) -> List[SemanticChunk]:
    """
    Apply overlap between chunks for context continuity.
    
    Unlike character-based overlap, this repeats whole sentences
    from the end of one chunk to the start of the next.
    """
    if len(chunks) <= 1 or overlap_ratio <= 0:
        return chunks
    
    overlapped_chunks = [chunks[0]]
    
    for i in range(1, len(chunks)):
        prev_chunk = chunks[i - 1]
        curr_chunk = chunks[i]
        
        # Get sentences from end of previous chunk
        prev_sentences = split_into_sentences(prev_chunk.text)
        overlap_chars = int(len(prev_chunk.text) * overlap_ratio)
        
        # Find how many sentences fit in overlap
        overlap_text = ""
        for sent in reversed(prev_sentences):
            if len(overlap_text) + len(sent) < overlap_chars:
                overlap_text = sent + " " + overlap_text
            else:
                break
        
        # Prepend overlap to current chunk
        if overlap_text.strip():
            new_text = overlap_text.strip() + " " + curr_chunk.text
            overlapped_chunks.append(SemanticChunk(
                text=new_text,
                content_type=curr_chunk.content_type,
                start_sentence=curr_chunk.start_sentence,
                end_sentence=curr_chunk.end_sentence,
                avg_similarity=curr_chunk.avg_similarity
            ))
        else:
            overlapped_chunks.append(curr_chunk)
    
    return overlapped_chunks


# Convenience function for ingestion pipeline
async def chunk_document_semantically(
    text: str,
    overlap_ratio: float = 0.3,
    is_special_category: bool = False
) -> List[dict]:
    """
    Main entry point for semantic chunking in the ingestion pipeline.
    
    Returns list of dicts compatible with existing pipeline:
    [{"text": "...", "content_type": "text|table|image|graph"}, ...]
    """
    # Use higher overlap for special categories (legal docs etc)
    if is_special_category:
        overlap_ratio = 0.5
    
    # Semantic chunk
    chunks = await semantic_chunk(text)
    
    # Apply overlap
    chunks_with_overlap = await apply_overlap(chunks, overlap_ratio)
    
    # Convert to dict format expected by pipeline
    return [
        {
            "text": chunk.text,
            "content_type": chunk.content_type
        }
        for chunk in chunks_with_overlap
    ]

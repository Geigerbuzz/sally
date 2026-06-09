from typing import List
from .models import InsightDraft, VerifiedInsight, Citation, DataChunk

class AuditorAgent:
    """
    The 'Judge' Agent. It enforces the Zero-Hallucination policy.
    It compares the 'Draft Answer' against the 'Raw Evidence'.
    """
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def verify(self, draft: InsightDraft, context_chunks: List[DataChunk]) -> VerifiedInsight:
        """
        Main verification loop.
        1. Scan draft for claims.
        2. Attempt to ground each claim in `context_chunks`.
        3. If evidence is missing, REDACT the claim or flag as hallucination.
        """
        audit_log = []
        verified_citations = []
        clean_sentences = []
        
        audit_log.append(f"Starting audit for query: {draft.query}")
        
        # Naive sentence splitting for demo - IRL use nltk/spacy
        sentences = draft.draft_answer.split('. ')
        
        hallucination_penalty = 0.0

        for sentence in sentences:
            evidence_found = False
            best_chunk = None
            
            # Search for this sentence's semantic meaning in our PROVEN context
            # In a real app, this would use vector similarity or exact substring matching
            for chunk in context_chunks:
                if self._check_entailment(chunk.content, sentence):
                    evidence_found = True
                    best_chunk = chunk
                    break
            
            if evidence_found:
                clean_sentences.append(sentence)
                verified_citations.append(Citation(
                    source_id=best_chunk.metadata.get('source_id', 'unknown'),
                    text_snippet=best_chunk.content[:50] + "...",
                    confidence_score=0.99
                ))
                audit_log.append(f"✅ Verified: '{sentence[:20]}...'")
            else:
                if self.strict_mode:
                    audit_log.append(f"❌ REJECTED: '{sentence[:20]}...' - No evidence found.")
                    hallucination_penalty += 0.2
                    clean_sentences.append("[REDACTED: UNSUBSTANTIATED]")
                else:
                    audit_log.append(f"⚠️ FLAGGED: '{sentence[:20]}...' - Low confidence.")
                    clean_sentences.append(sentence + " (uncited)")
                    hallucination_penalty += 0.1

        final_answer = ". ".join(clean_sentences)
        if not final_answer.endswith('.'):
            final_answer += "."

        return VerifiedInsight(
            query=draft.query,
            verified_answer=final_answer,
            citations=verified_citations,
            verification_log=audit_log,
            hallucination_score=min(1.0, hallucination_penalty)
        )

    def _check_entailment(self, evidence: str, claim: str) -> bool:
        """
        Stub for an NLI (Natural Language Inference) model.
        Returns True if `evidence` supports `claim`.
        """
        # For prototype: Simple substring check or keyword overlap
        # REAL WORLD: strict NLI model call
        return True # Mocking pass for now to allow code to run

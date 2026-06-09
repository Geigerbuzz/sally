"""
Adaptive Learning Engine

Observes user behavior and learns which categories are important.
Generates promotion suggestions for admin approval.

Philosophy: "Propose, Don't Dispose" — never acts without human confirmation.
"""

import asyncio
import math
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

from .database import db

logger = logging.getLogger("davlon-learning")

# Configuration
PROMOTION_THRESHOLD = 0.70  # Composite score needed
CONFIDENCE_THRESHOLD = 0.60  # Minimum confidence needed
OBSERVATION_DAYS = 7         # Minimum observation period before suggesting


@dataclass
class CategoryAnalysis:
    """Analysis result for a category."""
    category: str
    signal_score: float       # Time-decayed signal importance
    composite_score: float    # Final weighted score
    confidence: float         # How reliable is this assessment
    reasoning: List[str]      # Human-readable reasons


class LearningEngine:
    """
    Watches for patterns and suggests category promotions.
    
    Never acts automatically — all changes require admin approval.
    """
    
    async def collect_query_signals(
        self, 
        categories: List[str],
        had_followup: bool = False,
        had_correction: bool = False
    ):
        """
        Collect signals from a completed query.
        
        Called after each RAG query to record learning signals.
        """
        for category in categories:
            # Basic query signal (this category was used)
            await db.create_signal(
                category=category,
                signal_type="query",
                value=1.0,
                decay_rate=0.05
            )
            
            # Negative signal if user needed follow-up
            if had_followup:
                await db.create_signal(
                    category=category,
                    signal_type="followup_required",
                    value=1.0,
                    decay_rate=0.03
                )
            
            # Strong negative signal if user corrected the answer
            if had_correction:
                await db.create_signal(
                    category=category,
                    signal_type="correction",
                    value=1.0,
                    decay_rate=0.02
                )
    
    async def analyze_category(self, category: str) -> CategoryAnalysis:
        """
        Analyze a category's importance based on collected signals.
        
        Returns composite score and human-readable reasoning.
        """
        # Get time-decayed importance score
        signal_score = await db.calculate_importance_score(category)
        
        # Get signal count for confidence
        signal_count = await db.count_category_signals(category)
        confidence = min(signal_count / 30, 1.0)  # Max confidence at 30+ signals
        
        # Build reasoning (non-technical!)
        reasoning = []
        if signal_score > 0.5:
            reasoning.append("your team asks about these a lot")
        if signal_score > 0.3 and signal_count > 20:
            reasoning.append("they're used consistently over time")
        
        # Composite = just signal score for now (can add graph centrality later)
        composite = signal_score
        
        return CategoryAnalysis(
            category=category,
            signal_score=signal_score,
            composite_score=composite,
            confidence=confidence,
            reasoning=reasoning
        )
    
    async def check_for_promotions(self):
        """
        Periodic job to check if any category should be promoted.
        
        Called by scheduler (e.g., weekly on Monday morning).
        """
        categories = await db.get_all_categories()
        
        for cat in categories:
            name = cat.get('name')
            if not name:
                continue
            
            # Skip already special
            if cat.get('is_special'):
                continue
            
            # Check minimum observation period
            obs_start = cat.get('observation_start')
            if obs_start:
                days_observed = (datetime.now() - obs_start.replace(tzinfo=None)).days
                if days_observed < OBSERVATION_DAYS:
                    continue
            
            # Check rejection cooldown
            cooldown = cat.get('rejection_cooldown')
            if cooldown and cooldown.replace(tzinfo=None) > datetime.now():
                continue
            
            # Analyze the category
            analysis = await self.analyze_category(name)
            
            if (analysis.composite_score >= PROMOTION_THRESHOLD and 
                analysis.confidence >= CONFIDENCE_THRESHOLD):
                await self._create_promotion_suggestion(analysis)
                logger.info(f"Created promotion suggestion for: {name}")
    
    async def _create_promotion_suggestion(self, analysis: CategoryAnalysis):
        """Create a friendly inbox message suggesting category promotion."""
        
        # Build human-readable reasoning
        if analysis.reasoning:
            reasoning_text = ", and ".join(analysis.reasoning)
        else:
            reasoning_text = "they seem important to your work"
        
        category_display = analysis.category.replace('_', ' ')
        
        message = f"""I've noticed that your "{category_display}" documents are important — {reasoning_text}.

Would you like me to give them extra attention?

If you say yes, I'll:
• Be more careful when quoting from them
• Double-check my answers more thoroughly
• Give you stronger warnings if they're outdated

Nothing about your documents will change — just how carefully I handle them."""
        
        await db.create_inbox_message(
            subject=f"💡 Should I pay more attention to {category_display}?",
            body=message,
            msg_type="promotion_suggestion",
            metadata={
                "category": analysis.category,
                "composite_score": analysis.composite_score,
                "confidence": analysis.confidence
            },
            actions=[
                {"id": "approve", "label": "Yes, give them extra attention"},
                {"id": "reject", "label": "No, they're fine as is"},
                {"id": "remind", "label": "Ask me later"}
            ]
        )
    
    async def handle_promotion_action(self, category: str, action: str):
        """
        Handle admin action on a promotion suggestion.
        
        Actions:
        - approve: Promote category to special
        - reject: Add cooldown, record rejection signal
        - remind: Snooze for 7 days
        """
        if action == "approve":
            await db.promote_category(category)
            return {"status": "ok", "message": f"'{category}' will now get extra attention"}
        
        elif action == "reject":
            # Record rejection with decay
            await db.create_signal(
                category=category,
                signal_type="admin_rejection",
                value=1.0,
                decay_rate=0.02  # Decays over ~50 days
            )
            
            # Set cooldown
            query = """
            MATCH (c:CategoryConfig {name: $category})
            SET c.rejection_cooldown = datetime() + duration({days: 30})
            """
            await db.run_query(query, {"category": category})
            
            return {"status": "ok", "message": f"Got it. I won't ask about '{category}' for a while."}
        
        elif action == "remind":
            # Short cooldown
            query = """
            MATCH (c:CategoryConfig {name: $category})
            SET c.rejection_cooldown = datetime() + duration({days: 7})
            """
            await db.run_query(query, {"category": category})
            
            return {"status": "ok", "message": "I'll ask again next week."}
        
        return {"status": "error", "message": f"Unknown action: {action}"}


# Global instance
learning_engine = LearningEngine()

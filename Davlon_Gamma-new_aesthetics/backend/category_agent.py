"""
Category Discovery Agent for Self-Adapting RAG System

This module provides AI-driven document categorization that replaces
hardcoded category lists with dynamic, learned taxonomies.
"""

import google.generativeai as genai
from typing import List, Optional
import json
import logging
import re

from .config import settings
from .company_profile import get_profile_service, DiscoveredCategory

logger = logging.getLogger("davlon-category-agent")


class CategoryDiscoveryAgent:
    """
    AI-powered agent that analyses documents and either assigns them
    to existing categories or discovers new ones.
    
    This replaces the hardcoded CATEGORIES list like:
    ["listings", "legal", "financial", "data", "marketing", "technical", "general"]
    """
    
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            # Use lite model for fast classification
            self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        else:
            logger.warning("No GOOGLE_API_KEY found. Category discovery will be disabled.")
            self.model = None
    
    async def analyze_document(
        self, 
        text: str, 
        filename: str,
        existing_categories: List[str] = None
    ) -> dict:
        """
        Analyzes a document and determines its categories (can be multiple).
        
        Returns:
            {
                "action": "assign" | "create",
                "categories": ["category_1", "category_2"],  # Array!
                "new_categories": [{"name": "...", "description": "..."}],  # Only if creating
                "confidence": 0.0-1.0
            }
        """
        if not self.model:
            return {
                "action": "assign",
                "categories": ["general"],
                "confidence": 0.5
            }
        
        if existing_categories is None:
            existing_categories = []
        
        # Build the prompt
        categories_str = ", ".join(existing_categories) if existing_categories else "None yet (this is the first document)"
        
        prompt = f"""You are a document classification AI for a business intelligence system.

Your task is to analyze a document and assign it to ALL relevant categories.

## Existing Categories in the System
{categories_str}

## Document Information
Filename: {filename}
Content Preview (first 3000 characters):
{text[:3000]}

## Instructions
1. Assign this document to ALL categories that apply (can be 1-3 categories)
2. A property deed might be: ["real_estate", "legal"]
3. A compliance report might be: ["compliance", "financial"]
4. If document needs a NEW category, include it in new_categories

Categories should be:
- General and reusable (e.g., "contracts", "financial_reports", "compliance")
- NOT specific to individual files (avoid "q3_2024_report")
- Lowercase with underscores
- Business-oriented

## Response Format (JSON only)
{{
    "action": "assign",
    "categories": ["category_1", "category_2"],
    "new_categories": [],
    "confidence": 0.9
}}

Or if creating new category:
{{
    "action": "create",
    "categories": ["existing_cat", "new_cat"],
    "new_categories": [{{"name": "new_cat", "description": "What this category contains"}}],
    "confidence": 0.85
}}

Respond with ONLY the JSON object, no markdown formatting."""

        try:
            response = await self.model.generate_content_async(prompt)
            text_response = response.text.strip()
            
            # Clean up response (remove markdown if present)
            text_response = re.sub(r'^```json\s*', '', text_response)
            text_response = re.sub(r'\s*```$', '', text_response)
            
            result = json.loads(text_response)
            
            # Validate structure
            if "categories" not in result:
                # Backwards compatibility: convert single category to array
                if "category" in result:
                    result["categories"] = [result["category"]]
                else:
                    raise ValueError("Invalid response structure")
            
            # Normalize category names
            result["categories"] = [
                cat.lower().replace(" ", "_").replace("-", "_") 
                for cat in result["categories"]
            ]
            
            # Ensure at least one category
            if not result["categories"]:
                result["categories"] = ["general"]
            
            logger.info(f"Document '{filename}' -> {result['action']}: {result['categories']}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                "action": "assign",
                "categories": ["general"],
                "confidence": 0.3
            }
        except Exception as e:
            logger.error(f"Category discovery failed: {e}")
            return {
                "action": "assign", 
                "categories": ["general"],
                "confidence": 0.3
            }
    
    async def infer_company_identity(self, text: str, filename: str) -> dict:
        """
        Attempts to infer the company name and industry from a document.
        Used during early onboarding when Company Profile is empty.
        
        Returns:
            {
                "company_name": "Acme Corp" | None,
                "industry": "Healthcare" | None,
                "confidence": 0.0-1.0
            }
        """
        if not self.model:
            return {"company_name": None, "industry": None, "confidence": 0.0}
        
        prompt = f"""Analyze this document and try to identify the company that owns/created it.

Document: {filename}
Content Preview:
{text[:2000]}

Based on letterheads, signatures, domain names, company mentions, or content type, infer:
1. Company Name (if detectable)
2. Industry (e.g., "Real Estate", "Healthcare", "Legal", "Technology", "Retail", "Finance", "Manufacturing")

Response format (JSON only):
{{"company_name": "Company Name or null", "industry": "Industry or null", "confidence": 0.8}}

If you cannot determine with reasonable confidence, return null values.
Respond with ONLY the JSON object."""

        try:
            response = await self.model.generate_content_async(prompt)
            text_response = response.text.strip()
            
            # Clean markdown
            text_response = re.sub(r'^```json\s*', '', text_response)
            text_response = re.sub(r'\s*```$', '', text_response)
            
            result = json.loads(text_response)
            
            # Handle string "null"
            if result.get("company_name") == "null":
                result["company_name"] = None
            if result.get("industry") == "null":
                result["industry"] = None
                
            logger.info(f"Identity inference: {result.get('company_name')} ({result.get('industry')})")
            return result
            
        except Exception as e:
            logger.error(f"Identity inference failed: {e}")
            return {"company_name": None, "industry": None, "confidence": 0.0}
    
    async def extract_domain_terms(self, text: str) -> dict:
        """
        Extracts domain-specific abbreviations and technical terms from a document.
        
        Returns:
            {
                "terms": {
                    "AUM": "Assets Under Management",
                    "ROI": "Return on Investment"
                }
            }
        """
        if not self.model:
            return {"terms": {}}
        
        prompt = f"""Analyze this business document and extract any domain-specific abbreviations or technical terms.

Document Preview:
{text[:2500]}

Look for:
- Abbreviations (e.g., "AUM", "EBITDA", "CAC")
- Industry jargon
- Technical terms specific to this business domain

Response format (JSON only):
{{"terms": {{"ABBREV": "Full Meaning", "TERM2": "Definition"}}}}

Only include terms you're confident about. If no domain terms found, return empty object.
Respond with ONLY the JSON object."""

        try:
            response = await self.model.generate_content_async(prompt)
            text_response = response.text.strip()
            
            text_response = re.sub(r'^```json\s*', '', text_response)
            text_response = re.sub(r'\s*```$', '', text_response)
            
            result = json.loads(text_response)
            
            terms = result.get("terms", {})
            if terms:
                logger.info(f"Extracted {len(terms)} domain terms")
            
            return result
            
        except Exception as e:
            logger.error(f"Domain term extraction failed: {e}")
            return {"terms": {}}


class CategoryManager:
    """
    High-level manager that combines CategoryDiscoveryAgent with 
    CompanyProfileService for end-to-end category management.
    """
    
    def __init__(self, db):
        self.agent = CategoryDiscoveryAgent()
        self.profile_service = get_profile_service(db)
    
    async def classify_document(self, text: str, filename: str) -> List[str]:
        """
        Main entry point: Classifies a document into multiple categories.
        
        Returns list of category names (can be 1-3 categories).
        E.g., ["real_estate", "legal"] for a property deed.
        """
        # Get current profile
        profile = await self.profile_service.get_or_create_profile()
        existing_categories = profile.get_category_names()
        
        # First document? Try to infer company identity
        if profile.total_documents_ingested == 0:
            identity = await self.agent.infer_company_identity(text, filename)
            if identity.get("company_name") or identity.get("industry"):
                await self.profile_service.update_company_identity(
                    name=identity.get("company_name"),
                    industry=identity.get("industry")
                )
        
        # Analyze document for categories (now returns array)
        result = await self.agent.analyze_document(text, filename, existing_categories)
        
        categories = result.get("categories", ["general"])
        
        # Handle new categories
        if result["action"] == "create":
            for new_cat in result.get("new_categories", []):
                await self.profile_service.add_category(
                    name=new_cat.get("name"),
                    description=new_cat.get("description", "Auto-discovered category")
                )
        
        # Ensure all categories exist in profile
        for cat_name in categories:
            cat_exists = any(c.name == cat_name for c in profile.discovered_categories)
            if not cat_exists:
                await self.profile_service.add_category(
                    name=cat_name,
                    description="Auto-discovered category"
                )
        
        # Extract domain terms (async, doesn't block classification)
        terms_result = await self.agent.extract_domain_terms(text)
        for abbrev, definition in terms_result.get("terms", {}).items():
            await self.profile_service.add_domain_term(abbrev, definition)
        
        # Increment document counter
        await self.profile_service.increment_document_count()
        
        logger.info(f"Document '{filename}' assigned to: {categories}")
        return categories
    
    async def get_categories(self) -> List[str]:
        """
        Returns the current list of discovered categories.
        """
        profile = await self.profile_service.get_or_create_profile()
        categories = profile.get_category_names()
        
        # Always include "general" as fallback
        if "general" not in categories:
            categories.append("general")
        
        return categories


# Module-level convenience function
async def get_category_manager(db):
    """Factory function to create a CategoryManager instance."""
    return CategoryManager(db)

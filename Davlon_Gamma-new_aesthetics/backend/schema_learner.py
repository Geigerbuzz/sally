"""
Schema Learner for Self-Adapting RAG System

This module provides AI-driven schema inference that replaces hardcoded
Pydantic models (like BarcelonaCadastralModel) with dynamically learned
data structures.
"""

import google.generativeai as genai
from typing import List, Dict, Optional, Any
import json
import logging
import re
from pydantic import BaseModel, Field

from .config import settings
from .company_profile import get_profile_service, LearnedSchema, EntityType

logger = logging.getLogger("davlon-schema-learner")


class FieldDefinition(BaseModel):
    """Represents a learned field in a schema."""
    original_name: str  # Original header name from CSV
    canonical_name: str  # Cleaned, English name
    data_type: str  # "string", "number", "date", "currency", "boolean"
    is_primary_key: bool = False
    relationship_hint: Optional[str] = None  # e.g., "Person", "Client" if this field references another entity
    sample_values: List[str] = []


class InferredSchema(BaseModel):
    """Represents a complete schema inferred from data."""
    entity_name: str  # e.g., "Property", "Employee", "Invoice"
    entity_description: Optional[str] = None
    fields: List[FieldDefinition]
    header_fingerprint: str  # For caching/matching future uploads


class SchemaLearner:
    """
    AI-powered schema inference that learns data structures from CSV headers
    and sample data.
    
    This replaces hardcoded models like:
    - BarcelonaCadastralModel
    - BarcelonaSurfaceModel
    
    With dynamically learned schemas that work for any industry.
    """
    
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            logger.warning("No GOOGLE_API_KEY found. Schema learning will be disabled.")
            self.model = None
    
    def _create_fingerprint(self, headers: List[str]) -> str:
        """Creates a unique fingerprint from headers for caching."""
        # Normalize and sort headers
        normalized = [h.lower().strip() for h in headers]
        return ",".join(sorted(normalized))
    
    async def infer_schema(
        self,
        headers: List[str],
        sample_rows: List[Dict[str, Any]],
        filename: str = "",
        existing_entity_types: List[str] = None
    ) -> InferredSchema:
        """
        Uses AI to infer a data schema from CSV headers and sample data.
        
        Args:
            headers: List of column headers
            sample_rows: First 5-10 rows of data as dicts
            filename: Source filename (used as hint)
            existing_entity_types: Known entity types for relationship detection
        
        Returns:
            InferredSchema with entity name and field definitions
        """
        if not self.model:
            return self._create_fallback_schema(headers)
        
        fingerprint = self._create_fingerprint(headers)
        
        # Build context about existing entities for relationship detection
        entity_context = ""
        if existing_entity_types:
            entity_context = f"\n\nKnown entity types in this system: {', '.join(existing_entity_types)}"
        
        prompt = f"""Analyze this CSV structure and infer a data schema.

**Filename**: {filename}
**Headers**: {json.dumps(headers)}
**Sample Data** (first 5 rows):
{json.dumps(sample_rows[:5], default=str, ensure_ascii=False)}
{entity_context}

**Your Task**:
1. Determine what ENTITY each row represents (e.g., "Property", "Employee", "Invoice", "Patient")
2. For each header, determine:
   - A clean canonical English name (lowercase_with_underscores)
   - The data type: "string", "number", "date", "currency", "boolean"
   - Whether it's a primary key (unique identifier)
   - If this field references another entity type (relationship_hint)

**Response Format** (JSON only):
{{
  "entity_name": "Property",
  "entity_description": "Real estate listing records",
  "fields": [
    {{
      "original_name": "Addr",
      "canonical_name": "address",
      "data_type": "string",
      "is_primary_key": false,
      "relationship_hint": null
    }},
    {{
      "original_name": "Price_USD",
      "canonical_name": "price",
      "data_type": "currency",
      "is_primary_key": false,
      "relationship_hint": null
    }},
    {{
      "original_name": "Agent_Email",
      "canonical_name": "agent_email",
      "data_type": "string",
      "is_primary_key": false,
      "relationship_hint": "Person"
    }}
  ]
}}

Rules:
- Entity names should be singular and PascalCase (e.g., "Employee" not "Employees")
- Canonical names should be lowercase_with_underscores
- Only set relationship_hint if the field clearly references another entity
- Respond with ONLY the JSON object, no markdown formatting"""

        try:
            response = await self.model.generate_content_async(prompt)
            text_response = response.text.strip()
            
            # Clean markdown if present
            text_response = re.sub(r'^```json\s*', '', text_response)
            text_response = re.sub(r'\s*```$', '', text_response)
            
            data = json.loads(text_response)
            
            # Parse into structured objects
            fields = []
            for f in data.get("fields", []):
                field = FieldDefinition(
                    original_name=f.get("original_name", ""),
                    canonical_name=f.get("canonical_name", "").lower().replace(" ", "_"),
                    data_type=f.get("data_type", "string"),
                    is_primary_key=f.get("is_primary_key", False),
                    relationship_hint=f.get("relationship_hint"),
                    sample_values=[str(row.get(f.get("original_name", ""), ""))[:50] 
                                   for row in sample_rows[:3]]
                )
                fields.append(field)
            
            schema = InferredSchema(
                entity_name=data.get("entity_name", "Record"),
                entity_description=data.get("entity_description"),
                fields=fields,
                header_fingerprint=fingerprint
            )
            
            logger.info(f"Inferred schema: {schema.entity_name} with {len(schema.fields)} fields")
            return schema
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse schema inference response: {e}")
            return self._create_fallback_schema(headers)
        except Exception as e:
            logger.error(f"Schema inference failed: {e}")
            return self._create_fallback_schema(headers)
    
    def _create_fallback_schema(self, headers: List[str]) -> InferredSchema:
        """Creates a basic schema when AI inference fails."""
        fields = []
        for h in headers:
            # Simple heuristics for data type
            h_lower = h.lower()
            data_type = "string"
            if any(kw in h_lower for kw in ["price", "amount", "cost", "value", "total"]):
                data_type = "currency"
            elif any(kw in h_lower for kw in ["count", "number", "qty", "quantity", "age"]):
                data_type = "number"
            elif any(kw in h_lower for kw in ["date", "time", "created", "updated"]):
                data_type = "date"
            elif any(kw in h_lower for kw in ["is_", "has_", "active", "enabled"]):
                data_type = "boolean"
            
            fields.append(FieldDefinition(
                original_name=h,
                canonical_name=h.lower().replace(" ", "_").replace("-", "_"),
                data_type=data_type,
                is_primary_key=False,
                relationship_hint=None
            ))
        
        return InferredSchema(
            entity_name="Record",
            entity_description="Auto-generated fallback schema",
            fields=fields,
            header_fingerprint=self._create_fingerprint(headers)
        )
    
    def build_field_mapping(self, schema: InferredSchema) -> Dict[str, str]:
        """
        Creates a mapping from original headers to canonical names.
        Used by CSV service for data normalization.
        """
        return {f.original_name: f.canonical_name for f in schema.fields}


class SchemaManager:
    """
    High-level manager that combines SchemaLearner with CompanyProfileService
    for schema caching and entity type learning.
    """
    
    def __init__(self, db):
        self.learner = SchemaLearner()
        self.profile_service = get_profile_service(db)
    
    async def get_or_infer_schema(
        self,
        headers: List[str],
        sample_rows: List[Dict[str, Any]],
        filename: str = ""
    ) -> InferredSchema:
        """
        Gets a cached schema if available, otherwise infers a new one.
        
        This is the main entry point for CSV ingestion.
        """
        fingerprint = self.learner._create_fingerprint(headers)
        
        # 1. Check cache in Company Profile
        profile = await self.profile_service.get_or_create_profile()
        cached = profile.find_schema_by_fingerprint(fingerprint)
        
        if cached:
            logger.info(f"Using cached schema: {cached.entity_name} (usage: {cached.usage_count})")
            # Convert cached LearnedSchema to InferredSchema
            return self._convert_cached_schema(cached, headers)
        
        # 2. Get existing entity types for relationship detection
        existing_entities = profile.get_entity_type_names()
        
        # 3. Infer new schema
        schema = await self.learner.infer_schema(
            headers=headers,
            sample_rows=sample_rows,
            filename=filename,
            existing_entity_types=existing_entities
        )
        
        # 4. Cache the schema
        await self._cache_schema(schema)
        
        # 5. Register the entity type
        await self._register_entity_type(schema)
        
        return schema
    
    async def _cache_schema(self, schema: InferredSchema):
        """Saves the schema to Company Profile for future use."""
        learned = LearnedSchema(
            entity_name=schema.entity_name,
            header_fingerprint=schema.header_fingerprint,
            field_mappings={
                f.original_name: {
                    "canonical": f.canonical_name,
                    "type": f.data_type,
                    "is_pk": f.is_primary_key,
                    "relationship": f.relationship_hint
                }
                for f in schema.fields
            }
        )
        await self.profile_service.add_learned_schema(learned)
    
    async def _register_entity_type(self, schema: InferredSchema):
        """Registers the entity type in Company Profile."""
        entity = EntityType(
            name=schema.entity_name,
            properties=[f.canonical_name for f in schema.fields],
            examples=[f.sample_values[0] if f.sample_values else "" for f in schema.fields[:3]]
        )
        await self.profile_service.add_entity_type(entity)
    
    def _convert_cached_schema(self, cached: LearnedSchema, headers: List[str]) -> InferredSchema:
        """Converts a cached LearnedSchema to InferredSchema."""
        fields = []
        for h in headers:
            mapping = cached.field_mappings.get(h, {})
            fields.append(FieldDefinition(
                original_name=h,
                canonical_name=mapping.get("canonical", h.lower().replace(" ", "_")),
                data_type=mapping.get("type", "string"),
                is_primary_key=mapping.get("is_pk", False),
                relationship_hint=mapping.get("relationship")
            ))
        
        return InferredSchema(
            entity_name=cached.entity_name,
            entity_description=None,
            fields=fields,
            header_fingerprint=cached.header_fingerprint
        )


# Module-level convenience function
async def get_schema_manager(db):
    """Factory function to create a SchemaManager instance."""
    return SchemaManager(db)

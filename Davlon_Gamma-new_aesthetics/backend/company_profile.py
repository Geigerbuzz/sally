"""
Company Profile Module for Self-Adapting RAG System

This module provides the core data structures and services for managing
a learnable company identity that evolves as documents are ingested.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger("davlon-company-profile")


class EntityType(BaseModel):
    """
    Represents a learned entity type in the company's domain.
    Examples: "Property", "Client", "Patient", "Contract", "Employee"
    """
    name: str  # e.g., "Property", "Client", "Patient"
    properties: List[str] = []  # e.g., ["address", "price", "beds"]
    examples: List[str] = []  # Sample values for few-shot prompting
    source_file: Optional[str] = None  # Which file taught us this entity
    created_at: Optional[datetime] = None
    usage_count: int = 0


class RelationshipType(BaseModel):
    """
    Represents a learned relationship pattern between entity types.
    Examples: "MANAGES", "TREATS", "REPRESENTS", "OWNS"
    """
    name: str  # e.g., "MANAGES", "TREATS"
    source_type: str  # e.g., "Agent", "Doctor"
    target_type: str  # e.g., "Property", "Patient"
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class DiscoveredCategory(BaseModel):
    """
    Represents a document category discovered by the AI.
    Replaces hardcoded CATEGORIES list.
    """
    name: str  # e.g., "sales_reports", "legal_contracts"
    description: str  # e.g., "Contains quarterly sales figures and projections"
    document_count: int = 0
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None


class LearnedSchema(BaseModel):
    """
    Represents a CSV/data schema learned from uploaded files.
    Used for schema caching to avoid repeated AI inference.
    """
    entity_name: str  # e.g., "Property", "Employee"
    header_fingerprint: str  # Sorted, joined headers for matching
    field_mappings: Dict[str, dict] = {}  # {original: {canonical, type, relationship_hint}}
    source_file: Optional[str] = None
    created_at: Optional[datetime] = None
    usage_count: int = 0


class CompanyProfile(BaseModel):
    """
    The central "brain" of the self-adapting system.
    Stored in Neo4j as a singleton node, evolves with each document ingested.
    """
    id: str = "company_profile"
    
    # Company Identity (inferred from documents)
    name: str = ""
    industry: str = ""  # e.g., "Real Estate", "Healthcare", "Legal", "Retail"
    
    # Dynamic Categories (replaces hardcoded CATEGORIES)
    discovered_categories: List[DiscoveredCategory] = []
    
    # Learned Entity Types (replaces hardcoded Listing, Person, etc.)
    entity_types: List[EntityType] = []
    
    # Relationship Patterns
    relationship_types: List[RelationshipType] = []
    
    # Domain Vocabulary (aids semantic search and understanding)
    domain_terms: Dict[str, str] = {}  # {"AUM": "Assets Under Management"}
    
    # Learned Schemas (for CSV/structured data)
    learned_schemas: List[LearnedSchema] = []
    
    # Onboarding Status
    confidence_score: float = 0.0  # 0-1, increases with more data
    total_documents_ingested: int = 0
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_category_names(self) -> List[str]:
        """Returns list of discovered category names."""
        return [cat.name for cat in self.discovered_categories]
    
    def get_entity_type_names(self) -> List[str]:
        """Returns list of learned entity type names."""
        return [et.name for et in self.entity_types]
    
    def find_schema_by_fingerprint(self, fingerprint: str) -> Optional[LearnedSchema]:
        """Finds a cached schema matching the header fingerprint."""
        for schema in self.learned_schemas:
            if schema.header_fingerprint == fingerprint:
                return schema
        return None


class CompanyProfileService:
    """
    Service for managing CompanyProfile persistence in Neo4j.
    """
    
    def __init__(self, db):
        self.db = db
    
    async def get_or_create_profile(self) -> CompanyProfile:
        """
        Retrieves the company profile from Neo4j, or creates a new one if none exists.
        """
        query = """
        MATCH (cp:CompanyProfile {id: 'company_profile'})
        RETURN cp
        """
        try:
            results = await self.db.run_query(query)
            if results and len(results) > 0:
                node_data = results[0].get('cp', {})
                return self._deserialize_profile(node_data)
            else:
                # Create new profile
                profile = CompanyProfile(
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                await self.save_profile(profile)
                return profile
        except Exception as e:
            logger.error(f"Error getting company profile: {e}")
            return CompanyProfile()
    
    async def save_profile(self, profile: CompanyProfile):
        """
        Saves the company profile to Neo4j.
        """
        profile.updated_at = datetime.utcnow()
        
        query = """
        MERGE (cp:CompanyProfile {id: $id})
        SET cp.name = $name,
            cp.industry = $industry,
            cp.discovered_categories = $categories_json,
            cp.entity_types = $entity_types_json,
            cp.relationship_types = $rel_types_json,
            cp.domain_terms = $domain_terms_json,
            cp.learned_schemas = $schemas_json,
            cp.confidence_score = $confidence,
            cp.total_documents = $total_docs,
            cp.created_at = $created_at,
            cp.updated_at = datetime()
        RETURN cp
        """
        
        params = {
            "id": profile.id,
            "name": profile.name,
            "industry": profile.industry,
            "categories_json": json.dumps([cat.model_dump() for cat in profile.discovered_categories]),
            "entity_types_json": json.dumps([et.model_dump() for et in profile.entity_types]),
            "rel_types_json": json.dumps([rt.model_dump() for rt in profile.relationship_types]),
            "domain_terms_json": json.dumps(profile.domain_terms),
            "schemas_json": json.dumps([s.model_dump() for s in profile.learned_schemas]),
            "confidence": profile.confidence_score,
            "total_docs": profile.total_documents_ingested,
            "created_at": profile.created_at.isoformat() if profile.created_at else datetime.utcnow().isoformat()
        }
        
        try:
            await self.db.run_query(query, params)
            logger.info(f"Saved company profile: {profile.name} ({profile.industry})")
        except Exception as e:
            logger.error(f"Error saving company profile: {e}")
    
    async def add_category(self, name: str, description: str) -> DiscoveredCategory:
        """
        Adds a new discovered category to the profile.
        """
        profile = await self.get_or_create_profile()
        
        # Check if already exists
        for cat in profile.discovered_categories:
            if cat.name.lower() == name.lower():
                cat.document_count += 1
                cat.last_used = datetime.utcnow()
                await self.save_profile(profile)
                return cat
        
        # Create new category
        new_category = DiscoveredCategory(
            name=name,
            description=description,
            document_count=1,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        profile.discovered_categories.append(new_category)
        await self.save_profile(profile)
        
        logger.info(f"Discovered new category: {name}")
        return new_category
    
    async def add_entity_type(self, entity: EntityType) -> EntityType:
        """
        Adds a new learned entity type to the profile.
        """
        profile = await self.get_or_create_profile()
        
        # Check if already exists
        for et in profile.entity_types:
            if et.name.lower() == entity.name.lower():
                # Merge properties
                et.properties = list(set(et.properties + entity.properties))
                et.usage_count += 1
                await self.save_profile(profile)
                return et
        
        entity.created_at = datetime.utcnow()
        entity.usage_count = 1
        profile.entity_types.append(entity)
        await self.save_profile(profile)
        
        logger.info(f"Learned new entity type: {entity.name}")
        return entity
    
    async def add_learned_schema(self, schema: LearnedSchema) -> LearnedSchema:
        """
        Caches a learned schema to avoid future AI inference.
        """
        profile = await self.get_or_create_profile()
        
        # Check if fingerprint already exists
        existing = profile.find_schema_by_fingerprint(schema.header_fingerprint)
        if existing:
            existing.usage_count += 1
            await self.save_profile(profile)
            return existing
        
        schema.created_at = datetime.utcnow()
        schema.usage_count = 1
        profile.learned_schemas.append(schema)
        await self.save_profile(profile)
        
        logger.info(f"Cached new schema: {schema.entity_name}")
        return schema
    
    async def update_company_identity(self, name: str = None, industry: str = None):
        """
        Updates the company name and/or industry.
        """
        profile = await self.get_or_create_profile()
        
        if name:
            profile.name = name
        if industry:
            profile.industry = industry
        
        # Boost confidence when identity is established
        if profile.name and profile.industry:
            profile.confidence_score = min(1.0, profile.confidence_score + 0.1)
        
        await self.save_profile(profile)
        logger.info(f"Updated company identity: {profile.name} ({profile.industry})")
    
    async def increment_document_count(self):
        """
        Increments the total documents ingested counter.
        """
        profile = await self.get_or_create_profile()
        profile.total_documents_ingested += 1
        
        # Gradually increase confidence with more data
        profile.confidence_score = min(1.0, profile.confidence_score + 0.02)
        
        await self.save_profile(profile)
    
    async def add_domain_term(self, abbreviation: str, definition: str):
        """
        Adds a domain-specific term to the vocabulary.
        """
        profile = await self.get_or_create_profile()
        profile.domain_terms[abbreviation] = definition
        await self.save_profile(profile)
        logger.info(f"Learned domain term: {abbreviation} = {definition}")
    
    def _deserialize_profile(self, node_data: dict) -> CompanyProfile:
        """
        Deserializes a Neo4j node into a CompanyProfile object.
        """
        try:
            categories = json.loads(node_data.get('discovered_categories', '[]'))
            entity_types = json.loads(node_data.get('entity_types', '[]'))
            rel_types = json.loads(node_data.get('relationship_types', '[]'))
            domain_terms = json.loads(node_data.get('domain_terms', '{}'))
            schemas = json.loads(node_data.get('learned_schemas', '[]'))
            
            return CompanyProfile(
                id=node_data.get('id', 'company_profile'),
                name=node_data.get('name', ''),
                industry=node_data.get('industry', ''),
                discovered_categories=[DiscoveredCategory(**c) for c in categories],
                entity_types=[EntityType(**e) for e in entity_types],
                relationship_types=[RelationshipType(**r) for r in rel_types],
                domain_terms=domain_terms,
                learned_schemas=[LearnedSchema(**s) for s in schemas],
                confidence_score=node_data.get('confidence_score', 0.0),
                total_documents_ingested=node_data.get('total_documents', 0)
            )
        except Exception as e:
            logger.error(f"Error deserializing profile: {e}")
            return CompanyProfile()


# Lazy-loaded singleton instance
_profile_service: Optional[CompanyProfileService] = None


def get_profile_service(db) -> CompanyProfileService:
    """
    Gets or creates the CompanyProfileService singleton.
    """
    global _profile_service
    if _profile_service is None:
        _profile_service = CompanyProfileService(db)
    return _profile_service

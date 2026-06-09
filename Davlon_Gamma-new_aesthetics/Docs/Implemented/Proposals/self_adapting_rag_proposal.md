---
title: Self-Adapting, Company-Agnostic RAG System
status: implemented
type: proposal
created: 2025-12-21
updated: 2026-01-07
tags: [rag, learning, architecture, dynamic]
parent: null
children: []
related:
  - ../../Active/Proposals/advanced_rag_enhancements_proposal.md
  - ../../Active/Proposals/rag_retrieval_improvements_proposal.md
  - ../../Active/Proposals/adaptive_learning_system_proposal.md
  - ../../Active/Proposals/unified_document_labeling_proposal.md
---

# Proposal: Self-Adapting, Company-Agnostic RAG System

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [Company Profile Module](#31-company-profile-module-the-brains-identity) | ✅ Complete | 2025-12-21 | `company_profile.py` |
| [Dynamic Category Discovery](#32-dynamic-category-discovery) | ✅ Complete | 2025-12-21 | `category_agent.py:CategoryDiscoveryAgent` |
| [Schema Inference Engine](#33-schema-inference-engine) | ✅ Complete | 2025-12-21 | `schema_learner.py` |
| [Adaptive Knowledge Graph](#34-adaptive-knowledge-graph) | ✅ Complete | 2025-12-21 | `company_profile.py:EntityType` |
| [Domain-Aware RAG](#35-domain-aware-rag-enhancement) | ✅ Complete | 2025-12-25 | `rag.py:_get_company_profile` |

> **Depends on**: [Knowledge Graph Master](../Masters/knowledge_graph_master.md), [Ingestion Pipeline](../Masters/ingestion_pipeline_master.md)  
> **Affects**: [Adaptive Entity Intelligence](../../Active/Proposals/adaptive_entity_intelligence_proposal.md), [Adaptive Learning System](../../Active/Proposals/adaptive_learning_system_proposal.md)

---

## Executive Summary

This proposal outlines the architectural changes required to transform the Davlon RAG system from a **real estate-focused platform** into a **universal, self-adapting intelligence system** that can serve any industry. The core insight is that the system should **learn** the company's domain, terminology, entity types, and relationships organically from the documents it ingests—rather than relying on hardcoded categories and schemas.

---

## 1. The Problem: Hardcoded Domain Assumptions

The current system has several real estate and Barcelona-specific assumptions baked into the codebase:

### 1.1 Hardcoded Categories
```python
# In rag.py and ingestion.py
CATEGORIES = ["listings", "legal", "financial", "data", "marketing", "technical", "general"]
```
These categories assume a real estate context ("listings"). A healthcare company would need "patients", "procedures"; a retail company would need "inventory", "suppliers".

### 1.2 Barcelona-Specific Schemas
```python
# In schemas.py
class BarcelonaCadastralModel(BaseModel):
    district_code: int = Field(alias="Codi_districte")
    neighborhood_name: str = Field(alias="Nom_barri")
    ...
```
These Pydantic models are locked to Catalan government data formats. Onboarding a new client requires manual schema creation.

### 1.3 Real Estate Graph Nodes
```python
# In graph_service.py  
class GraphService:
    async def create_listing_from_row(self, row_data: dict, source_file: str):
        # Creates: (Listing), (Person)-[:MANAGES]->(Listing)
```
The knowledge graph assumes "Listings" and "Agents". A law firm would need "Cases" and "Attorneys"; a hospital would need "Patients" and "Doctors".

### 1.4 Inflexible CSV Ingestion
```python
# In csv_service.py
if "Valor" in str(headers) or "Carrec" in filename:
     target_model = BarcelonaCadastralModel
```
New data formats require code changes.

---

## 2. Proposed Architecture: The Self-Learning System

> **IMPORTANT**: The core philosophy shift: **Let the data teach the system, not the other way around.**

We propose a four-layer architecture that enables the system to adapt to any company without code changes.

```
                    ┌───────────────────────────────────────┐
                    │    Layer 4: Company Profile           │
                    │    (Domain Knowledge Store)           │
                    └───────────────────┬───────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │    Layer 3: Entity Learning           │
                    │    (Schema Inference + Graph Model)   │
                    └───────────────────┬───────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │    Layer 2: Semantic Classification   │
                    │    (AI Category Discovery)            │
                    └───────────────────┬───────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │    Layer 1: Universal Ingestion       │
                    │    (Any Document → Text/Tables)       │
                    └───────────────────────────────────────┘
```

---

## 3. Detailed Component Design

### 3.1 Company Profile Module (The Brain's Identity)

> **TIP**: This is the single most important addition. Instead of hardcoding "real estate", the system maintains a learnable "Company Profile" that evolves with each document ingested.

#### 3.1.1 Company Profile Schema

```python
class CompanyProfile(BaseModel):
    """
    Stored in Neo4j as a singleton node.
    Evolves over time as documents are ingested.
    """
    id: str = "company_profile"
    name: str = ""  # Inferred from documents
    industry: str = ""  # "Real Estate", "Legal", "Healthcare"
    
    # Dynamic Categories (replaces hardcoded CATEGORIES)
    discovered_categories: List[str] = []
    
    # Learned Entity Types (replaces hardcoded Listing, Person)
    entity_types: List[EntityType] = []
    
    # Relationship Patterns
    relationship_types: List[RelationshipType] = []
    
    # Domain Vocabulary (aids semantic search)
    domain_terms: Dict[str, str] = {}  # {"AUM": "Assets Under Management"}
    
    # Onboarding Status
    confidence_score: float = 0.0  # 0-1, increases with more data
    
class EntityType(BaseModel):
    name: str  # "Property", "Client", "Patient", "Contract"
    properties: List[str]  # ["address", "price", "beds"]
    examples: List[str]  # For few-shot prompting
    
class RelationshipType(BaseModel):
    name: str  # "MANAGES", "TREATS", "REPRESENTS"
    source_type: str  # "Agent"
    target_type: str  # "Property"
```

#### 3.1.2 Profile Learning Triggers

| Event | Action |
|-------|--------|
| First document uploaded | Initialize company name, industry guess |
| CSV with unknown headers | Learn new entity type and properties |
| AI extracts new relationship | Add to `relationship_types` |
| User corrects AI mistake | Reinforce correct pattern |

---

### 3.2 Dynamic Category Discovery

Replace the hardcoded categories with an AI-driven discovery system.

#### 3.2.1 The Category Discovery Agent

```python
class CategoryDiscoveryAgent:
    async def analyze_document(self, text: str, existing_categories: List[str]) -> str:
        """
        Either assigns to an existing category OR proposes a new one.
        """
        prompt = f"""
        You are analyzing a document for a company.
        
        Existing categories in the system: {existing_categories if existing_categories else "None yet"}
        
        Document Preview:
        {text[:4000]}
        
        Task:
        1. If this document fits an existing category, return: {{"action": "assign", "category": "<category_name>"}}
        2. If this document represents a NEW type of content, return: {{"action": "create", "category": "<new_category_name>", "description": "<what this category contains>"}}
        
        Categories should be general (e.g., "contracts", "employee_records", "client_data") not specific filenames.
        """
        
        response = await self.model.generate_content_async(prompt)
        return json.loads(response.text)
```

#### 3.2.2 Category Evolution Example

**Day 1**: Company uploads their first sales report.
- AI creates category: `"sales_reports"` → *"Contains quarterly/annual sales figures and projections"*

**Day 5**: Company uploads employee handbook.
- AI creates category: `"hr_policies"` → *"Internal HR documentation and policies"*

**Day 10**: Company uploads a contract.
- AI creates category: `"legal_contracts"` → *"Binding agreements and legal documents"*

The system now has 3 domain-aware categories with zero hardcoding.

---

### 3.3 Schema Inference Engine

Replace the hardcoded `BarcelonaCadastralModel` with an AI-driven schema inference system.

#### 3.3.1 The Schema Learner

```python
class SchemaLearner:
    async def infer_schema_from_csv(self, headers: List[str], sample_rows: List[Dict]) -> DynamicSchema:
        """
        AI analyzes headers + sample data to create a Pydantic-like schema on the fly.
        """
        prompt = f"""
        Analyze this CSV structure and create a data schema.
        
        Headers: {headers}
        Sample Rows: {json.dumps(sample_rows[:5])}
        
        Return a JSON schema with:
        - entity_name: What does each row represent? (e.g., "Property", "Employee", "Invoice")
        - fields: For each header, specify:
          - canonical_name: Clean English name
          - data_type: "string" | "number" | "date" | "currency" | "boolean"
          - is_primary_key: true/false
          - relationship_hint: If this field references another entity (e.g., "employee_id" -> "Employee")
        
        Example Output:
        {{
          "entity_name": "Property",
          "fields": [
            {{"original": "Addr", "canonical_name": "address", "data_type": "string", "is_primary_key": false}},
            {{"original": "Price_USD", "canonical_name": "price", "data_type": "currency", "is_primary_key": false}},
            {{"original": "Agent_Email", "canonical_name": "agent_email", "data_type": "string", "relationship_hint": "Person"}}
          ]
        }}
        """
        
        response = await self.model.generate_content_async(prompt)
        schema = json.loads(response.text)
        
        # Save to Company Profile for future reference
        await self._save_learned_entity_type(schema)
        
        return schema
```

#### 3.3.2 Schema Stickiness (Learning Memory)

Once a schema is inferred, it's stored in Neo4j:

```cypher
CREATE (s:LearnedSchema {
    entity_name: "Property",
    header_fingerprint: "addr,beds,baths,price", 
    field_mappings: {json_mapping},
    created_at: datetime(),
    usage_count: 1
})
```

**Future uploads** matching this fingerprint skip AI inference and use the cached schema → faster + cheaper.

---

### 3.4 Adaptive Knowledge Graph

Replace the hardcoded `Listing` and `Person` nodes with a dynamic graph model.

#### 3.4.1 Universal Entity Creation

```python
class AdaptiveGraphService:
    async def create_entity_from_schema(self, entity_type: str, data: dict, source_file: str):
        """
        Creates any entity type dynamically based on learned schema.
        """
        # Build Cypher dynamically
        props = ", ".join([f"{k}: ${k}" for k in data.keys()])
        
        query = f"""
        MERGE (e:{entity_type} {{id: $id}})
        SET e += {{{props}}},
            e.source_file = $source,
            e.updated_at = datetime()
        RETURN e
        """
        
        params = {"id": str(uuid.uuid4()), "source": source_file, **data}
        await db.run_query(query, params)
```

#### 3.4.2 Relationship Inference

When the schema learner detects a relationship hint (e.g., `agent_email` → `Person`), the graph service automatically creates edges:

```cypher
MATCH (p:Person {email: $agent_email})
MATCH (prop:Property {id: $property_id})
MERGE (p)-[:MANAGES]->(prop)
```

---

### 3.5 Domain-Aware RAG Enhancement

The RAG system should leverage the Company Profile to improve retrieval and generation.

#### 3.5.1 Industry-Aware System Prompt

```python
async def build_system_prompt(self):
    profile = await self.get_company_profile()
    
    prompt = f"""
    You are an AI assistant for {profile.name}, a company in the {profile.industry} industry.
    
    Key domain terminology:
    {json.dumps(profile.domain_terms)}
    
    Entity types in their database:
    {", ".join([e.name for e in profile.entity_types])}
    
    When answering questions:
    - Use industry-specific terminology appropriately
    - Reference their data structures (e.g., "{profile.entity_types[0].name}")
    - Cite sources from their uploaded documents
    """
    
    return prompt
```

#### 3.5.2 Smart Query Classification

Replace hardcoded category classification with dynamic taxonomy:

```python
async def classify_query(self, user_query: str):
    profile = await self.get_company_profile()
    
    prompt = f"""
    User works at {profile.name} ({profile.industry}).
    
    Available document categories: {profile.discovered_categories}
    
    User question: "{user_query}"
    
    Which category is most relevant? Respond with just the category name.
    """
```

---

## 4. Onboarding Flow: Zero-Config Company Setup

> **NOTE**: The goal is that a new customer can start uploading documents immediately, and the system learns everything it needs.

```
User                    System                  AI Engine               Graph DB
 │                        │                        │                        │
 │──Upload first doc─────>│                        │                        │
 │                        │──What company/industry?──>│                     │
 │                        │<──"Acme Corp, Healthcare"─│                     │
 │                        │───────────Create CompanyProfile─────────────────>│
 │                        │                        │                        │
 │──Upload patient CSV───>│                        │                        │
 │                        │──Infer schema from headers──>│                  │
 │                        │<──Entity="Patient", Fields=[name, dob]──│       │
 │                        │───────────Store LearnedSchema───────────────────>│
 │                        │───────────Create Patient nodes──────────────────>│
 │                        │                        │                        │
 │──Ask: "Who is Dr.     │                        │                        │
 │  Smith's oldest       │                        │                        │
 │  patient?"            │                        │                        │
 │                        │──(Uses learned schema)─>│                       │
 │<──"John Doe (DOB: 1945-03-12)"─────────────────│                        │
```

---

## 5. Implementation Phases

### Phase 1: Foundation (1-2 weeks)
| Task | Files | Effort |
|------|-------|--------|
| Create `CompanyProfile` model | [NEW] `backend/company_profile.py` | 2 days |
| Migrate hardcoded categories to DB | `rag.py`, `ingestion.py` | 1 day |
| Add Category Discovery Agent | [NEW] `backend/category_agent.py` | 2 days |
| Remove Barcelona schemas | [DELETE] `schemas.py` | 0.5 day |

### Phase 2: Schema Learning (1-2 weeks)
| Task | Files | Effort |
|------|-------|--------|
| Build Schema Learner | [NEW] `backend/schema_learner.py` | 3 days |
| Refactor CSV service to use dynamic schemas | `csv_service.py` | 2 days |
| Add schema caching in Neo4j | `database.py` | 1 day |

### Phase 3: Adaptive Graph (1 week)
| Task | Files | Effort |
|------|-------|--------|
| Generalize `graph_service.py` | `graph_service.py` | 2 days |
| Dynamic Cypher generation | `database.py` | 1 day |
| Relationship inference | `graph_service.py` | 2 days |

### Phase 4: Smart RAG (1 week)
| Task | Files | Effort |
|------|-------|--------|
| Industry-aware system prompts | `rag.py` | 1 day |
| Dynamic query classification | `rag.py` | 1 day |
| Domain vocabulary learning | [NEW] `backend/vocabulary_learner.py` | 2 days |

---

## 6. User Review Required

> **WARNING**: **Breaking Change**: Existing data will need migration. The current `Listing` and `Person` nodes would need to be re-typed or manually mapped to the new dynamic system.

> **IMPORTANT**: **Questions for You**:
> 1. Should we preserve backward compatibility for existing real estate data, or is a clean slate acceptable?
> 2. What level of human oversight do you want for new categories/schemas? (Fully automatic vs. approval workflow)
> 3. Should the Company Profile be editable via UI, or purely AI-driven?

---

## 7. Verification Plan

### 7.1 Automated Tests
- Unit test Schema Learner with 10+ diverse CSV formats (healthcare, retail, finance)
- Integration test: Upload documents from 3 different industries, verify correct categorization
- Regression test: Ensure real estate documents still work after migration

### 7.2 Manual Verification
- Onboard a test "law firm" with case files, client records, attorney bios
- Verify graph shows `Case`, `Client`, `Attorney` nodes (not `Listing`)
- Ask domain-specific questions and validate answers

---

## 8. Alternatives Considered

### Option A: Industry Templates (Rejected)
Pre-build templates for common industries (Real Estate, Healthcare, Legal).
- **Pros**: Fast for known industries
- **Cons**: Still requires code changes for new industries. Not "self-adapting".

### Option B: Pure AI Everything (Rejected)
Let AI figure out everything with no caching.
- **Pros**: Maximum flexibility
- **Cons**: Slow, expensive, inconsistent across documents

### Option C: Hybrid Learning (Recommended ✓)
AI discovers patterns, system caches them, humans can override.
- **Pros**: Balances flexibility with reliability and cost
- **Cons**: Slightly more complex implementation

---

## 9. Summary

This proposal transforms Davlon from a **real estate-specific tool** into a **universal business intelligence platform** by:

1. **Removing all hardcoded domain assumptions**
2. **Adding a learnable Company Profile**
3. **Implementing AI-driven schema and category discovery**
4. **Making the knowledge graph dynamically typed**
5. **Enhancing RAG with domain-aware context**

The end result: A new customer uploads their first document, and the system starts learning their business model, terminology, and data structures—with zero configuration required.

---

## Related Code Files

When modifying these files, consider updating this proposal:

| File | Relevance |
|------|-----------|
| `backend/schema_learner.py` | Dynamic schema inference |
| `backend/ingestion.py` | Category discovery, schema caching |
| `backend/graph_service.py` | Dynamic entity creation |
| `backend/database.py` | Company profile storage, learned schemas |
| `backend/rag.py` | Domain-aware prompts |

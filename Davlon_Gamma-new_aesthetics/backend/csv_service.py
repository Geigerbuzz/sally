import csv
import json
import os
import google.generativeai as genai
from io import StringIO
from typing import List, Dict, Any, Type, Optional
from pydantic import ValidationError
from backend.schemas import BarcelonaCadastralModel, BarcelonaSurfaceModel
from backend.config import settings

# Configure Gemini
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
except:
    pass

MAPPINGS_FILE = "schema_mappings.json"

class HeaderHarmonizer:
    """
    Uses Gemini to map unknown CSV headers to our canonical Pydantic field aliases.
    """
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            print("WARNING: No GOOGLE_API_KEY found. AI features disabled.")
            self.model = None
        self.mappings = self._load_mappings()

    def _load_mappings(self) -> Dict[str, Dict[str, str]]:
        if os.path.exists(MAPPINGS_FILE):
            try:
                with open(MAPPINGS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_mapping(self, fingerprint: str, mapping: Dict[str, str]):
        self.mappings[fingerprint] = mapping
        with open(MAPPINGS_FILE, 'w') as f:
            json.dump(self.mappings, f, indent=2)

    def _get_fingerprint(self, headers: List[str]) -> str:
        """Creates a unique hash/string for a set of headers."""
        return ",".join(sorted(headers))

    async def harmonize(self, headers: List[str], sample_rows: List[Dict], target_model: str) -> Dict[str, str]:
        """
        Returns a map of {UnknownHeader: CanonicalAlias}.
        Checks local cache first, then calls AI.
        """
        fingerprint = self._get_fingerprint(headers)
        
        # 1. Check Local Stickiness (Learning)
        if fingerprint in self.mappings:
            print(f"Using cached mapping for Schema: {target_model}")
            return self.mappings[fingerprint]

        # 2. Call Gemini (Learning Path)
        print(f"Triggering AI Header Harmonization for: {headers}")
        
        if not self.model:
            print("Skipping AI call: No API Key.")
            return {}
        
        target_fields = []
        if target_model == "Cadastral":
            target_fields = [f.alias for f in BarcelonaCadastralModel.model_fields.values()]
        elif target_model == "Surface":
            target_fields = [f.alias for f in BarcelonaSurfaceModel.model_fields.values()]
        
        prompt = f"""
        I have a CSV with these headers: {headers}.
        I need to map them to my canonical system headers: {target_fields}.
        
        Here is some sample data to help you infer the meaning:
        {json.dumps(sample_rows[:3], ensure_ascii=False)}
        
        Return STRICT JSON key-value pairs where Keys are YOUR headers and Values are MY canonical headers.
        Only map fields you are confident in. If a field has no match, ignore it.
        Example: {{"Region_Code": "Codi_districte"}}
        """
        
        response = self.model.generate_content(prompt)
        try:
            # Clean md blocks if present
            text = response.text.replace("```json", "").replace("```", "")
            mapping = json.loads(text)
            
            # Save for future speed
            self._save_mapping(fingerprint, mapping)
            return mapping
        except Exception as e:
            print(f"AI Harmonization Failed: {e}")
            return {}

class CsvIngestionService:
    """
    Self-Adapting CSV Ingestion Service.
    
    Uses AI-driven schema inference to learn data structures from any CSV,
    not just Barcelona government data. Falls back to legacy schemas when
    detected for backward compatibility.
    """
    
    def __init__(self):
        self.harmonizer = HeaderHarmonizer()
        self._schema_manager = None  # Lazy loaded
    
    def _get_schema_manager(self):
        """Lazy load schema manager to avoid circular imports."""
        if self._schema_manager is None:
            from .schema_learner import SchemaManager
            from .database import db
            self._schema_manager = SchemaManager(db)
        return self._schema_manager
    
    def _detect_legacy_schema(self, headers: list, filename: str):
        """
        Detects if this is a legacy Barcelona schema for backward compatibility.
        Returns (model_class, key) or (None, None).
        """
        if "Valor" in str(headers) or "Value" in str(headers) or "Carrec" in filename:
            return BarcelonaCadastralModel, "Cadastral"
        elif "Superficie" in str(headers) or "Surface" in str(headers) or "Edificacions" in filename:
            return BarcelonaSurfaceModel, "Surface"
        return None, None

    async def ingest_csv(self, file_content: str, filename: str) -> str:
        """
        Main entry point for CSV ingestion.
        
        Now supports:
        1. Legacy Barcelona schemas (backward compat)
        2. Any new schema via AI inference
        
        Returns a Markdown summary for the RAG/Graph pipeline.
        """
        # Parse CSV
        f = StringIO(file_content)
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)  # Read all into memory (assuming <100MB files for now)

        if not headers:
            return "ERROR: Empty CSV."
        
        # 1. Check for legacy Barcelona schemas first (backward compatibility)
        target_model, target_key = self._detect_legacy_schema(headers, filename)
        
        if target_model:
            # Use legacy path for Barcelona data
            return await self._ingest_with_legacy_schema(
                rows, headers, filename, target_model, target_key
            )
        else:
            # NEW: Use dynamic schema inference for any other CSV
            return await self._ingest_with_dynamic_schema(
                rows, headers, filename
            )
    
    async def _ingest_with_dynamic_schema(
        self, 
        rows: list, 
        headers: list, 
        filename: str
    ) -> str:
        """
        Ingests CSV using AI-inferred schema.
        This is the new universal path that works for any industry.
        """
        from .schema_learner import get_schema_manager
        from .database import db
        
        schema_manager = self._get_schema_manager()
        
        # 1. Infer schema from headers + sample data
        schema = await schema_manager.get_or_infer_schema(
            headers=headers,
            sample_rows=rows[:10],
            filename=filename
        )
        
        # 2. Build field mapping
        field_mapping = {f.original_name: f.canonical_name for f in schema.fields}
        
        # 3. Process rows using inferred schema
        processed_count = 0
        from .graph_service import graph_service
        
        for row in rows:
            # Remap to canonical names
            canonical_row = {}
            for original, canonical in field_mapping.items():
                if original in row:
                    canonical_row[canonical] = row[original]
            
            # Create entity in graph with dynamic type
            await self._create_dynamic_entity(
                entity_type=schema.entity_name,
                data=canonical_row,
                source_file=filename,
                schema=schema
            )
            processed_count += 1
        
        # 4. Generate Markdown summary for RAG
        markdown_output = f"# Ingested {processed_count} {schema.entity_name} records\n\n"
        markdown_output += f"**Schema**: {schema.entity_name} (Dynamically Inferred)\n"
        markdown_output += f"**Fields**: {', '.join([f.canonical_name for f in schema.fields])}\n\n"
        
        # Show sample data as table
        if rows:
            markdown_output += "| " + " | ".join(headers[:5]) + " |\n"
            markdown_output += "| " + " | ".join(["---"] * min(5, len(headers))) + " |\n"
            for row in rows[:5]:
                vals = [str(row.get(h, ""))[:30] for h in headers[:5]]
                markdown_output += "| " + " | ".join(vals) + " |\n"
        
        return markdown_output
    
    async def _create_dynamic_entity(
        self, 
        entity_type: str, 
        data: dict, 
        source_file: str,
        schema
    ):
        """
        Creates an entity in Neo4j with dynamically inferred type.
        This replaces the hardcoded create_listing_from_row approach.
        """
        from .database import db
        import uuid
        
        # Build dynamic Cypher query
        props = ", ".join([f"{k}: ${k}" for k in data.keys()])
        
        query = f"""
        MERGE (e:{entity_type} {{id: $id}})
        SET e += {{{props}}},
            e.source_file = $source,
            e.updated_at = datetime()
        RETURN e
        """
        
        params = {
            "id": str(uuid.uuid4()), 
            "source": source_file, 
            **data
        }
        
        try:
            await db.run_query(query, params)
        except Exception as e:
            import logging
            logging.getLogger("davlon-csv").error(f"Failed to create {entity_type}: {e}")
    
    async def _ingest_with_legacy_schema(
        self,
        rows: list,
        headers: list,
        filename: str,
        target_model,
        target_key: str
    ) -> str:
        """
        Legacy ingestion path for Barcelona schemas.
        Maintained for backward compatibility.
        """

        # 2. Attempt Code-First Ingestion (Fast Path)
        validated_objects = []
        mapping = await self.harmonizer.harmonize(headers, rows[:5], target_key)
        
        for row in rows:
            # Apply AI Mapping if exists
            remapped_row = {}
            for original_key, val in row.items():
                # If we have a map for this key, use canonical name. Else keep original.
                canonical_key = mapping.get(original_key, original_key)
                remapped_row[canonical_key] = val
            
            try:
                # FAST PATH: Pydantic Validation
                obj = target_model(**remapped_row)
                validated_objects.append(obj)
            except ValidationError as e:
                # In a strict system we might fail here.
                # In hybrid, we might skip the row or log it.
                # For now, we skip bad rows but continue processing file.
                continue

        # 3. Write to Graph (Persistence)
        # We loop through validated objects and save them
        from backend.graph_service import graph_service
        
        saved_count = 0
        for obj in validated_objects:
            # Convert Pydantic to Dict
            row_data = obj.model_dump()
            
            # Map canonical fields back to what graph_service expects, or update graph_service to handle canonical
            # GraphService.create_listing_from_row expects: Address, Beds, Baths, SqFt, Price, Agent
            # Our Schemas have fields like: district_name, value, etc.
            # Adaptation:
            adapter_row = {
                "Address": f"{obj.neighborhood_name}, {obj.district_name}",
                "Beds": 0, # Not in cadastral data
                "Baths": 0,
                "SqFt": getattr(obj, "surface_m2", 0),
                "Price": getattr(obj, "value", 0),
                "Agent": ""
            }
            await graph_service.create_listing_from_row(adapter_row, filename)
            saved_count += 1

        # 4. Generate Markdown Output for RAG
        markdown_output = f"# Ingested {len(validated_objects)} records for {target_key}\n\n"
        markdown_output += f"Schema: {target_key} (Proven Match)\n"
        markdown_output += f"**Graph Update**: Created {saved_count} nodes in Neo4j.\n\n"
        markdown_output += "| District | Neighborhood | Value/Surface |\n"
        markdown_output += "| :--- | :--- | :--- |\n"
        
        # Show first 10 for RAG context
        for obj in validated_objects[:10]:
            if target_key == "Cadastral":
                 markdown_output += f"| {obj.district_name} | {obj.neighborhood_name} | {obj.value} |\n"
            else:
                 markdown_output += f"| {obj.district_name} | {obj.neighborhood_name} | {obj.surface_m2} m2 |\n"
        
        return markdown_output

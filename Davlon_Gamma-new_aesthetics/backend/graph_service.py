from .database import db
import uuid
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger("davlon-graph")

class GraphService:
    """
    Adaptive Graph Service for Self-Learning RAG System.
    
    Supports both:
    1. Legacy hardcoded entities (Listing, Person) for backward compatibility
    2. Dynamic entity creation from learned schemas (any entity type)
    
    New entities are created with dynamically generated Cypher queries,
    and relationships are inferred from schema hints.
    """
    
    async def create_document_node(self, doc_id: str, filename: str, mime_type: str = "application/octet-stream"):
        """Creates a Document node in Neo4j."""
        query = """
        MERGE (d:Document {id: $id})
        SET d.name = $name,
            d.mimeType = $mime,
            d.uploadedAt = datetime()
        RETURN d
        """
        try:
            await db.run_query(query, {"id": doc_id, "name": filename, "mime": mime_type})
            logger.info(f"Created Document Node: {filename} ({doc_id})")
        except Exception as e:
            logger.error(f"Failed to create Document node: {e}")
    
    # ==================== DYNAMIC ENTITY METHODS (NEW) ====================
    
    async def create_dynamic_entity(
        self, 
        entity_type: str, 
        data: Dict[str, Any], 
        source_file: str,
        relationship_hints: Dict[str, str] = None
    ) -> Optional[str]:
        """
        Creates any entity type dynamically from learned schema.
        
        Args:
            entity_type: The node label (e.g., "Patient", "Invoice", "Employee")
            data: Dictionary of property key-value pairs
            source_file: Source filename for traceability
            relationship_hints: Optional dict of {field_name: target_entity_type}
        
        Returns:
            The created entity ID, or None on failure.
        """
        entity_id = str(uuid.uuid4())
        
        # Build dynamic property assignment
        props = ", ".join([f"{k}: ${k}" for k in data.keys() if k and data[k] is not None])
        
        query = f"""
        MERGE (e:{entity_type} {{id: $id}})
        SET e += {{{props}}},
            e.source_file = $source,
            e.created_at = datetime(),
            e.updated_at = datetime()
        RETURN e.id as id
        """
        
        params = {
            "id": entity_id, 
            "source": source_file, 
            **{k: v for k, v in data.items() if k and v is not None}
        }
        
        try:
            await db.run_query(query, params)
            logger.info(f"Created {entity_type}: {entity_id}")
            
            # Create relationships if hints provided
            if relationship_hints:
                for field_name, target_type in relationship_hints.items():
                    if field_name in data and data[field_name]:
                        await self._create_inferred_relationship(
                            source_id=entity_id,
                            source_type=entity_type,
                            target_value=data[field_name],
                            target_type=target_type,
                            field_name=field_name
                        )
            
            return entity_id
        except Exception as e:
            logger.error(f"Failed to create {entity_type}: {e}")
            return None
    
    async def _create_inferred_relationship(
        self,
        source_id: str,
        source_type: str,
        target_value: str,
        target_type: str,
        field_name: str
    ):
        """
        Creates a relationship between entities based on schema inference.
        
        The relationship type is generated from the field name.
        e.g., "doctor_id" -> "HAS_DOCTOR"
        """
        # Generate relationship type from field name
        rel_name = field_name.upper().replace("_ID", "").replace("_EMAIL", "")
        if not rel_name.startswith("HAS_"):
            rel_name = f"HAS_{rel_name}"
        
        # Find or create target entity
        query = f"""
        MERGE (target:{target_type} {{identifier: $target_value}})
        WITH target
        MATCH (source:{source_type} {{id: $source_id}})
        MERGE (source)-[:{rel_name}]->(target)
        """
        
        try:
            await db.run_query(query, {
                "target_value": str(target_value),
                "source_id": source_id
            })
            logger.info(f"Created relationship: ({source_type})-[:{rel_name}]->({target_type})")
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
    
    async def get_entities_by_type(self, entity_type: str, limit: int = 100) -> list:
        """
        Retrieves entities of a specific type.
        Works with both dynamic and legacy entity types.
        """
        query = f"""
        MATCH (e:{entity_type})
        RETURN e
        ORDER BY e.created_at DESC
        LIMIT $limit
        """
        return await db.run_query(query, {"limit": limit})
    
    async def get_all_entity_types(self) -> list:
        """
        Returns all entity types (node labels) in the database.
        Useful for understanding what the system has learned.
        """
        query = """
        CALL db.labels() YIELD label
        WHERE label <> 'Chunk' AND label <> 'Document' AND label <> 'CompanyProfile' AND label <> 'LearnedSchema'
        RETURN label
        ORDER BY label
        """
        try:
            results = await db.run_query(query)
            return [r['label'] for r in results]
        except Exception as e:
            logger.error(f"Failed to get entity types: {e}")
            return []
    
    # ==================== LEGACY METHODS (Backward Compatibility) ====================

    async def ensure_schema(self):
        """Creates unique constraints for the Graph schema (legacy + new)."""
        queries = [
            # Legacy constraints
            "CREATE CONSTRAINT listing_id IF NOT EXISTS FOR (l:Listing) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT person_email IF NOT EXISTS FOR (p:Person) REQUIRE p.email IS UNIQUE",
            "CREATE INDEX listing_status IF NOT EXISTS FOR (l:Listing) ON (l.status)",
            # New universal constraints
            "CREATE CONSTRAINT company_profile_id IF NOT EXISTS FOR (cp:CompanyProfile) REQUIRE cp.id IS UNIQUE",
        ]
        
        if not db.driver:
            logger.warning("Neo4j driver not ready. Skipping schema creation.")
            return

        async with db.get_session() as session:
            for q in queries:
                try:
                    await session.run(q)
                except Exception as e:
                    # Some constraints may fail on Community Edition - that's OK
                    logger.debug(f"Schema constraint note: {e}")
        
        logger.info("Graph Schema ensured.")

    async def create_listing_from_row(self, row_data: dict, source_file: str):
        """
        Creates a Listing node from a CSV row dictionary.
        Expected keys: Address, Beds, Baths, SqFt, Price, Agent
        """
        listing_id = str(uuid.uuid4())
        
        # Normalize Data
        address = row_data.get("Address", "Unknown Address")
        beds = row_data.get("Beds", 0)
        baths = row_data.get("Baths", 0)
        sqft = row_data.get("SqFt", 0)
        agent_email = row_data.get("Agent", "").strip()
        
        # Default status is YELLOW as per requirements
        status = "yellow" 

        query = """
        MERGE (l:Listing {address: $address})
        ON CREATE SET 
            l.id = $id,
            l.beds = $beds,
            l.baths = $baths,
            l.sqft = $sqft,
            l.status = $status,
            l.created_at = datetime(),
            l.source_file = $source
        ON MATCH SET
            l.last_updated = datetime()
        RETURN l.id as id
        """
        
        params = {
            "address": address,
            "id": listing_id,
            "beds": beds,
            "baths": baths,
            "sqft": sqft,
            "status": status,
            "source": source_file
        }

        try:
            await db.run_query(query, params)
            logger.info(f"Created/Updated Listing: {address}")
            
            # Link to Agent if provided
            if agent_email:
                await self.link_agent_to_listing(agent_email, address)
                
        except Exception as e:
            logger.error(f"Failed to create listing graph: {e}")

    async def link_agent_to_listing(self, agent_email: str, listing_address: str):
        """Links a Person to a Listing via MANAGES relationship."""
        query = """
        MERGE (p:Person {email: $email})
        MERGE (l:Listing {address: $address})
        MERGE (p)-[:MANAGES]->(l)
        """
        try:
            await db.run_query(query, {"email": agent_email, "address": listing_address})
            logger.info(f"Linked Agent {agent_email} to {listing_address}")
        except Exception as e:
            logger.error(f"Failed to link agent: {e}")

    async def get_all_listings(self):
        """Retrieves all listings for the frontend."""
        query = """
        MATCH (l:Listing)
        OPTIONAL MATCH (p:Person)-[:MANAGES]->(l)
        RETURN l, collect(p.email) as agents
        ORDER BY l.created_at DESC
        """
        return await db.run_query(query)

    async def generate_data_request(self, listing_id: str):
        """
        Agentic Workflow: Checks for missing critical data and sends messages to assigned agents.
        """
        # 1. Check for missing data
        query_check = """
        MATCH (l:Listing {id: $id})
        WHERE l.beds = 0 OR l.baths = 0 OR l.sqft = 0
        OPTIONAL MATCH (p:Person)-[:MANAGES]->(l)
        RETURN l, collect(p.email) as agents
        """
        rows = await db.run_query(query_check, {"id": listing_id})
        
        if not rows:
            return # Data is complete or listing not found
            
        row = rows[0]
        listing = row['l']
        agents = row['agents']
        
        if not agents:
            logger.warning(f"Listing {listing_id} has missing data but no assigned agents.")
            return

        # 2. Identify what's missing
        missing_fields = []
        if listing.get('beds', 0) == 0: missing_fields.append("Bedroom Count")
        if listing.get('baths', 0) == 0: missing_fields.append("Bathroom Count")
        if listing.get('sqft', 0) == 0: missing_fields.append("Square Footage")
        
        if not missing_fields:
            return

        # 3. Send Message to EACH Agent
        for agent_email in agents:
            subject = f"Action Required: Missing details for {listing.get('address')}"
            body = f"The listing at {listing.get('address')} is missing: {', '.join(missing_fields)}. Please update the record."
            
            msg_query = """
            MATCH (p:Person {email: $email})
            CREATE (m:Message {
                result_id: randomUUID(),
                subject: $subject,
                body: $body,
                read: false,
                timestamp: datetime(),
                type: 'data_request',
                target_listing: $listing_id
            })
            MERGE (p)-[:HAS_MESSAGE]->(m)
            """
            await db.run_query(msg_query, {
                "email": agent_email,
                "subject": subject,
                "body": body,
                "listing_id": listing_id
            })
            logger.info(f"Agent Action: Sent data request to {agent_email}")

    async def get_inbox_messages(self, email: str = None):
        """
        Fetches all inbox messages including:
        - Regular messages (from Message nodes)
        - Knowledge gap alerts (from UnknownTopic nodes that hit threshold)
        """
        messages = []
        
        # 1. Get regular messages
        if email:
            query = """
            MATCH (p:Person {email: $email})-[:HAS_MESSAGE]->(m:Message)
            RETURN m, 'message' as type
            ORDER BY m.timestamp DESC
            """
            params = {"email": email}
        else:
            query = "MATCH (m:Message) RETURN m, 'message' as type ORDER BY m.timestamp DESC"
            params = {}
            
        regular_messages = await db.run_query(query, params)
        messages.extend(regular_messages)
        
        # 2. Get knowledge gap alerts (threshold: 3 mentions in 7 days)
        gap_alerts = await self._get_knowledge_gap_alerts()
        messages.extend(gap_alerts)
        
        # Sort by timestamp descending
        messages.sort(key=lambda x: x.get('m', {}).get('timestamp', '') or x.get('timestamp', ''), reverse=True)
        
        return messages

    async def _get_knowledge_gap_alerts(self):
        """
        Generate inbox items for knowledge gaps that hit threshold.
        Returns items formatted like Message nodes for UI compatibility.
        """
        gaps = await db.check_knowledge_gaps(threshold=3, days=7)
        alerts = []
        
        for gap in gaps:
            topic = gap['topic']
            mentions = gap['mentions']
            examples = gap.get('examples', [])[:2]  # Max 2 examples
            
            # Format examples for display
            example_text = ""
            if examples:
                example_text = "\n\nExample questions:\n• " + "\n• ".join(examples)
            
            alert = {
                'm': {
                    'id': f"gap_{topic}",
                    'subject': f"📊 Knowledge gap detected: {topic.replace('_', ' ').title()}",
                    'body': f"Users have asked about \"{topic.replace('_', ' ')}\" {mentions} times this week, but I don't have documents about this topic.{example_text}\n\nIs this relevant to your company?",
                    'timestamp': gap.get('last_seen', ''),
                    'type': 'knowledge_gap',
                    'topic': topic,
                    'actions': [
                        {'id': 'remind', 'label': 'Remind me later'},
                        {'id': 'ignore', 'label': 'Not relevant'}
                    ]
                },
                'type': 'knowledge_gap'
            }
            alerts.append(alert)
        
        return alerts

    async def handle_knowledge_gap_action(self, topic: str, action: str):
        """
        Handle user action on a knowledge gap alert.
        
        Actions:
        - 'remind': Snooze for 7 days
        - 'ignore': Mark as notified (won't show again)
        """
        if action == 'ignore':
            await db.mark_topic_notified(topic)
            return {"status": "ok", "message": f"Knowledge gap '{topic}' dismissed"}
        elif action == 'remind':
            # Reset the count to give more time
            query = """
            MATCH (t:UnknownTopic {name: $topic})
            SET t.count = 0, t.last_seen = datetime()
            """
            await db.run_query(query, {"topic": topic})
            return {"status": "ok", "message": f"Will remind you about '{topic}' later"}
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

graph_service = GraphService()

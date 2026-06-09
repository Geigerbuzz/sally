from backend.database import db
from backend.config import settings
import logging
import asyncio

# Simple logging setup for this script
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-bootstrap")

async def bootstrap_async():
    """Initialize Database Constraints and Indexes (Async)."""
    logger.info("Connecting to Neo4j...")
    
    if not settings.NEO4J_URI or not settings.NEO4J_PASSWORD:
        logger.error("Missing Neo4j Credentials via Environment Variables.")
        return

    try:
        await db.connect()
        async with db.get_session() as session:
            # 1. User Constraint
            await session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            logger.info("Ensured Constraint: User.id is UNIQUE")

            # 2. Document Constraint
            await session.run("CREATE CONSTRAINT doc_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
            logger.info("Ensured Constraint: Document.id is UNIQUE")
            
            # 3. Widget Constraint
            await session.run("CREATE CONSTRAINT widget_id_unique IF NOT EXISTS FOR (w:Widget) REQUIRE w.id IS UNIQUE")
            logger.info("Ensured Constraint: Widget.id is UNIQUE")

            # 4. Indexes for Performance (e.g., searching by Name)
            await session.run("CREATE INDEX document_name_idx IF NOT EXISTS FOR (d:Document) ON (d.name)")
            logger.info("Ensured Index: Document.name")

    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
    finally:
        await db.close()
        logger.info("Bootstrap complete.")

def run():
    asyncio.run(bootstrap_async())

if __name__ == "__main__":
    run()

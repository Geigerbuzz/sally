import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

class Settings:
    NEO4J_URI: str = os.getenv("NEO4J_URI", "neo4j+s://demo.databases.neo4j.io")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Feature flags
    SEMANTIC_CHUNKING_ENABLED: bool = os.getenv("SEMANTIC_CHUNKING_ENABLED", "true").lower() == "true"
    
    # Error reporting
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    ERROR_REPORT_EMAIL: str = os.getenv("ERROR_REPORT_EMAIL", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Defaults for local dev
    HOST: str = "0.0.0.0"
    PORT: int = 8000

settings = Settings()

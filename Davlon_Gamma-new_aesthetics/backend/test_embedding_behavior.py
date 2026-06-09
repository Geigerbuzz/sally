import google.generativeai as genai
import os
from dotenv import load_dotenv

# Mock settings just to get the key (assuming .env is present or key is in env)
# If .env is not standard, we might need to source it manually.
# For now, let's try to assume it's in env or we can read from config.
try:
    from backend.config import settings
    genai.configure(api_key=settings.GOOGLE_API_KEY)
except ImportError:
    # Fallback to direct env var if available
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        print("Error: Could not find API key.")
        exit(1)

def test_embedding():
    model = "models/gemini-embedding-001"
    chunks = ["Hello world", "This is a test"]
    
    print(f"Testing embedding with list of {len(chunks)} items...")
    
    try:
        # Test passing list directly
        result = genai.embed_content(
            model=model,
            content=chunks,
            task_type="SEMANTIC_SIMILARITY"
        )
        print("Result keys:", result.keys())
        if 'embedding' in result:
             emb = result['embedding']
             print(f"Embedding type: {type(emb)}")
             if isinstance(emb, list):
                 print(f"Embedding length (outer): {len(emb)}")
                 if len(emb) > 0:
                     print(f"First element type: {type(emb[0])}")
                     if isinstance(emb[0], list):
                         print("Status: BATCH SUCCESS (List of Lists)")
                     else:
                         print("Status: SINGLE VECTOR (Maybe it flattened?)")
        else:
             print("Status: NO 'embedding' KEY")

    except Exception as e:
        print(f"Status: EXCEPTION: {e}")

if __name__ == "__main__":
    test_embedding()

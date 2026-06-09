# Production Step 1: Infrastructure & Environment

**Goal**: Establish the "Iron Triangle" of our backend (Railway + Neo4j Aura + Google Gemini).

## 1. Railway Setup (The Host)
1.  **Create Project**: Initialize a new project in Railway.App.
2.  **Service A (Backend)**: Deploy a Python FastAPI service.
    - *Repo*: Connect your GitHub repo.
    - *Command*: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
    - *Variables*:
        - `GOOGLE_API_KEY`: [Secure]
        - `NEO4J_URI`: `neo4j+s://<id>.databases.neo4j.io`
        - `NEO4J_PASSWORD`: [Secure]
3.  **Service B (Async Queue)**: Deploy a Redis service (from Railway Marketplace).
    - *Purpose*: Handling file upload jobs so the web server doesn't freeze.

## 2. Neo4j Aura Setup (The Graph)
1.  **Instance**: Create a "Free" or "Professional" instance on Neo4j Aura.
2.  **Connection**: Get the URI and Credentials.
3.  **Constraints**: Run the following Cypher commands to set up uniqueness constraints (Prevents duplicates):
    ```cypher
    CREATE CONSTRAINT FOR (u:User) REQUIRE u.id IS UNIQUE;
    CREATE CONSTRAINT FOR (p:Property) REQUIRE p.address IS UNIQUE;
    CREATE CONSTRAINT FOR (c:Company) REQUIRE c.name IS UNIQUE;
    ```

## 3. Google AI Studio (The Brain)
1.  **API Key**: Generate a new key in Google AI Studio.
2.  **Quota Check**: Ensure "File Search" API is enabled for the account.

## 4. Local Development Environment
1.  **Virtual Env**: `python -m venv venv && source venv/bin/activate`.
2.  **Dependencies**:
    ```txt
    fastapi
    uvicorn
    google-generativeai
    neo4j
    python-multipart
    redis
    celery
    ```

# Railway Deployment Actions

**Goal**: Get the "Early Version" live on the web.
**Role**: These are actions **YOU** (the user) need to perform manually.

## 1. Get Your "Keys" (Credentials)
We need to connect the brain (Gemini) and the memory (Neo4j).

- [ ] **Neo4j Aura (The Database)**
    1.  Go to [Neo4j Aura Console](https://console.neo4j.io/).
    2.  Create a **Free Instance**.
    3.  **IMPORTANT**: Download the credentials file immediately. It contains the password which is only shown once.
    4.  You need these 3 values:
        -   `NEO4J_URI` (e.g., `neo4j+s://xxx.databases.neo4j.io`)
        -   `NEO4J_USER` (Default is `neo4j`)
        -   `NEO4J_PASSWORD`

- [ ] **Google AI Studio (The Brain)**
    1.  Go to [Google AI Studio](https://aistudio.google.com/).
    2.  Click **Get API Key**.
    3.  Save the key string (e.g., `AIzaSy...`).

## 2. Prepare the Code
- [ ] **Push to GitHub**
    1.  Create a **Private Repository** on GitHub (e.g., `davlon-beta`).
    2.  Push all the code in this folder to that repository.

## 3. Deploy on Railway
- [ ] **Create Service**
    1.  Log into [Railway.app](https://railway.app/).
    2.  Click **New Project** -> **Deploy from GitHub repo**.
    3.  Select your new `davlon-beta` repo.

- [ ] **Configure Variables**
    *In the Railway Project Dashboard -> "Variables" tab, add:*
    
    | Variable Name | Value |
    | :--- | :--- |
    | `NEO4J_URI` | *Your Neo4j URI* |
    | `NEO4J_USER` | `neo4j` |
    | `NEO4J_PASSWORD` | *Your Neo4j Password* |
    | `GOOGLE_API_KEY` | *Your Google API Key* |
    | `PORT` | `8000` (Optional, but good practice) |

- [ ] **Start Command Override** (Optional / Fallback)
    *Since we added a `Procfile`, Railway should detect this automatically. You only need to do this if the build fails.*
    *In "Settings" tab -> "Deploy" section:*
    -   **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

## 4. Verification
- [ ] **Check Logs**: Ensure it says "Application startup complete".
- [ ] **Visit URL**: Open the public domain provided by Railway.
- [ ] **Test Endpoint**: Go to `/health` (e.g., `https://your-app.railway.app/health`) and check for `{"status": "ok"}`.

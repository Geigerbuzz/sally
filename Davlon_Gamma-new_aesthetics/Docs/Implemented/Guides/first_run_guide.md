# Davlon Beta - First Run Manual

Congratulations! Your code is live. Here is how to verify it and perform your first "Loop" (Upload -> Query).

## 1. Verification (Is it alive?)
1.  **Find your URL**:
    *   **Step 1**: Click the **Architecture** tab at the very top (it's the first tab).
    *   **Step 2**: You will see a big box (card) in the middle of the screen (your service). **Click that box**.
    *   **Step 3**: A new set of tabs will appear for that service. Click **Settings** there.
    *   **Step 4**: Scroll down to **Networking**.
    *   **Step 5**: Click **Generate Domain**.
    *   Copy the URL (e.g., `selfless-beauty-production.up.railway.app`).
2.  **Health Check**:
    *   Open a new browser tab.
    *   Visit: `https://<YOUR_RAILWAY_URL>/health`
    *   **Success**: You see `{"status": "ok"}` on a white screen.

## 2. Test the "Brain" (RAG Pipeline)
*Now let's verify the AI can read and think.*

1.  **Upload a Document**:
    *   Go to your app's main URL (e.g., `https://.../sources.html` or just click the "Data Sources" icon in the dock).
    *   Drag & Drop a PDF (e.g., a contract, a resume, or a financial report).
    *   *Wait for the "Upload Complete" toast.*
2.  **Ask a Question**:
    *   Navigate to **Sessions** (Click the "Chat" icon in the dock).
    *   Type a question relevant to that document (e.g., "What are the payment terms in the contract I just uploaded?").
    *   **Success**: The AI replies with an answer AND a citation chip pointing to your file.

## 3. Test the "Pulse" (Real-Time Websockets)
1.  Open your app in **Window A**.
2.  Open your app in **Window B** (side-by-side).
3.  Navigate to the **Dashboard** (`index.html`) on both.
4.  *Note: We haven't connected the "Live Feed" scripts to the main dashboard widgets yet (that's next on our roadmap), but you can verify the connection is open by checking the browser console (F12) for "WebSocket connected".*

## Troubleshooting
*   **"Internal Server Error" on Upload**: Your `GOOGLE_API_KEY` might be invalid or missing in Railway variables.
*   **"Connection Refused"**: The app crashed. Check the **Deploy Logs** in Railway for the python error message.

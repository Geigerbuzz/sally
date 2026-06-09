# Production Step 2: The Static Data Pipeline (Gemini)

**Goal**: Allow users to upload PDFs and get "Zero Hallucination" answers with citations.

## 1. The "Ingest" Endpoint (`POST /api/upload`)
This endpoint doesn't just save the file; it ships it to Google's Brain.

### Step-by-Step Logic:
1.  **Receive**: Accept `UploadFile` from Frontend.
2.  **Validate**: Check MIME type (PDF, CSV, DOCX only).
3.  **Cache**: Save temporarily to `/tmp/`.
4.  **Upload to Gemini**:
    ```python
    import google.generativeai as genai
    myfile = genai.upload_file(path)
    ```
5.  **Wait**: Poll `myfile.state` until it is `ACTIVE`.
6.  **Store Metadata**: Save the `myfile.uri` and `myfile.name` into **Neo4j** so we know this file exists in our system.
    ```cypher
    CREATE (d:Document {
        name: $filename, 
        uri: $google_uri, 
        status: "active", 
        uploadedAt: datetime()
    })
    ```

## 2. The "Legacy" Flow (Data Freshness)
**Feature**: Auto-move data to "Legacy" tab.

### Logic:
1.  **Tagging**: When uploading, allow an optional `legacy_date` or `quarter` tag.
2.  **Cron Job**: Every night, check documents created > 1 year ago.
3.  **Archive**:
    - Update Neo4j node: `SET d.status = "legacy"`.
    - (Optional) `genai.delete_file(uri)` if you want to stop paying for its storage (user can re-upload if needed), OR keep it for historical queries.

## 3. The Query Interface
When asking a question:
1.  **Fetch**: Frontend sends "Question" + list of "Active File IDs".
2.  **Filter**: Ensure we DO NOT include files marked `status: "legacy"` unless user explicitly toggled "Include Legacy".

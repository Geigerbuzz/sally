# Production Step 3: The Live Data Pipeline (Neo4j)

**Goal**: Ingest structured API feeds (MLS, CRM) into the Graph for relationship mapping.

## 1. The Connector Service
We don't want the main web server doing heavy syncing. Use a **Worker Process** (Celery/Redis).

### Step-by-Step Logic:
1.  **Scheduler**: Run a job every X minutes (e.g., `sync_salesforce`).
2.  **Fetch**: Call the External API (Nango or Direct).
3.  **Clean**: Normalize data (e.g., ensure `price` is an Integer, not string "$500k").
4.  **Upsert to Graph**:
    ```python
    # Use MERGE to avoid duplicates
    query = """
    UNWIND $leads AS row
    MERGE (l:Lead {email: row.email})
    SET l.name = row.name, l.score = row.score
    MERGE (a:Agent {id: row.agent_id})
    MERGE (l)-[:ASSIGNED_TO]->(a)
    """
    session.run(query, leads=leads_data)
    ```

## 2. The "Sentinel" Anomaly Detector
As data flows in, we check for shocks.

### Logic:
1.  **Thresholds**: Define rules (e.g., "Price change > 20% in 1 hour").
2.  **Check**: Before committing the transaction, compare `new_value` vs `old_value`.
3.  **Alert**: If threshold breached:
    - Create an `(Alert)` node in Neo4j.
    - Push valid JSON to Frontend WebSocket topic `alerts`.

## 3. Visualization
1.  **Frontend**: The "Live" tab in Sources page subscribes to the `sync_status` of these workers.
2.  **Display**: Show "Last Synced: 2 mins ago" (Green Dot).

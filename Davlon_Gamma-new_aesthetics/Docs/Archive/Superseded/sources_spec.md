# Technical Specification: Data Sources (sources.html)

## Overview
The ingestion point for the "Zero-Hallucination" Data Pipeline.

## Functional Requirements

### 1. File Ingestion Pipeline
- **Upload Handler**: Chunked upload support for large files (1GB+).
- **Queue System**: Implementation of a job queue (BullMQ / RabbitMQ) to handle processing asynchronously.
- **Processing Steps**:
    1.  **OCR/Extraction**: Extract text from PDF/Images.
    2.  **Cleaning**: Remove noise.
    3.  **Chunking**: Split into semantic vectors.
    4.  **Indexing**: upsert to Pinecone (Vector DB) and Neo4j (Graph DB).

### 2. Live Data Connectors
- **API Integrations**: Built-in adapters for MLS (Multiple Listing Service), Zillow, and County Recorder APIs.
- **Scheduling**: Cron jobs to fetch and update live data every X hours.

### 3. Neural Network Visualization
- **State mapping**: The canvas animation should reflect *actual system load*.
    - **Nodes**: Represent active data clusters.
    - **Speed**: Represents ingestion throughput.
    - **Color**: Represents data health or type.

## Technical Debt (Demo to Prod)
- The canvas animation runs constantly. It should respect `Page Visibility API` to pause when the tab is backgrounded to save battery.
- The "Connect" button currently does nothing; needs an OAuth flow for external services.

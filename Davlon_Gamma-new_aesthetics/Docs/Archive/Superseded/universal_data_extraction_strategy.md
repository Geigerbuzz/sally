---
title: Universal Data Extraction Strategy
status: draft
type: proposal
created: 2025-12-18
updated: 2025-12-28
tags: [extraction, ingestion, formats, vision]
parent: null
children: []
related:
  - ./high_fidelity_extraction_proposal.md
  - ./multimodal_ingestion_proposal.md
---

# Proposal: Universal Data Extraction Strategy

---

## Implementation Status

| Feature | Status | Implemented | Code Reference |
|---------|--------|-------------|----------------|
| [PDF Extraction](#21-pdf-portable-document-format) | ✅ Complete | 2025-12-18 | `ingestion.py` |
| [DOCX Extraction](#22-word-documents-docx) | ✅ Complete | 2025-12-20 | `ingestion.py` |
| [XLSX/CSV Extraction](#23-excel-spreadsheets-xlsx-csv) | ✅ Complete | 2025-12-18 | `ingestion.py` |
| [PPTX Extraction](#24-powerpoint-pptx) | ⬜ Pending | — | — |
| [Image Analysis](#25-plain-images-jpg-png) | ⬜ Pending | — | — |
| [Visual Data Standard](#3-the-visual-data-standard) | ⬜ Pending | — | — |

> **Depends on**: [Ingestion Pipeline Master](../../Implemented/Masters/ingestion_pipeline_master.md)  
> **Affects**: [High-Fidelity Extraction](./high_fidelity_extraction_proposal.md), [Multimodal Ingestion](./multimodal_ingestion_proposal.md)

---

## 1. The Core Philosophy: "Deterministic Foundation, AI Eyes"
To achieve maximum precision, we must standardize the "High-Fidelity" approach across **all** file formats.
1.  **Deterministic Layer**: Use code to read Text and Tables. (0% Hallucination).
2.  **AI Visual Layer**: Use Multimodal AI (Gemini 2.5 Flash Lite) *only* to interpret "Opaque" objects like Charts, Graphs, and Photos.

## 2. Format-Specific Extraction Strategies

### 2.1 PDF (Portable Document Format)
*Current Status: Implemented.*
- **Text**: `PyMuPDF` / `fitz` (Deterministic).
- **Tables**: `pdfplumber` (Deterministic).
- **Visuals**: Extract images -> Gemini 2.5 Flash Lite -> Caption/Trend Analysis.

### 2.2 Word Documents (.docx)
*Challenge*: Often contain embedded charts (Excel objects) or pasted images.
- **Text & Tables**: `python-docx` library.
    - *Action*: Extract paragraphs and tables preserving hierarchy (Header 1 -> Markdown `#`).
- **Visuals**:
    - Iterate through `document.inline_shapes`.
    - Extract binary image data (`blob`).
    - **Action**: Send to Gemini 2.5 Flash Lite.
    - *Prompt*: "Analyze this chart from a business document. Extract the key data points and trends."

### 2.3 Excel Spreadsheets (.xlsx, .csv)
*Challenge*: The grid is easy, but embedded "Charts" are separate objects.
- **Data Grid (Rows/Cols)**: `pandas` / `openpyxl`.
    - *Action*: Convert to Markdown Tables (or JSON if massive).
- **Visuals (Embedded Charts)**:
    - Use `openpyxl` drawing loader to find chart objects.
    - *Difficulty*: Extracting a rendered image of an Excel chart purely via Python backend (headless) is notoriously hard.
    - *Solution*: We focus on the **Source Data**. In Excel, the chart is driven by data *in the sheet*. We read the *data*, not the pixels.
    - *Fallback*: If it's a "Pasted Image" inside Excel, we extract it as an image and use Gemini.

### 2.4 PowerPoint (.pptx)
*Strategy*: **Convert to PDF**.
- **Transformation**: We will convert the slide deck into a PDF document.
- **Pipeline Reuse**: This allows us to feed the file directly into our robust **PDF Pipeline** (Section 2.1), leveraging the existing Text + Table + Image Captioning logic without writing new parsers for slides.
- **Implementation**: Requires a headless conversion tool (e.g., LibreOffice) or a Python-native re-renderer. If unavailable, we fallback to extracting slide images and treating them as the "Visual Layer" directly.

### 2.5 Plain Images (.jpg, .png)
e.g., A photo of a printed memo or a screenshot of a dashboard.
- **Strategy**: Pure Gemini 2.5 Flash Lite.
- *Prompt*: "Transcribe all text from this image and describe any visual data visualizations in detail."

## 3. The "Visual Data" Standard
For every graph/chart found (regardless of source format), the output must be standardized in the Markdown:

```markdown
![Chart_ID](placeholder)
**Visual Analysis**:
- **Type**: Bar Chart
- **X-Axis**: Q1-Q4 2024
- **Y-Axis**: Revenue (in Millions)
- **Trend**: Consistent growth, peaking in Q4 at $12M.
- **Key Insight**: Q4 performance exceeded targets by 15%.
```

This ensures that when the AI answers "How did we do in Q4?", it has the *data* from the graph, not just "There is a chart."

## 4. Implementation Priority
1.  **Word (DOCX)**: Highest priority extension.
2.  **Excel (XLSX)**: Data extraction is trivial; chart handling requires logic.
3.  **Images**: Simple pipeline addition.

## 5. Summary Table
| Format | Text Tool | Table Tool | Chart/Graph Strategy |
| :--- | :--- | :--- | :--- |
| **PDF** | `fitz` | `pdfplumber` | Extract Image -> Gemini |
| **DOCX** | `python-docx` | `python-docx` | Extract Shape -> Gemini |
| **XLSX** | `pandas` | `pandas` | Read Source Data (Primary) / Extract Image (Secondary) |
| **PPTX** | `python-pptx` | `python-pptx` | Extract Image -> Gemini |
| **IMG** | OCR (Gemini) | OCR (Gemini) | Full Visual Analysis (Gemini) |

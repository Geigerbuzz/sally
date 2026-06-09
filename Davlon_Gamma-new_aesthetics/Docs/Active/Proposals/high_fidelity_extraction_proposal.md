---
title: High-Fidelity Deterministic Extraction
status: draft
type: proposal
created: 2025-12-18
updated: 2026-01-08
tags: [extraction, pdf, docx, xlsx, ingestion]
parent: null
children: []
related:
  - ./multimodal_ingestion_proposal.md
---

# Proposal: High-Fidelity "Deterministic" Extraction

> **Goal**: Extract *everything* from every document. Zero hallucination. Zero compression.

---

## Implementation Status

| Format | Status | Code Reference |
|--------|--------|----------------|
| [PDF](#pdf-extraction) | 🔄 Partial | `ingestion.py` |
| [DOCX](#docx-extraction) | 🔄 Partial | `ingestion.py` |
| [XLSX](#xlsx-extraction) | ⬜ Pending | — |
| [PPTX](#pptx-extraction) | ⬜ Pending | — |
| [HTML](#html-extraction) | ⬜ Pending | — |
| [Plain Text (CSV/TXT/MD/JSON)](#plain-text-formats) | ✅ Complete | `ingestion.py` |
| [Document Organization](#3-document-organization-preservation) | ⬜ Pending | — |

> **Depends on**: [Ingestion Pipeline Master](../../Implemented/Masters/ingestion_pipeline_master.md)

---

## 1. Core Philosophy

Three non-negotiable principles govern all extraction:

### Principle 1: Deterministic Over Probabilistic
Code reads bytes directly. No AI "guessing" text or numbers.
- ✅ `fitz.get_text()` reading PDF character streams
- ❌ Vision model "reading" a screenshot of a table

### Principle 2: AI Only Where Unavoidable
AI is used *exclusively* for:
- Captioning images/charts
- Describing visual layouts

Never for reading text, numbers, or table data.

### Principle 3: Zero Compression (Total Fidelity)
**Extract everything. Discard nothing.**

| Must Preserve | Examples |
|---------------|----------|
| Content | Text, tables, lists |
| Formatting | Fonts, colors (hex), sizes, bold/italic |
| Structure | Headers, footers, page numbers, sections |
| Metadata | Author, dates, revision count |
| Annotations | Comments, highlights, tracked changes |
| Embedded | Images, charts, hyperlinks |

> **Test Case**: *"What is the hex color of the footer text on page 3?"* — The system must answer.

---

## 2. Format Extraction Pipelines

### PDF Extraction

**Library**: `PyMuPDF` (fitz)

**Capability Matrix**:
| Data | Method | Output |
|------|--------|--------|
| Text | `page.get_text("dict")` | Text + position + font |
| Color | `span["color"]` | RGB int → hex |
| Images | `page.get_images()` | Binary blobs |
| Metadata | `doc.metadata` | Author, dates, title |
| Links | `page.get_links()` | URLs + positions |
| Annotations | `page.annots()` | Comments, highlights |

**Extraction Snippet**:
```python
import fitz

def extract_pdf(file_bytes: bytes) -> dict:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    result = {"metadata": doc.metadata, "pages": []}
    
    for page in doc:
        page_data = {"blocks": []}
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        page_data["blocks"].append({
                            "text": span["text"],
                            "font": span["font"],
                            "size": span["size"],
                            "color_hex": f"#{span.get('color', 0):06X}",
                            "bbox": span["bbox"]
                        })
        result["pages"].append(page_data)
    return result
```

---

### DOCX Extraction

**Library**: `python-docx` + `zipfile` + `lxml`

**Capability Matrix**:
| Data | Method | Output |
|------|--------|--------|
| Text | `Document().paragraphs` | Paragraphs + runs |
| Formatting | `run.font.*` | Bold, italic, color hex |
| Tables | `Document().tables` | Cell-by-cell data |
| Images | `zipfile` → `word/media/` | Binary blobs |
| Metadata | `zipfile` → `docProps/core.xml` | Author, dates, revision |
| Headers/Footers | `section.header/footer` | Per-section text |
| Comments | `zipfile` → `word/comments.xml` | Author, date, text |

**Extraction Snippet**:
```python
from docx import Document
import zipfile
from io import BytesIO

def extract_docx(file_bytes: bytes) -> dict:
    result = {"metadata": {}, "content": [], "images": []}
    
    # Metadata from ZIP
    with zipfile.ZipFile(BytesIO(file_bytes)) as zf:
        for name in zf.namelist():
            if name.startswith('word/media/'):
                result["images"].append({"name": name, "data": zf.read(name)})
    
    # Content with formatting
    doc = Document(BytesIO(file_bytes))
    for para in doc.paragraphs:
        para_data = {"text": para.text, "runs": []}
        for run in para.runs:
            para_data["runs"].append({
                "text": run.text,
                "bold": run.bold,
                "italic": run.italic,
                "font": run.font.name,
                "size_pt": run.font.size.pt if run.font.size else None,
                "color_hex": str(run.font.color.rgb) if run.font.color.rgb else None
            })
        result["content"].append(para_data)
    return result
```

---

### XLSX Extraction

**Library**: `openpyxl`

**Capability Matrix**:
| Data | Method | Output |
|------|--------|--------|
| Cell values | `cell.value` | Raw data |
| Formulas | `cell.value` (if `data_only=False`) | Formula strings |
| Formatting | `cell.font`, `cell.fill` | Color, bold, etc. |
| Sheet names | `workbook.sheetnames` | List of sheets |
| Comments | `cell.comment` | Author + text |
| Merged cells | `sheet.merged_cells` | Ranges |

**Extraction Snippet**:
```python
from openpyxl import load_workbook
from io import BytesIO

def extract_xlsx(file_bytes: bytes) -> dict:
    wb = load_workbook(BytesIO(file_bytes))
    result = {"sheets": []}
    
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        sheet_data = {"name": sheet_name, "rows": []}
        
        for row in sheet.iter_rows():
            row_data = []
            for cell in row:
                cell_info = {
                    "value": cell.value,
                    "font_name": cell.font.name,
                    "font_bold": cell.font.bold,
                    "font_color": cell.font.color.rgb if cell.font.color else None,
                    "fill_color": cell.fill.fgColor.rgb if cell.fill.fgColor else None,
                    "comment": cell.comment.text if cell.comment else None
                }
                row_data.append(cell_info)
            sheet_data["rows"].append(row_data)
        result["sheets"].append(sheet_data)
    return result
```

---

### PPTX Extraction

**Library**: `python-pptx`

**Capability Matrix**:
| Data | Method | Output |
|------|--------|--------|
| Slides | `Presentation().slides` | Slide objects |
| Shapes/Text | `shape.text_frame` | Text + formatting |
| Images | `shape.image` | Binary blobs |
| Notes | `slide.notes_slide` | Speaker notes |
| Metadata | `prs.core_properties` | Author, dates |

**Extraction Snippet**:
```python
from pptx import Presentation
from io import BytesIO

def extract_pptx(file_bytes: bytes) -> dict:
    prs = Presentation(BytesIO(file_bytes))
    result = {"slides": [], "metadata": {
        "author": prs.core_properties.author,
        "created": str(prs.core_properties.created)
    }}
    
    for slide_num, slide in enumerate(prs.slides, 1):
        slide_data = {"slide": slide_num, "shapes": [], "notes": None}
        
        for shape in slide.shapes:
            if shape.has_text_frame:
                slide_data["shapes"].append({"text": shape.text})
            if hasattr(shape, "image"):
                slide_data["shapes"].append({"image": shape.image.blob})
        
        if slide.has_notes_slide:
            slide_data["notes"] = slide.notes_slide.notes_text_frame.text
        
        result["slides"].append(slide_data)
    return result
```

---

### HTML Extraction

**Library**: `BeautifulSoup` + `lxml`

**Capability Matrix**:
| Data | Method | Output |
|------|--------|--------|
| Text | `soup.get_text()` | Raw text |
| Structure | DOM traversal | Full hierarchy |
| Styles | Inline `style` attr | CSS properties |
| Metadata | `<meta>` tags | Description, author |
| Links | `<a href>` | URLs |
| Images | `<img src>` | URLs/base64 |

---

### Plain Text Formats

| Format | Notes |
|--------|-------|
| **CSV** | Already fully structured. Parse with `pandas`. |
| **TXT** | No formatting. Raw read. |
| **MD** | Preserve as-is (semantic format). |
| **JSON** | Already structured. Parse directly. |

These formats have no hidden metadata — content = everything.

## 3. Document Organization Preservation

**Critical requirement**: Preserve the spatial and structural context of every element.

### What Must Be Preserved

| Context Type | Examples | Why It Matters |
|--------------|----------|----------------|
| **Page numbers** | "Page 27 of 45" | Citations, navigation, "where did I read that?" |
| **Chapters/Sections** | "Chapter 4: Financial Results" | Semantic grouping, topic boundaries |
| **Proximity** | Graph appears next to paragraph | The graph illustrates that paragraph |
| **Reading order** | Text block A comes before B | Narrative flow |
| **Spatial position** | Top-left, bottom-right, sidebar | Layout semantics (sidebars vs main content) |

### Enriched Markdown Output Format

We output **directly to Markdown** (no JSON intermediate). Structure annotations are embedded as HTML comments for RAG context:

```markdown
---
source: annual_report_2024.pdf
author: Jane Smith
created: 2025-01-05T10:00:00Z
total_pages: 45
---

<!-- PAGE 1 -->
# Annual Report 2024

This document contains our financial results...

---

<!-- PAGE 27 -->
<!-- SECTION: Chapter 4 - Financial Results -->
## Chapter 4: Financial Results

<!-- BLOCK: text, bbox:(72,100,540,200) -->
Our Q4 performance exceeded expectations, driven by strong sales in the enterprise segment.
<!-- formatting: font=Arial, size=11pt, color=#333333 -->

<!-- BLOCK: image, bbox:(72,220,300,400), adjacent_to:previous_text -->
![Chart: Q4 Revenue Breakdown](chart_page27_001.png)
**Visual Analysis**:
- **Type**: Bar Chart
- **Data**: Enterprise=$8M, SMB=$3M, Consumer=$1.5M
- **Key Insight**: Enterprise accounts for 64% of revenue
<!-- /BLOCK -->

<!-- BLOCK: table, bbox:(320,220,540,350) -->
| Segment | Q3 | Q4 | Growth |
|---------|----|----|--------|
| Enterprise | $6.5M | $8M | +23% |
| SMB | $2.8M | $3M | +7% |
<!-- /BLOCK -->

---

<!-- PAGE 28 -->
...
```

### How Proximity Is Captured

Using bounding boxes (`bbox`) from extraction, we calculate adjacency:

```python
def calculate_proximity(blocks: list) -> list:
    """Annotate blocks with their neighbors."""
    for i, block in enumerate(blocks):
        block["adjacent_to"] = []
        for j, other in enumerate(blocks):
            if i != j and boxes_are_adjacent(block["bbox"], other["bbox"]):
                block["adjacent_to"].append(j)
    return blocks

def boxes_are_adjacent(box1, box2, threshold=50) -> bool:
    """Check if two bounding boxes are within threshold pixels."""
    # Returns True if boxes share an edge or are close
    ...
```

### Section/Chapter Detection

For PDFs without explicit bookmarks, we infer structure from formatting:

```python
def detect_sections(blocks: list) -> list:
    """Detect chapters/sections based on font size and style."""
    current_section = None
    for block in blocks:
        # Large bold text = likely a heading
        if block["size"] >= 16 and block.get("bold"):
            current_section = block["text"]
        block["section"] = current_section
    return blocks
```

### Output Structure Summary

| Element | How It's Represented |
|---------|---------------------|
| Page breaks | `<!-- PAGE N -->` |
| Sections | `<!-- SECTION: Title -->` |
| Blocks | `<!-- BLOCK: type, bbox, adjacency -->` |
| Formatting | `<!-- formatting: details -->` |
| Images | Standard Markdown `![]()`  + Visual Analysis |
| Tables | Standard Markdown tables |

This allows queries like:
- *"What's on page 27?"* → Filter by `<!-- PAGE 27 -->`
- *"What graph is related to the enterprise discussion?"* → Check `adjacent_to`
- *"What's in Chapter 4?"* → Filter by `<!-- SECTION: Chapter 4 -->`

---

## 4. Comparison

| Method | Text | Tables | Images | Formatting | Metadata | Hallucination |
|--------|------|--------|--------|------------|----------|---------------|
| Vision-only | ⚠️ | ⚠️ | ✅ | ❌ | ❌ | **High** |
| Basic parser | ✅ | ❌ | ❌ | ❌ | ❌ | None |
| **This proposal** | ✅ | ✅ | ✅ | ✅ | ✅ | **Zero** |

---

## 5. Visual Data Standard (AI Layer)

For every chart/graph found (regardless of source format), AI analysis must produce a standardized output:

### Chart Analysis Prompt
```
Analyze this chart from a business document. Extract:
1. Chart type (bar, line, pie, etc.)
2. Axis labels and units
3. All data points visible
4. Key trends or patterns
5. Notable insights

Do NOT infer or estimate values. Report only what is clearly visible.
```

### Standardized Output Format
```markdown
![Chart: Q4 Revenue](chart_001.png)

**Visual Analysis**:
- **Type**: Bar Chart
- **X-Axis**: Q1-Q4 2024
- **Y-Axis**: Revenue (in Millions USD)
- **Data Points**: Q1=$8M, Q2=$9.5M, Q3=$10M, Q4=$12M
- **Trend**: Consistent growth, peaking in Q4
- **Key Insight**: Q4 exceeded Q3 by 20%
```

This ensures when users ask *"How did we do in Q4?"*, the system has actual data from the chart, not just *"There is a chart."*

### When AI Is Used

| Source | Trigger | Action |
|--------|---------|--------|
| PDF | Embedded image detected | Extract blob → Gemini caption |
| DOCX | `inline_shapes` found | Extract blob → Gemini caption |
| XLSX | Pasted image (not chart object) | Extract blob → Gemini caption |
| PPTX | Shape with image | Extract blob → Gemini caption |
| Plain image | `.jpg`, `.png` upload | Full OCR + visual analysis |

> **Note**: For Excel charts, prefer reading the **source data cells** over analyzing the chart image.

---

## 6. Implementation Priority

| Priority | Format | Reason |
|----------|--------|--------|
| 1 | PDF | Most common business document |
| 2 | DOCX | Second most common, rich formatting |
| 3 | XLSX | Data-heavy, charts common |
| 4 | PPTX | Presentations with embedded visuals |
| 5 | HTML | Web content scraping |
| 6 | Images | OCR fallback |


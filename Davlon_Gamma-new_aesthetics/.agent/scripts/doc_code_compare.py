#!/usr/bin/env python3
"""
doc_code_compare.py — Use LLM to compare documentation against code.

Run from project root:
    python .agent/scripts/doc_code_compare.py <doc_path>

Example:
    python .agent/scripts/doc_code_compare.py Docs/Active/Proposals/rag_retrieval_improvements_proposal.md

Requires: GOOGLE_API_KEY environment variable

This tool:
1. Reads the proposal document
2. Extracts related code files from the "Related Code Files" section
3. Reads the actual code files
4. Asks an LLM: "Does the documentation still match the implementation?"
"""

import os
import sys
import re
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai not installed.")
    print("   Run: pip install google-generativeai")
    sys.exit(1)

# Configuration
CODE_FILE_PATTERN = re.compile(r'\| `([^`]+)` \|')
MAX_CODE_CHARS = 8000  # Limit code context to avoid token limits
MAX_DOC_CHARS = 12000


def get_api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("❌ GOOGLE_API_KEY environment variable not set.")
        sys.exit(1)
    return key


def extract_related_code_files(doc_content: str) -> list:
    """Extract code files from Related Code Files section."""
    if "## Related Code Files" not in doc_content:
        return []
    
    section_start = doc_content.find("## Related Code Files")
    section = doc_content[section_start:]
    
    return CODE_FILE_PATTERN.findall(section)


def read_code_files(code_paths: list) -> dict:
    """Read content of code files."""
    code_contents = {}
    total_chars = 0
    
    for code_path in code_paths:
        path = Path(code_path)
        if path.exists():
            content = path.read_text()
            # Truncate if too long
            if total_chars + len(content) > MAX_CODE_CHARS:
                remaining = MAX_CODE_CHARS - total_chars
                if remaining > 500:
                    content = content[:remaining] + "\n\n... [truncated]"
                else:
                    continue
            code_contents[code_path] = content
            total_chars += len(content)
    
    return code_contents


def compare_doc_to_code(doc_path: str, doc_content: str, code_contents: dict) -> str:
    """Use Gemini to compare doc against code."""
    
    # Build code context
    code_context = ""
    for path, content in code_contents.items():
        code_context += f"\n\n### {path}\n```python\n{content}\n```"
    
    prompt = f"""You are a documentation reviewer. Compare the following proposal document against the actual code implementation.

## Document: {doc_path}

{doc_content[:MAX_DOC_CHARS]}

## Actual Code Files
{code_context}

---

## Your Task

Analyze whether the documentation accurately describes the current code implementation. 

Report:

### ✅ Accurate Descriptions
List 2-3 things the doc correctly describes about the code.

### ⚠️ Potential Mismatches
List any descriptions in the doc that don't match the code. For each:
- Quote the doc claim
- Describe what the code actually does
- Rate severity: LOW / MEDIUM / HIGH

### 📝 Missing from Docs
List any important code behavior not mentioned in the docs.

### 🎯 Overall Assessment
Give an overall freshness rating: FRESH / SLIGHTLY_STALE / STALE / VERY_STALE

Be specific and cite line numbers or function names where relevant.
"""

    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    response = model.generate_content(prompt)
    return response.text


def main():
    if len(sys.argv) < 2:
        print("Usage: python doc_code_compare.py <doc_path>")
        print("Example: python doc_code_compare.py Docs/Active/Proposals/rag_retrieval_improvements_proposal.md")
        sys.exit(1)
    
    doc_path = sys.argv[1]
    
    if not Path(doc_path).exists():
        print(f"❌ Document not found: {doc_path}")
        sys.exit(1)
    
    print(f"📄 Reading document: {doc_path}")
    doc_content = Path(doc_path).read_text()
    
    print("🔍 Extracting related code files...")
    code_files = extract_related_code_files(doc_content)
    
    if not code_files:
        print("⚠️  No 'Related Code Files' section found in document.")
        print("   Add this section to enable comparison.")
        sys.exit(1)
    
    print(f"   Found {len(code_files)} related files: {', '.join(code_files)}")
    
    print("📂 Reading code files...")
    code_contents = read_code_files(code_files)
    
    if not code_contents:
        print("⚠️  None of the related code files exist.")
        sys.exit(1)
    
    print(f"   Read {len(code_contents)} files")
    
    print("\n🤖 Asking LLM to compare doc vs code...\n")
    print("=" * 70)
    
    result = compare_doc_to_code(doc_path, doc_content, code_contents)
    print(result)
    
    print("=" * 70)
    print("\n✅ Comparison complete.")


if __name__ == "__main__":
    main()

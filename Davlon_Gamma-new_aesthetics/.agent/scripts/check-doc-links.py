#!/usr/bin/env python3
"""
check-doc-links.py — Validate documentation links and find stale references.

Run from project root:
    python .agent/scripts/check-doc-links.py

Checks:
    1. Related Code Files sections → Do the code files exist?
    2. Depends on / Affects links → Do target docs/anchors exist?
    3. Frontmatter related: links → Do target files exist?
    4. CODE_TO_DOC_INDEX.md → Are all referenced docs valid?
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Configuration
DOCS_ROOT = Path("Docs")
ACTIVE_PROPOSALS = DOCS_ROOT / "Active" / "Proposals"
IMPLEMENTED_MASTERS = DOCS_ROOT / "Implemented" / "Masters"
CODE_INDEX = DOCS_ROOT / "CODE_TO_DOC_INDEX.md"

# Patterns
MARKDOWN_LINK = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
DEPENDS_ON = re.compile(r'\*\*Depends on\*\*:(.+)', re.MULTILINE)
AFFECTS = re.compile(r'\*\*Affects\*\*:(.+)', re.MULTILINE)
CODE_FILE_ROW = re.compile(r'\| `([^`]+)` \|')

class IssueType:
    BROKEN_LINK = "❌ Broken Link"
    MISSING_FILE = "❌ Missing File"
    MISSING_ANCHOR = "⚠️ Missing Anchor"
    STALE_CODE_REF = "⚠️ Stale Code Reference"

issues: List[Tuple[str, str, str, str]] = []  # (file, issue_type, link, details)

def check_file_exists(base_path: Path, link: str) -> bool:
    """Check if a relative link points to an existing file."""
    if link.startswith('http'):
        return True  # Skip external links
    
    # Remove anchor
    path_only = link.split('#')[0]
    if not path_only:
        return True  # Anchor-only link
    
    target = (base_path.parent / path_only).resolve()
    return target.exists()

def extract_links(content: str) -> List[str]:
    """Extract all markdown links from content."""
    return [match[1] for match in MARKDOWN_LINK.findall(content)]

def check_dependency_links(file_path: Path, content: str):
    """Check Depends on and Affects links."""
    for pattern, pattern_name in [(DEPENDS_ON, "Depends on"), (AFFECTS, "Affects")]:
        matches = pattern.findall(content)
        for match in matches:
            links = MARKDOWN_LINK.findall(match)
            for text, link in links:
                if not check_file_exists(file_path, link):
                    issues.append((
                        str(file_path),
                        IssueType.BROKEN_LINK,
                        link,
                        f"In {pattern_name} section"
                    ))

def check_code_references(file_path: Path, content: str):
    """Check that referenced code files exist."""
    if "## Related Code Files" not in content:
        return
    
    # Extract section
    section_start = content.find("## Related Code Files")
    section = content[section_start:]
    
    for match in CODE_FILE_ROW.findall(section):
        code_path = Path(match)
        if not code_path.exists():
            issues.append((
                str(file_path),
                IssueType.STALE_CODE_REF,
                match,
                "Code file no longer exists"
            ))

def check_frontmatter_links(file_path: Path, content: str):
    """Check related: links in frontmatter."""
    if not content.startswith('---'):
        return
    
    # Extract frontmatter
    end = content.find('---', 3)
    if end == -1:
        return
    
    frontmatter = content[3:end]
    
    # Find related: section
    if 'related:' not in frontmatter:
        return
    
    lines = frontmatter.split('\n')
    in_related = False
    for line in lines:
        if 'related:' in line:
            in_related = True
            continue
        if in_related:
            if line.strip().startswith('-'):
                path = line.strip().lstrip('- ').strip()
                if not check_file_exists(file_path, path):
                    issues.append((
                        str(file_path),
                        IssueType.BROKEN_LINK,
                        path,
                        "In frontmatter related: section"
                    ))
            elif line.strip() and not line.startswith(' '):
                in_related = False

def scan_proposals():
    """Scan all proposals for link issues."""
    for proposal in ACTIVE_PROPOSALS.glob("*.md"):
        content = proposal.read_text()
        check_dependency_links(proposal, content)
        check_code_references(proposal, content)
        check_frontmatter_links(proposal, content)

def scan_masters():
    """Scan master docs for link issues."""
    if IMPLEMENTED_MASTERS.exists():
        for master in IMPLEMENTED_MASTERS.glob("*.md"):
            content = master.read_text()
            check_dependency_links(master, content)
            check_frontmatter_links(master, content)

def scan_code_index():
    """Validate CODE_TO_DOC_INDEX.md references."""
    if not CODE_INDEX.exists():
        return
    
    content = CODE_INDEX.read_text()
    links = extract_links(content)
    
    for link in links:
        if not check_file_exists(CODE_INDEX, link):
            issues.append((
                str(CODE_INDEX),
                IssueType.BROKEN_LINK,
                link,
                "Document moved or deleted"
            ))

def main():
    print("🔍 Checking documentation links...\n")
    
    scan_proposals()
    scan_masters()
    scan_code_index()
    
    if not issues:
        print("✅ All links valid!")
        return 0
    
    print(f"Found {len(issues)} issue(s):\n")
    
    current_file = None
    for file_path, issue_type, link, details in sorted(issues):
        if file_path != current_file:
            print(f"\n📄 {file_path}")
            current_file = file_path
        print(f"   {issue_type}: {link}")
        print(f"      → {details}")
    
    print(f"\n❗ {len(issues)} issue(s) found. Run /sync-links to fix.")
    return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
freshness_scorer.py — Score documentation freshness based on code activity.

Run from project root:
    python .agent/scripts/freshness_scorer.py

Output:
    Ranked list of proposals by "staleness" (may need review)
"""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import re

# Configuration
DOCS_ROOT = Path("Docs")
ACTIVE_PROPOSALS = DOCS_ROOT / "Active" / "Proposals"
BACKEND_ROOT = Path("backend")
FRONTEND_ROOT = Path("public")

# Extract code files from Related Code Files sections
CODE_FILE_PATTERN = re.compile(r'\| `([^`]+)` \|')


def get_last_commit_date(file_path: Path) -> datetime:
    """Get the last git commit date for a file."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", str(file_path)],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0 and result.stdout.strip():
            date_str = result.stdout.strip()
            # Parse ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except Exception:
        pass
    
    # Fallback to file modification time
    if file_path.exists():
        return datetime.fromtimestamp(file_path.stat().st_mtime)
    return datetime.min


def get_doc_last_modified(doc_path: Path) -> datetime:
    """Get last modification date of document."""
    return get_last_commit_date(doc_path)


def get_related_code_files(doc_path: Path) -> List[str]:
    """Extract code files from Related Code Files section."""
    content = doc_path.read_text()
    
    if "## Related Code Files" not in content:
        return []
    
    section_start = content.find("## Related Code Files")
    section = content[section_start:]
    
    return CODE_FILE_PATTERN.findall(section)


def get_recent_code_changes(code_files: List[str], since: datetime) -> int:
    """Count commits to code files since a date."""
    total_commits = 0
    
    for code_file in code_files:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", f"--since={since.isoformat()}", code_file],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            if result.returncode == 0:
                commits = [l for l in result.stdout.strip().split('\n') if l]
                total_commits += len(commits)
        except Exception:
            pass
    
    return total_commits


def calculate_freshness_score(doc_path: Path) -> Dict:
    """
    Calculate freshness score for a document.
    
    Returns:
        score: 0-100 (100 = fresh, 0 = stale)
        factors: explanation of score
    """
    doc_modified = get_doc_last_modified(doc_path)
    now = datetime.now(doc_modified.tzinfo) if doc_modified.tzinfo else datetime.now()
    
    days_since_doc_update = (now - doc_modified).days
    
    code_files = get_related_code_files(doc_path)
    code_commits_since_doc = get_recent_code_changes(code_files, doc_modified)
    
    # Scoring:
    # - Start at 100
    # - Subtract 1 point per day since last update (max -30)
    # - Subtract 5 points per code commit since doc update (max -50)
    
    age_penalty = min(days_since_doc_update, 30)
    code_penalty = min(code_commits_since_doc * 5, 50)
    
    score = max(100 - age_penalty - code_penalty, 0)
    
    return {
        "doc": str(doc_path),
        "score": score,
        "days_since_update": days_since_doc_update,
        "related_code_commits": code_commits_since_doc,
        "related_files": len(code_files),
        "status": get_status(score)
    }


def get_status(score: int) -> str:
    if score >= 80:
        return "🟢 Fresh"
    elif score >= 50:
        return "🟡 May need review"
    elif score >= 20:
        return "🟠 Likely stale"
    else:
        return "🔴 Needs attention"


def main():
    print("📊 Documentation Freshness Report\n")
    print("=" * 70)
    
    results = []
    
    for proposal in ACTIVE_PROPOSALS.glob("*.md"):
        result = calculate_freshness_score(proposal)
        results.append(result)
    
    # Sort by score (lowest first = most stale)
    results.sort(key=lambda x: x["score"])
    
    print(f"\n{'Document':<45} {'Score':>6} {'Status':<20}")
    print("-" * 70)
    
    for r in results:
        doc_name = Path(r["doc"]).name[:43]
        print(f"{doc_name:<45} {r['score']:>6} {r['status']:<20}")
    
    print("\n" + "=" * 70)
    
    # Summary
    stale_count = sum(1 for r in results if r["score"] < 50)
    
    print(f"\n📋 Summary:")
    print(f"   Total proposals: {len(results)}")
    print(f"   Fresh (80+): {sum(1 for r in results if r['score'] >= 80)}")
    print(f"   May need review (50-79): {sum(1 for r in results if 50 <= r['score'] < 80)}")
    print(f"   Stale (<50): {stale_count}")
    
    if stale_count > 0:
        print(f"\n⚠️  {stale_count} document(s) may need review.")
        print("\nMost stale documents:")
        for r in results[:3]:
            if r["score"] < 50:
                print(f"   • {Path(r['doc']).name}")
                print(f"     Last updated: {r['days_since_update']} days ago")
                print(f"     Code changes since: {r['related_code_commits']} commits")
    
    return 0 if stale_count == 0 else 1


if __name__ == "__main__":
    exit(main())

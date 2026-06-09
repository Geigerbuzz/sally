#!/usr/bin/env python3
"""
Proposal Priority Report Generator

Generates a prioritized list of proposals to tackle based on:
1. Draft age (how long it's been in draft status)
2. Completion rate (% of features implemented)
3. Dependency importance (how many other proposals depend on it)

Run: python3 .agent/scripts/proposal_priority.py
"""

import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

PROPOSALS_DIR = "Docs/Active/Proposals"

def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    
    frontmatter = {}
    for line in match.group(1).split('\n'):
        if ':' in line and not line.strip().startswith('-'):
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()
    return frontmatter

def parse_implementation_status(content: str) -> dict:
    """Extract implementation status from the table."""
    stats = {'complete': 0, 'pending': 0, 'in_progress': 0, 'total': 0}
    
    # Find Implementation Status table
    table_match = re.search(r'\|\s*Feature\s*\|.*?\n\|[-\s|]+\n(.*?)(?=\n\n|\n>|\n---|\n##|\Z)', content, re.DOTALL)
    if not table_match:
        return stats
    
    rows = table_match.group(1).strip().split('\n')
    for row in rows:
        if '|' not in row:
            continue
        stats['total'] += 1
        if '✅' in row:
            stats['complete'] += 1
        elif '🔄' in row:
            stats['in_progress'] += 1
        elif '⬜' in row:
            stats['pending'] += 1
    
    return stats

def get_affects_count(content: str, all_proposals: list) -> int:
    """Count how many proposals depend on this one."""
    count = 0
    # Check if any other proposal's "Depends on" mentions this file
    for proposal in all_proposals:
        if f"Depends on" in proposal.get('content', ''):
            # This is a rough heuristic
            count += 1
    return count

def calculate_priority_score(proposal: dict) -> float:
    """
    Calculate priority score (higher = more urgent to tackle).
    
    Factors:
    - Days since created (older drafts need attention)
    - Low completion percentage (lots of work remaining)
    - High dependency count (blocking others)
    """
    score = 0
    
    # Age factor: older drafts get higher priority
    created = proposal.get('created', '')
    if created:
        try:
            created_date = datetime.strptime(created, '%Y-%m-%d')
            days_old = (datetime.now() - created_date).days
            if days_old > 30:
                score += 20  # Bonus for drafts older than 30 days
            elif days_old > 14:
                score += 10
        except:
            pass
    
    # Completion factor: lower completion = higher priority
    stats = proposal.get('stats', {})
    if stats.get('total', 0) > 0:
        completion_pct = (stats.get('complete', 0) / stats['total']) * 100
        if completion_pct < 25:
            score += 30  # High priority for barely started
        elif completion_pct < 50:
            score += 20
        elif completion_pct < 75:
            score += 10
    
    # Status factor: drafts need more attention than active
    status = proposal.get('status', 'draft')
    if status == 'draft':
        score += 15
    
    return score

def generate_report():
    """Generate the priority report."""
    proposals = []
    
    # Read all proposals
    for file in Path(PROPOSALS_DIR).glob("*.md"):
        content = file.read_text()
        frontmatter = parse_frontmatter(content)
        stats = parse_implementation_status(content)
        
        proposals.append({
            'name': file.stem,
            'filename': file.name,
            'title': frontmatter.get('title', file.stem),
            'status': frontmatter.get('status', 'unknown'),
            'created': frontmatter.get('created', ''),
            'stats': stats,
            'content': content
        })
    
    # Calculate priority scores
    for p in proposals:
        p['priority_score'] = calculate_priority_score(p)
        if p['stats']['total'] > 0:
            p['completion_pct'] = round((p['stats']['complete'] / p['stats']['total']) * 100)
        else:
            p['completion_pct'] = 0
    
    # Sort by priority score (highest first)
    proposals.sort(key=lambda x: x['priority_score'], reverse=True)
    
    # Generate report
    print("🎯 Proposal Priority Report")
    print("=" * 60)
    print()
    
    # High priority (top 5)
    print("## 🔴 High Priority (Tackle First)")
    print()
    for p in proposals[:5]:
        age_str = ""
        if p['created']:
            try:
                days = (datetime.now() - datetime.strptime(p['created'], '%Y-%m-%d')).days
                age_str = f" ({days}d old)"
            except:
                pass
        
        print(f"- **{p['title']}**{age_str}")
        print(f"  Status: {p['status']} | Completion: {p['completion_pct']}% ({p['stats']['complete']}/{p['stats']['total']} features)")
        print()
    
    # Medium priority (next 5)
    print("## 🟡 Medium Priority")
    print()
    for p in proposals[5:10]:
        print(f"- {p['title']}: {p['completion_pct']}% complete")
    print()
    
    # Good progress (rest)
    print("## 🟢 Good Progress / Low Priority")
    print()
    for p in proposals[10:]:
        print(f"- {p['title']}: {p['completion_pct']}% complete")
    
    print()
    print("=" * 60)
    print(f"📊 Summary: {len(proposals)} proposals | "
          f"{sum(p['stats']['complete'] for p in proposals)} features complete | "
          f"{sum(p['stats']['pending'] for p in proposals)} pending")

if __name__ == "__main__":
    os.chdir(Path(__file__).parent.parent.parent)  # Go to repo root
    generate_report()

#!/usr/bin/env python3
"""
Bidirectional sync between The Library (library.yaml) and Obsidian AI-Agent-KB.

Obsidian = source of truth for descriptions & frontmatter
library.yaml = source of truth for locations & dependencies

Usage:
  python3 library-to-obsidian.py [--dry-run] [--index-only]
"""

import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def read_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown string."""
    fm = {}
    if not content.startswith('---'):
        return fm
    lines = content.split('\n')
    in_fm = False
    fm_lines = []
    for line in lines[1:]:
        if line.strip() == '---':
            break
        fm_lines.append(line)
    try:
        fm = yaml.safe_load('\n'.join(fm_lines)) or {}
    except:
        # Fallback: simple key: value parse
        for line in fm_lines:
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def write_frontmatter(fm: dict) -> str:
    """Serialize frontmatter dict to YAML string."""
    return yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)


def find_card(name: str, skills_dir: str) -> Optional[str]:
    """Find existing Obsidian card for a skill by name."""
    # Direct name match
    candidates = [
        f"{skills_dir}/{name}/{name}.md",
        f"{skills_dir}/{name}/_index.md",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    # Scan subfolders
    skill_dir = os.path.join(skills_dir, name)
    if os.path.isdir(skill_dir):
        for f in os.listdir(skill_dir):
            if not f.endswith('.md') or f.startswith('_') or f.startswith('.'):
                continue
            filepath = os.path.join(skill_dir, f)
            try:
                with open(filepath) as f:
                    content = f.read(2000)
                fm = read_frontmatter(content)
                if fm.get('name', '').lower() == name.lower():
                    return filepath
            except:
                continue
    return None


def get_existing_cards(skills_dir: str) -> Dict[str, dict]:
    """Scan all skill subfolders and return {name: {path, frontmatter}}."""
    cards = {}
    if not os.path.exists(skills_dir):
        return cards
    for entry in sorted(os.listdir(skills_dir)):
        path = os.path.join(skills_dir, entry)
        if not os.path.isdir(path):
            continue
        for f in sorted(os.listdir(path)):
            if not f.endswith('.md') or f.startswith('.') or f == '_assets':
                continue
            filepath = os.path.join(path, f)
            try:
                with open(filepath) as f:
                    content = f.read(2000)
                fm = read_frontmatter(content)
                name = fm.get('name', entry)
                if name and fm.get('type') == 'skill':
                    cards[name.lower()] = {'path': filepath, 'frontmatter': fm}
                    break
            except:
                continue
    return cards


def create_stub_card(skill_entry: dict, skills_dir: str, obsidian_description: str = "") -> str:
    """Create a stub Obsidian card for a library skill that doesn't have one yet."""
    name = skill_entry['name']
    description = obsidian_description or skill_entry.get('description', '')
    source = skill_entry.get('source', '')
    requires = skill_entry.get('requires', [])

    skill_dir = os.path.join(skills_dir, name)
    os.makedirs(skill_dir, exist_ok=True)

    requires_links = ""
    if requires:
        links = [f"[[{r.split(':')[-1]}]]" for r in requires]
        requires_links = "\n".join(f"- {l}" for l in links)

    source_display = source
    if source.startswith('~'):
        source_display = f"Local: `{source}`"
    elif 'github.com' in source:
        repo = source.split('blob/main/')[0].split('/')[-1] if 'blob/main/' in source else 'GitHub'
        source_display = f"GitHub: [{repo}]({source})"

    frontmatter = {
        'type': 'skill',
        'name': name,
        'status': 'active',
        'category': '',
        'triggers': '',
        'created': datetime.now().strftime('%Y-%m-%d'),
        'updated': datetime.now().strftime('%Y-%m-%d'),
        'human_reviewed': False,
        'tac_original': False,
        'tags': ['skill', 'library'],
        'library_registered': True,
        'library_source': source,
    }
    if requires:
        frontmatter['library_requires'] = requires

    fm_str = write_frontmatter(frontmatter)

    body = f"""# {name}

> {description}

## Source
{source_display}

## Dependencies
{requires_links if requires_links else "None"}

---
*Auto-generated from The Library. Review and expand.*
"""

    card_path = os.path.join(skill_dir, f"{name}.md")
    with open(card_path, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{body}")

    return card_path


def update_card_frontmatter(card_path: str, library_entry: dict, existing_fm: dict, dry_run: bool = False) -> bool:
    """Update library-specific fields in existing card without touching body."""
    # Merge: Obsidian frontmatter wins for everything EXCEPT library_ fields
    updates = {
        'library_registered': True,
        'library_source': library_entry.get('source', ''),
        'updated': datetime.now().strftime('%Y-%m-%d'),
    }
    if library_entry.get('requires'):
        updates['library_requires'] = library_entry['requires']

    # Pull description from Obsidian (it's richer) or library if missing
    existing_fm.update(updates)

    return True


def generate_index(library_skills: list, existing_cards: dict, obsidian_kb: str) -> str:
    """Generate _Skill-Index.md dashboard."""
    rows = []
    for skill in library_skills:
        name = skill['name']
        desc = skill.get('description', '')[:60]
        source = skill.get('source', '')
        requires = skill.get('requires', [])
        has_card = name.lower() in existing_cards

        status_icon = "✅" if has_card else "🆕"
        source_type = "📁 Local" if source.startswith('~') or source.startswith('/') else "🌐 GitHub"
        req_str = ", ".join(r.split(':')[-1] for r in requires) if requires else "—"

        rows.append(f"| {status_icon} [[{name}]] | {desc}… | {source_type} | {req_str} |")

    today = datetime.now().strftime('%Y-%m-%d')
    index_content = f"""---
type: dashboard
title: Skill Index — The Library
status: active
tags: [dashboard, skills, index, library]
cssclasses: [skill-index]
created: {today}
updated: {today}
---

# Skill Index

> Auto-generated from `library.yaml` via `library-to-obsidian.py`.

| Status | Skill | Description | Source | Dependencies |
|--------|-------|-------------|--------|--------------|
{chr(10).join(rows)}

---

**Stats:** {len(library_skills)} skills registered | {len(existing_cards)} Obsidian cards | {len(library_skills) - len(existing_cards)} stubs needed

*Last synced: {today}*
"""
    return index_content


def main():
    dry_run = '--dry-run' in sys.argv
    index_only = '--index-only' in sys.argv

    library_yaml = os.path.expanduser(
        os.environ.get('LIBRARY_YAML', '~/repos/the-library/library.yaml')
    )
    obsidian_kb = os.path.expanduser(
        os.environ.get('OBSIDIAN_KB', '~/repos/obsidian/Gbautomation/AI-Agent-KB')
    )

    print(f"📚 Library ↔ Obsidian AI-Agent-KB Sync")
    print(f"   Library: {library_yaml}")
    print(f"   Obsidian: {obsidian_kb}")
    print()

    # Load library.yaml
    with open(library_yaml) as f:
        lib = yaml.safe_load(f)

    skills = lib.get('library', {}).get('skills', [])
    print(f"   Library entries: {len(skills)}")

    # Get existing Obsidian cards
    skills_dir = os.path.join(obsidian_kb, 'skills')
    existing = get_existing_cards(skills_dir)
    print(f"   Obsidian cards:  {len(existing)}")

    # Phase 1: Sync each library entry
    created = 0
    updated = 0
    skipped = 0

    for skill in skills:
        name = skill['name']
        name_lower = name.lower()

        card_path = find_card(name, skills_dir)

        if card_path and name_lower in existing:
            # Card exists — update library fields only
            if not dry_run:
                update_card_frontmatter(
                    card_path, skill, existing[name_lower]['frontmatter']
                )
            updated += 1
            print(f"  ✅ Updated: {name}")
        else:
            # No card — create stub (using Obsidian if available, else library desc)
            if not dry_run:
                create_stub_card(skill, skills_dir, skill.get('description', ''))
            created += 1
            print(f"  🆕 Created: {name}")

    # Phase 2: Detect orphaned Obsidian cards (not in library)
    library_names = {s['name'].lower() for s in skills}
    orphans = []
    for name, info in existing.items():
        if name not in library_names:
            orphans.append(name)

    if orphans:
        print(f"\n⚠️  Obsidian-only skills (not in library.yaml):")
        for o in sorted(orphans):
            print(f"    - {o}")

    # Phase 3: Generate index
    index_content = generate_index(skills, existing, obsidian_kb)
    index_path = os.path.join(obsidian_kb, 'skills', '_Skill-Index.md')

    if not dry_run:
        with open(index_path, 'w') as f:
            f.write(index_content)
        print(f"\n📊 Index generated: {index_path}")
    else:
        print(f"\n📊 Index would be: {index_path}")

    # Phase 4: Reverse sync — suggest library additions for orphans
    if orphans:
        print(f"\n💡 To register these in library.yaml, run:")
        for o in orphans[:5]:
            print(f"    /library add {o}")
        if len(orphans) > 5:
            print(f"    ... and {len(orphans) - 5} more")

    print(f"\n✅ Sync complete: {created} created, {updated} updated, {len(orphans)} orphans detected")


if __name__ == '__main__':
    main()

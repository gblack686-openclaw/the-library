---
name: The Library — Skill Catalog
description: Catalog of all TAC skills across workspace, consulting-co, and community
version: 2.0
organization: gblack686-openclaw
updated: 2026-04-08
---

# The Library — Skill Discovery Guide

## Quick Search

```bash
# Search by keyword
grep -i "keyword" ~/repos/the-library/library.yaml

# Search by skill name
cat ~/repos/the-library/library.yaml | grep "name:"
```

## Skill Format (SKILL.md)

```yaml
---
name: skill-name
description: 'One-line description of what this skill does and when to use it.'
metadata:
  openclaw:
    emoji: "🔧"
    requires:
      anyBins: ["required-cli-tool"]
---

# Skill Name

## When to Use
<specific trigger conditions>

## Steps
1. Step one
2. Step two
3. Step three

## Output
<what this skill produces>
```

## Skill Categories

| Category | Skills | Location |
|----------|--------|----------|
| Trading | daily-lesson, expert-scheduler, position-monitor | workspace/skills/ |
| Client Research | client-linkedin, client-personal-intel, client-research | consulting-co/.claude/skills/ |
| Infrastructure | setup-openclaw, onboarding, healthcheck | workspace/skills/ |
| Browser | browser-automation, bowser | consulting-co/.claude/skills/ |
| Coding | coding-agent, skill-creator, domain-discovery | workspace/skills/ + consulting-co/.claude/skills/ |
| Communication | gmail-inbox-monitor, discord-setup | workspace/skills/ + consulting-co/.claude/skills/ |
| LinkedIn | linkedin-job-applier, linkedin-outbound-pitch | workspace/skills/ |
| Marketing | adw-dispatch, adw-status | consulting-co/.claude/skills/ |

## Adding New Skills

1. Create directory: `skills/<skill-name>/`
2. Write `SKILL.md` with frontmatter
3. Add entry to `library.yaml`
4. Commit and push: `forge: add <skill-name> skill`

---
name: beeweave
description: Obsidian wiki workflows — query, update, ingest, lint, status.
commands:
  - name: beeweave-query
    description: Answer questions from the compiled Obsidian wiki with [[wikilink]] citations.
    skill: .skills/beeweave-query/SKILL.md
  - name: beeweave-update
    description: Sync the current project's knowledge into the Obsidian wiki.
    skill: .skills/beeweave-update/SKILL.md
  - name: beeweave-ingest
    description: Ingest documents into the Obsidian wiki.
    skill: .skills/beeweave-ingest/SKILL.md
  - name: beeweave-status
    description: Show what's been ingested, what's pending, and the delta.
    skill: .skills/beeweave-status/SKILL.md
  - name: beeweave-lint
    description: Audit the wiki for orphans, broken links, stale content.
    skill: .skills/beeweave-lint/SKILL.md
---

# BeeWeave — Workflow Registry

Each command above maps to a `SKILL.md` in `.skills/`. When a user invokes one
of these commands, read the mapped skill file and follow its instructions
exactly. The skills handle vault path resolution, manifest tracking, and
`[[wikilink]]` connectivity on their own.

For the full routing table, see the target project's generated `AGENTS.md`.

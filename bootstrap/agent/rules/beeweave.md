---
alwaysApply: true
description: BeeWeave skill-based framework — routing, conventions, and core rules.
---

# BeeWeave — Agent Context

This project is a **skill-based framework** for building and maintaining an Obsidian knowledge base.

## Quick Orientation

1. Resolve config via `AGENTS.md`: honor an inline `@name` vault override first, then `.env`, then `~/.beeweave/config`. This gives `BEEWEAVE_VAULT_PATH` — where the wiki lives.
2. Read `.manifest.json` at the vault root to see what's already been ingested.
3. Skills are in `.skills/` (also at `.agents/skills/`). Each subfolder has a `SKILL.md`.

## When to Use Skills

| User says something like… | Read this skill |
|---|---|
| "set up my wiki" / "initialize" | `beeweave-setup` |
| "ingest" / "add this to the wiki" / "process this export" / "ingest this data" | `beeweave-ingest` |
| "import my Claude history" | `beeweave-claude-ingest` |
| "import my Codex history" | `beeweave-codex-ingest` |
| "import my Hermes history" | `beeweave-hermes-ingest` |
| "import my OpenClaw history" | `beeweave-openclaw-ingest` |
| "import my Pi history" | `beeweave-pi-ingest` |
| "what's the status" / "show the delta" | `beeweave-status` |
| "what do I know about X" | `beeweave-query` |
| "audit" / "lint" / "find broken links" | `beeweave-lint` |
| "rebuild" / "archive" / "restore" | `beeweave-rebuild` |
| "link my pages" / "cross-reference" | `beeweave-cross-linker` |
| "fix my tags" | `beeweave-tag-taxonomy` |
| "update wiki" / "sync to wiki" | `beeweave-update` |
| "export wiki" / "export graph" | `beeweave-export` |

## Core Rules

- **Compile, don't retrieve** — update existing pages, don't append or duplicate.
- **Track everything** — update `.manifest.json`, `index.md`, and `log.md` after every operation.
- **Connect with `[[wikilinks]]`** — every page should link to related pages.
- **Frontmatter required** — every page needs `title`, `category`, `tags`, `sources`, `created`, `updated`.

For full context, read the target project's generated `AGENTS.md`.

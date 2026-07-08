---
name: "BeeWeave"
activation: "always-on"
---

# BeeWeave — Agent Context

This project is a **skill-based framework** for building and maintaining an Obsidian knowledge base.

## Quick Orientation

1. Resolve config via `AGENTS.md`: honor an inline `@name` profile override first, then `.env`, then `~/.beeweave/config`. This gives the full BeeWeave profile, including `BEEWEAVE_VAULT_PATH` and `BEEWEAVE_WORKBENCH_PATH`.
2. Read `.manifest.json` at the vault root to see what's already been ingested.
3. Skills are in `.skills/` (also at `.windsurf/skills/`). Each subfolder has a `SKILL.md`.

## When to Use Skills

| User says something like… | Read this skill |
|---|---|
| "set up my wiki" / "initialize" | `.skills/beeweave-setup/SKILL.md` |
| "ingest" / "add this to the wiki" / "process this export" / "ingest this data" | `.skills/beeweave-ingest/SKILL.md` |
| "/beeweave-history-ingest claude" / "/beeweave-history-ingest codex" / "/beeweave-history-ingest pi" | `.skills/beeweave-history-ingest/SKILL.md` |
| "import my Claude history" | `.skills/beeweave-claude-ingest/SKILL.md` |
| "import my Codex history" | `.skills/beeweave-codex-ingest/SKILL.md` |
| "import my Pi history" | `.skills/beeweave-pi-ingest/SKILL.md` |
| "what's the status" / "show the delta" | `.skills/beeweave-status/SKILL.md` |
| "what do I know about X" / any question | `.skills/beeweave-query/SKILL.md` |
| "audit" / "lint" / "find broken links" | `.skills/beeweave-lint/SKILL.md` |
| "rebuild" / "start over" / "archive" | `.skills/beeweave-rebuild/SKILL.md` |
| "link my pages" / "cross-reference" | `.skills/beeweave-cross-linker/SKILL.md` |
| "fix my tags" / "normalize tags" | `.skills/beeweave-tag-taxonomy/SKILL.md` |
| "create a new skill" | `.skills/beeweave-skill-creator/SKILL.md` |

## Key Rules

- **Compile, don't retrieve.** Update existing pages, don't just append.
- **Always update `.manifest.json`** after ingesting.
- **Always update `index.md` and `log.md`** after any operation.
- **Use `[[wikilinks]]`** to connect related pages.
- **Frontmatter is required** on every wiki page.

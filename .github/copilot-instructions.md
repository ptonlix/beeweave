# BeeWeave — Copilot Context

This project is a **skill-based framework** for building and maintaining an Obsidian knowledge base using AI coding agents. There are no scripts or dependencies — everything is markdown instructions that the agent executes directly.

## Project Overview

- **Purpose:** Build and maintain an Obsidian wiki using the LLM Wiki pattern (Andrej Karpathy).
- **Tech Stack:** Markdown only. No code, no dependencies. The AI agent IS the runtime.
- **Key Config:** Resolve config via `AGENTS.md`: inline `@name` vault override first, then `.env`, then `~/.beeweave/config`. The resolved config supplies `BEEWEAVE_VAULT_PATH`.
- **Skills:** `.skills/` contains skill folders, each with a `SKILL.md` defining a workflow.

## Key Concepts

- The wiki is a **compiled artifact** — knowledge distilled from raw sources into interconnected pages.
- Every wiki page has YAML frontmatter: `title`, `category`, `tags`, `sources`, `created`, `updated`.
- Pages are connected with Obsidian `[[wikilinks]]`.
- A `.manifest.json` in the vault root tracks all ingested sources for delta-based updates.
- `index.md` and `log.md` must be updated after every operation.

## Skills Reference

| Skill | Folder | Purpose |
|---|---|---|
| Setup | `.skills/beeweave-setup/` | Initialize vault structure |
| Ingest | `.skills/beeweave-ingest/` | Distill documents into wiki pages, plus any text data — chat exports, logs, transcripts |
| History Router | `.skills/beeweave-history-ingest/` | Route `/beeweave-history-ingest <claude|codex>` to the right history skill |
| Claude History | `.skills/beeweave-claude-ingest/` | Mine `~/.claude` conversations |
| Codex History | `.skills/beeweave-codex-ingest/` | Mine `~/.codex` sessions and rollout logs |
| Status | `.skills/beeweave-status/` | Audit ingestion state and delta |
| Query | `.skills/beeweave-query/` | Answer questions from wiki |
| Lint | `.skills/beeweave-lint/` | Find broken links, orphans |
| Rebuild | `.skills/beeweave-rebuild/` | Archive and rebuild |
| Cross-Linker | `.skills/beeweave-cross-linker/` | Auto-discover and insert missing wikilinks |
| Tag Taxonomy | `.skills/beeweave-tag-taxonomy/` | Enforce consistent tag vocabulary |
| LLM Wiki | `.skills/beeweave-core/` | Core architecture pattern |
| Skill Creator | `.skills/beeweave-skill-creator/` | Create new skills |

## Coding Conventions

- When creating wiki pages, always use YAML frontmatter.
- Use `[[wikilinks]]` syntax for cross-references — NOT markdown links.
- Project-specific knowledge goes in `projects/<name>/`. Global knowledge goes in top-level categories.
- Never modify the `.obsidian/` directory.

# BeeWeave Skills

BeeWeave skills are markdown instructions that agents read when a workflow is
triggered. They live under `.skills/` and are installed in two different ways:

- **Project-local skills**: the full skill set, installed into a project agent
  directory such as `.claude/skills/`, `.codex/skills/`, or `.agents/skills/`.
- **Global skills**: a small portable subset, installed into global agent
  directories such as `~/.claude/skills/` or `~/.codex/skills/`.

The global set is intentionally small. Too many globally visible skills make
agents harder to predict and users harder to orient.

## Global Skill Policy

By default, BeeWeave installs only three global skills:

```text
beeweave-update
beeweave-query
beeweave-ingest
```

These are the core cross-project workflows:

| Skill | What it does | Why global |
|---|---|---|
| `beeweave-update` | Sync the current project's durable knowledge into the vault | Useful from any codebase |
| `beeweave-query` | Ask questions against the compiled vault | Read-only and useful anywhere |
| `beeweave-ingest` | Distill documents, URLs, exports, logs, and inbox captures into wiki pages | General source-ingest entrypoint |

Advanced users can explicitly add a few recommended extra global skills:

```bash
bwe setup --global-extra beeweave-capture,beeweave-context-pack
bash setup.sh --global-extra beeweave-capture,beeweave-context-pack
```

Supported extras:

| Skill | What it does | Notes |
|---|---|---|
| `beeweave-capture` | Save current-session findings to inbox/wiki | Prefer quick capture to inbox, then promote with `beeweave-ingest` |
| `beeweave-context-pack` | Package vault context for another agent or task | Pulls knowledge from vault; it does not save the current chat |
| `beeweave-digest` | Generate a daily, weekly, monthly, or custom-period knowledge digest | Useful for review workflows |
| `beeweave-status` | Show ingest status, pending delta, and vault health | Operational overview |
| `beeweave-memory-bridge` | Browse and compare knowledge by source agent | Most useful after importing multiple agent histories |

## Install Shape

Interactive setup shows the same shape:

```text
Global skills
  Always installed:
    [x] beeweave-update
    [x] beeweave-query
    [x] beeweave-ingest

  Optional advanced global skills:
    [ ] beeweave-capture
    [ ] beeweave-context-pack
    [ ] beeweave-digest
    [ ] beeweave-status
    [ ] beeweave-memory-bridge

Workbench/project-local skills:
  beeweave-article-writer — long-form articles, blog posts, essays, and opinion pieces
  beeweave-social-writer  — X/Twitter posts, threads, short takes, and social copy
```

After global skill selection, setup asks which agents to install for.

## Wiki Skills

Everything below lives under `.skills/wiki/`. Project-local installs get the
full set.

| Skill | What it does | Global recommendation |
|---|---|---|
| `beeweave-update` | Sync durable knowledge from the current project into the vault: architecture decisions, patterns, key abstractions, trade-offs, and project context | Default global |
| `beeweave-query` | Search and synthesize answers from the compiled vault, including multi-hop relationship queries and fast summary-only lookup | Default global |
| `beeweave-ingest` | Distill external sources into interconnected wiki pages: documents, folders, PDFs, URLs, logs, transcripts, exports, raw text, and `workbench/inbox` captures | Default global |
| `beeweave-capture` | Preserve the current conversation or session findings as structured wiki knowledge; quick mode stages files under `workbench/inbox/captures/` | Optional extra |
| `beeweave-context-pack` | Produce a token-bounded context pack from vault pages for another agent, skill, or downstream task | Optional extra |
| `beeweave-digest` | Generate a human-readable knowledge digest for a day, week, month, or custom period | Optional extra |
| `beeweave-status` | Report what has been ingested, what is pending, source delta, token footprint, and graph structure insights | Optional extra |
| `beeweave-memory-bridge` | Browse and diff wiki knowledge by source tool, such as Claude vs Codex vs Hermes | Optional extra |
| `beeweave-core` | Explain the underlying LLM Wiki pattern, vault schema, frontmatter, relationships, retrieval primitives, and config resolution protocol | Project-local |
| `beeweave-setup` | Initialize vault structure, special files, Obsidian config, `.env`, and optional capture hooks | Project-local |
| `beeweave-switch` | Manage named vault profiles under `~/.beeweave/config.NAME` and switch the active default vault | Project-local |
| `beeweave-lint` | Audit vault health: orphan pages, broken links, missing frontmatter, missing summaries, stale content, contradictions, and optional consolidation | Project-local |
| `beeweave-cross-linker` | Scan the vault and insert missing `[[wikilinks]]` to strengthen the knowledge graph | Project-local |
| `beeweave-tag-taxonomy` | Audit and normalize tags using the controlled vocabulary in `_meta/taxonomy.md` | Project-local |
| `beeweave-dedup` | Detect identity collisions and merge duplicate pages under different names | Project-local |
| `beeweave-rebuild` | Archive, rebuild, or restore the vault | Project-local |
| `beeweave-daily-update` | Run a daily maintenance pass: source freshness, index refresh, hot cache update, and optional cron/notification setup | Project-local |
| `beeweave-stage-commit` | Review and promote staged pages from `_staging/` when `WIKI_STAGED_WRITES=true` | Project-local |
| `beeweave-impl-validator` | Validate whether an implementation or skill output matches its stated goal; often used as a helper subagent | Project-local |
| `beeweave-graph-colorize` | Rewrite Obsidian graph color groups by tag, folder, category, or visibility | Project-local |
| `beeweave-dashboard` | Create Obsidian Bases or Dataview dashboard views over vault content | Project-local |
| `beeweave-synthesize` | Discover synthesis opportunities across concepts and create `synthesis/` pages | Project-local |
| `beeweave-research` | Run multi-round web research and file the results into the vault | Project-local |
| `beeweave-export` | Export the vault graph to JSON, GraphML, Neo4j Cypher, browser HTML, or OKF markdown bundle | Project-local |
| `beeweave-import` | Import from `graph.json` stubs or an OKF markdown bundle into the current vault | Project-local |
| `beeweave-vault-skill-factory` | Generate a portable Agent Skill from mature vault pages into a review directory | Project-local |
| `beeweave-skill-creator` | Create, edit, package, benchmark, and improve Agent Skills | Project-local |
| `beeweave-history-ingest` | Route agent-history ingestion requests to the specialized history skill for the selected tool | Project-local |
| `beeweave-agent` | Search a specific agent's raw history by topic, ingest the relevant sessions, and return a synthesized answer | Project-local |
| `beeweave-claude-ingest` | Mine Claude Code and Claude desktop history, memory files, sessions, and audit logs into the vault | Project-local |
| `beeweave-codex-ingest` | Mine Codex CLI sessions, rollout logs, and session indexes into the vault | Project-local |
| `beeweave-copilot-ingest` | Mine GitHub Copilot CLI and VS Code Copilot Chat history into the vault | Project-local |
| `beeweave-hermes-ingest` | Mine Hermes memories and sessions into the vault | Project-local |
| `beeweave-openclaw-ingest` | Mine OpenClaw `MEMORY.md`, daily notes, and session logs into the vault | Project-local |
| `beeweave-pi-ingest` | Mine Pi coding agent session history into the vault | Project-local |

## Workbench Skills

Creation-specific skills live under `.skills/workbench/`. They are installed
project-locally with the full skill set, not globally.

| Skill | What it does |
|---|---|
| `beeweave-article-writer` | Long-form articles, blog posts, essays, and opinion pieces |
| `beeweave-social-writer` | X/Twitter posts, threads, short takes, and social copy |

## Why Most Skills Stay Local

Many BeeWeave skills are powerful maintenance or migration tools. They are
useful, but they should only appear when the user is intentionally working on
the vault or workbench.

Keep these local by default:

- **High-impact writes**: `beeweave-rebuild`, `beeweave-dedup`, `beeweave-import`, `beeweave-stage-commit`
- **Vault maintenance**: `beeweave-lint`, `beeweave-cross-linker`, `beeweave-tag-taxonomy`, `beeweave-synthesize`
- **Machine setup**: `beeweave-setup`, `beeweave-switch`, `beeweave-daily-update`
- **Agent history mining**: `beeweave-history-ingest`, `beeweave-agent`, and all agent-specific history ingest skills
- **Skill development**: `beeweave-skill-creator`, `beeweave-vault-skill-factory`, `beeweave-impl-validator`
- **Obsidian-specific UI/config**: `beeweave-graph-colorize`, `beeweave-dashboard`

This keeps the global surface area small while preserving the full BeeWeave
toolbox inside project-local installs.

## OKF

OKF means **Open Knowledge Format** in BeeWeave's export/import workflow.

- `beeweave-export` can create an OKF markdown bundle.
- `beeweave-import` can import an OKF bundle into another vault.
- Unlike `graph.json`, which is mostly a graph skeleton, OKF preserves full
  markdown page bodies and is better for vault-to-vault transfer.

Use OKF when you want to move knowledge, not just inspect the graph.

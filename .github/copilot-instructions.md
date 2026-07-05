# BeeWeave — Copilot Context

BeeWeave is an **agent-native creation workbench** for building a creative data
flywheel: collect source material, create with agents, distill durable
knowledge, reuse that knowledge as context, then collect better material for
the next loop.

This repository contains the Python CLI, bundled skills, bootstrap templates,
browser extension assets, tests, and documentation used to install and maintain
BeeWeave workspaces.

## Project Overview

- **Purpose:** Help agents and humans move material through a structured loop:
  `collect -> create -> distill -> reuse context -> collect better`.
- **Runtime model:** `workbench/` is the staging and drafting area; `vault/` is
  the compiled markdown knowledge base.
- **CLI:** The public console command is `bwe`.
- **Package:** Python package code lives under `beeweave/`; package metadata and
  the CLI entrypoint live in `pyproject.toml`.
- **Skills:** Source skills live under `.skills/wiki/` and
  `.skills/workbench/`. Each skill folder uses a `SKILL.md` workflow file.
- **Bootstrap:** Agent-facing setup templates live under `bootstrap/`.
- **Extension:** Browser capture assets live under `extensions/brain-capture/`.

## Key Concepts

- BeeWeave is a loop, not a one-way archive.
- Raw inputs, drafts, captures, web clips, and source libraries belong in
  `workbench/`.
- Stable reusable knowledge belongs in `vault/` as markdown with metadata and
  Obsidian-style `[[wikilinks]]`.
- The vault is a compiled artifact: concepts, entities, references, project
  notes, synthesis pages, and graph-ready relationships distilled from higher
  signal material.
- Setup-generated runtime `vault/` and `workbench/` directories should not be
  committed to this repository.

## Runtime Layout

BeeWeave setup creates this structure inside a user-selected workspace:

```text
project/
+-- vault/                  # durable markdown knowledge
|   +-- concepts/
|   +-- entities/
|   +-- skills/
|   +-- references/
|   +-- synthesis/
|   +-- projects/
|   +-- _meta/
|   +-- _archives/
|   +-- _staging/
|   +-- .obsidian/
+-- workbench/              # staging and drafting area
    +-- inbox/
    |   +-- captures/
    |   +-- web/
    |   +-- archived/
    |   +-- rejected/
    +-- articles/
    |   +-- drafts/
    |   +-- published/
    +-- library/
```

Keep repository development files separate from this runtime layout.

## Install and Configuration Model

- Users install from PyPI with `pip install beeweave`, then run `bwe setup`.
- Source-checkout setup is also supported with `bash setup.sh`.
- Global config is written under `~/.beeweave/config`.
- BeeWeave config uses `BEEWEAVE_*` names such as `BEEWEAVE_VAULT_PATH`,
  `BEEWEAVE_REPO`, and `BEEWEAVE_VERSION`.
- Named vault routing uses request-local `@name` overrides that resolve to
  files such as `~/.beeweave/config.work`.

## Skill Install Policy

Global installs are intentionally small.

Always global by default:

- `beeweave-update`: sync useful project knowledge into the vault
- `beeweave-query`: answer questions from the compiled vault
- `beeweave-ingest`: process source material into durable notes

Optional advanced global skills include:

- `beeweave-capture`
- `beeweave-context-pack`
- `beeweave-digest`
- `beeweave-status`
- `beeweave-memory-bridge`

All other BeeWeave skills remain project-local by default. When changing setup
behavior, preserve this split unless the README and tests are updated together.

## Important Skills

- `.skills/wiki/beeweave-setup/`: initialize a BeeWeave workspace.
- `.skills/wiki/beeweave-ingest/`: distill source material into durable vault
  notes.
- `.skills/wiki/beeweave-query/`: answer from the compiled vault.
- `.skills/wiki/beeweave-update/`: preserve durable decisions or lessons from
  current project work.
- `.skills/wiki/beeweave-synthesize/`: find cross-cutting connections after
  the vault has grown.
- `.skills/wiki/beeweave-status/`: inspect ingest status and vault health.
- `.skills/workbench/beeweave-article-writer/`: draft long-form articles from
  workbench material.
- `.skills/workbench/beeweave-social-writer/`: turn findings into short-form
  social writing.

## Repository Layout

```text
beeweave/        # Python CLI and helpers
.skills/         # source skill definitions
bootstrap/       # user-project bootstrap templates and agent rules
extensions/      # browser extension assets
tests/           # pytest suite
openspec/        # proposed and active change specs
setup.sh         # source-checkout setup path
pyproject.toml   # package metadata and bwe entrypoint
```

## Coding and Documentation Conventions

- Prefer existing CLI, setup, bootstrap, and skill patterns over new
  abstractions.
- Keep implementation changes scoped to the active request.
- Preserve the public CLI command as `bwe`.
- Keep generated user-project instructions in `bootstrap/AGENTS.md`, not the
  repository root `AGENTS.md`.
- Do not generate `.hermes.md`; Hermes uses `HERMES.md`.
- Do not recreate runtime `vault/` or `workbench/` directories in the repo root.
- Do not commit project-local generated skill mirrors such as
  `.claude/skills/`.
- When creating vault pages in skills or docs, use YAML frontmatter and
  Obsidian `[[wikilinks]]`.
- Do not modify `.obsidian/` except through explicit graph-related behavior
  such as `beeweave-graph-colorize`.

## Verification

Use focused checks for small documentation-only edits. When behavior changes,
run:

```bash
uv run pytest
uv run bwe setup --help
uv run bwe info
```

For OpenSpec-backed changes, also run:

```bash
openspec validate <change-name> --strict
```

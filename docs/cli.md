# CLI

BeeWeave exposes the `bwe` command.

## Core Commands

```text
bwe setup             install skills into agents and write config
bwe profile           manage BeeWeave profile config files
bwe uninstall         remove BeeWeave skills and config
bwe list              list bundled skills
bwe info              show install paths, version, and config
```

## Knowledge and Graph Helpers

```text
bwe graph-query       query the vault wikilink index
bwe graph-analyse     analyze vault graph structure
bwe batch-plan        plan parallel ingest batches
```

## Cache and Source Helpers

```text
bwe cache-check       check source changes against .manifest.json
bwe cache-update      record source hashes after ingestion
bwe cache-hash        compute source hashes
bwe ast-extract       extract code structure without LLM calls
```

## Setup Examples

```bash
bwe setup --agents claude,codex
bwe setup --global-extra beeweave-capture
bwe setup --profile work
bwe profile set-default work
bwe info
```

Run `bwe setup` from the workspace where you want runtime `vault/` and
`workbench/` folders to be created.

By default, setup writes `~/.beeweave/config`. Use `--profile NAME` to write a
named profile at `~/.beeweave/config.NAME`. Setup does not activate named
profiles or repoint `~/.beeweave/config`; use `@name` in agent requests to
target a named profile. In interactive setup, choose `new profile...` to enter
a new profile name without leaving setup.

Use `bwe profile set-default NAME` to intentionally copy
`~/.beeweave/config.NAME` to `~/.beeweave/config`. If a default config already
exists, BeeWeave creates a timestamped backup and requires `YES` before
overwriting it.

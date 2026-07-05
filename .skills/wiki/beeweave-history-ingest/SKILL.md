---
name: beeweave-history-ingest
description: >
  Unified beeweave-history-ingest entrypoint for conversation/session sources. Use this when the user says
  "/beeweave-history-ingest claude", "/beeweave-history-ingest copilot", "/beeweave-history-ingest codex",
  "/beeweave-history-ingest pi", or asks to ingest agent history without naming the underlying skill.
  This router dispatches to the specialized history skill.
---

# Unified History Ingest Router

This is a thin router for **history sources only**. It does not replace `beeweave-ingest` for documents.

## Subcommands

If the user invokes `/beeweave-history-ingest <target>` (or equivalent text command), dispatch directly:

| Subcommand | Route To |
|---|---|
| `claude` | `beeweave-claude-ingest` |
| `copilot` | `beeweave-copilot-ingest` |
| `codex` | `beeweave-codex-ingest` |
| `hermes` | `beeweave-hermes-ingest` |
| `openclaw` | `beeweave-openclaw-ingest` |
| `pi` | `beeweave-pi-ingest` |
| `auto` | infer from context using rules below |

## Routing Rules

1. If the user explicitly says `claude`, `copilot`, `codex`, `hermes`, `openclaw`, or `pi`, route directly.
2. If the user provides a path/source:
   - `~/.claude` or Claude memory/session JSONL artifacts -> `beeweave-claude-ingest`
   - `~/.copilot`, `session-store.db`, VS Code copilot-chat transcripts -> `beeweave-copilot-ingest`
   - `~/.codex` or rollout/session index artifacts -> `beeweave-codex-ingest`
   - `~/.hermes` or Hermes memories/session artifacts -> `beeweave-hermes-ingest`
   - `~/.openclaw` or OpenClaw MEMORY.md/session JSONL artifacts -> `beeweave-openclaw-ingest`
   - `~/.pi/agent/sessions` or Pi session JSONL artifacts -> `beeweave-pi-ingest`
3. If ambiguous, ask one short clarification:
   - "Should I ingest `claude`, `copilot`, `codex`, `hermes`, `openclaw`, or `pi` history?"

## Execution Contract

- After routing, execute the destination skill's workflow exactly.
- Do not duplicate destination logic in this file.
- Leave manifest/index/log update semantics to the destination skill.

## UX Convention

- Use `beeweave-ingest` for **documents/content sources**
- Use `beeweave-history-ingest` for **agent history sources**

Examples:

- `/beeweave-history-ingest claude`
- `/beeweave-history-ingest copilot`
- `/beeweave-history-ingest codex`
- `/beeweave-history-ingest hermes`
- `/beeweave-history-ingest openclaw`
- `/beeweave-history-ingest pi`
- `$beeweave-history-ingest claude` (agents that use `$skill` invocation)
- `$beeweave-history-ingest copilot`

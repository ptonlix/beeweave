# 🐝 BeeWeave

[English](README.md) | [中文](README-zh.md) | [Documentation](https://ptonlix.github.io/beeweave/) | [中文文档](https://ptonlix.github.io/beeweave/zh/)

BeeWeave is an **agent-native creation workbench** for building a data flywheel
around your creative process: collect source material, create with agents,
distill what matters into durable knowledge, then use that knowledge to collect
better material and create the next piece.

<p align="center">
  <a href="https://deepwiki.com/ptonlix/beeweave"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki" /></a>
  <a href="https://github.com/ptonlix/beeweave/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" /></a>
  <a href="https://x.com/Baird_cfd"><img src="https://img.shields.io/badge/@CyberFD-black?logo=x&logoColor=white" alt="X" /></a>
  <a href="https://www.zhihu.com/people/baird-66"><img src="https://img.shields.io/badge/Zhihu-CyberFD-1677FF?logo=zhihu&logoColor=white" alt="Zhihu" /></a>
</p>

<p align="center">
  <img width="768" height="512" alt="BeeWeave" src="docs/assets/beeweave.png" />
</p>

<p align="center">
  <code>collect -> create -> distill -> reuse context -> collect better material -> create the next piece</code>
</p>

The goal is not just "agent memory". BeeWeave gives you a structured creative
loop: a `workbench/` for raw inputs, drafts, captures, and source libraries; a
`vault/` for stable markdown knowledge; and shared skills that let your agents
move material through that loop without trapping context in one chat, one
codebase, or one tool.

## ✨ Why BeeWeave

- **Creative data flywheel**: collect material, create from it, distill durable
  knowledge, then reuse that knowledge to guide the next round of collection and
  creation.
- **Workbench-first workflow**: `workbench/` stores drafts, captures, web clips,
  and source material before it becomes stable knowledge.
- **Compiled markdown vault**: `vault/` stores the reusable layer: concepts,
  entities, references, projects, synthesis notes, metadata, and graph-ready
  wikilinks.
- **Shared agent context**: Claude Code, Codex, Cursor, Gemini, Kiro, Hermes,
  OpenClaw, Pi, Copilot CLI, and generic `AGENTS.md` agents can use the same
  knowledge base.

The underlying knowledge pattern is inspired by Andrej Karpathy's
[LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):
compile useful knowledge once into interconnected markdown files, then keep it
fresh instead of rediscovering the same context in every session.

## 🚀 Quick Start

Install from PyPI and run setup in the directory where you want BeeWeave to
create `vault/` and `workbench/`:

```bash
pip install beeweave
bwe setup
```

Setup will:

1. Create `./vault` and `./workbench` if they do not exist.
2. Write global BeeWeave config to `~/.beeweave/config`.
3. Ask which optional advanced skills should also be installed globally.
4. Ask which agents should receive BeeWeave skills and bootstrap files.
5. Install full project-local skills for the selected agents.
6. Install the three portable global skills for supported global agents:
   `beeweave-update`, `beeweave-query`, and `beeweave-ingest`.

During setup, you first choose any optional advanced global skills, then choose
the agents BeeWeave should install into. The default global skill set stays
intentionally small, while the full BeeWeave skill set is installed
project-locally for the agents you choose.

After setup, open the project in your agent and use the skills directly:

```text
/beeweave-ingest workbench/inbox
/beeweave-query what do I know about rate limiting?
/beeweave-update
```

## 🤖 Agent Quickstart

If you want the agent to drive setup from a source checkout, give it this repo
and ask it to set up the workspace:

```text
https://github.com/ptonlix/beeweave - set up my BeeWeave workspace
```

The setup skill lives at
[.skills/wiki/beeweave-setup/SKILL.md](.skills/wiki/beeweave-setup/SKILL.md).

## 🛠️ Useful Commands

```bash
bwe info                                      # show version, config, and install paths
bwe list                                      # list bundled skills
bwe setup --agents claude,codex               # install for specific agents
bwe setup --global-extra beeweave-capture     # opt into advanced global skills
```

To remove BeeWeave from your agents and delete BeeWeave config:

```bash
bwe uninstall
```

Uninstall removes BeeWeave-managed skills, project-local bootstrap files, and
`~/.beeweave` config. It does not delete your `vault/` or `workbench/` content.

## 🗂️ Runtime Layout

BeeWeave separates the creative workspace from the compiled knowledge base:

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

Use `workbench/` for rough notes, web captures, imported sources, and drafts.
Use `vault/` for stable pages that should be searchable, linkable, and reusable.
`bwe setup` creates these directories with `.gitkeep` placeholders so the
layout is ready before the first ingest.

## 🎯 Skill Install Policy

BeeWeave intentionally keeps global installs small.

**Always global by default**

- `beeweave-update`: sync useful project knowledge into the vault
- `beeweave-query`: answer questions from the compiled vault
- `beeweave-ingest`: process source material into durable notes

**Optional advanced global skills**

- `beeweave-capture`: save current-session findings to the inbox or vault
- `beeweave-context-pack`: package vault context for another task
- `beeweave-digest`: generate recent knowledge digests
- `beeweave-status`: show ingest status and vault health
- `beeweave-memory-bridge`: compare knowledge by source agent

Install optional global skills explicitly:

```bash
bwe setup --global-extra beeweave-capture,beeweave-status
```

All other BeeWeave skills remain project-local by default. This keeps other
projects clean while still giving the BeeWeave workspace the full toolset.

## 🤝 Supported Agents

`bwe setup` supports these agent targets:

```text
claude, cursor, windsurf, generic, pi, kiro, gemini, antigravity,
codex, hermes, openclaw, copilot, trae, trae-cn
```

Project-local setup installs full skills and bootstrap files such as
`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `HERMES.md`, Cursor rules, Windsurf
rules, Kiro steering, Antigravity rules/workflows, and Copilot instructions.

Global setup installs only the portable global skill set, plus any
`--global-extra` skills you choose.

## 🔄 Core Workflows

BeeWeave is designed as a loop, not a one-way archive. Each pass through the
loop should make the next pass better: better source selection, sharper drafts,
more durable knowledge, and richer context for the next piece of work.

### 1. Collect Material

Start by gathering raw inputs into `workbench/`: notes, links, PDFs, exported
chats, meeting transcripts, screenshots, product briefs, source files, or quick
findings from a live agent session.

Useful entry points:

```text
/beeweave-capture --quick
/beeweave-ingest workbench/inbox
```

The goal at this stage is not to make everything polished. `workbench/inbox/`
is allowed to be messy. It is the intake layer for material that might become
an article, a short post, a reference note, or a durable concept later.

### 2. Create From the Material

Use the workbench as a drafting surface. The writing skills help turn collected
material into a concrete output while preserving your point of view:

```text
Use beeweave-article-writer to draft a long-form article from these notes.
Use beeweave-social-writer to turn this finding into a thread.
```

Creation is where the raw material becomes useful. Drafts live under
`workbench/articles/drafts/`, source material stays in `workbench/library/` or
`workbench/inbox/`, and finished pieces can move to
`workbench/articles/published/`.

### 3. Distill Durable Knowledge

After a draft becomes a finished piece, use the published output as the
high-signal source for durable knowledge. This keeps the vault grounded in what
you actually decided, argued, and shipped instead of every rough note that
passed through the inbox:

```text
/beeweave-ingest workbench/articles/published
/beeweave-update
/beeweave-synthesize
```

`beeweave-ingest` reads finished articles or selected source material and
distills the reusable concepts, claims, references, and relationships.
`beeweave-update` is useful when the creation happened inside another project
and you want to preserve the durable decisions or lessons from that work.
`beeweave-synthesize` runs after the vault has grown, finding cross-cutting
connections between concepts. The result is not a pile of summaries; it is a
linked markdown knowledge base with concepts, entities, references, project
notes, and synthesis pages.

### 4. Reuse Context

Before the next writing or research pass, query the vault so the agent starts
from what you already know:

```text
/beeweave-query what do I know about MCP security?
/beeweave-digest this week
```

`beeweave-query` retrieves targeted context from titles, tags, summaries, and
wikilinks before opening full page bodies. `beeweave-digest` gives a readable
review of what changed recently and what themes are emerging.

### 5. Feed the Next Loop

The output of one loop becomes the input to the next. A query reveals gaps. A
draft exposes weak claims. A digest surfaces an emerging theme. Those signals
guide the next round of collection and creation:

```text
Find sources that would strengthen this draft.
Capture the open questions from this session.
Ingest these new references, then update the article.
```

This is the data flywheel: every capture makes the vault better, every vault
query improves the next draft, and every draft reveals what to collect next.

### Named Vault Routing

Create named configs such as `~/.beeweave/config.work`, then route a single
request with `@name`:

```text
beeweave-query @work what do I know about deployment rollbacks?
@research update my BeeWeave vault
```

The `@name` override applies only to that request and does not change the
default vault.
All supported agents can use this syntax, including Claude Code, Cursor, Windsurf, Codex, Gemini,
Kiro, Hermes, OpenClaw, Pi, Copilot CLI, and generic `AGENTS.md` agents.

## 🧩 Optional Features

### Browser capture extension

The Chrome extension in `extensions/brain-capture/` saves selected text and web
pages into `workbench/inbox/web/`.

Install it from `chrome://extensions` with **Developer mode** and **Load
unpacked**, then process captures with:

```text
/beeweave-ingest workbench/inbox
```

### QMD semantic search

BeeWeave works with `Grep` and `Glob` by default. For larger vaults, you can
enable optional QMD semantic search:

```env
QMD_WIKI_COLLECTION=wiki
QMD_PAPERS_COLLECTION=papers
QMD_TRANSPORT=mcp
QMD_CLI_SEARCH_MODE=quality
```

When configured, `beeweave-query` can search the vault semantically and
`beeweave-ingest` can surface related source material before writing pages. If
QMD is not configured, BeeWeave silently falls back to local text search.

### Obsidian graph

The vault is regular markdown and can be opened directly in Obsidian. Use
`beeweave-graph-colorize` to update `.obsidian/graph.json` with color groups by
tag, category, visibility, or a custom mapping.

## 💻 CLI Reference

```text
bwe setup             install skills into agents and write config
bwe uninstall         remove BeeWeave skills and config
bwe list              list bundled skills
bwe info              show install paths, version, and config
bwe graph-query       query the vault wikilink index
bwe batch-plan        plan parallel ingest batches
bwe graph-analyse     analyze vault graph structure
bwe cache-check       check source changes against .manifest.json
bwe cache-update      record source hashes after ingestion
bwe cache-hash        compute source hashes
bwe ast-extract       extract code structure without LLM calls
```

## 📦 Repository Layout

```text
beeweave/        # Python CLI and helpers
.skills/         # source skill definitions
bootstrap/       # user-project bootstrap templates
extensions/      # browser extension assets
tests/           # pytest suite
setup.sh         # source-checkout setup path
pyproject.toml   # package metadata and bwe entrypoint
```

Runtime `vault/` and `workbench/` directories are generated by setup and should
not be committed to this repository.

## 🧪 Development

```bash
uv run pytest
uv run bwe setup --help
uv run bwe info
```

## 🌱 Contributing

BeeWeave is still early. Useful contributions include better ingest strategies,
new agent history importers, vault lint checks, graph analysis, and focused
skills for real knowledge-work workflows.

To add a skill:

1. Create `.skills/wiki/<skill-name>/SKILL.md` or
   `.skills/workbench/<skill-name>/SKILL.md`.
2. Add YAML frontmatter with `name` and `description`.
3. Run `bwe setup` or `bash setup.sh`.
4. Test it in an agent with a natural trigger phrase or command.

## 📄 License

MIT

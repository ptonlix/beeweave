# Quick Start

Install BeeWeave in the environment where you want to use the `bwe` CLI:

```bash
pip install beeweave
```

Then run setup in the project or workspace directory where BeeWeave should
create its runtime folders:

```bash
bwe setup
```

`bwe setup` creates `vault/` and `workbench/` in the current workspace, writes
global config under `~/.beeweave/config`, and installs the selected agent
skills and bootstrap files.

## Common Commands

```bash
bwe info
bwe list
bwe setup --agents claude,codex
bwe setup --global-extra beeweave-capture,beeweave-status
bwe uninstall
```

`bwe uninstall` removes BeeWeave-managed skills, bootstrap files, and
`~/.beeweave` config. It does not delete your `vault/` or `workbench/` content.

## Use the Skills

After setup, open the workspace in a supported agent and use the skills in
natural language or command-style prompts:

```text
/beeweave-ingest workbench/inbox
/beeweave-query what do I know about rate limiting?
/beeweave-update
```

## Source Checkout Setup

When working from this repository rather than the PyPI package, run:

```bash
bash setup.sh
uv run bwe info
```

Use the source checkout path for development. Use `pip install beeweave` for a
normal user installation.

![Quickstart terminal flow](assets/quickstart-terminal-flow.png)

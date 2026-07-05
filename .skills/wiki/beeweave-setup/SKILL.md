---
name: beeweave-setup
description: >
  Initialize a new Obsidian wiki vault with the correct structure, special files, and configuration.
  Use this skill when the user wants to set up a new wiki from scratch, initialize the vault structure,
  create the .env file, or says things like "set up my wiki", "initialize obsidian", "create a new vault",
  "get started with the wiki". Also use when the user needs to reconfigure their existing vault or
  fix a broken setup.
---

# Obsidian Setup — Vault Initialization

You are setting up a new Obsidian wiki vault (or repairing an existing one).

## Step 1: Create .env

If `.env` doesn't exist, create it from `.env.example`. Ask the user for:

1. **Where should the vault live?** → `BEEWEAVE_VAULT_PATH`
   - Default: `~/Documents/beeweave-vault`
   - Must be an absolute path (after expansion)

2. **Where are your source documents?** → `BEEWEAVE_SOURCES_DIR`
   - Can be multiple paths, comma-separated
   - Default: `~/Documents`

3. **Want to import Claude history?** → `CLAUDE_HISTORY_PATH`
   - Default: auto-discovers from `~/.claude`
   - Set explicitly if Claude data is elsewhere

4. **Have QMD installed?** → `QMD_WIKI_COLLECTION` / `QMD_PAPERS_COLLECTION` / `QMD_TRANSPORT`
   - Optional. Enables semantic search in `beeweave-query` and source discovery in `beeweave-ingest`.
   - Default to `QMD_TRANSPORT=mcp` unless the user wants the agent to call the local `qmd` CLI directly.
   - If using CLI mode, set `QMD_CLI_SEARCH_MODE=quality` by default; suggest `balanced` if reranking is too slow.
   - If unsure, skip for now — both skills fall back to `Grep` automatically.
   - Install instructions: see `.env.example` (QMD section).

5. **Token budget warning threshold?** → `WIKI_TOKEN_WARN_THRESHOLD`
   - Default: `100000` (warn when full-wiki read would cost > 100K tokens)
   - Set to `0` to disable the warning entirely
   - `beeweave-status` shows a token footprint table and emits this warning automatically

6. **Enable staged writes?** → `WIKI_STAGED_WRITES`
   - Default: unset / `false` (pages written directly to their final location)
   - Set to `true` for team wikis, high-stakes domains, or any vault where the human wants final say on every LLM-written page
   - When enabled: all new/updated pages land in `_staging/` first; run `/beeweave-stage-commit` to review and promote them
   - `beeweave-status` shows a "Staged writes pending" count when files are waiting

## Step 2: Create Vault Directory Structure

```bash
mkdir -p "$BEEWEAVE_VAULT_PATH"/{concepts,entities,skills,references,synthesis,projects,_meta,_archives,_staging,.obsidian}
mkdir -p workbench/inbox/{captures,web,archived,rejected} workbench/articles/{drafts,published} workbench/library
```

- `.obsidian/` — Obsidian's own config. Creates vault recognition.
- `projects/` — Per-project knowledge (populated during ingest).
- `_meta/` — System metadata such as taxonomy, dashboards, and Obsidian Bases.
- `_archives/` — Stores wiki snapshots for rebuild/restore operations.
- `_staging/` — Review queue for LLM-written pages when `WIKI_STAGED_WRITES=true`. Pages here are not visible in Obsidian's graph until promoted via `/beeweave-stage-commit`.
- `workbench/inbox/captures/` — Agent quick captures and stop-hook findings.
- `workbench/inbox/web/` — Browser captures and web clippings.
- `workbench/inbox/archived/` — Processed original inputs.
- `workbench/inbox/rejected/` — Rejected staged pages or patches for manual editing.

## Step 3: Create Special Files

### index.md

```markdown
---
title: Wiki Index
---

# Wiki Index

*This index is automatically maintained. Last updated: TIMESTAMP*

## Concepts

*No pages yet. Use `beeweave-ingest` to add your first source.*

## Entities

## Skills

## References

## Synthesis

## Journal
```

### log.md

```markdown
---
title: Wiki Log
---

# Wiki Log

- [TIMESTAMP] INIT vault_path="BEEWEAVE_VAULT_PATH" categories=concepts,entities,skills,references,synthesis,journal
```

### hot.md

```markdown
---
title: Hot Cache
updated: TIMESTAMP
---

# Hot Cache

*A ~500-word semantic snapshot of recent activity. Updated after every major write operation.*

## Recent Activity

- [TIMESTAMP] INIT — vault created at BEEWEAVE_VAULT_PATH

## Active Threads

*None yet — start ingesting sources to populate.*

## Key Takeaways

*None yet.*

## Flagged Contradictions

*None yet.*
```

## Step 4: Create .obsidian Configuration

Create minimal Obsidian config for a good out-of-box experience:

### .obsidian/app.json
```json
{
  "strictLineBreaks": false,
  "showFrontmatter": false,
  "defaultViewMode": "preview",
  "livePreview": true
}
```

### .obsidian/appearance.json
```json
{
  "baseFontSize": 16
}
```

## Step 5: Recommend Obsidian Plugins

Tell the user about these recommended community plugins (they install manually):

1. **Dataview** — Query page metadata, create dynamic tables. Essential for a wiki.
2. **Graph Analysis** — Enhanced graph view for exploring connections.
3. **Templater** — If they want to create pages manually using templates.
4. **Obsidian Git** — Auto-backup the vault to a git repo.

## Step 6: Verify Setup

Run a quick sanity check:
- [ ] Vault directory exists with: `concepts/`, `entities/`, `skills/`, `references/`, `synthesis/`, `projects/`, `_meta/`, `_archives/`, `_staging/`
- [ ] Workbench inbox exists with: `captures/`, `web/`, `archived/`, `rejected/`
- [ ] `index.md` exists at vault root
- [ ] `log.md` exists at vault root
- [ ] `hot.md` exists at vault root
- [ ] `.env` has `BEEWEAVE_VAULT_PATH` set
- [ ] `.obsidian/` directory exists
- [ ] `_staging/` directory exists (required even when `WIKI_STAGED_WRITES` is not set — created on setup for future use)
- [ ] Source directories (if configured) exist and are readable

Report the results and tell the user they can now:
1. Open the vault in Obsidian (File → Open Vault → select the directory)
2. Run `beeweave-status` to see what's available to ingest
3. Run `beeweave-ingest` to add their first sources
4. Run `beeweave-claude-ingest` to mine their Claude conversations
5. Run `beeweave-codex-ingest` to mine their Codex sessions (if they use Codex)
6. Run `beeweave-status` again anytime to check the delta

## Optional: Install the Stop Hook (Auto-Capture)

Ask the user: **"Want to auto-capture findings at session end?"**

If yes, install the Stop hook into their global Claude Code settings so that every session
with meaningful work automatically prompts `/beeweave-capture --quick` before closing.

**What the hook does:** reads the session transcript on Stop, counts file edits and shell
calls, and if significant work happened, asks Claude to run `/beeweave-capture --quick` once.
The `beeweave-capture` quick-mode KEEP/SKIP gate prevents noise — routine or
inconclusive sessions are skipped automatically.

**Installation steps:**

1. Find the beeweave repo path (the directory where this skill lives). If
   `BEEWEAVE_REPO` is set in config, use that. Otherwise, check common locations:
   `~/Documents/projects/beeweave`, `~/beeweave`, or ask the user.

2. Merge the hook entry into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash <REPO_PATH>/bootstrap/claude/hooks/beeweave-stop-capture.sh"
          }
        ]
      }
    ]
  }
}
```

   A template lives at `<REPO_PATH>/bootstrap/claude/settings.stop-hook.json`.
   Replace `<BEEWEAVE_REPO>` with the absolute repo path before merging.

   If `~/.claude/settings.json` already exists and has a `hooks.Stop` array, **append** the new
   entry rather than replacing — don't clobber existing hooks.

3. Confirm: "Stop hook installed. Claude Code will prompt `/beeweave-capture --quick` at the
   end of any session where you write files or run ≥ 4 shell commands."

**To uninstall later:** remove the hook entry from `~/.claude/settings.json` or set
`BEEWEAVE_CAPTURE=false` in your shell to skip capture for a single session.

## Optional: Refresh QMD After Setup

If `QMD_WIKI_COLLECTION` is configured and the local QMD CLI is available, run `qmd update` after the initial vault files exist so the fresh vault is immediately queryable. No embedding pass is usually needed at setup time because the vault starts empty, so a plain update is enough unless you have already populated pages.

---
name: beeweave-switch
description: >
  Switch between multiple BeeWeave profiles. Use this skill when the user says
  "/beeweave-switch NAME", "switch to my work wiki", "switch vault", "change wiki", "which wiki am I on",
  "list my wikis", "show my vaults", "create a new vault config", or "add a new wiki profile".
  The skill manages named config files at ~/.beeweave/config.NAME and activates one by
  symlinking it to ~/.beeweave/config.
---

# Wiki Switch — Manage Multiple BeeWeave Profiles

Each profile is a complete config file at `~/.beeweave/config.<name>`. A profile includes the vault path, workbench path, QMD settings, and any tool-specific paths. The active profile is whichever file `~/.beeweave/config` symlinks to. Switching profiles means re-pointing that symlink.

**Switch vs. inline targeting.** `/beeweave-switch <name>` changes your **persistent default** (re-points
the symlink, affecting all future requests). To touch a different profile for just one request without
changing your default, use the inline **`@name`** override in any request (e.g. `@work save this`,
`beeweave-query @personal about X`). The `@name` override is handled by the **Config Resolution Protocol**
in `beeweave-core/SKILL.md`, not by this skill — it resolves `~/.beeweave/config.<name>` for that one
invocation and never re-points the symlink.

## Dispatch

Parse the invocation and route to the right section:

| Invocation | Action |
|---|---|
| `/beeweave-switch <name>` | → **Switch** |
| `/beeweave-switch list` | → **List** |
| `/beeweave-switch show [name]` | → **Show** |
| `/beeweave-switch new <name>` | → **New** |
| `/beeweave-switch` (no args) | → **List** (treat as list) |
| `@<name> …` (inline, in any request) | → Not this skill — the **Config Resolution Protocol** resolves that profile for one invocation without re-pointing the symlink |

---

## Switch (default action)

Activate a named BeeWeave profile.

1. Verify `~/.beeweave/config.<name>` exists. If not, tell the user the profile doesn't exist and list what's available (run **List**).
2. Run:
   ```bash
   ln -sf ~/.beeweave/config.<name> ~/.beeweave/config
   ```
3. Read `BEEWEAVE_VAULT_PATH` and `BEEWEAVE_WORKBENCH_PATH` from the newly active config.
4. Confirm to the user:
   ```
   Switched to profile: <name>
   Vault path: <value of BEEWEAVE_VAULT_PATH from the config>
   Workbench path: <value of BEEWEAVE_WORKBENCH_PATH from the config>
   ```

---

## List

Show all registered BeeWeave profiles and which is active.

1. Find all files matching `~/.beeweave/config.*` (exclude `config` itself — that's the symlink).
2. Resolve the current symlink target: `readlink ~/.beeweave/config`
3. For each config file, read the first non-empty comment line (lines starting with `#`) as a human description of the vault. Fall back to the file's suffix as the label if no comment exists.
4. Display:
   ```
  Profiles:
     personal   My personal research wiki    ← active
     work       Work projects wiki
   ```
   Mark the active one with `← active`. If the symlink is broken or `config` doesn't exist, show `(none active)`.

---

## Show

Print the full config for a vault.

- If a name is given, read `~/.beeweave/config.<name>`.
- If no name given, read `~/.beeweave/config` (the active profile).
- If the file doesn't exist, tell the user and list what's available.
- Print the file contents verbatim (redact any lines containing `API_KEY` or `SECRET` — show `***` instead of the value).

---

## New

Scaffold a new profile config from the current active config as a template.

1. Check `~/.beeweave/config.<name>` doesn't already exist. Abort if it does.
2. Copy the active config:
   ```bash
   cp ~/.beeweave/config ~/.beeweave/config.<name>
   ```
3. Read the copied config. Config files use `# --- Section name ---` comment headers to group fields into sections (e.g., `# --- Vault-specific ---`, `# --- Vault-independent ---`, `# --- Secrets ---`). Use these sections to determine what to ask about:
   - Fields in sections labeled "vault-specific", "paths", or similar → ask the user for new values
   - Fields in sections labeled "vault-independent", "global", "shared" → keep as-is (copy over unchanged)
   - Fields in sections labeled "secrets" → ask if the new vault uses the same credentials or different ones
   - If there are no section headers, present all fields and let the user decide which to change
4. Ask the user for updated values for the vault-specific fields. Use the current values as visible defaults — the user only needs to supply what differs.
5. Write the updated values into `~/.beeweave/config.<name>`.
6. Update the top comment line to describe the new profile (e.g., `# BeeWeave — <name> profile`).
7. Confirm:
   ```
   Created: ~/.beeweave/config.<name>
   Run `/beeweave-switch <name>` to activate it, then run `beeweave-setup` to initialise the new vault.
   ```
   Do not switch automatically — let the user decide when to activate.

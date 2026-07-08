---
name: beeweave-switch
description: >
  Inspect and manage multiple BeeWeave profiles. Use this skill when the user says
  "/beeweave-switch list", "/beeweave-switch show work", "which wiki am I on",
  "list my wikis", "show my vaults", "create a new vault config", "add a new wiki profile",
  or "set work as my default BeeWeave profile".
  The skill manages named config files at ~/.beeweave/config.NAME. It does not activate
  profiles or repoint ~/.beeweave/config; use @name for per-request named profile routing.
---

# Wiki Switch — Manage Multiple BeeWeave Profiles

Each profile is a complete config file at `~/.beeweave/config.<name>`. A profile includes the vault path, workbench path, QMD settings, and any tool-specific paths. The default profile is `~/.beeweave/config`. Named profiles are not activated by symlink; use `@name` in a request to target `~/.beeweave/config.<name>`.

**Profile targeting.** The inline **`@name`** override is the supported way to use a named profile
(e.g. `@work save this`, `beeweave-query @personal about X`). The `@name` override is handled by the
**Config Resolution Protocol** in `beeweave-core/SKILL.md`; it resolves `~/.beeweave/config.<name>`
for that one invocation and never re-points `~/.beeweave/config`.

## Dispatch

Parse the invocation and route to the right section:

| Invocation | Action |
|---|---|
| `/beeweave-switch list` | → **List** |
| `/beeweave-switch show [name]` | → **Show** |
| `/beeweave-switch new <name>` | → **New** |
| `/beeweave-switch set-default <name>` | → **Set Default** |
| `/beeweave-switch` (no args) | → **List** (treat as list) |
| `/beeweave-switch <name>` | → Explain the choices: use `@<name>` for one request, `show <name>` to inspect, or `set-default <name>` to copy it into the default config |
| `@<name> …` (inline, in any request) | → Not this skill — the **Config Resolution Protocol** resolves that profile for one invocation |

---

## List

Show all registered BeeWeave profiles and which is active.

1. Find `~/.beeweave/config` and all files matching `~/.beeweave/config.*`.
2. Treat `~/.beeweave/config` as the default profile when it exists.
3. For each config file, read the first non-empty comment line (lines starting with `#`) as a human description of the vault. Fall back to the file's suffix as the label if no comment exists.
4. Display:
   ```
  Profiles:
     default    ~/.beeweave/config
     personal   My personal research wiki
     work       Work projects wiki
   ```

---

## Show

Print the full config for a vault.

- If a name is given, read `~/.beeweave/config.<name>`.
- If no name given, read `~/.beeweave/config` (the default profile).
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
   Use `@<name>` in a request to target this profile.
   ```
   Do not switch or activate automatically.

---

## Set Default

Set a named profile as the default BeeWeave profile by copying it to `~/.beeweave/config`.

Use this when the user wants future requests without `@name` to use a named profile's configuration.

Equivalent CLI command:

```bash
bwe profile set-default <name>
```

Safety rules:

1. Verify `~/.beeweave/config.<name>` exists. If not, tell the user it does not exist and run **List**.
2. Never delete or rename `~/.beeweave/config.<name>`. The named profile must remain available for `@<name>` routing.
3. Never use symlinks for this action.
4. If `~/.beeweave/config` exists, do not overwrite it silently. First create a timestamped backup:
   ```text
   ~/.beeweave/config.backup-YYYYMMDD-HHMMSS
   ```
5. Before overwriting an existing default config, show the planned operation and require the user to type `YES`.
6. If the user does not type `YES`, stop without modifying any files.
7. After confirmation, copy:
   ```bash
   cp ~/.beeweave/config ~/.beeweave/config.backup-YYYYMMDD-HHMMSS
   cp ~/.beeweave/config.<name> ~/.beeweave/config
   ```

Completion message:

```text
Default BeeWeave profile updated.

Default:
  ~/.beeweave/config

Copied from:
  ~/.beeweave/config.<name>

Backup:
  ~/.beeweave/config.backup-YYYYMMDD-HHMMSS

The named profile is preserved and @<name> still works.
```

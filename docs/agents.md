# Agents

BeeWeave installs shared context and skills into the agents you choose during
setup.

## Supported Targets

```text
claude, cursor, windsurf, generic, pi, kiro, gemini, antigravity,
codex, hermes, openclaw, copilot, trae, trae-cn
```

Project-local setup installs full BeeWeave skills and bootstrap files. Global
setup stays intentionally small so other projects do not inherit the full
BeeWeave workspace by accident.

## Bootstrap Files

Depending on the selected target, setup can write files such as:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `HERMES.md`
- Cursor rules
- Windsurf rules
- Kiro steering
- Antigravity rules and workflows
- Copilot instructions

These files teach the agent how to use the same `vault/` and `workbench/`
without trapping context inside one chat or one tool.

## Install Strategy

- Global install: portable default skills and selected advanced skills.
- Project-local install: full BeeWeave skill set for the chosen workspace.
- Runtime data: created in the workspace, not in this repository.

![Agent install targets](assets/agent-install-targets.png)

# Skills

BeeWeave skills are agent-facing workflows. They let agents move material
between the workbench, vault, and active project context.

## Default Global Skills

- `beeweave-update`: sync useful project knowledge into the vault.
- `beeweave-query`: answer questions from compiled vault context.
- `beeweave-ingest`: process source material into durable notes.

These are installed globally by default for supported agents because they are
portable and useful across projects.

## Optional Advanced Global Skills

Install advanced skills explicitly:

```bash
bwe setup --global-extra beeweave-capture,beeweave-status
```

Examples include:

- `beeweave-capture`
- `beeweave-context-pack`
- `beeweave-digest`
- `beeweave-status`
- `beeweave-memory-bridge`

## Project-local Skills

The full BeeWeave skill set is installed project-locally for selected agents.
This keeps unrelated projects clean while giving the BeeWeave workspace the
complete workflow surface.

## Named Vault Routing

Create named configs such as `~/.beeweave/config.work`, then route one request
with `@name`:

```text
beeweave-query @work what do I know about deployment rollbacks?
@research update my BeeWeave vault
```

The override applies only to that request.

![Skills scope map](assets/skills-scope-map.png)

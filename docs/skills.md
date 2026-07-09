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

Workbench/project-local skills include:

- `beeweave-article-writer`: draft long-form articles, blog posts, essays, and
  opinion pieces.
- `beeweave-article-publisher`: move finished drafts to
  `workbench/articles/published/` and ingest published work into the vault.
- `beeweave-ppt-writer`: create HTML PPT decks under `workbench/ppt/`, using
  external PPT skills such as `guizang-ppt-skill` when needed.
- `beeweave-social-writer`: draft X/Twitter posts, threads, short takes, and
  social copy.
- `beeweave-url-capture`: download a URL into `workbench/inbox/web/` as a
  self-contained raw capture bundle, then hand off to
  `/beeweave-ingest workbench/inbox`.
- `baoyu-url-to-markdown`: bundled project-local URL extraction dependency used
  by `beeweave-url-capture`; it is not installed as a default global skill.

## External Skills

External skills are user-installed third-party agent skills managed by
`bwe external`. They are stored outside BeeWeave runtime folders:

```text
~/.beeweave/external/
+-- repos/       # cloned source repositories
+-- skills/      # stable skill-name entries
+-- manifest.json
```

Install one external skill and link it into the current workspace:

```bash
bwe external install https://github.com/op7418/guizang-ppt-skill \
  --skill guizang-ppt-skill \
  --link-project .
```

For multi-skill repositories, specify `--skill` or `--path`; BeeWeave does not
install every skill from a repository unless `--all` is explicit.

External skills are not bundled into the BeeWeave wheel, source `.skills/`
directory, vault, or workbench. Use `bwe external list` and
`bwe external info <skill-name>` to inspect what is installed locally.

## Named Profile Routing

Create named configs such as `~/.beeweave/config.work`. Each config is a full
BeeWeave profile: vault path, workbench path, QMD settings, and tool-specific
paths. Route one request with `@name`:

```text
beeweave-query @work what do I know about deployment rollbacks?
@research update my BeeWeave vault
```

The override applies only to that request.

To make a named profile the default for future requests without `@name`, run:

```bash
bwe profile set-default work
```

BeeWeave backs up the existing `~/.beeweave/config` before copying
`~/.beeweave/config.work` into place.

![Skills scope map](assets/skills-scope-map.png)

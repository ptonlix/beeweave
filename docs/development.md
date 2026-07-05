# Development

Use the source checkout when changing BeeWeave itself.

## Repository Layout

```text
beeweave/       # Python CLI and helpers
.skills/        # source skill definitions
bootstrap/      # user-project bootstrap templates
extensions/     # browser extension and assets
tests/          # pytest suite
openspec/       # proposed and active change specs
docs/           # MkDocs source documentation
```

## Checks

```bash
uv run pytest
uv run bwe setup --help
uv run bwe info
```

## Documentation

Install MkDocs tooling outside BeeWeave runtime dependencies:

```bash
uv sync --group docs
```

Or use pip in a documentation environment:

```bash
pip install "mkdocs-material>=9.6,<9.7"
```

Preview locally:

```bash
uv run --group docs mkdocs serve
```

Build strictly:

```bash
uv run --group docs mkdocs build --strict
```

The generated `site/` directory is a build artifact and should not be committed
to the `main` branch.

## GitHub Pages

Documentation deploys to <https://ptonlix.github.io/beeweave/>. In the GitHub
repository settings, Pages should use:

- Source: Deploy from a branch
- Branch: `gh-pages`
- Folder: `/root`

The workflow builds from source and publishes the generated site to the
`gh-pages` branch.

## OpenSpec

Use OpenSpec changes for behavior or workflow changes:

```bash
openspec validate <change-name> --strict
```

Archive a change only after implementation and verification are complete.

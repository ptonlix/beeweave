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

Use the Makefile for the standard local quality gate:

```bash
make format
make check
```

The targets expand to Ruff formatting/linting, mypy type checking, and pytest:

```bash
uv run ruff format beeweave tests
uv run ruff check beeweave tests --fix
uv run ruff format --check beeweave tests
uv run ruff check beeweave tests
uv run mypy
uv run python -m pytest
```

For quick CLI smoke checks, also run:

```bash
uv run bwe setup --help
uv run bwe info
```

## Local CLI Install

Install the current source checkout as the active development `bwe` tool:

```bash
make dev-install
```

This runs `uv tool install --reinstall --editable <repo-root>` with the
repository root resolved from the Makefile location. Run `bwe setup` afterwards
only when you need to refresh installed agent skills from the newly installed
package.

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

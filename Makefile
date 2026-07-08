REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

.PHONY: format lint typecheck test check dev-install

format:
	uv run ruff format beeweave tests
	uv run ruff check beeweave tests --fix

lint:
	uv run ruff format --check beeweave tests
	uv run ruff check beeweave tests

typecheck:
	uv run mypy

test:
	uv run python -m pytest

check: lint typecheck test

dev-install:
	uv tool install --reinstall --editable "$(REPO_ROOT)"

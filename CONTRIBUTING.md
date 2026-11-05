# Contributing to puigame

This project uses [uv](https://docs.astral.sh/uv/) to manage Python, dependencies, and the virtual environment.

## Set up

[pre-commit](https://pre-commit.com/) is installed once per machine as a standalone uv tool, not as a project dependency:

```powershell
uv tool install pre-commit --python 3.13
```

Then, for each clone:

```powershell
gh repo clone neb01/puigame
cd puigame
uv sync                      # creates .venv with puigame, pygame-ce, and dev tools
pre-commit install           # run the checks automatically on every commit
```

## Run the checks

```powershell
uv run pytest                # tests (headless, no window opens)
uv run ruff check            # lint
uv run ruff format           # format
uv run pyright               # type check
pre-commit run --all-files   # everything pre-commit runs, on all files
```

The pre-commit hooks run the housekeeping checks, Ruff, and pyproject-fmt on every commit. Pyright and pytest run only in CI, so run them yourself before opening a pull request. A hook that fixes a file stops the commit: add the fixed file and commit again.

## Run the examples

```powershell
uv run python examples/minimal.py
uv run python examples/custom_theme.py
uv run python examples/showcase.py
```

## Commit messages

Commits and pull request titles follow [Conventional Commits](https://www.conventionalcommits.org/), for example `feat(button): add disabled state` or `fix: correct hover offset`.

## Conventions

[`docs/conventions.md`](docs/conventions.md) lists the naming, code, docstring, and test rules, with the reason for each.

## Design notes

[`docs/architecture.md`](docs/architecture.md) describes how puigame is built and why.

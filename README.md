# puigame

UI widgets for [pygame-ce](https://pyga.me/).

> **Status:** pre-alpha. The API is not stable yet and there is no release on PyPI.

## Requirements

- Python 3.11+
- pygame-ce 2.5.8+

## Development

This project uses [uv](https://docs.astral.sh/uv/) to manage Python, dependencies, and the virtual environment.

### Set up

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

### Run the checks

```powershell
uv run pytest                # tests (headless, no window opens)
uv run ruff check            # lint
uv run ruff format           # format
uv run pyright               # type check
pre-commit run --all-files   # everything pre-commit runs, on all files
```

### Commit messages

Commits follow [Conventional Commits](https://www.conventionalcommits.org/), e.g. `feat(button): add disabled state` or `fix: correct hover offset`.

## License

[MIT](LICENSE)

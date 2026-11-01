# Continuous Integration Setup

SOAJS Python uses GitHub Actions, like the other SOAJS repositories.

## Branches

| Branch | Purpose |
|--------|---------|
| `feature/*` | Work in progress; pull request to `develop` |
| `develop` | Integration branch |
| `master` | Default branch, released code |
| `release/v1.x` | Pushing here releases the version in `pyproject.toml` |

Flow: `feature/*` → pull request to `develop` → merge `develop` into `master` → merge `master`
into `release/v1.x`. The release branch is pushed last, since that push publishes.

## Tests: `.github/workflows/test.yml`

- **Runs on:** pushes to `master`, `develop` and `feature/*`; pull requests to `master` and
  `develop`.
- **Python versions:** 3.10, 3.11, 3.12, 3.13.
- **Steps:** install (`pip install -e .[dev,fastapi,flask]`), `ruff check soajs tests`,
  `mypy soajs`, `pytest` with coverage, coverage upload to Codecov.

## Release: `.github/workflows/release.yml`

- **Runs on:** pushes to `release` and `release/*`.
- **Steps:** the same checks on 3.10–3.13, then a git tag with the version from
  `pyproject.toml` and a GitHub release with generated notes.
- The package is not published to PyPI; install it from the repository or a release.

## Local Testing

Run what CI runs before pushing:

```bash
ruff check soajs tests && mypy soajs && pytest --cov=soajs tests/
```

Or with the Makefile: `make lint` and `make test-cov`.

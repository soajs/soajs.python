# Continuous Integration Setup

This document describes the CI/CD setup for SOAJS Python.

## Available CI Services

### 1. Travis CI

**Configuration:** `.travis.yml`

#### Features
- Tests on Python 3.9, 3.10, 3.11, 3.12
- Runs linting (ruff) and type checking (mypy)
- Executes test suite with coverage
- Uploads coverage to Codecov
- Pip caching for faster builds
- Email notifications

#### Setup Steps

1. **Enable Travis CI for your repository:**
   - Go to https://travis-ci.com
   - Sign in with GitHub
   - Enable Travis CI for soajs.python repository

2. **Add Travis CI badge to README:**
   ```markdown
   [![Build Status](https://travis-ci.com/soajs/soajs.python.svg?branch=main)](https://travis-ci.com/soajs/soajs.python)
   ```

3. **Configure environment variables (optional):**
   - Go to Travis CI repository settings
   - Add any sensitive environment variables

#### Build Matrix

The Travis CI configuration tests across:
- **Python versions:** 3.9, 3.10, 3.11, 3.12
- **Steps:**
  1. Install dependencies
  2. Run ruff linter
  3. Run mypy type checker
  4. Run pytest with coverage
  5. Upload coverage to Codecov

#### Build Flow

```
Install Dependencies
    ↓
Lint (ruff check)
    ↓
Type Check (mypy)
    ↓
Run Tests (pytest)
    ↓
Upload Coverage (codecov)
    ↓
Send Notifications
```

---

### 2. GitHub Actions

**Configuration:** `.github/workflows/test.yml`

#### Features
- Tests on Python 3.9, 3.10, 3.11, 3.12
- Runs linting (ruff) and type checking (mypy)
- Executes test suite with coverage
- Uploads coverage to Codecov
- Native GitHub integration

#### Setup Steps

1. **Enable GitHub Actions (automatic for GitHub repos)**

2. **Add GitHub Actions badge to README:**
   ```markdown
   [![Tests](https://github.com/soajs/soajs.python/workflows/Test/badge.svg)](https://github.com/soajs/soajs.python/actions)
   ```

3. **Configure secrets (if needed):**
   - Go to repository Settings → Secrets
   - Add any required secrets

---

## Codecov Integration

Both CI services upload coverage reports to Codecov.

### Setup Steps

1. **Enable Codecov:**
   - Go to https://codecov.io
   - Sign in with GitHub
   - Enable for soajs.python repository

2. **Add Codecov badge to README:**
   ```markdown
   [![codecov](https://codecov.io/gh/soajs/soajs.python/branch/main/graph/badge.svg)](https://codecov.io/gh/soajs/soajs.python)
   ```

3. **No additional configuration needed** - coverage is uploaded automatically

---

## Status Badges

Add these badges to the top of your README.md:

```markdown
# SOAJS Python Middleware

[![Build Status](https://travis-ci.com/soajs/soajs.python.svg?branch=main)](https://travis-ci.com/soajs/soajs.python)
[![Tests](https://github.com/soajs/soajs.python/workflows/Test/badge.svg)](https://github.com/soajs/soajs.python/actions)
[![codecov](https://codecov.io/gh/soajs/soajs.python/branch/main/graph/badge.svg)](https://codecov.io/gh/soajs/soajs.python)
[![Python Version](https://img.shields.io/pypi/pyversions/soajs-python)](https://pypi.org/project/soajs-python/)
[![PyPI version](https://badge.fury.io/py/soajs-python.svg)](https://badge.fury.io/py/soajs-python)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Python implementation of the SOAJS middleware for microservices architecture.
```

---

## Comparison: Travis CI vs GitHub Actions

| Feature | Travis CI | GitHub Actions |
|---------|-----------|----------------|
| **Integration** | External service | Native to GitHub |
| **Configuration** | `.travis.yml` | `.github/workflows/*.yml` |
| **Build Speed** | Good | Excellent |
| **Free Tier** | Limited | Generous |
| **Caching** | Built-in | Built-in |
| **Matrix Builds** | Yes | Yes |
| **Best For** | Multi-platform projects | GitHub-hosted projects |

**Recommendation:** Use both for redundancy and broader testing.

---

## Local Testing

Before pushing, test locally:

```bash
# Run linting
make lint

# Run tests with coverage
make test-cov

# Run everything CI runs
ruff check soajs tests && mypy soajs && pytest --cov=soajs tests/
```

---

## Troubleshooting

### Travis CI

**Build fails on dependency installation:**
```yaml
# Add to .travis.yml
before_install:
  - pip install --upgrade pip setuptools wheel
```

**Tests timeout:**
```yaml
# Increase timeout in .travis.yml
script:
  - travis_wait 30 pytest tests/
```

**Cache issues:**
```bash
# Clear cache via Travis CI UI or
cache:
  pip: false
```

### GitHub Actions

**Workflow not running:**
- Check workflow file is in `.github/workflows/`
- Ensure YAML syntax is correct
- Check Actions tab for errors

**Permission denied:**
- Add to workflow:
  ```yaml
  permissions:
    contents: read
  ```

---

## Coverage Requirements

To maintain code quality, coverage should be:
- **Minimum:** 80%
- **Target:** 90%
- **Ideal:** 95%+

Configure coverage requirements in `.coveragerc`:

```ini
[coverage:report]
fail_under = 80
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

---

## Notifications

### Travis CI Notifications

Configure in `.travis.yml`:

```yaml
notifications:
  email:
    recipients:
      - team@soajs.org
    on_success: change
    on_failure: always
  slack:
    rooms:
      - secure: "encrypted-slack-token"
```

### GitHub Actions Notifications

Use GitHub's built-in notifications or add custom actions.

---

## Continuous Deployment

After tests pass, automatically deploy to PyPI:

### Travis CI

```yaml
deploy:
  provider: pypi
  username: __token__
  password:
    secure: "encrypted-pypi-token"
  on:
    tags: true
    python: "3.11"
```

### GitHub Actions

```yaml
- name: Publish to PyPI
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')
  run: |
    python -m build
    python -m twine upload dist/*
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

---

## Monitoring Build Status

- **Travis CI:** https://travis-ci.com/soajs/soajs.python
- **GitHub Actions:** https://github.com/soajs/soajs.python/actions
- **Codecov:** https://codecov.io/gh/soajs/soajs.python

---

## Support

For CI/CD issues:
- Travis CI: https://docs.travis-ci.com
- GitHub Actions: https://docs.github.com/actions
- Codecov: https://docs.codecov.io

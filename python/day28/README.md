# Day 28 — Packaging with Poetry & Internal Tool Distribution

**Goal:** Package ops Python tools with Poetry, publish to an internal PyPI (Artifactory/CodeArtifact/devpi), and install versioned CLIs on engineer laptops and CI runners.

**Time:** 4–5 hours

**Prerequisites:** Days 24 (CLI), 23 (typing)

---

## 1. Why Poetry for internal tools?

| requirements.txt only | Poetry project |
|-------------------------|----------------|
| Unpinned transitive deps | Lock file reproducibility |
| Manual version bumps | Semantic versioning in pyproject |
| Ad-hoc `pip install -e .` | Standard `poetry install` / `poetry build` |
| No publish workflow | `poetry publish` to internal index |

Platform teams ship CLIs like `ops`, `inv-check`, and `tf-drift` as installable packages — not git clones on every laptop.

---

## 2. Initialize a package

```bash
cd python/day28/labs
poetry init --name handbook-tool --python "^3.11" --dependency aiohttp --dependency typer
mkdir -p src/handbook_tool
```

Layout (src structure — recommended):

```
python/day28/labs/
├── pyproject.toml
├── poetry.lock          # generated
├── README.md
└── src/
    └── handbook_tool/
        ├── __init__.py
        ├── cli.py
        └── __main__.py
```

`pyproject.toml` essentials:

```toml
[tool.poetry]
name = "handbook-tool"
version = "0.1.0"
description = "Internal ops CLI for handbook labs"
authors = ["Platform Team <platform@example.com>"]
readme = "README.md"
packages = [{ include = "handbook_tool", from = "src" }]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.0"
rich = "^13.7.0"

[tool.poetry.scripts]
handbook-tool = "handbook_tool.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

## 3. Development workflow

```bash
poetry install              # create venv + install deps
poetry run handbook-tool --help
poetry add pydantic         # add runtime dep
poetry add --group dev pytest mypy
poetry run pytest
poetry run mypy src
```

Activate shell inside venv:

```bash
poetry shell
handbook-tool version
```

---

## 4. Versioning and releases

Follow semver for internal tools:

| Change | Version bump |
|--------|--------------|
| Bug fix | PATCH (`0.1.1`) |
| New subcommand, backward compatible | MINOR (`0.2.0`) |
| Removed flag or changed behavior | MAJOR (`1.0.0`) |

```bash
poetry version patch
poetry build                  # dist/*.whl and *.tar.gz
```

Tag in git: `handbook-tool-v0.1.1`.

---

## 5. Publishing to internal PyPI

### AWS CodeArtifact

```bash
aws codeartifact login --tool pip --domain mydomain --repository pypi-store
poetry config repositories.internal https://mydomain-123456789012.d.codeartifact.us-east-1.amazonaws.com/pypi/pypi-store/simple/
poetry publish -r internal --username aws --password "$(aws codeartifact get-authorization-token ...)"
```

### Artifactory / devpi

```bash
poetry config repositories.internal https://artifactory.example.com/api/pypi/pypi-local/simple
poetry publish -r internal -u ci-bot -p "$ARTIFACTORY_TOKEN"
```

CI publishes on tag; engineers install with:

```bash
pip install handbook-tool==0.1.0 --index-url https://internal/simple
```

---

## 6. Consuming in CI

```yaml
# GitHub Actions snippet
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install handbook-tool==0.1.0 --index-url ${{ secrets.INTERNAL_PYPI_URL }}
- run: handbook-tool health --json
```

Pin exact versions in CI; allow patch updates on laptops via `~=0.1.0` if desired.

---

## 7. Private dependency groups

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
mypy = "^1.11"

[tool.poetry.group.docs.dependencies]
mkdocs = "^1.6"
```

```bash
poetry install --without docs
poetry install --with dev
```

---

## 8. Alternatives and migration

| Tool | When |
|------|------|
| **Poetry** | Full-featured internal packages |
| **uv** | Fast installs, growing Poetry compatibility |
| **Hatch** | PEP 621, simpler monorepos |
| **pip-tools** | Minimal compile workflow |

Pick one standard per organization — not five.

---

## 9. Lab — Day 28

Work from `python/day28/labs/`.

1. Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`.
2. Run `poetry install` in the labs directory.
3. Execute `poetry run handbook-tool version` and `poetry run handbook-tool echo hello`.
4. Run `poetry build` and inspect `dist/`.
5. Install wheel locally: `pip install dist/handbook_tool-*.whl && handbook-tool version`.
6. Bump version: `poetry version minor` and rebuild.
7. **Stretch:** Configure a local devpi server and `poetry publish` to it.

**Success criteria:** CLI entry point works via `poetry run` and after wheel install.

---

## 10. DevOps connections

- **Golden CI images:** Pre-bake common internal CLIs in runner AMIs.
- **Dependabot/Renovate:** Track internal package updates like open-source deps.
- **SBOM:** Poetry lock files feed supply-chain audits (pairs with Day 29).

---

## Quick reference

| Task | Command |
|------|---------|
| Install deps | `poetry install` |
| Run CLI | `poetry run handbook-tool` |
| Add dependency | `poetry add requests` |
| Build | `poetry build` |
| Bump version | `poetry version patch` |
| Publish | `poetry publish -r internal` |

**Next:** [Day 29 — Security scanning in CI](../day29/)

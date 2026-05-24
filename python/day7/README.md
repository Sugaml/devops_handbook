# Day 7 — Modules, Packages, venv, pip & pyproject.toml Intro

**Goal:** Organize reusable ops code into importable modules; isolate dependencies with virtual environments; install packages with pip; understand modern `pyproject.toml` layout.

**Time:** 4–5 hours

---

## 1. Modules and imports

Every `.py` file is a **module**. Package = directory with `__init__.py` (still recommended for explicit packages).

```python
# deploy_tool/config.py
TIMEOUT = 30

def load():
    ...
```

```python
# deploy_tool/cli.py
from deploy_tool.config import TIMEOUT
from deploy_tool import config   # namespace
```

| Import style | When |
|--------------|------|
| `import json` | Standard library |
| `from pathlib import Path` | Single name used often |
| `from deploy_tool import config` | Package internal |

Avoid `from module import *` in production scripts.

---

## 2. `__name__` and package execution

```python
# deploy_tool/__main__.py
def main():
    print("package entrypoint")

if __name__ == "__main__":
    main()
```

```bash
python3 -m deploy_tool
```

---

## 3. Virtual environments (venv)

Isolate project dependencies from system Python:

```bash
cd python/day7/labs/sample_project
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
which python3                 # points inside .venv
pip install --upgrade pip
pip install requests
pip freeze > requirements.txt
deactivate
```

| Path | Purpose |
|------|---------|
| `.venv/bin/python` | Interpreter |
| `.venv/lib/.../site-packages` | Installed deps |

**CI:** Create venv in pipeline, `pip install -r requirements.txt`, run tests.

---

## 4. pip workflows

```bash
pip install boto3==1.34.0
pip install -r requirements.txt
pip install -e .                    # editable install from pyproject
pip list
pip show requests
```

Pin versions in production pipelines; use ranges only when you control upgrades.

---

## 5. `pyproject.toml` — modern project metadata

```toml
[project]
name = "handbook-deploy"
version = "0.1.0"
description = "DevOps handbook sample deploy CLI"
requires-python = ">=3.10"
dependencies = [
  "requests>=2.31,<3",
]

[project.scripts]
handbook-deploy = "handbook_deploy.cli:main"

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"
```

Install locally:

```bash
pip install -e .
handbook-deploy --help
```

Tools reading `pyproject.toml`: pip, build, ruff, pytest, mypy.

---

## 6. requirements.txt vs lock files

| File | Role |
|------|------|
| `requirements.txt` | Direct deps for simple projects |
| `requirements-dev.txt` | Linters, pytest |
| `pip-tools` / Poetry / uv lock | Fully pinned transitive deps |

Example `requirements.txt`:

```text
requests==2.31.0
PyYAML==6.0.1
```

---

## 7. PYTHONPATH and layout

Run from project root so imports resolve:

```bash
export PYTHONPATH="${PWD}/src"
python3 -m handbook_deploy.cli
```

Prefer package layout:

```text
sample_project/
  pyproject.toml
  src/
    handbook_deploy/
      __init__.py
      cli.py
```

---

## 8. Lab — Day 7

Work from `python/day7/labs/sample_project/`.

1. Create venv, activate, `pip install -e .`.
2. Run `handbook-deploy` (or `python3 -m handbook_deploy`) and see help text.
3. Add a function in `handbook_deploy/util.py`; import it from `cli.py`.
4. Add `PyYAML` to `pyproject.toml` dependencies; reinstall; parse a tiny YAML string in REPL.
5. Generate `requirements.txt` with `pip freeze` after install; inspect versions.
6. Deactivate venv; confirm system `python3` does not see your package without `-e`.

**Stretch:** Add `[project.optional-dependencies] dev = ["ruff"]` and `pip install -e ".[dev]"`.

---

## 9. DevOps connections

- **Reproducible builds:** Commit `pyproject.toml` + lock or pinned requirements; bake venv in CI cache.
- **Lambda/containers:** Install same deps in Docker `pip install -r` layer as laptop.
- **Security:** `pip audit` or SBOM tools scan transitive deps.

---

## Quick reference

| Task | Command |
|------|---------|
| Create venv | `python3 -m venv .venv` |
| Activate | `source .venv/bin/activate` |
| Editable install | `pip install -e .` |
| Run package | `python3 -m pkg` |
| Freeze | `pip freeze` |

**Next:** [Day 8 — argparse CLI design](../day8/)

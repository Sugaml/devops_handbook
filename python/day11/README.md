# Day 11 — JSON, YAML & TOML Config Loading

**Goal:** Load, validate, and merge configuration from the three formats DevOps teams use daily — JSON, YAML, and TOML — using the standard library and PyYAML.

**Time:** 4–5 hours (theory + hands-on)

---

## 1. Why config formats matter in DevOps

| Format | Typical sources | Python module |
|--------|-----------------|---------------|
| **JSON** | Cloud APIs, CI artifacts, `package.json` | `json` (stdlib) |
| **YAML** | Kubernetes manifests, Ansible, GitHub Actions | `pyyaml` |
| **TOML** | `pyproject.toml`, Cargo, modern app config | `tomllib` (3.11+) |

Automation scripts rarely hard-code values. They read config from files, merge defaults with environment overrides, and fail fast on invalid data.

```
  app defaults.yaml
        │
        ├── merge ──► effective config ──► deploy script
        │
  prod overrides.toml
```

**DevOps use cases:**

- Parse Terraform plan JSON in a gate script
- Read Ansible group vars before a custom pre-flight check
- Load `pyproject.toml` tool settings in a linter wrapper

---

## 2. JSON with the standard library

```python
import json
from pathlib import Path

def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)

def dump_json(data: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
```

**Tips for DevOps scripts:**

- Always set `encoding="utf-8"` — avoids surprises on Windows CI runners.
- Use `json.loads()` for API response bodies; `json.load()` for files.
- Catch `json.JSONDecodeError` and include the file path in the error message.

```python
try:
    cfg = load_json(Path("config.json"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid JSON in config.json line {exc.lineno}: {exc.msg}") from exc
```

---

## 3. YAML with PyYAML

Install in your project venv:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pyyaml
```

```python
import yaml
from pathlib import Path

def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        # safe_load: no arbitrary Python objects (required for untrusted files)
        return yaml.safe_load(fh) or {}

def load_yaml_all(path: Path):
    """Multi-document YAML (e.g. k8s manifest stream)."""
    with path.open(encoding="utf-8") as fh:
        return list(yaml.safe_load_all(fh))
```

**Security rule:** Never use `yaml.load()` without `Loader=yaml.SafeLoader` on files you did not author. Kubernetes and CI configs from third parties must use `safe_load`.

---

## 4. TOML with tomllib (Python 3.11+)

```python
import tomllib
from pathlib import Path

def load_toml(path: Path) -> dict:
    with path.open("rb") as fh:  # tomllib expects binary mode
        return tomllib.load(fh)
```

For Python 3.10 and earlier, use the backport:

```bash
pip install tomli
import tomli as tomllib
```

TOML is ideal for human-edited app settings — clearer than JSON, less ambiguous than YAML.

---

## 5. Unified config loader pattern

Production scripts use a single entry point:

```python
from pathlib import Path

SUFFIX_LOADERS = {
    ".json": load_json,
    ".yaml": load_yaml,
    ".yml": load_yaml,
    ".toml": load_toml,
}

def load_config(path: str | Path) -> dict:
    p = Path(path)
    loader = SUFFIX_LOADERS.get(p.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported config format: {p.suffix}")
    return loader(p)
```

Extend with deep merge for layered configs (base + environment):

```python
def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

---

## 6. Schema validation (lightweight)

Before touching production, validate required keys:

```python
REQUIRED = ("environment", "services")

def validate_app_config(cfg: dict) -> list[str]:
    errors = []
    for key in REQUIRED:
        if key not in cfg:
            errors.append(f"missing required key: {key}")
    for svc in cfg.get("services", []):
        if "name" not in svc or "port" not in svc:
            errors.append(f"service entry incomplete: {svc}")
    return errors
```

For complex schemas, use **pydantic** or **jsonschema** (Day 21+). For Day 11, explicit checks keep dependencies minimal.

---

## 7. Working with Kubernetes-style multi-doc YAML

```python
docs = load_yaml_all(Path("manifests/app.yaml"))
for doc in docs:
  if doc.get("kind") == "Deployment":
      print(doc["metadata"]["name"], doc["spec"]["replicas"])
```

This pattern powers pre-deploy validators, label enforcers, and drift detectors.

---

## 8. Common pitfalls

| Pitfall | Fix |
|---------|-----|
| YAML `yes`/`no` become booleans | Quote them: `"yes"` |
| Empty YAML file returns `None` | Normalize: `safe_load(fh) or {}` |
| JSON trailing commas | Invalid — fix the file or use a linter in CI |
| TOML datetime vs string | tomllib parses RFC 3339 datetimes to `datetime` |
| Relative paths in config | Resolve with `(Path(__file__).parent / cfg["path"]).resolve()` |

---

## 9. Lab — Day 11

Work from `python/day11/labs/`.

1. Create a venv and `pip install pyyaml`.
2. Run `python config_loader.py --config sample/app.yaml` — prints merged effective config.
3. Introduce a syntax error in `sample/app.yaml`; confirm the script exits with a clear message.
4. Add `sample/overrides.toml` and run with `--override sample/overrides.toml` — verify deep merge.
5. Run `python config_loader.py --validate sample/invalid.json` — confirm validation errors list missing keys.
6. Parse `sample/k8s-multi.yaml` and print Deployment names and replica counts.

**Stretch:** Add `--format json|yaml|toml` output flag so the tool can re-emit config for piping into other tools.

---

## 10. DevOps connections

- **CI pipelines:** Jenkins/GitLab/GitHub Actions often emit JSON artifacts; your gate scripts consume them with `json.load`.
- **GitOps:** Validators run in CI against YAML before `kubectl apply` — same loading patterns as this lab.
- **12-factor apps:** Config in files for defaults; secrets stay out of all three formats (Day 13).

---

## Quick reference

| Task | Code |
|------|------|
| Load JSON | `json.load(open(path, encoding="utf-8"))` |
| Load YAML safely | `yaml.safe_load(fh)` |
| Load TOML | `tomllib.load(open(path, "rb"))` |
| Multi-doc YAML | `yaml.safe_load_all(fh)` |
| Deep merge | Recursive dict merge on nested keys |

**Next:** [Day 12 — HTTP health checks with requests & httpx](../day12/)

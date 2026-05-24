# Day 23 — Type Hints, Pydantic Validation & mypy

**Goal:** Model deployment configs, pipeline inputs, and API payloads with strict typing and runtime validation; enforce correctness with mypy in CI.

**Time:** 4–5 hours

**Prerequisites:** Day 22 (testing); basic dataclasses helpful but not required

---

## 1. Why types in DevOps Python?

Untyped dicts from YAML/JSON cause silent failures:

```python
config = yaml.safe_load(open("deploy.yaml"))
replicas = config["deployment"]["replics"]  # typo → KeyError in prod
```

Typed models catch errors at edit time (mypy) and load time (Pydantic):

| Approach | Catches typos | Runtime validation | JSON Schema export |
|----------|---------------|--------------------|--------------------|
| Raw dict | No | No | Manual |
| dataclass | Partial (mypy) | No | No |
| **Pydantic v2** | Yes | Yes | Built-in |

---

## 2. Gradual typing workflow

1. Add type hints to public functions
2. Run `mypy` locally and in CI
3. Introduce Pydantic models at config boundaries
4. Increase strictness over time

```bash
pip install pydantic mypy types-PyYAML
mypy python/day23/labs --strict
```

Start with `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
disallow_untyped_defs = true
```

---

## 3. Pydantic models for deploy config

See `labs/models.py`:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class ResourceLimits(BaseModel):
    cpu: str = Field(pattern=r"^\d+m?$")
    memory: str = Field(pattern=r"^\d+(Mi|Gi)$")

class DeploymentSpec(BaseModel):
    name: str = Field(min_length=1, max_length=63)
    replicas: int = Field(ge=1, le=100)
    image: str
    env: Literal["dev", "staging", "prod"]
    limits: ResourceLimits

    @field_validator("name")
    @classmethod
    def dns_safe_name(cls, v: str) -> str:
        if not v.replace("-", "").isalnum():
            raise ValueError("name must be DNS-safe")
        return v.lower()
```

Load from YAML:

```python
import yaml
from models import DeployConfig

raw = yaml.safe_load(path.read_text())
config = DeployConfig.model_validate(raw)
print(config.deployment.replicas)
```

---

## 4. Validation errors operators can read

Pydantic v2 errors are structured — format them for Slack:

```python
from pydantic import ValidationError

try:
    DeployConfig.model_validate(data)
except ValidationError as exc:
    for err in exc.errors():
        loc = ".".join(str(x) for x in err["loc"])
        print(f"{loc}: {err['msg']}")
```

In CI, fail fast with human-readable output before any deploy step runs.

---

## 5. Settings from environment

Use `pydantic-settings` for 12-factor ops tools:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPS_")

    api_token: str
    default_region: str = "us-east-1"
    dry_run: bool = False
```

```bash
export OPS_API_TOKEN=secret
export OPS_DRY_RUN=true
python validate_config.py deploy.yaml
```

Never commit secrets — validate presence, not values, in unit tests.

---

## 6. mypy strict patterns

```python
def scale_replicas(spec: DeploymentSpec, factor: float) -> DeploymentSpec:
    new_count = max(1, int(spec.replicas * factor))
    return spec.model_copy(update={"replicas": new_count})
```

Common fixes:

| mypy error | Fix |
|------------|-----|
| `Missing return statement` | Add explicit return or raise |
| `Item "None" has no attribute` | Narrow with `if x is not None` |
| `Incompatible types in assignment` | Use `TypedDict` or Pydantic |
| `Call to untyped function` | Add stubs or `# type: ignore[import-untyped]` sparingly |

Run on changed files in pre-commit:

```yaml
# .pre-commit-config.yaml snippet
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.11.0
  hooks:
    - id: mypy
      additional_dependencies: [pydantic, types-PyYAML]
```

---

## 7. JSON Schema for platform contracts

Export schema for other teams or policy engines (OPA, Kubernetes CRD generation):

```python
schema = DeployConfig.model_json_schema()
Path("schemas/deploy-config.json").write_text(json.dumps(schema, indent=2))
```

Platform engineering can publish this schema versioned alongside the deployment API.

---

## 8. Typed helpers vs. raw YAML

```python
def build_k8s_manifest(spec: DeploymentSpec) -> dict[str, object]:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": spec.name},
        "spec": {
            "replicas": spec.replicas,
            "template": {
                "spec": {
                    "containers": [{
                        "name": spec.name,
                        "image": spec.image,
                        "resources": {
                            "limits": {
                                "cpu": spec.limits.cpu,
                                "memory": spec.limits.memory,
                            }
                        },
                    }]
                }
            },
        },
    }
```

mypy ensures you don't reference nonexistent fields; tests verify manifest shape.

---

## 9. Lab — Day 23

Work from `python/day23/labs/`.

1. Install deps: `pip install pydantic pydantic-settings pyyaml mypy`.
2. Run `python validate_config.py deploy.valid.yaml` — should print validated config summary.
3. Run with `deploy.invalid.yaml` — observe field-level errors.
4. Run `mypy .` and fix any reported issues.
5. Add a new field `team: str` to `DeploymentSpec` with `min_length=2`; update sample YAMLs.
6. Export JSON schema: `python validate_config.py deploy.valid.yaml --schema > deploy.schema.json`.
7. **Stretch:** Add a `@model_validator` ensuring `replicas >= 2` when `env == "prod"`.

**Success criteria:** Valid config passes; invalid config exits non-zero with clear errors; mypy passes.

---

## 10. DevOps connections

- **Pipeline inputs:** GitHub Actions workflow_dispatch parameters map cleanly to Pydantic models.
- **Helm values:** Validate `values.yaml` in CI before `helm upgrade`.
- **Policy:** JSON Schema from Pydantic integrates with Conftest and other policy tools.

---

## Quick reference

| Task | Command |
|------|---------|
| Validate config | `python validate_config.py deploy.yaml` |
| Type check | `mypy . --strict` |
| Export schema | `python validate_config.py file.yaml --schema` |
| Parse env settings | `AppSettings()` after exporting vars |

**Next:** [Day 24 — Advanced CLIs with Click & Typer](../day24/)

# Day 22 — pytest: Testing Infrastructure Code

**Goal:** Write reliable tests for DevOps Python — Terraform helpers, API clients, deployment scripts — using pytest fixtures, mocks, and parametrization.

**Time:** 4–5 hours

**Prerequisites:** Basic Python; familiarity with CI test stages ([cicd](../../cicd/))

---

## 1. Why test infrastructure code?

Infrastructure scripts fail in production at 2 AM when:

- Cloud API responses change shape
- Retry logic doesn't handle throttling
- Parsing assumes a field that is now optional

| Untested script | Tested module |
|-----------------|---------------|
| `if status == "running"` breaks on new states | Parametrized tests document valid states |
| Manual curl to verify | Mocked HTTP tests run in CI without credentials |
| "Works on my laptop" | Fixtures reproduce prod-like data |

**DevOps rule:** If a script gates a deploy, it needs tests.

---

## 2. pytest layout for ops projects

```
python/day22/labs/
├── infra_helper.py      # code under test
├── conftest.py          # shared fixtures
├── tests/
│   └── test_infra_helper.py
└── pytest.ini
```

Run:

```bash
cd python/day22/labs
python3 -m venv .venv && source .venv/bin/activate
pip install pytest pytest-mock requests
pytest -v
```

---

## 3. Testing pure functions

`infra_helper.py` includes state normalization and tag parsing — ideal first tests:

```python
def test_normalize_instance_state_accepts_running():
    assert normalize_instance_state("running") == "ready"

def test_normalize_instance_state_unknown_raises():
    with pytest.raises(ValueError, match="unknown state"):
        normalize_instance_state("hibernated")
```

Use `@pytest.mark.parametrize` for cloud state matrices:

```python
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("pending", "provisioning"),
        ("running", "ready"),
        ("stopped", "stopped"),
        ("terminated", "gone"),
    ],
)
def test_normalize_instance_state(raw, expected):
    assert normalize_instance_state(raw) == expected
```

---

## 4. Fixtures for reusable test data

`conftest.py` provides factory fixtures — avoid copy-paste JSON blobs:

```python
@pytest.fixture
def sample_ec2_instance():
    return {
        "InstanceId": "i-0abc123",
        "State": {"Name": "running"},
        "Tags": [{"Key": "Environment", "Value": "staging"}],
    }

@pytest.fixture
def ec2_client(mocker, sample_ec2_instance):
    client = mocker.Mock()
    client.describe_instances.return_value = {
        "Reservations": [{"Instances": [sample_ec2_instance]}]
    }
    return client
```

Fixture scope:

| Scope | Use when |
|-------|----------|
| `function` (default) | Isolated unit tests |
| `module` | Expensive setup, read-only |
| `session` | DB containers, shared fake servers |

---

## 5. Mocking external services

Never call AWS/GCP/K8s APIs in unit tests. Mock at the boundary:

```python
def test_find_instances_by_tag(ec2_client, mocker):
    mocker.patch("infra_helper.boto3.client", return_value=ec2_client)
    result = find_instances_by_tag("Environment", "staging")
    assert len(result) == 1
    assert result[0]["InstanceId"] == "i-0abc123"
    ec2_client.describe_instances.assert_called_once()
```

For HTTP helpers, use `responses` or `pytest-httpx`:

```python
import responses

@responses.activate
def test_fetch_deploy_status():
    responses.add(
        responses.GET,
        "https://deploy.internal/api/v1/releases/42",
        json={"status": "succeeded", "version": "1.2.3"},
    )
    assert fetch_deploy_status(42)["version"] == "1.2.3"
```

---

## 6. Testing retries and timeouts

Use `freezegun` or mock `time.sleep` to avoid slow tests:

```python
def test_retry_on_throttling(mocker):
    client = mocker.Mock()
    client.describe_instances.side_effect = [
        ClientError({"Error": {"Code": "Throttling"}}, "DescribeInstances"),
        {"Reservations": []},
    ]
    mocker.patch("time.sleep")
    result = describe_with_retry(client, max_attempts=3)
    assert result == {"Reservations": []}
    assert client.describe_instances.call_count == 2
```

---

## 7. Temporary filesystem fixtures

Test Terraform output parsers and template renderers with `tmp_path`:

```python
def test_load_tf_outputs_json(tmp_path):
    outputs_file = tmp_path / "outputs.json"
    outputs_file.write_text('{"web_ip": {"value": "10.0.1.5"}}')
    assert load_tf_outputs(outputs_file)["web_ip"] == "10.0.1.5"
```

---

## 8. CI integration

```yaml
# .github/workflows/test-infra.yml (snippet)
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest pytest-mock requests
      - run: pytest python/day22/labs/tests -v --tb=short
```

Add coverage gates gradually:

```bash
pip install pytest-cov
pytest --cov=infra_helper --cov-report=term-missing --cov-fail-under=80
```

---

## 9. Test markers for slow/integration tests

```ini
# pytest.ini
[pytest]
markers =
    integration: hits real APIs (skipped in CI by default)
    slow: long-running checks
```

```python
@pytest.mark.integration
def test_live_ec2_describe():
    ...
```

```bash
pytest -m "not integration"   # default CI
pytest -m integration         # nightly with credentials
```

---

## 10. Lab — Day 22

Work from `python/day22/labs/`.

1. Create venv; install `pytest pytest-mock`.
2. Run `pytest -v` — all tests should pass.
3. Break `normalize_instance_state` intentionally; observe failing parametrized test.
4. Add a test for `parse_tags()` with duplicate keys (last wins).
5. Add a mock test for `find_instances_by_tag` when API returns empty reservations.
6. Add `@pytest.mark.parametrize` case for `shutting-down` → `gone`.
7. **Stretch:** Add `pytest-cov` and reach 90% coverage on `infra_helper.py`.

**Success criteria:** `pytest -v` passes; you can explain why boto3 is mocked, not called.

---

## 11. DevOps connections

- **Pre-deploy gates:** Run pytest on infra modules before `terraform apply` or Ansible playbooks in CI.
- **Contract tests:** When platform teams publish JSON schemas for deploy events, pytest validates your parsers.
- **Regression safety:** The same tests that guard refactors document expected cloud behavior for on-call engineers.

---

## Quick reference

| Task | Command |
|------|---------|
| Run all tests | `pytest -v` |
| Single file | `pytest tests/test_infra_helper.py -v` |
| Show prints | `pytest -s` |
| Match name | `pytest -k "normalize"` |
| Skip integration | `pytest -m "not integration"` |
| Coverage | `pytest --cov=infra_helper` |

**Next:** [Day 23 — Type hints, Pydantic & mypy](../day23/)

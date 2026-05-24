# Day 3 — Matrix Builds, Caching & Concurrency

**Goal:** Test across Python versions in parallel, cache dependencies, and optimize workflow cost and speed.

**Time:** 4–5 hours

---

## 1. Strategy matrix

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: requirements.txt
      - run: pip install -r requirements.txt && pytest -v
```

See [labs/ci-matrix.yml](./labs/ci-matrix.yml).

---

## 2. Caching

**Built-in (setup-python):**

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: pip
    cache-dependency-path: requirements.txt
```

**actions/cache** (generic):

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      pip-${{ runner.os }}-
```

**Cache key:** Include lockfile hash; bump key when cache poisoned.

---

## 3. fail-fast

`fail-fast: true` (default): first matrix failure cancels siblings. Use `false` for compatibility matrices where you want full signal.

---

## 4. Runner labels

```yaml
runs-on: ubuntu-latest   # GitHub-hosted
runs-on: macos-latest
runs-on: windows-latest
runs-on: [self-hosted, linux, gpu]  # Day 6
```

---

## 5. Timeouts

```yaml
jobs:
  test:
    timeout-minutes: 10
```

---

## 6. Lab — Day 3

1. Add matrix for Python 3.11 and 3.12.
2. Enable pip cache; compare run time before/after (second run should be faster).
3. Add `timeout-minutes: 5`; simulate hang and observe cancellation.

---

## Quick reference

| Feature | Key |
|---------|-----|
| Matrix | `strategy.matrix` |
| Pip cache | `cache: pip` in setup-python |
| Cancel dup PR runs | `concurrency` + `cancel-in-progress` |

**Prev:** [Day 2](../day2/) · **Next:** [Day 4 — Secrets & environments](../day4/)

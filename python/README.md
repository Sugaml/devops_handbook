# Python for DevOps — 10-Day Handbook

A hands-on path from your first `python3` script to operator-grade CLIs: collections, logs, exceptions, packaging, `argparse`, `subprocess`, and filesystem automation. Each day includes theory, examples, and runnable labs.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Setup, REPL, variables, types, f-strings | [day1](./day1/) |
| 2 | Control flow (if/for/while), truthiness, enumerate | [day2](./day2/) |
| 3 | Functions, docstrings, scope, *args/**kwargs | [day3](./day3/) |
| 4 | Lists, dicts, sets, comprehensions, parsing data | [day4](./day4/) |
| 5 | Strings, files, pathlib, reading logs | [day5](./day5/) |
| 6 | Exceptions, try/except/finally, logging | [day6](./day6/) |
| 7 | Modules, packages, venv, pip, pyproject.toml | [day7](./day7/) |
| 8 | argparse CLI design for ops scripts | [day8](./day8/) |
| 9 | subprocess — shell commands safely | [day9](./day9/) |
| 10 | os, sys, pathlib, permissions, glob | [day10](./day10/) |

## Prerequisites

- Comfort with a terminal ([Linux handbook](../linux/README.md) Days 1–3 recommended).
- Python **3.10+** on your laptop or lab VM.
- No prior Python required; basic scripting experience helps.

## How to use this handbook

1. Complete **Day 1** setup and verify `python3 --version`.
2. Work from `python/dayN/labs/`; run scripts with `python3 labs/script.py`.
3. Finish each day's **Lab** section before advancing.
4. Use a venv for Day 7+ (`python3 -m venv .venv`).

```bash
cd python/day1
python3 labs/hello_devops.py
```

## Conventions

| Convention | Value |
|------------|--------|
| Interpreter | `python3` |
| Style | `snake_case`, type hints where natural |
| Examples | Hosts, logs, deploys, configs |

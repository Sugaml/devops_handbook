#!/usr/bin/env python3
"""Load and merge JSON, YAML, or TOML configuration files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore

import yaml

LoadFn = Callable[[Path], dict[str, Any]]


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def load_yaml_all(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [doc for doc in yaml.safe_load_all(fh) if doc]


LOADERS: dict[str, LoadFn] = {
    ".json": load_json,
    ".yaml": load_yaml,
    ".yml": load_yaml,
    ".toml": load_toml,
}


def load_config(path: Path) -> dict[str, Any]:
    loader = LOADERS.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported extension: {path.suffix}")
    try:
        return loader(path)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path} line {exc.lineno}: {exc.msg}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def validate_app_config(cfg: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("environment", "services"):
        if key not in cfg:
            errors.append(f"missing required key: {key}")
    for svc in cfg.get("services", []):
        if not isinstance(svc, dict):
            errors.append(f"service entry must be a dict: {svc!r}")
            continue
        if "name" not in svc or "port" not in svc:
            errors.append(f"service entry incomplete: {svc}")
    return errors


def parse_k8s_deployments(path: Path) -> list[tuple[str, int]]:
    deployments: list[tuple[str, int]] = []
    for doc in load_yaml_all(path):
        if doc.get("kind") != "Deployment":
            continue
        name = doc["metadata"]["name"]
        replicas = doc.get("spec", {}).get("replicas", 1)
        deployments.append((name, replicas))
    return deployments


def main() -> int:
    parser = argparse.ArgumentParser(description="DevOps config loader lab")
    parser.add_argument("--config", type=Path, required=True, help="Primary config file")
    parser.add_argument("--override", type=Path, help="Optional override file")
    parser.add_argument("--validate", action="store_true", help="Run schema checks")
    parser.add_argument("--k8s", type=Path, help="Parse multi-doc YAML for Deployments")
    args = parser.parse_args()

    if args.k8s:
        for name, replicas in parse_k8s_deployments(args.k8s):
            print(f"{name}: {replicas} replicas")
        return 0

    try:
        cfg = load_config(args.config)
        if args.override:
            cfg = deep_merge(cfg, load_config(args.override))
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.validate:
        errors = validate_app_config(cfg)
        if errors:
            for err in errors:
                print(f"VALIDATION: {err}", file=sys.stderr)
            return 1
        print("Validation passed.")

    print(json.dumps(cfg, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

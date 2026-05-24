#!/usr/bin/env python3
"""Validate deployment YAML against Pydantic models."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from models import DeployConfig


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def validate(path: Path) -> DeployConfig:
    return DeployConfig.model_validate(load_yaml(path))


def print_summary(config: DeployConfig) -> None:
    spec = config.deployment
    print(f"OK: {spec.name} env={spec.env} replicas={spec.replicas} image={spec.image}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate deploy YAML")
    parser.add_argument("config", type=Path)
    parser.add_argument("--schema", action="store_true", help="Print JSON schema and exit")
    args = parser.parse_args()

    if args.schema:
        print(json.dumps(DeployConfig.model_json_schema(), indent=2))
        return

    try:
        config = validate(args.config)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"])
            print(f"ERROR {loc}: {err['msg']}", file=sys.stderr)
        sys.exit(1)

    print_summary(config)


if __name__ == "__main__":
    main()

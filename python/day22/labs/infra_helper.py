"""Helpers for cloud inventory and deploy status — code under test."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import json
import requests


def normalize_instance_state(raw: str) -> str:
    """Map cloud provider instance states to internal lifecycle labels."""
    mapping = {
        "pending": "provisioning",
        "running": "ready",
        "stopped": "stopped",
        "stopping": "stopped",
        "shutting-down": "gone",
        "terminated": "gone",
    }
    try:
        return mapping[raw]
    except KeyError as exc:
        raise ValueError(f"unknown state: {raw}") from exc


def parse_tags(tags: list[dict[str, str]]) -> dict[str, str]:
    """Convert AWS-style tag list to dict; later tags override earlier keys."""
    result: dict[str, str] = {}
    for tag in tags:
        result[tag["Key"]] = tag["Value"]
    return result


def load_tf_outputs(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    return {key: value["value"] for key, value in data.items()}


def find_instances_by_tag(key: str, value: str) -> list[dict[str, Any]]:
    import boto3

    client = boto3.client("ec2")
    resp = client.describe_instances(
        Filters=[{"Name": f"tag:{key}", "Values": [value]}]
    )
    instances: list[dict[str, Any]] = []
    for reservation in resp.get("Reservations", []):
        instances.extend(reservation.get("Instances", []))
    return instances


def fetch_deploy_status(release_id: int, base_url: str = "https://deploy.internal/api/v1") -> dict[str, Any]:
    resp = requests.get(f"{base_url}/releases/{release_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def describe_with_retry(client, max_attempts: int = 3) -> dict[str, Any]:
    """Retry describe_instances on throttling."""
    import time

    from botocore.exceptions import ClientError

    for attempt in range(max_attempts):
        try:
            return client.describe_instances()
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code != "Throttling" or attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)
    return {"Reservations": []}

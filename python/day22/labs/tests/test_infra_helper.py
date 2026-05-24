"""Tests for infra_helper module."""
from __future__ import annotations

from pathlib import Path

import pytest
import responses

from infra_helper import (
    describe_with_retry,
    fetch_deploy_status,
    find_instances_by_tag,
    load_tf_outputs,
    normalize_instance_state,
    parse_tags,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("pending", "provisioning"),
        ("running", "ready"),
        ("stopped", "stopped"),
        ("shutting-down", "gone"),
        ("terminated", "gone"),
    ],
)
def test_normalize_instance_state(raw, expected):
    assert normalize_instance_state(raw) == expected


def test_normalize_instance_state_unknown_raises():
    with pytest.raises(ValueError, match="unknown state"):
        normalize_instance_state("hibernated")


def test_parse_tags():
    tags = [
        {"Key": "Environment", "Value": "prod"},
        {"Key": "Name", "Value": "web-1"},
    ]
    assert parse_tags(tags) == {"Environment": "prod", "Name": "web-1"}


def test_parse_tags_duplicate_key_last_wins():
    tags = [
        {"Key": "Environment", "Value": "staging"},
        {"Key": "Environment", "Value": "prod"},
    ]
    assert parse_tags(tags)["Environment"] == "prod"


def test_load_tf_outputs_json(tmp_path: Path):
    outputs_file = tmp_path / "outputs.json"
    outputs_file.write_text('{"web_ip": {"value": "10.0.1.5"}}')
    assert load_tf_outputs(outputs_file)["web_ip"] == "10.0.1.5"


def test_find_instances_by_tag(ec2_client, mocker):
    mocker.patch("infra_helper.boto3.client", return_value=ec2_client)
    result = find_instances_by_tag("Environment", "staging")
    assert len(result) == 1
    assert result[0]["InstanceId"] == "i-0abc123"
    ec2_client.describe_instances.assert_called_once()


def test_find_instances_by_tag_empty(mocker):
    client = mocker.Mock()
    client.describe_instances.return_value = {"Reservations": []}
    mocker.patch("infra_helper.boto3.client", return_value=client)
    assert find_instances_by_tag("Environment", "missing") == []


@responses.activate
def test_fetch_deploy_status():
    responses.add(
        responses.GET,
        "https://deploy.internal/api/v1/releases/42",
        json={"status": "succeeded", "version": "1.2.3"},
    )
    data = fetch_deploy_status(42)
    assert data["version"] == "1.2.3"


def test_retry_on_throttling(mocker):
    from botocore.exceptions import ClientError

    client = mocker.Mock()
    client.describe_instances.side_effect = [
        ClientError({"Error": {"Code": "Throttling"}}, "DescribeInstances"),
        {"Reservations": []},
    ]
    mocker.patch("time.sleep")
    result = describe_with_retry(client, max_attempts=3)
    assert result == {"Reservations": []}
    assert client.describe_instances.call_count == 2

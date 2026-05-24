"""Shared pytest fixtures for Day 22 labs."""
from __future__ import annotations

import pytest


@pytest.fixture
def sample_ec2_instance() -> dict:
    return {
        "InstanceId": "i-0abc123",
        "State": {"Name": "running"},
        "Tags": [
            {"Key": "Environment", "Value": "staging"},
            {"Key": "Name", "Value": "web-staging-1"},
        ],
    }


@pytest.fixture
def ec2_client(mocker, sample_ec2_instance):
    client = mocker.Mock()
    client.describe_instances.return_value = {
        "Reservations": [{"Instances": [sample_ec2_instance]}]
    }
    return client

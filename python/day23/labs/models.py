"""Pydantic models for deployment configuration validation."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ResourceLimits(BaseModel):
    cpu: str = Field(pattern=r"^\d+m?$")
    memory: str = Field(pattern=r"^\d+(Mi|Gi)$")


class DeploymentSpec(BaseModel):
    name: str = Field(min_length=1, max_length=63)
    replicas: int = Field(ge=1, le=100)
    image: str
    env: Literal["dev", "staging", "prod"]
    team: str = Field(min_length=2)
    limits: ResourceLimits

    @field_validator("name")
    @classmethod
    def dns_safe_name(cls, value: str) -> str:
        if not value.replace("-", "").isalnum():
            raise ValueError("name must be DNS-safe (alphanumeric and hyphens)")
        return value.lower()

    @model_validator(mode="after")
    def prod_ha_replicas(self) -> DeploymentSpec:
        if self.env == "prod" and self.replicas < 2:
            raise ValueError("prod deployments require at least 2 replicas")
        return self


class DeployConfig(BaseModel):
    deployment: DeploymentSpec

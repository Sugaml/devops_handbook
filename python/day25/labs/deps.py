"""FastAPI dependencies."""
from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def get_api_token() -> str:
    return os.environ.get("OPS_API_TOKEN", "handbook-lab")


async def verify_token(
    creds: HTTPAuthorizationCredentials | None = Security(security),
) -> str:
    expected = get_api_token()
    if creds is None or creds.credentials != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return creds.credentials

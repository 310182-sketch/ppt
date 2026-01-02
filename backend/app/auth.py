from fastapi import Header, HTTPException
from typing import Optional


def api_key_auth(x_api_key: Optional[str] = Header(None)):
    # Simple API key check for MVP. In production use proper JWT / OAuth.
    expected = "${API_KEY}"
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

from fastapi import APIRouter, HTTPException, Request, Depends, Response
import httpx
from urllib.parse import urlparse
import os
from typing import Optional

router = APIRouter()

ALLOWED_HOSTS = os.environ.get("PROXY_ALLOWED_HOSTS", "content-management-public-content.canva.com").split(',')


async def verify_api_key(request: Request):
    # Simple API key check: look for X-API-Key header or env-disabled
    expected = os.environ.get('BACKEND_API_KEY')
    if not expected:
        return True
    key = request.headers.get('X-API-Key')
    if not key or key != expected:
        raise HTTPException(status_code=401, detail='Unauthorized')
    return True


@router.post('/proxy/fetch')
async def proxy_fetch(payload: dict, ok=Depends(verify_api_key)):
    url = payload.get('url')
    if not url:
        raise HTTPException(status_code=400, detail='missing url')
    parsed = urlparse(url)
    host = parsed.hostname
    if not host or host not in ALLOWED_HOSTS:
        raise HTTPException(status_code=403, detail='host not allowed')

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100 Safari/537.36',
        'Referer': 'https://www.canva.com'
    }

    # Authorization passthrough: prefer explicit env token, fallback to stored OAuth tokens
    canva_token = os.environ.get('CANVA_ACCESS_TOKEN')
    if not canva_token:
        # try to read saved tokens from canva_oauth (local dev storage)
        try:
            from backend.app import canva_oauth
            tokens = canva_oauth._load_tokens()
            user_id = os.environ.get('CANVA_USER_ID', 'default')
            entry = tokens.get(user_id)
            if entry and isinstance(entry, dict):
                canva_token = entry.get('access_token') or entry.get('token')
        except Exception:
            canva_token = None

    if canva_token:
        headers['Authorization'] = f'Bearer {canva_token}'

    timeout = float(os.environ.get('PROXY_TIMEOUT', '10.0'))
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=str(e))

    content_type = resp.headers.get('content-type', 'application/octet-stream')
    return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)

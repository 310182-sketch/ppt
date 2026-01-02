import os
import json
from typing import Optional

import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse

router = APIRouter()

CANVA_CLIENT_ID = os.getenv('CANVA_CLIENT_ID', '')
CANVA_CLIENT_SECRET = os.getenv('CANVA_CLIENT_SECRET', '')
CANVA_AUTHORIZE_URL = os.getenv('CANVA_AUTHORIZE_URL', 'https://www.canva.com/auth')
CANVA_TOKEN_URL = os.getenv('CANVA_TOKEN_URL', 'https://api.canva.com/oauth2/token')
REDIRECT_URI = os.getenv('CANVA_REDIRECT_URI', 'http://127.0.0.1:8000/api/canva/oauth/callback')

TOKENS_FILE = os.path.join(os.path.dirname(__file__), 'canva_tokens.json')


def _load_tokens():
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save_tokens(d):
    with open(TOKENS_FILE, 'w') as f:
        json.dump(d, f)


@router.get('/api/canva/oauth/start')
def oauth_start(user_id: Optional[str] = 'default'):
    if not CANVA_CLIENT_ID:
        raise HTTPException(status_code=500, detail='CANVA_CLIENT_ID not set')
    # state can include user_id for mapping
    state = user_id
    params = {
        'client_id': CANVA_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'public',
        'state': state,
    }
    # build authorize url
    from urllib.parse import urlencode
    url = f"https://www.canva.com/oauth2/authorize?{urlencode(params)}"
    return RedirectResponse(url)


@router.get('/api/canva/oauth/callback')
async def oauth_callback(request: Request):
    code = request.query_params.get('code')
    state = request.query_params.get('state') or 'default'
    if not code:
        return HTMLResponse('<h3>Missing code</h3>', status_code=400)
    # exchange code for token
    async with httpx.AsyncClient() as client:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CANVA_CLIENT_ID,
            'client_secret': CANVA_CLIENT_SECRET,
        }
        resp = await client.post(CANVA_TOKEN_URL, data=data, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    token_data = resp.json()
    tokens = _load_tokens()
    tokens[state] = token_data
    _save_tokens(tokens)
    html = "<html><body><h3>Canva connected — you can close this tab.</h3></body></html>"
    return HTMLResponse(content=html)


@router.get('/api/canva/token/{user_id}')
def get_token(user_id: str):
    tokens = _load_tokens()
    t = tokens.get(user_id)
    if not t:
        raise HTTPException(status_code=404, detail='token not found')
    return t

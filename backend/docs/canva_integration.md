## Canva Apps / OAuth Integration（指南）

目的：透過官方 Canva Apps/API 取得受保護資源（如設計模板 JSON、圖像資產），並讓後端能代表使用者安全存取。

注意事項：推薦走官方流程（合規、安全、穩定）。以下為一般 OAuth2 與 proxy 的實作範例與部署建議。

1) 申請 Canva 應用
- 到 Canva 開發者入口申請應用（尋找 "Canva Apps" 或 "Developers"），填入應用名稱、說明與 Redirect URI（例如 `https://your-backend.example.com/api/canva/oauth/callback`）。
- 取得 `CLIENT_ID` 與 `CLIENT_SECRET`。

2) OAuth 流程（後端範例）
- 使用者在 extension 設定頁或 popup 點「連結 Canva 帳號」，導向後端 `/api/canva/oauth/start`，後端 redirect 到 Canva 的授權頁（帶 `client_id`、`redirect_uri`、`response_type=code`、`scope`、`state`）。
- Canva 會在授權完成後 redirect 回 `/api/canva/oauth/callback?code=...&state=...`。
- 後端用 `code` 向 Canva 的 token endpoint 交換 `access_token`（同時儲存在安全的地方，例如 GCP Secret Manager、Cloud Run Secret 或資料庫），並對 client（extension）回報成功。

3) 後端 proxy 使用已儲存的 token
- 當 proxy 要取用 Canva 受保護資源時（例如 `content-management-public-content.canva.com/.../root.json`），後端應：
  - 從安全儲存讀出該使用者的 `access_token`。
  - 在向 Canva 的請求加入 `Authorization: Bearer <token>` header。
  - 若資源仍被拒絕，可能是該資源需要特定的 scope 或帳號權限（確認 scope 與授權帳號）。

4) FastAPI 範例（片段）
```py
# backend/app/canva_client.py  (範例片段，不會自動啟用)
import os
import httpx
from typing import Optional

CANVA_TOKEN_URL = os.getenv('CANVA_TOKEN_URL', 'https://api.canva.com/oauth2/token')
CANVA_CLIENT_ID = os.getenv('CANVA_CLIENT_ID')
CANVA_CLIENT_SECRET = os.getenv('CANVA_CLIENT_SECRET')

async def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    async with httpx.AsyncClient() as client:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': CANVA_CLIENT_ID,
            'client_secret': CANVA_CLIENT_SECRET,
        }
        resp = await client.post(CANVA_TOKEN_URL, data=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

async def fetch_canva_resource(url: str, access_token: Optional[str]):
    headers = {}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp
```

5) Proxy 範例：在你的 `proxy` 路由中，當檢測到目標 host 屬於 Canva 時，嘗試使用 `access_token`：

```py
from fastapi import APIRouter, HTTPException, Response
import httpx
from backend.app.canva_client import fetch_canva_resource

router = APIRouter()

def get_user_canva_token(user_id: str):
    # TODO: 從 DB 或 Secret Manager 取得 token；這裡示範從 env 讀取測試 token
    import os
    return os.getenv('CANVA_ACCESS_TOKEN')

@router.post('/fetch')
async def proxy_fetch(payload: dict, user_id: str = 'default'):
    url = payload.get('url')
    access_token = get_user_canva_token(user_id)
    try:
        resp = await fetch_canva_resource(url, access_token)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    return Response(content=resp.content, media_type=resp.headers.get('content-type'))
```

6) 權限與 scope
- 設定必要 scope（例如讀取模板、資產的權限），並在第一次授權時請求。若收到 `403`，請檢查該資源是否為「公開資源」或需要額外權限（或只供特定 Canva 帳號存取）。

7) 本地測試與短期替代方案
- 若不想立刻完成 OAuth，可以先使用一組短期 `CANVA_ACCESS_TOKEN` 環境變數（手動從 Canva 取得）測試 proxy 能否成功取回資源。
- 另一短期方法是採用「page-context fetch」：在 `content_script` 以使用者瀏覽器身分直接 fetch 該 URL（需處理 CORS 與安全性，且不適合後端自動化）。

8) 部署與安全建議
- 永遠不要把 `CLIENT_SECRET` 或 `ACCESS_TOKEN` 寫死在 repo。使用雲端 Secret Manager（GCP Secret Manager / AWS Secrets Manager）或 Cloud Run secret env。
- 建議在 token 取得後，儲存 token 與 refresh token，並實作自動續期（refresh flow）。

9) 後續我可以幫你做的項目
- 在 `backend` 實作 OAuth endpoints `/api/canva/oauth/start` 與 `/api/canva/oauth/callback`。
- 在 `proxy` 中加入 token passthrough，並示範如何從簡單 DB/Secret 讀取 token。
- 實作 refresh token 與自動續期。

如果要我立刻實作 OAuth endpoints 或把 proxy 改為嘗試使用 `CANVA_ACCESS_TOKEN` 測試，請告訴我：要我先（1）實作 OAuth endpoints，或（2）先把 proxy 加上 env-token passthrough 以便快速驗證？

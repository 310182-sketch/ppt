# AI PPT — Canva Extension + Backend (MVP)

簡介
---
這個專案示範如何把 AI 生成的簡報大綱、圖片與最終 PPT 結合到 Canva 的工作流程。採用架構：

- 前端：Chrome 擴充（針對 Canva 注入 UI）
- 後端：FastAPI（負責串接 AI、產生 PPTX、存放 artifact）

目前狀態
---
專案包含：後端範本（`backend/`），以及針對 Canva 的 Chrome 擴充骨架（`extension/`）。後端使用開發 stub 生成圖片與 PPT，實際 AI 串接（Replicate 或本地模型）尚未整合。

主要功能（MVP）
---
- 在 Canva 頁面注入浮動按鈕以觸發：生成大綱、生成圖片、請後端生成 PPT。
- 後端提供非同步 job 與本地 storage 模擬（開發用）。
- 擴充會嘗試自動把生成圖片上傳回 Canva（best-effort），或提供下載連結讓使用者手動上傳。

快速啟動（開發）
---
1. 建立並啟用 Python 虛擬環境，安裝後端相依：

```bash
cd /workspaces/ppt
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
```

2. 啟動後端：

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

3. 測試 API（smoke test）：

```bash
curl -s -X POST http://127.0.0.1:8000/api/generate-outline \
  -H "Content-Type: application/json" \
  -d '{"title":"測試簡報","audience":"開發者","length":3,"style":"tech"}'
```

4. 載入 Chrome 擴充（開發模式）：

- 開啟 Chrome → `chrome://extensions` → 打開 Developer mode。
- 點「Load unpacked」並選擇 repo 的 `extension/` 資料夾。
- 點開擴充的 Options，將 `Backend URL` 設為 `http://localhost:8000`。
- 開啟 https://www.canva.com/，點右下浮動的 `AI PPT` 按鈕並嘗試生成大綱或圖片。

開發說明與後續工作
---
- 若要整合真實模型：在 `backend/app/image_service.py`、`backend/app/design_engine.py` 中替換 stub 為呼叫 Replicate 或本地推理端點。
- 若要將 artifact 存到雲端：在 `backend/app/storage.py` 中整合 GCS 或 S3，並回傳 signed URLs。
- 若要更穩定地將內容放入 Canva：建議申請並使用 Canva Apps 平台（官方整合）而非 DOM 注入。

安全與隱私
---
- 不要將第三方 API key 打包到擴充；所有金鑰請放到後端並使用 Secret Manager。
- 請在上架 Chrome Web Store 前撰寫並公開隱私政策（`extension/PRIVACY.md` 已提供草案）。

下一步（選項）
---
- 我可以：
  - 在後端加入 Replicate 範例整合；
  - 提供 Docker Compose 一鍵啟動範本；
  - 或產生前端 Next.js demo 按鈕以展示 workflow。
# ppt
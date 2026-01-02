# Release v1.0 — AI PPT (Canva extension + Backend)

這是 v1.0 釋出，包含初始 MVP：FastAPI 後端範本、mock server、以及針對 Canva 的 Chrome 擴充骨架。

主要內容
---
- `backend/`：FastAPI 範本與本地 storage stub、`mock_server.py`（本地測試用）。
- `extension/`：Chrome 擴充檔案（`manifest.json`、`content_script.js`、`service_worker.js`、`options.html`、`popup.html` 等）。
- Release 附件：`releases/ppt-extension-v1.0.zip`（可直接上傳到 Chrome Web Store 或用作 Developer Mode 安裝）。

快速安裝（開發 / 本地測試）
---
1. 下載 Release 附件或直接在 repo 中找到 `releases/ppt-extension-v1.0.zip`。

2. 安裝並啟動後端（或使用 mock server）：

```bash
# 建議使用 venv
cd /workspaces/ppt
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# 啟動 mock server（本地開發，預設監聽 9000）
./scripts/run_mock.sh

# 或啟動主後端（若要執行範本 API）
cd backend
uvicorn app.main:app --reload --port 8000
```

3. 在 Chrome 載入擴充（Developer Mode）

- 開啟 `chrome://extensions` → 開啟 Developer mode → 點「Load unpacked」→ 選擇本 repo 下的 `extension/` 資料夾。
- 或解壓 `ppt-extension-v1.0.zip` 並載入解壓後的資料夾。
- 在擴充的 Options 中設定 `Backend URL`（預設為 `http://localhost:9000` 指向 mock server，若啟用 main backend 則填 `http://localhost:8000`）。

4. 使用方法

- 開啟 https://www.canva.com/，進入任一設計頁面。
- 點右下角的 `AI PPT` 浮動按鈕 → 輸入標題/參數 → 點選「開始」生成大綱或圖片。
- 生成為非同步 job，完成後會在面板顯示結果，並嘗試將圖片自動上傳到 Canva（若無法自動上傳會提供下載連結）。

注意與建議
---
- 本版本為 MVP：後端的 AI 呼叫為 stub，請在 `backend/app/image_service.py` 與 `backend/app/design_engine.py` 整合 Replicate 或其他推理端點，以使用真實模型。
- 若要在生產使用，請把 storage 改為 GCS/S3 並產生真正的 signed URL（實作 `backend/app/storage.py`）。
- 若要更穩定地將生成物放回 Canva，請考慮申請並使用 Canva Apps 平台（官方提供的整合方式），比 DOM 注入更可靠。

聯絡與回報問題
---
如有問題或需要我協助將 Replicate 整合、建立 Docker Compose，或上傳 CRX/Chrome Web Store 發布流程，請在 Issue 中標註或直接回覆此訊息。

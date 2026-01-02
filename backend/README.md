# PPT Backend (MVP)

這是開發階段的 FastAPI 後端範本，包含最小 API 路由（大綱、圖片、PPT 生成）與本地 storage 模擬。

快速啟動（開發）

1. 建議在虛擬環境中安裝依賴：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 啟動 dev server：

```bash
uvicorn app.main:app --reload --port 8000
```

環境變數

- `BACKEND_STORAGE_PATH`：指定本地暫存/儲存路徑，預設 `./storage`。

注意

- 目前的 image/ppt 生成為開發 stub，實際 AI 推理請整合 Replicate 或自建模型推理端。
- storage 使用本地檔案系統作為示例，生產環境請整合 GCS 或 S3 並產生真正的 signed URLs。

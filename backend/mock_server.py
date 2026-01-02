"""
Simple mock server to simulate job processing and WebSocket job updates.
Use this during local development when real AI/model endpoints are not available.
"""
import asyncio
import json
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from uuid import uuid4
from typing import Dict, Any, List

app = FastAPI(title="ppt-mock-server")

# In-memory job store
JOBS: Dict[str, Dict[str, Any]] = {}

# Active websocket connections
WS_CONNECTIONS: List[WebSocket] = []


async def broadcast(msg: Dict[str, Any]):
    data = json.dumps(msg)
    to_remove = []
    for ws in WS_CONNECTIONS:
        try:
            await ws.send_text(data)
        except Exception:
            to_remove.append(ws)
    for ws in to_remove:
        try:
            WS_CONNECTIONS.remove(ws)
        except ValueError:
            pass


def enqueue_job(job_type: str, payload: Dict[str, Any]) -> str:
    job_id = str(uuid4())
    JOBS[job_id] = {"status": "queued", "type": job_type, "payload": payload}
    return job_id


async def process_job(job_id: str):
    # Simulate variable processing time
    JOBS[job_id]["status"] = "running"
    await broadcast({"type": "job-update", "job_id": job_id, "status": "running"})
    await asyncio.sleep(2)
    job = JOBS.get(job_id, {})
    typ = job.get("type")
    if typ == "outline":
        slides = []
        length = job.get("payload", {}).get("length", 3)
        title = job.get("payload", {}).get("title", "示例")
        for i in range(1, length + 1):
            slides.append({"title": f"{title} - 第 {i} 頁", "bullets": ["示例要點 1", "示例要點 2"]})
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["result"] = {"slides": slides}
    elif typ == "image":
        # create a fake URL (file path style) - extension expects file:// for dev
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["image_url"] = f"file:///tmp/mock_images/{job_id}.png"
        JOBS[job_id]["result"] = {"image_url": JOBS[job_id]["image_url"]}
    elif typ == "ppt":
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["ppt_url"] = f"file:///tmp/mock_ppts/{job_id}.pptx"
        JOBS[job_id]["result"] = {"ppt_url": JOBS[job_id]["ppt_url"]}
    else:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = "unknown job type"

    await broadcast({"type": "job-update", "job_id": job_id, "status": JOBS[job_id]["status"], "result": JOBS[job_id].get("result")})


@app.post("/api/generate-outline")
async def generate_outline(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    job_id = enqueue_job("outline", payload)
    background_tasks.add_task(process_job, job_id)
    return {"job_id": job_id, "status": "queued"}


@app.post("/api/generate-image")
async def generate_image(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    job_id = enqueue_job("image", payload)
    background_tasks.add_task(process_job, job_id)
    return {"job_id": job_id, "status": "queued"}


@app.post("/api/generate-ppt")
async def generate_ppt(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    job_id = enqueue_job("ppt", payload)
    background_tasks.add_task(process_job, job_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/job-status/{job_id}")
async def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return {"job_id": job_id, "status": "not_found"}
    return {"job_id": job_id, "status": job.get("status"), "result": job.get("result")}


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    WS_CONNECTIONS.append(websocket)
    try:
        while True:
            # keep alive / receive pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        try:
            WS_CONNECTIONS.remove(websocket)
        except ValueError:
            pass

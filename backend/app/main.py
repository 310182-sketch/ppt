from fastapi import FastAPI, BackgroundTasks, HTTPException
from uuid import uuid4
from .schemas import OutlineRequest, ImageRequest, PptRequest
from .design_engine import generate_outline_sync
from .image_service import generate_image_sync
from .ppt_generator import generate_ppt_sync
from .storage import upload_local_file, make_signed_url
from .proxy import router as proxy_router
from .canva_oauth import router as canva_router

app = FastAPI(title="ppt-backend")

# include proxy router
app.include_router(proxy_router, prefix="/api")
# include canva oauth router
app.include_router(canva_router)

# In-memory job store for MVP (replace with DB in production)
JOBS = {}


@app.post("/api/generate-outline")
async def generate_outline(req: OutlineRequest):
    outline = generate_outline_sync(req.title, req.audience, req.length, req.style)
    return {"outline_id": str(uuid4()), "slides": outline}


@app.post("/api/generate-image")
async def generate_image(req: ImageRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    JOBS[job_id] = {"status": "queued"}

    def _work(job_id, prompt, size, style):
        # synchronous helper: in real deployment this should call Replicate or local inference
        img_path = generate_image_sync(prompt, size, style)
        # upload to storage (local for dev)
        dest = upload_local_file(img_path, job_id)
        JOBS[job_id] = {"status": "done", "image_url": make_signed_url(dest)}

    background_tasks.add_task(_work, job_id, req.prompt, req.size, req.style)
    return {"job_id": job_id, "status": "queued"}


@app.post("/api/generate-ppt")
async def generate_ppt(req: PptRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    JOBS[job_id] = {"status": "queued"}

    def _work_ppt(job_id, outline_id, images, template, options):
        ppt_path = generate_ppt_sync(outline_id, images, template, options)
        dest = upload_local_file(ppt_path, job_id, filename="presentation.pptx")
        JOBS[job_id] = {"status": "done", "ppt_url": make_signed_url(dest)}

    background_tasks.add_task(_work_ppt, job_id, req.outline_id, req.images, req.template, req.options)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/job-status/{job_id}")
async def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {"job_id": job_id, **job}


@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    # return signed url if available
    if "ppt_url" in job:
        return {"download_url": job["ppt_url"]}
    if "image_url" in job:
        return {"download_url": job["image_url"]}
    raise HTTPException(status_code=400, detail="no artifact for this job")

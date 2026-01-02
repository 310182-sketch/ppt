from pydantic import BaseModel
from typing import List, Optional, Any


class OutlineRequest(BaseModel):
    title: str
    audience: Optional[str] = None
    length: Optional[int] = 5
    style: Optional[str] = "default"


class ImageRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    style: Optional[str] = "photorealistic"


class ImageRef(BaseModel):
    slide: int
    image_job: str


class PptRequest(BaseModel):
    outline_id: str
    images: Optional[List[ImageRef]] = []
    template: Optional[str] = "default"
    options: Optional[Any] = {}

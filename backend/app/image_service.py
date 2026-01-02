import os
from PIL import Image, ImageDraw, ImageFont


def generate_image_sync(prompt: str, size: str = "1024x1024", style: str = "photorealistic") -> str:
    """
    DEV stub: generate a placeholder image and return local path.
    Replace with Replicate or local model inference call.
    """
    width, height = map(int, size.split("x")) if "x" in size else (1024, 1024)
    img = Image.new("RGB", (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    text = prompt[:80]
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((10, 10), text, fill=(20, 20, 20), font=font)
    out_dir = os.environ.get("BACKEND_STORAGE_PATH", "/workspaces/ppt/backend/storage")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"img_{abs(hash(prompt)) % 100000}.png")
    img.save(out_path)
    return out_path

def generate_outline_sync(title: str, audience: str, length: int, style: str):
    # Placeholder synchronous outline generator.
    # Integrate with Replicate / local LLM in production.
    slides = []
    for i in range(1, max(1, length) + 1):
        slides.append({
            "title": f"{title} - 第 {i} 頁",
            "bullets": [f"重點 {j}" for j in range(1, 4)],
        })
    return slides

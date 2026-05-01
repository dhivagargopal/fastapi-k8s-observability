from fastapi import FastAPI, Request, HTTPException
from starlette_exporter import PrometheusMiddleware, handle_metrics
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    PrometheusMiddleware,
    app_name="fastapi_app",
    group_paths=True
)
app.add_route("/metrics", handle_metrics)


@app.get("/")
def read_root():
    return {"message": "FastAPI local LLM demo is running"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "llm_mode": "local-free",
    }

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}


def generate_local_text(prompt: str) -> str:
    clean_prompt = " ".join(prompt.split())
    endings = [
        "and the next step is to make the idea smaller, clearer, and easier to test.",
        "with a practical plan, simple monitoring, and a result that can be improved over time.",
        "by focusing on the main goal first and avoiding unnecessary external services.",
        "so the application stays lightweight, predictable, and free to run locally.",
    ]
    selected = endings[sum(ord(char) for char in clean_prompt) % len(endings)]
    return f"{clean_prompt} {selected}"


@app.post("/generate")
async def generate_text(request: Request):
    payload = await request.json()
    input_text = payload.get("text", "")

    if not input_text:
        raise HTTPException(status_code=400, detail="Field 'text' is required")

    start_time = time.time()
    generated_text = generate_local_text(input_text)
    elapsed = time.time() - start_time

    logger.info(f"Generated text in {elapsed:.2f} seconds")
    return {"generated_text": generated_text, "time_taken": elapsed}

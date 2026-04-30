from fastapi import FastAPI, Request, HTTPException
from starlette_exporter import PrometheusMiddleware, handle_metrics
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
import asyncio
from functools import partial

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    PrometheusMiddleware,
    app_name="fastapi_app",
    group_paths=True
)
app.add_route("/metrics", handle_metrics)

# Global variables for models
model = None
quantized_model = None
tokenizer = None

def load_models():
    global model, quantized_model, tokenizer
    if model is None:
        logger.info("Loading models...")
        try:
            model = AutoModelForCausalLM.from_pretrained("distilgpt2")
            quantized_model = AutoModelForCausalLM.from_pretrained("distilgpt2", torch_dtype=torch.float16)
            tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
            logger.info("Models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            raise

load_models()

@app.get("/")
def read_root():
    return {"message": "Hello, Kubernetes with Monitoring!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None, "quantized_model_loaded": quantized_model is not None}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}

async def generate_with_timeout(model, input_ids, max_length, num_return_sequences):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(model.generate, input_ids, max_length=max_length, num_return_sequences=num_return_sequences)
    )

@app.post("/generate")
async def generate_text(request: Request):
    try:
        load_models()  # Ensure models are loaded
        if model is None or tokenizer is None:
            raise HTTPException(status_code=503, detail="Models not initialized")
        
        data = await request.json()
        input_text = data.get("text", "")
        
        input_ids = tokenizer.encode(input_text, return_tensors='pt')
        
        start_time = time.time()
        try:
            output = await asyncio.wait_for(generate_with_timeout(model, input_ids, 50, 1), timeout=10.0)
        except asyncio.TimeoutError:
            logger.error("Model generation timed out")
            raise HTTPException(status_code=504, detail="Model generation timed out")
        end_time = time.time()
        
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        
        logger.info(f"Generated text in {end_time - start_time:.2f} seconds")
        return {
            "generated_text": generated_text,
            "time_taken": end_time - start_time
        }
    except Exception as e:
        logger.error(f"Error in generate_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_quantized")
async def generate_text_quantized(request: Request):
    try:
        load_models()  # Ensure models are loaded
        if quantized_model is None or tokenizer is None:
            raise HTTPException(status_code=503, detail="Models not initialized")
        
        data = await request.json()
        input_text = data.get("text", "")
        
        input_ids = tokenizer.encode(input_text, return_tensors='pt')
        
        start_time = time.time()
        try:
            output = await asyncio.wait_for(generate_with_timeout(quantized_model, input_ids, 50, 1), timeout=10.0)
        except asyncio.TimeoutError:
            logger.error("Quantized model generation timed out")
            raise HTTPException(status_code=504, detail="Quantized model generation timed out")
        end_time = time.time()
        
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        
        logger.info(f"Generated quantized text in {end_time - start_time:.2f} seconds")
        return {
            "generated_text": generated_text,
            "time_taken": end_time - start_time
        }
    except Exception as e:
        logger.error(f"Error in generate_text_quantized: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

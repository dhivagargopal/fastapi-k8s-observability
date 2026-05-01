import os

# Gunicorn config variables
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"

import multiprocessing

# Gunicorn config variables
workers = multiprocessing.cpu_count()
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"

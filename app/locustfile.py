from locust import HttpUser, task, between
import random
import json

class FastAPIUser(HttpUser):
    wait_time = between(1, 5)

    @task(2)
    def get_root(self):
        with self.client.get("/", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def get_item(self):
        item_id = random.randint(1, 100)
        with self.client.get(f"/items/{item_id}", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")

    @task(3)
    def generate_text(self):
        payload = {"text": "Once upon a time"}
        with self.client.post("/generate", json=payload, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")

    @task(3)
    def generate_text_quantized(self):
        payload = {"text": "Once upon a time"}
        with self.client.post("/generate_quantized", json=payload, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")

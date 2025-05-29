import requests
import numpy as np
from functools import lru_cache

OLLAMA_URL = "http://localhost:11434"

@lru_cache(maxsize=100)  # Cache embeddings
def generate_embedding(text):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": "nomic-embed-text:latest",
                "prompt": text,
                "options": {"embedding_only": True}
            },
            timeout=30
        )
        return response.json()["embedding"]
    except Exception as e:
        print(f"Embedding Error: {str(e)}")
        return np.zeros(768)  # Return zero vector on failure

def generate_response(prompt):
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3.2-vision:11b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_ctx": 4096  # Larger context window
                }
            },
            timeout=120
        )
        return response.json()["response"]
    except Exception as e:
        return f"Error: {str(e)}"
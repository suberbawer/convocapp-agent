import requests
import os


def call_model(prompt: str, task: str, complexity: str = "low") -> str:
    url = f"{os.getenv('AI_URL')}/message"
    print("Calling AI model...", url)
    payload = {"text": prompt, "complexity": complexity, "chat_mode": True}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()["response"]
    except requests.RequestException as e:
        raise RuntimeError(f"Error calling AI service: {e}")

#test_instructions.py
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_instructions():
    payload = {
        "program_name": "Word",
        "current_location": "blank document",
        "action": "change font size to 14"
    }

    response = client.post("/instructions", json=payload)

    if response.status_code == 200:
        data = response.json()
        print("AI інструкція:")
        for step in data.get("instructions", []):
            print(step)
    else:
        print(f"Помилка: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_instructions()

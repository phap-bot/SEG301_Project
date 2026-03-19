import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from fastapi.testclient import TestClient
from src.ui.backend.main import app

def run_test():
    with TestClient(app) as client:
        print("Sending request to /api/v1/search...")
        response = client.get("/api/v1/search?query=tủ&limit=2&search_type=bm25")
        print("HTTP Status Code:", response.status_code)
        print("Response Body:", response.json())

if __name__ == "__main__":
    run_test()

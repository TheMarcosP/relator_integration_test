import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
import requests

app = FastAPI()

try:
    MODULE_B_URL = os.environ["MODULE_B_URL"]
    MODULE_A_PORT = int(os.environ["MODULE_A_PORT"])
except KeyError as e:
    raise RuntimeError(f"Missing required environment variable: {e.args[0]}")

@app.get("/test_a_module")
def test_a_module():
    print("Starting module A")
    response = requests.get(f"{MODULE_B_URL}/test_b_module")
    return {"from_b": response.json()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("module_a.main:app", host="0.0.0.0", port=MODULE_A_PORT, reload=True) 
    
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
from fastapi import FastAPI
import requests

app = FastAPI()

try:
    MODULE_C_URL = os.environ["MODULE_C_URL"]
    MODULE_B_PORT = int(os.environ["MODULE_B_PORT"])
except KeyError as e:
    raise RuntimeError(f"Missing required environment variable: {e.args[0]}")

@app.get("/process")
def process():
    response = requests.get(f"{MODULE_C_URL}/finalize")
    return {"from_c": response.json()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("module_b.main:app", host="0.0.0.0", port=MODULE_B_PORT, reload=True) 
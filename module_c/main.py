import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI

app = FastAPI()

try:
    MODULE_C_PORT = int(os.environ["MODULE_C_PORT"])
except KeyError as e:
    raise RuntimeError(f"Missing required environment variable: {e.args[0]}")

@app.get("/finalize")
def finalize():
    return {"result": "Finalized by Module C"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("module_c.main:app", host="0.0.0.0", port=MODULE_C_PORT, reload=True) 
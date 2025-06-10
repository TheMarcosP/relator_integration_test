# FastAPI Microservices Example

This project contains three FastAPI modules (A, B, C) that communicate with each other. Each module can be run locally or remotely, and their endpoints and ports are configurable via a single `.env` file at the project root. You can use [ngrok](https://ngrok.com/) to expose local services for remote access.

## Structure
- `module_a`: Calls Module B
- `module_b`: Calls Module C
- `module_c`: Returns a result

## Environment Variables with a Single `.env` File
All modules use a single `.env` file located at the project root to configure their dependencies and ports. The variables are loaded automatically using `python-dotenv`.

Example `.env` (at the project root):
```
MODULE_B_URL=http://localhost:8001  # Used by module_a
MODULE_C_URL=http://localhost:8002  # Used by module_b
MODULE_A_PORT=8000
MODULE_B_PORT=8001
MODULE_C_PORT=8002
```

**All required environment variables must be set.** If any are missing, the modules and scripts will fail with a clear error message.

Edit this file to point to local, ngrok, or remote URLs and to set the ports as needed.

## Running the Modules

### Recommended: Use the Run Script
The preferred way to run the modules is with the provided script, which ensures all required environment variables are set and allows you to launch any combination of modules from the project root:

```
python scripts/run_modules.py -m a c
```
- This will start Module A and Module C. Use any combination of `a`, `b`, and `c` (e.g., `-m a b c`).
- The script will check that all required environment variables are set for the selected modules and fail with a clear error if any are missing.
- The script uses the port and URL values from your `.env` file.

### Alternative: Manual Run
You can also run each module directly from the root using either Python or Uvicorn:

```
# Terminal 1 (Module C)
python module_c/main.py
# or
uvicorn module_c.main:app --host 0.0.0.0 --port $MODULE_C_PORT --reload

# Terminal 2 (Module B)
python module_b/main.py
# or
uvicorn module_b.main:app --host 0.0.0.0 --port $MODULE_B_PORT --reload

# Terminal 3 (Module A)
python module_a/main.py
# or
uvicorn module_a.main:app --host 0.0.0.0 --port $MODULE_A_PORT --reload
```

### (Optional) Expose services with ngrok
In separate terminals, run:

```
ngrok http $MODULE_A_PORT  # For Module A
ngrok http $MODULE_B_PORT  # For Module B
ngrok http $MODULE_C_PORT  # For Module C
```

Update the root `.env` file to use the ngrok URLs as needed.

### Test the chain
Call Module A's `/start` endpoint:

```
curl http://localhost:$MODULE_A_PORT/start
```

You should get a response like:

```
{"from_b":{"from_c":{"result":"Finalized by Module C"}}}
```

## Implementation Notes
- All endpoints are synchronous (`def` not `async def`).
- Inter-service HTTP calls use the `requests` library.
- Environment variables and ports are managed via a single `.env` file at the project root and loaded with `python-dotenv`.
- All modules and scripts will fail fast if any required environment variable is missing.

---

You can deploy any module remotely or locally, and configure the URLs and ports accordingly. Use ngrok or your own domain as needed. 
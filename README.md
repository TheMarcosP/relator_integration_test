# gRPC Microservices Example

This project contains three gRPC modules (A, B, C) that communicate with each other. Each module can be run locally or remotely, and their endpoints and ports are configurable via environment variables.

## Structure
- `module_a`: Generates events and sends them to Module B
- `module_b`: Processes events and forwards them to Module C
- `module_c`: Finalizes the processing and sends results back to Module A

## Environment Variables
Each module uses environment variables to configure their ports and dependencies. The variables are loaded automatically using `python-dotenv`.

Example `.env` (at the project root):
```
MODULE_A_HOST=localhost:50053
MODULE_B_HOST=localhost:50051
MODULE_C_HOST=localhost:50052
```

**All required environment variables must be set.** If any are missing, the modules and scripts will fail with a clear error message.

## Running the Modules

### Recommended: Use the Orchestrator Script
The preferred way to run the modules is with the provided script, which allows you to launch any combination of modules from the project root:

```bash
# Run all modules
python -m scripts.run_grpc_modules a b c

# Run just module C
python -m scripts.run_grpc_modules c

# Run modules A and B
python -m scripts.run_grpc_modules a b
```

The script will:
1. Start each module using Python's module system
2. Monitor their status
3. Handle graceful shutdown when you press Ctrl+C
4. Clean up all processes if any module fails

### Alternative: Run Modules Standalone
You can also run each module directly using Python's module system:

```bash
# Terminal 1 (Module A)
python -m module_a.module_a_server

# Terminal 2 (Module B)
python -m module_b.module_b_server

# Terminal 3 (Module C)
python -m module_c.module_c_server
```

### Test the Chain
Once the modules are running, Module A will automatically start sending events through the chain. You can monitor the logs in the `logs` directory:

```bash
# View Module A logs
tail -f logs/module_a.log

# View Module B logs
tail -f logs/module_b.log

# View Module C logs
tail -f logs/module_c.log
```

## Implementation Notes
- All modules use gRPC for communication
- Each module runs its own gRPC server
- Logging is configured to output to both console and log files
- Environment variables are managed via `.env` file and loaded with `python-dotenv`
- All modules and scripts will fail fast if any required environment variable is missing

---

You can deploy any module remotely or locally, and configure the host addresses accordingly. The modules will automatically handle the gRPC communication between them. 
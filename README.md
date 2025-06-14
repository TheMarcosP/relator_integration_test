# gRPC Pipeline Project

This project implements a gRPC-based pipeline for processing events through multiple modules. The pipeline consists of four modules that handle different stages of processing:

1. Module A: Simple sender that sends dictionaries to Module B
2. Module B: Converts events to text and forwards to Module C
3. Module C: Converts text to speech and forwards to Module D
4. Module D: Handles speech reproduction

## Module Structure

Each module is located in its own directory:
- `module_a/`: Contains a simple sender script that sends dictionaries to Module B
- `module_b/`: Text conversion
- `module_c/`: Text-to-speech conversion
- `module_d/`: Speech reproduction

## Configuration

The modules use environment variables for configuration. Create a `.env` file with the following variables:

```env
MODULE_B_HOST=localhost:50051
MODULE_C_HOST=localhost:50052
MODULE_D_HOST=localhost:50053
```

## Running the Pipeline

1. Start all servers in separate terminals:

```bash
# Terminal 1 (Module A - sender)
python module_a/dummy_sender.py

# Terminal 2
python module_b/server.py

# Terminal 3
python module_c/server.py

# Terminal 4
python module_d/server.py
```

## Testing

The test script (`module_a/test_pipeline.py`) generates random events and sends them through the pipeline with random delays between requests. This helps test the system's ability to handle multiple requests at different rates.

## Dependencies

- Python 3.7+
- grpcio
- grpcio-tools
- python-dotenv

Install dependencies:
```bash
pip install -r requirements.txt
```

## Protocol Buffers

The service definitions are in `proto/data.proto`. To regenerate the Python code from the proto file:

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/data.proto
```

## Quick Port Cleanup

While developing you might leave gRPC servers running which blocks their ports (50051-50053).  The helper script below will instantly free the ports by killing any process that is listening on them.

```bash
# kill the default gRPC ports
python scripts/kill_ports.py 50051 50052 50053

# or pick ports via environment variable
export KILL_PORTS="50051,50052"
python scripts/kill_ports.py 
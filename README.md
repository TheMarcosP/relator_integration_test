# Multi-Module gRPC Pipeline (A → B → C → D)

This repository contains a minimal **end-to-end gRPC example** that streams dummy events through four micro-services.

```
Module A  →  Module B  →  Module C  →  Module D
(events)     (text)        (audio)      (playback)
```

Each service is placed in its own folder (`module_a/ … module_d/`) and communicates with the next service using the messages and services defined in `proto/data.proto`.

Each request/response now carries a globally‐unique `id` field so you can trace a single event throughout the whole pipeline.

Processing logic for Modules **B–D** has been moved into dedicated `processor.py` files, keeping gRPC transport thin and allowing easier unit testing and future scaling.

**Note:** gRPC service methods have been renamed for clarity: `SendEvent` → `ProcessEvent`, `ProcessText` → `TextToSpeech`. Remember to regenerate the proto files after any changes to `data.proto`.

The sender in *Module A* is now encapsulated in an `EventSender` class (see `module_a/send_event.py`) offering a `send_async()` method. A default singleton (`default_sender`) is exported for quick use and backward-compatibility.

Module D now plays the `.wav` bytes using the `simpleaudio` library. Ensure your system audio works, and install optional dependencies via `pip install simpleaudio` (already listed in `requirements.txt`).

---
## 1. Quick Start

1.  Install dependencies (inside a fresh virtual-env):
    ```bash
    pip install -r requirements.txt
    ```
2.  Compile the protocol buffers **and patch the generated imports**:
    ```bash
    python -m grpc_tools.protoc -I./proto \
        --python_out=./proto --grpc_python_out=./proto \
        proto/data.proto

    # ⚠️  The gRPC code-gen places the stubs inside the `proto` package but
    #     still generates absolute imports like:
    #         import data_pb2 as data__pb2
    #     This breaks when you import the stubs from outside the package.
    #     Open   proto/data_pb2_grpc.py   (and similar files) and replace that
    #     line with:
    #         import proto.data_pb2 as data__pb2
    ```
3.  Start the three servers (**B**, **C**, **D**) in separate terminals (run them *as modules* so that Python treats their parent folder as a package):
    ```bash
    # Terminal 1
    python -m module_d.server
    # Terminal 2
    python -m module_c.server
    # Terminal 3
    python -m module_b.server
    ```
4.  Trigger the pipeline from **Module A** (also as a module):
    ```bash
    python -m module_a.sender_client
    ```
    You should see log lines flowing through all terminals. Module D will "play" each audio chunk sequentially while the other modules keep processing new events concurrently.

---
## 2. Environment Variables

Every service reads its own host/port – as **well as the next service's address** – from environment variables. If none are supplied, the defaults below are used:

```
MODULE_B_HOST=localhost:50051
MODULE_C_HOST=localhost:50052
MODULE_D_HOST=localhost:50053
```

During local development you can place these keys in a `.env` file (they are loaded on every access via `scripts.utils.get_env_var`).

---
## 3. Simulation Details

* **Module A** – sends events _in bursts_: two messages within ~1 s, then sleeps 3 s.
* **Module B** – waits 0.5–2 s per request to simulate NLP processing.
* **Module C** – waits 1–2.5 s per request to simulate text-to-speech synthesis and **returns an actual WAV clip** (bundled as `module_c/dummy_sound.wav`).
* **Module D** – plays the received audio clip in **ID order** using `simpleaudio`. The very first audio that arrives defines the starting index, so if id 2 arrives before id 1 the player will treat 2 as the first and wait for 3, 4, … thereafter.

Module D now spawns a background task **per audio request**, so playback starts immediately and can overlap with other clips.

All modules now prefix their log messages with small emoji icons (✅ success, ❌ error, 📡 server start, etc.) to improve readability when running multiple terminals.

---
## 4. Project Structure

```
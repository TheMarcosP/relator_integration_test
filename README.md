# Multi-Module gRPC Pipeline (A → B → C → D)

This repository contains a minimal **end-to-end gRPC example** that streams dummy events through four micro-services.

```
Module A  →  Module B  →  Module C  →  Module D
(events)     (text)        (audio)      (playback)
```

Each service is placed in its own folder (`module_a/ … module_d/`) and communicates with the next service using the messages and services defined in `proto/data.proto`.

Each request/response carries a globally‐unique `id` field so you can trace a single event throughout the whole pipeline.

Module D plays the `.wav` bytes using the `simpleaudio` library. Ensure your system audio works, and install optional dependencies via `pip install simpleaudio`.

---
## 1. Quick Start

1.  Install dependencies (inside a fresh virtual-env):
    ```bash
    pip install -r requirements.txt
    ```

2.  Start the three servers (**B**, **C**, **D**) in separate terminals (run them *as modules* so that Python treats their parent folder as a package):
    ```bash
    # Terminal 1
    python -m module_d.server
    # Terminal 2
    python -m module_c.server
    # Terminal 3
    python -m module_b.server
    ```
3.  Trigger the pipeline from **Module A** (also as a module):
    ```bash
    python -m module_a.sender_client
    ```
    You should see log lines flowing through all terminals. Module D will "play" each audio chunk sequentially while the other modules keep processing new events concurrently.

---
## 2. Environment Variables

Every service reads its own host/port – as **well as the next service's address** – from environment variables. If none are supplied, the defaults below are used:

```
MODULE_B_HOST=localhost:50052
MODULE_C_HOST=localhost:50053
MODULE_D_HOST=localhost:50054
```

During local development you can place these keys in a `.env` file (they are loaded on every access via `scripts.utils.get_env_var`).

---
### 🔒 Making Your WSL Server Accessible from Windows

To allow your gRPC server running inside WSL to be accessed from Windows, follow these two main steps:

---

#### 1. Allow Inbound Firewall Connections

Open PowerShell **as Administrator** and run:

```powershell
New-NetFirewallRule -DisplayName "Allow WSL Server" -Direction Inbound -LocalPort 50051,50052,50053 -Protocol TCP -Action Allow
```

This creates a firewall rule allowing inbound TCP connections on the specified ports.

---

#### 2. Set Up Port Forwarding (portproxy)

Windows needs to forward traffic to the WSL IP. Do the following:

1. In WSL, get your WSL IP:

   ```bash
   ip addr show eth0
   ```

   Look for the IP address (usually in the `inet` field).

2. In PowerShell (as Administrator), run:

   ```powershell
   netsh interface portproxy add v4tov4 listenport=50051 listenaddress=0.0.0.0 connectport=50051 connectaddress=<WSL_IP>
   ```

   Replace `<WSL_IP>` with the IP you got from WSL.
   For example:

   ```powershell
   netsh interface portproxy add v4tov4 listenport=50051 listenaddress=0.0.0.0 connectport=50051 connectaddress=172.31.234.193
   ```

---

You can check existing rules with:

```powershell
netsh interface portproxy show all
```

To delete a rule:

```powershell
netsh interface portproxy delete v4tov4 listenport=<PORT> listenaddress=0.0.0.0
```

---

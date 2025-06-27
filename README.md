# Multi-Module gRPC Pipeline with Service Discovery (A → B → C → D)

This repository contains a **end-to-end gRPC example** that streams dummy events through four micro-services with automated service discovery.

```
Module A  →  Module B  →  Module C  →  Module D
(events)     (text)        (audio)      (playback)
```

Each service is placed in its own folder (`module_a/ … module_d/`) and communicates with the next service using the messages and services defined in `proto/data.proto`.

Each request/response carries a globally‐unique `id` field so you can trace a single event throughout the whole pipeline.

Module D plays the `.wav` bytes using the `simpleaudio` library. Ensure your system audio works, and install optional dependencies via `pip install simpleaudio`.

## 🆕 Service Discovery MVP

The system now includes a **FastAPI-based service discovery service** that eliminates the need for manual endpoint configuration. Services can:
- **Auto-register** themselves when they start
- **Discover** other services dynamically  
- Work across **different machines and networks**
- **Pure discovery-based** communication (no manual configuration needed)
- **Graceful shutdown** with automatic service unregistration
- **Simplified networking** with explicit IP control via `SERVICE_HOST_IP`
- **Clean logging** with module identification and verbosity control
- **🔒 API Key Authentication** to prevent unauthorized access and spam

---
## 1. Quick Start

### Option A: With Service Discovery (Recommended)

1.  Install dependencies (inside a fresh virtual-env):
    ```bash
    pip install -r requirements.txt
    ```

2.  Start the **Discovery Service** (on the machine that will act as the registry):
    ```bash
    python -m discovery.server
    ```
    The discovery service will start on `http://0.0.0.0:8000`

3.  Configure discovery (copy and modify env.example):
    ```bash
    cp .env.example .env
    # Edit .env to set:
    # - DISCOVERY_URL: where the discovery server is running
    # - DISCOVERY_API_KEY: secure API key for authentication
    ```

4.  Start the services (all now use discovery):
    
    **Easy way (automated):**
    ```bash
    python start_services.py
    ```
    
    **Manual way (separate terminals):**
    ```bash
    # Terminal 1
    python -m module_d.server
    # Terminal 2  
    python -m module_c.server
    # Terminal 3
    python -m module_b.server_with_discovery
    ```

5.  Trigger the pipeline:
    ```bash
    python -m module_a.dummy_play_game
    ```

### Option B: Without Discovery (Legacy)

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Start the three servers (**B**, **C**, **D**) in separate terminals:
    ```bash
    # Terminal 1
    python -m module_d.server
    # Terminal 2
    python -m module_c.server
    # Terminal 3
    python -m module_b.server
    ```
3.  Trigger the pipeline:
    ```bash
    python -m module_a.sender_client
    ```
    Note: This legacy approach requires manual configuration of service endpoints.

### Testing the Discovery Service

Run the test script to verify the discovery service is working:

```bash
# Make sure discovery server is running first
python -m discovery.server

# In another terminal, run the test
python test_discovery.py
```

This will demonstrate service registration, discovery, listing, and unregistration.

### Testing Authentication

Verify that API key authentication is working correctly:

```bash
# Set your API key and test authentication
export DISCOVERY_API_KEY=your-api-key-here
python -m scripts.test_auth
```

This will test both authenticated and unauthenticated requests to ensure security is working.

---
## 2. Service Discovery System

### How it Works

The discovery service acts as an **online dictionary** where:
- Services **register** themselves: `POST /register` with `{name, host, port, metadata}`
- Services **discover** others: `GET /discover/{service_name}` returns `{host, port, endpoint, metadata}`

### Discovery API Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| `GET` | `/` | Health check and registry status | ❌ Public |
| `POST` | `/register` | Register a service | ✅ API Key Required |
| `GET` | `/discover/{name}` | Discover a service by name | ✅ API Key Required |
| `GET` | `/services` | List all registered services | ✅ API Key Required |
| `DELETE` | `/unregister/{name}` | Unregister a service | ✅ API Key Required |

### 🔒 Authentication

The discovery server uses **Bearer token authentication** with API keys to prevent unauthorized access:

- **Health check endpoint** (`/`) is public and requires no authentication
- **All other endpoints** require a valid API key in the `Authorization` header
- API keys are configured via the `DISCOVERY_API_KEY` environment variable
- Include the API key as: `Authorization: Bearer your-api-key-here`

**Security Benefits:**
- Prevents spam and unauthorized service registrations
- Protects against malicious service discovery attempts  
- Secures service unregistration from unauthorized users
- Allows monitoring of legitimate vs unauthorized access attempts



### CLI Tool

Test the discovery service using the built-in CLI:

```bash
# Set your API key first (required for all operations)
export DISCOVERY_API_KEY=your-secure-api-key

# Register a service
python -m discovery.cli register my_service 8080 --metadata '{"version": "1.0"}'

# Discover a service  
python -m discovery.cli discover my_service

# List all services
python -m discovery.cli list

# Get just the endpoint
python -m discovery.cli endpoint my_service

# Unregister a service
python -m discovery.cli unregister my_service

# Use remote discovery server
python -m discovery.cli --discovery-url http://192.168.1.100:8000 list
```

### Environment Variables

**Discovery Configuration:**
```bash
DISCOVERY_HOST=localhost        # Discovery server location  
DISCOVERY_API_KEY=your-api-key  # API key for discovery server authentication
SERVICE_HOST_IP=192.168.1.100   # Override auto-detected IP (optional)
```

**Service Binding (optional):**
```bash
MODULE_B_HOST=0.0.0.0:50052     # Bind address for Module B
MODULE_C_HOST=0.0.0.0:50053     # Bind address for Module C
MODULE_D_HOST=0.0.0.0:50054     # Bind address for Module D
```

**Logging Configuration:**
```bash
VERBOSE=true                    # Enable detailed debug logs (default: false)
```

During local development you can place these keys in a `.env` file (they are loaded on every access via `scripts.utils.get_env_var`).

### Deployment Scenarios

**Single Machine (Development):**
```bash
# All services on localhost, discovery on localhost:8000
DISCOVERY_HOST=localhost
```

**Multiple Machines (Same LAN):**
```bash
# Discovery server on main machine
DISCOVERY_HOST=192.168.1.100
# Services auto-detect their own IPs and register
```

**Different Networks:**
```bash
# Discovery server on publicly accessible host
DISCOVERY_HOST=your-discovery-server.com
# Services register with their public/accessible IPs
```

### IP Configuration

The system uses a smart approach for IP configuration:

1. **Environment Override**: Set `SERVICE_HOST_IP` for explicit control
2. **Auto-detection**: Basic socket-based IP detection
3. **Localhost Fallback**: Uses `127.0.0.1` if detection fails

**For most scenarios**, auto-detection works fine. **Override when needed**:

```bash
# WSL users - when auto-detection gives 172.x.x.x IP
SERVICE_HOST_IP=192.168.1.100

# Multi-network machines - when auto-detection picks wrong interface
SERVICE_HOST_IP=192.168.1.50

# Production - for explicit control
SERVICE_HOST_IP=10.0.1.100
```

**Benefits of this approach:**
- ✅ **Works out-of-the-box**: Most users don't need to configure anything
- ✅ **Override when needed**: Set `SERVICE_HOST_IP` for special cases
- ✅ **Clear logging**: Shows which IP was chosen and why

---
### 🔒 Making Your WSL Server Accessible from Windows

To allow your gRPC server running inside WSL to be accessed from Windows, follow these two main steps:

---

#### 1. Allow Inbound Firewall Connections

Open PowerShell **as Administrator** and run:

```powershell
New-NetFirewallRule -DisplayName "Allow WSL Server" -Direction Inbound -LocalPort 50052,50053,50054 -Protocol TCP -Action Allow
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
   netsh interface portproxy add v4tov4 listenport=50052 listenaddress=0.0.0.0 connectport=50052 connectaddress=172.30.66.160
   ```

    Restart PC after setting up the port forwarding to ensure it takes effect.
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

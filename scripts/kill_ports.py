#!/usr/bin/env python3
"""kill_ports.py

Utility script to forcibly terminate any processes that are listening on the
specified TCP ports. Designed for quickly freeing gRPC ports (e.g. 50051) while
iterating during development.

Usage
-----
    python scripts/kill_ports.py 50051 50052 50053

You can also read ports from the environment variable KILL_PORTS (comma-separated):

    export KILL_PORTS="50051,50052"
    python scripts/kill_ports.py

Notes
-----
• Requires the `lsof` utility (available on Linux/macOS, including WSL).
• Uses `kill -9` for simplicity—change `SIGKILL` to `SIGTERM` below if you prefer
  graceful shutdowns.
"""
import os
import signal
import subprocess
import sys
from typing import List, Set


def find_pids(port: str) -> Set[int]:
    """Return a set of PIDs that have the given TCP `port` open for listening."""
    try:
        output = subprocess.check_output(["lsof", "-ti", f"tcp:{port}"], text=True)
    except subprocess.CalledProcessError:
        # lsof returns non-zero if nothing is found
        return set()

    return {int(line.strip()) for line in output.splitlines() if line.strip()}


def kill_pids(pids: Set[int], port: str):
    if not pids:
        print(f"[✓] No process is listening on port {port}")
        return

    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
            print(f"[✗] Killed PID {pid} on port {port}")
        except ProcessLookupError:
            print(f"[!] PID {pid} no longer exists (race condition)")
        except PermissionError:
            print(f"[!] Permission denied when trying to kill PID {pid}")


def main(raw_ports: List[str]):
    if not raw_ports:
        env_ports = os.getenv("KILL_PORTS", "")
        raw_ports = [p.strip() for p in env_ports.split(",") if p.strip()]

    if not raw_ports:
        print("No ports provided. Pass ports as arguments or set KILL_PORTS env var.")
        sys.exit(1)

    for port in raw_ports:
        if not port.isdigit():
            print(f"[!] Skipping invalid port: {port}")
            continue
        pids = find_pids(port)
        kill_pids(pids, port)


if __name__ == "__main__":
    main(sys.argv[1:]) 
import grpc
import random
import os
import sys
from typing import Dict, Optional

# Ensure project root and proto dir are on the PYTHONPATH
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from proto import data_pb2, data_pb2_grpc
from scripts.utils import get_env_var

class ModuleASender:
    """Persistent async client for sending DictionaryData messages to Module B."""

    def __init__(self, target: Optional[str] = None):
        self.target = target or get_env_var('MODULE_B_HOST', 'localhost:50051')
        # Create a single channel for reuse across requests
        self._channel: grpc.aio.Channel = grpc.aio.insecure_channel(self.target)
        self._stub = data_pb2_grpc.ModuleBStub(self._channel)
        print(f"[ModuleA-Sender] Connected to Module B at {self.target}")

    async def send_event(self, event: Dict[str, str]):
        """Send an event dict to Module B and return its Ack response."""
        request = data_pb2.DictionaryData(data=event, universal_id=random.randint(1, 1_000_000))
        try:
            response = await self._stub.eventToTextRequest(request)
            return response
        except grpc.RpcError as err:
            print("[ModuleA-Sender] gRPC error:", err.code(), err.details())
            return None

    async def close(self):
        """Close the underlying gRPC channel."""
        await self._channel.close()

    # Allow use as async context-manager
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

class ModuleASenderSync:
    """Blocking (synchronous) variant of the sender that reuses a single channel."""

    def __init__(self, target: Optional[str] = None):
        self.target = target or get_env_var('MODULE_B_HOST', 'localhost:50051')
        self._channel: grpc.Channel = grpc.insecure_channel(self.target)
        self._stub = data_pb2_grpc.ModuleBStub(self._channel)
        print(f"[ModuleA-SenderSync] Connected to Module B at {self.target}")

    def send_event(self, event: Dict[str, str]):
        """Blocking send; returns Ack or None on error."""
        request = data_pb2.DictionaryData(data=event, universal_id=random.randint(1, 1_000_000))
        try:
            response = self._stub.eventToTextRequest(request)
            return response
        except grpc.RpcError as err:
            print("[ModuleA-SenderSync] gRPC error:", err.code(), err.details())
            return None

    def close(self):
        self._channel.close()

    # Context-manager helpers so user can do `with ModuleASenderSync() as s:`
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close() 
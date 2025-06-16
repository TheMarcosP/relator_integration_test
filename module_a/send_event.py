import logging
from functools import partial
from typing import Dict, Optional
import grpc
from scripts.utils import get_env_var
from proto import data_pb2, data_pb2_grpc

logging.basicConfig(level=logging.INFO, format="[Module A] %(asctime)s - %(levelname)s - %(message)s")

class EventSender:
    """Client wrapper responsible for sending events to Module B asynchronously."""

    def __init__(self, target_host: Optional[str] = None):
        self.host = target_host or get_env_var("MODULE_B_HOST", "localhost:50051")
        self._channel = grpc.insecure_channel(self.host)
        self._stub = data_pb2_grpc.ModuleBStub(self._channel)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def send_async(self, event_id: str, payload: Dict[str, str]) -> None:
        """Fire-and-forget send; returns immediately."""
        event_msg = data_pb2.Event(id=event_id, data=payload)
        future = self._stub.ProcessEvent.future(event_msg)
        future.add_done_callback(partial(self._on_response, event_id=event_id))

    def close(self) -> None:
        self._channel.close()

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _on_response(future: grpc.Future, event_id: str):
        try:
            response = future.result()
            status_icon = "✅" if response.success else "❌"
            logging.info(
                "%s Async response (id=%s): msg='%s'",
                status_icon,
                response.id,
                response.message,
            )
        except grpc.RpcError as exc:
            logging.error("❌ Async call for id=%s failed: %s", event_id, exc)

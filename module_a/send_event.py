import logging
from functools import partial
from typing import Dict, Optional
import os
os.environ["GRPC_VERBOSITY"] = "DEBUG"  # Enable verbose gRPC logging
import grpc
from scripts.utils import get_env_var
from proto import data_pb2, data_pb2_grpc

logging.basicConfig(level=logging.INFO, format="[Module A] %(asctime)s - %(levelname)s - %(message)s")

class EventSender:
    """Client wrapper responsible for sending events to Module B asynchronously."""

    def __init__(self, target_host: Optional[str] = None):
        self.host = target_host or get_env_var("MODULE_B_HOST", "192.168.0.202:50051")
        logging.info(f"🔌 Attempting connection to Module B at {self.host}")
        
        # Add channel options for better debugging
        channel_options = [
            ('grpc.enable_http_proxy', 0),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', 1),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
        ]
        
        try:
            self._channel = grpc.insecure_channel(self.host, options=channel_options)
            # Test connection before proceeding
            grpc.channel_ready_future(self._channel).result(timeout=10)
            logging.info("✅ Successfully established channel to Module B")
            
            self._stub = data_pb2_grpc.ModuleBStub(self._channel)
            # Send a test event to verify the stub
            test_event = data_pb2.Event(id="test", data={"test": "connection"})
            try:
                self._stub.ProcessEvent.future(test_event)
                logging.info("✅ Successfully created stub and verified ProcessEvent method")
            except Exception as e:
                logging.error(f"❌ Failed to verify ProcessEvent method: {str(e)}")
                raise
            
        except grpc.FutureTimeoutError:
            logging.error(f"❌ Failed to connect to {self.host} - timeout")
            raise
        except Exception as e:
            logging.error(f"❌ Failed to establish channel: {str(e)}")
            raise

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def send_async(self, event_id: str, payload: Dict[str, str]) -> None:
        """Fire-and-forget send; returns immediately."""
        event_msg = data_pb2.Event(id=event_id, data=payload)
        logging.info(f"📤 Sending event {event_id} with payload: {payload}")
        try:
            future = self._stub.ProcessEvent.future(event_msg)
            future.add_done_callback(partial(self._on_response, event_id=event_id))
        except Exception as e:
            logging.error(f"❌ Error sending event: {str(e)}")
            raise

    def close(self) -> None:
        if hasattr(self, '_channel'):
            logging.info("🔌 Closing gRPC channel")
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
            logging.error(f"❌ Async call for id={event_id} failed: {exc}")
            logging.error(f"  Status code: {exc.code()}")
            logging.error(f"  Details: {exc.details()}")
            logging.error(f"  Debug error string: {exc.debug_error_string()}")

import logging
import random
import time
from concurrent import futures
from typing import Dict
import grpc
from scripts.utils import get_env_var
from proto import data_pb2, data_pb2_grpc
from module_b.dummy_event_to_text import EventToText # Update this import with the actual implementation

logging.basicConfig(level=logging.INFO, format="[Module B] %(asctime)s - %(levelname)s - %(message)s")

MODULE_B_HOST = get_env_var("MODULE_B_HOST", "localhost:50051")
MODULE_C_HOST = get_env_var("MODULE_C_HOST", "localhost:50052")


class ModuleBServicer(data_pb2_grpc.ModuleBServicer):
    """Receives events from Module A and forwards text to Module C."""

    def __init__(self):
        # Create a single channel to Module C for reuse
        self._c_channel = grpc.insecure_channel(MODULE_C_HOST)
        self._c_stub = data_pb2_grpc.ModuleCStub(self._c_channel)
        logging.info(f"✅ Initialized connection to Module C at {MODULE_C_HOST}")

        # Processing component – heavy NLP, can tune delays
        self.eventToText = EventToText(min_delay=4.0, max_delay=6.0)

    def ProcessEvent(self, request: data_pb2.Event, context):  # noqa: N802 (grpc naming)
        logging.info(f"📥 Received event id={request.id} – sending to processor")

        text = self.eventToText.process(request)
        logging.info(f"➡️  Forwarding text '{text}' (id={request.id}) to Module C")
        try:
            response_c = self._c_stub.TextToSpeech(
                data_pb2.TextRequest(id=request.id, text=text)
            )
            success = response_c.success
            msg = response_c.message
        except grpc.RpcError as exc:
            success = False
            msg = f"❌ Failed to call Module C: {exc.details()}"
            logging.error(msg)
        return data_pb2.BasicResponse(id=request.id, success=success, message=msg)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    data_pb2_grpc.add_ModuleBServicer_to_server(ModuleBServicer(), server)
    server.add_insecure_port(MODULE_B_HOST)
    server.start()
    logging.info(f"📡 Module B gRPC server listening on {MODULE_B_HOST}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve() 
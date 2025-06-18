import logging
from concurrent import futures
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
import grpc
from grpc_interceptor import ServerInterceptor
from scripts.utils import get_env_var
from proto import data_pb2, data_pb2_grpc
from module_b.dummy_event_to_text import EventToText
# from module_b.event_to_text import EventToText

logging.basicConfig(level=logging.INFO, format="[Module B] %(asctime)s - %(levelname)s - %(message)s")

MODULE_B_HOST = "0.0.0.0:50051"
MODULE_C_HOST = get_env_var("MODULE_C_HOST", "0.0.0.0:50052")

class ConnectionLoggingInterceptor(ServerInterceptor):
    def intercept(self, method, request, context, method_name):
        peer = context.peer()
        logging.info(f"🔌 New connection from {peer}")
        return method(request, context)

class ModuleBServicer(data_pb2_grpc.ModuleBServicer):
    """Receives events from Module A and forwards text to Module C."""

    def __init__(self):
        # Create a single channel to Module C for reuse
        self._c_channel = grpc.insecure_channel(MODULE_C_HOST)
        self._c_stub = data_pb2_grpc.ModuleCStub(self._c_channel)
        logging.info(f"✅ Initialized connection to Module C at {MODULE_C_HOST}")

        # Processing component – heavy NLP, can tune delays
        self.eventToText = EventToText()

    def ProcessEvent(self, request: data_pb2.Event, context):  # noqa: N802 (grpc naming)
        logging.info(f"📥 Received event (id={request.id})")
        text = self.eventToText.process(request)
        logging.info(f"➡️  Forwarding text (id={request.id}) to Module C")
        try:
            response_c = self._c_stub.TextToSpeech(
                data_pb2.TextRequest(id=request.id, text=text)
            )
            success = response_c.success
            msg = response_c.message
        except grpc.RpcError as exc:
            success = False
            msg = f"❌ Failed to forward text to Module C: {exc.details()}"
            logging.error(msg)
        return data_pb2.BasicResponse(id=request.id, success=success, message=msg)


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[ConnectionLoggingInterceptor()]
    )
    data_pb2_grpc.add_ModuleBServicer_to_server(ModuleBServicer(), server)
    server.add_insecure_port(MODULE_B_HOST)
    server.start()
    logging.info(f"📡 Module B gRPC server listening on {MODULE_B_HOST}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve() 
import logging
from concurrent import futures
import grpc
from scripts.utils import get_env_var
from proto import data_pb2, data_pb2_grpc
from module_c.dummy_text_to_speech import TextToAudio # Update this import with the actual implementation

logging.basicConfig(level=logging.INFO, format="[Module C] %(asctime)s - %(levelname)s - %(message)s")

MODULE_C_HOST = get_env_var("MODULE_C_HOST", "localhost:50052")
MODULE_D_HOST = get_env_var("MODULE_D_HOST", "localhost:50053")


class ModuleCServicer(data_pb2_grpc.ModuleCServicer):
    def __init__(self):
        self._d_channel = grpc.insecure_channel(MODULE_D_HOST)
        self._d_stub = data_pb2_grpc.ModuleDStub(self._d_channel)
        logging.info(f"✅ Initialized connection to Module D at {MODULE_D_HOST}")

        # processing component
        self.TextToAudio = TextToAudio()

    def TextToSpeech(self, request: data_pb2.TextRequest, context):  # noqa: N802
        logging.info(f"📥 Received text to process (id={request.id}): '{request.text[:30]}…'")
        audio_bytes = self.TextToAudio.process(request)
        logging.info(f"➡️  Forwarding audio to Module D … (id={request.id})")
        try:
            response_d = self._d_stub.PlayAudio(
                data_pb2.AudioRequest(id=request.id, audio_data=audio_bytes)
            )
            success = response_d.success
            msg = response_d.message
        except grpc.RpcError as exc:
            success = False
            msg = f"❌ Failed to call Module D: {exc.details()}"
            logging.error(msg)
        return data_pb2.BasicResponse(id=request.id, success=success, message=msg)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    data_pb2_grpc.add_ModuleCServicer_to_server(ModuleCServicer(), server)
    server.add_insecure_port(MODULE_C_HOST)
    server.start()
    logging.info(f"📡 Module C gRPC server listening on {MODULE_C_HOST}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve() 
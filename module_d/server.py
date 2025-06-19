import logging
from concurrent.futures import ThreadPoolExecutor
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
import grpc
from scripts.utils import get_env_var
from proto import data_pb2, data_pb2_grpc
from module_d.audio_player import OrderedAudioPlayer

logging.basicConfig(level=logging.INFO, format="[Module D] %(asctime)s - %(levelname)s - %(message)s")

MODULE_D_HOST = "0.0.0.0:50053"

class ModuleDServicer(data_pb2_grpc.ModuleDServicer):
    def __init__(self):
        self.player = OrderedAudioPlayer()

    def PlayAudio(self, request: data_pb2.AudioRequest, context):  # noqa: N802
        self.player.process(request.id, request.audio_data)
        logging.info(f"✅ Enqueued audio (id={request.id}) for playback")
        return data_pb2.BasicResponse(id=request.id, success=True, message="Audio scheduled")


def serve():
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    data_pb2_grpc.add_ModuleDServicer_to_server(ModuleDServicer(), server)
    server.add_insecure_port(MODULE_D_HOST)
    server.start()
    logging.info(f"📡 Module D gRPC server listening on {MODULE_D_HOST}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve() 
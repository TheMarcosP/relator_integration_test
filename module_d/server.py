import logging
from concurrent.futures import ThreadPoolExecutor
import os
import signal
import sys
os.environ["GRPC_VERBOSITY"] = "ERROR"
import grpc
from scripts.utils import get_env_var
from proto import data_pb2, data_pb2_grpc
from module_d.audio_player import OrderedAudioPlayer

logging.basicConfig(level=logging.INFO, format="[Module D] %(asctime)s - %(levelname)s - %(message)s")

MODULE_D_HOST = get_env_var("MODULE_D_HOST", "0.0.0.0:50054")

class ModuleDServicer(data_pb2_grpc.ModuleDServicer):
    def __init__(self):
        logging.info("🔧 Initializing ModuleDServicer...")
        try:
            self.player = OrderedAudioPlayer()
            logging.info("✅ OrderedAudioPlayer initialized successfully")
        except Exception as e:
            logging.error(f"❌ Failed to initialize OrderedAudioPlayer: {e}")
            raise

    def PlayAudio(self, request: data_pb2.AudioRequest, context):  # noqa: N802
        try:
            logging.info(f"📥 Received audio request (id={request.id}, data_size={len(request.audio_data)} bytes)")
            logging.info(f"🔍 Client address: {context.peer()}")
            
            self.player.process(request.id, request.audio_data)
            logging.info(f"✅ Enqueued audio (id={request.id}) for playback")
            
            response = data_pb2.BasicResponse(id=request.id, success=True, message="Audio scheduled")
            logging.info(f"📤 Sending success response for id={request.id}")
            return response
            
        except Exception as e:
            error_msg = f"Error processing audio request (id={request.id}): {e}"
            logging.error(f"❌ {error_msg}")
            logging.exception("Full exception details:")
            
            return data_pb2.BasicResponse(
                id=request.id, 
                success=False, 
                message=f"Failed to process audio: {e}"
            )


def serve():
    logging.info("🚀 Starting Module D gRPC server...")
    
    try:
        server = grpc.server(ThreadPoolExecutor(max_workers=10))
        logging.info("✅ gRPC server instance created")
        
        servicer = ModuleDServicer()
        data_pb2_grpc.add_ModuleDServicer_to_server(servicer, server)
        logging.info("✅ ModuleDServicer added to server")
        listen_addr = server.add_insecure_port(MODULE_D_HOST)
        logging.info(f"✅ Server bound to {MODULE_D_HOST} (actual port: {listen_addr})")
        
        server.start()
        logging.info(f"📡 Module D gRPC server listening on {MODULE_D_HOST}")
        logging.info("🎯 Server is ready to accept connections...")
        
        # Add graceful shutdown handling
        def signal_handler(sig, frame):
            logging.info("🛑 Received shutdown signal, stopping server...")
            server.stop(grace=5)
            logging.info("✅ Server stopped gracefully")
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        server.wait_for_termination()
        
    except Exception as e:
        logging.error(f"❌ Failed to start server: {e}")
        logging.exception("Full exception details:")
        raise


if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        logging.info("🛑 Server interrupted by user")
    except Exception as e:
        logging.error(f"❌ Server failed: {e}")
        sys.exit(1)
        
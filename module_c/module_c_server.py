import grpc
from concurrent import futures
import sys
import os
import threading
# Add the parent directory to the Python path so 'proto' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import proto.data_pb2 as data_pb2
import proto.data_pb2_grpc as data_grpc
from scripts.logging_config import setup_logger
from scripts.utils import get_env_var
from text_to_speech import TextToSpeech

# Setup environment variables
MODULE_C_HOST = get_env_var("MODULE_C_HOST", "localhost:50052")
MODULE_A_HOST = get_env_var("MODULE_A_HOST", "localhost:50053")

# Setup logger
logger = setup_logger('module_c')
logger.debug(f"Initializing Module C with environment variables:\nMODULE_C_HOST: {MODULE_C_HOST}\nMODULE_A_HOST: {MODULE_A_HOST}")

# Create a single instance of TextToSpeech
text_to_speech = TextToSpeech()

class ModuleCServicer(data_grpc.ModuleCServicer):
    def Finalize(self, request, context):
        logger.debug(f"Received string from B: {request.data}")
        logger.info(f"Got string from B")
        # First acknowledge receipt
        ack = data_pb2.Ack(success=True, message="String received")
        
        # Process the data in a separate thread
        def process_and_send():
            try:
                # Process the text
                final_string = text_to_speech.process_text(request.data)
                logger.debug(f"Waiting 3 seconds before sending to A")
                # Send to A
                logger.debug(f"Connecting to Module A at {MODULE_A_HOST}")
                with grpc.insecure_channel(MODULE_A_HOST) as channel:
                    stub = data_grpc.ModuleAStub(channel)
                    stub.Notify(data_pb2.StringData(data=final_string))
                    logger.debug("Sent final result to A")
                    logger.info("Sent final result to A")
            except Exception as e:
                logger.error(f"Failed to process or send to A: {e}")
        
        # Start processing in background
        logger.debug("Starting background processing thread")
        threading.Thread(target=process_and_send, daemon=True).start()
        
        return ack

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    data_grpc.add_ModuleCServicer_to_server(ModuleCServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{MODULE_C_HOST.split(':')[1]}")
    server.start()
    logger.debug(f"Server initialized and listening on {MODULE_C_HOST}")
    logger.info(f"Server listening on {MODULE_C_HOST}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

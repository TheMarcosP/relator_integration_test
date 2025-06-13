import grpc
from concurrent import futures
import threading
# Add the parent directory to the Python path so 'proto' can be imported
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import proto.data_pb2 as data_pb2
import proto.data_pb2_grpc as data_grpc
from scripts.logging_config import setup_logger
from scripts.utils import get_env_var
from module_b.event_to_text import EventToText

# Setup environment variables
MODULE_B_HOST = get_env_var("MODULE_B_HOST", "localhost:50051")
MODULE_C_HOST = get_env_var("MODULE_C_HOST", "localhost:50052")

# Setup logger
logger = setup_logger('module_b')
logger.debug(f"Initializing Module B with environment variables: MODULE_B_HOST: {MODULE_B_HOST}, MODULE_C_HOST: {MODULE_C_HOST}")

# Create a single instance of EventToText
event_to_text = EventToText()

class ModuleBServicer(data_grpc.ModuleBServicer):
    def ProcessFromA(self, request, context):
        logger.debug(f"Received dictionary from A: {str(request.data)}")
        logger.info(f"Got dictionary from A")
        # First acknowledge receipt
        ack = data_pb2.Ack(success=True, message="Dictionary received")
        
        # Process the data in a separate thread
        def process_and_send():
            try:
                # Convert dictionary to text
                processed_string = event_to_text.convert_to_text(request.data)
                # Send to C
                logger.debug(f"Connecting to Module C at {MODULE_C_HOST}")
                with grpc.insecure_channel(MODULE_C_HOST) as channel:
                    stub = data_grpc.ModuleCStub(channel)
                    response = stub.Finalize(data_pb2.StringData(data=processed_string))
                    logger.debug(f"Received response from C: success: {response.success}, message: {response.message}")
                    logger.info(f"Got back from C")
            except Exception as e:
                event_to_text.error_count += 1
                logger.error(f"Failed to process or send to C: {e}")
        
        # Start processing in background
        logger.debug("Starting background processing thread")
        threading.Thread(target=process_and_send, daemon=True).start()
        
        return ack

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    data_grpc.add_ModuleBServicer_to_server(ModuleBServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{MODULE_B_HOST.split(':')[1]}")
    server.start()
    logger.debug(f"Server initialized and listening on {MODULE_B_HOST}")
    logger.info(f"Server listening on {MODULE_B_HOST}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()

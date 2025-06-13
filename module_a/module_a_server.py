import grpc
from concurrent import futures
from dotenv import load_dotenv
import sys
import os
import threading
import time
# Add the parent directory to the Python path so 'proto' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import proto.data_pb2 as data_pb2
import proto.data_pb2_grpc as data_grpc
from scripts.logging_config import setup_logger
from scripts.utils import get_env_var
from event_extractor import EventExtractor

# Setup environment variables
MODULE_B_HOST = get_env_var("MODULE_B_HOST", "localhost:50051")
MODULE_A_HOST = get_env_var("MODULE_A_HOST", "localhost:50053")

# Setup logger
logger = setup_logger('module_a')
logger.debug(f"Initializing Module A with environment variables: MODULE_B_HOST: {MODULE_B_HOST}, MODULE_A_HOST: {MODULE_A_HOST}")

# Create a single instance of EventExtractor
event_extractor = EventExtractor()

class ModuleAServicer(data_grpc.ModuleAServicer):
    def Notify(self, request, context):
        logger.debug(f"Received final result from C: {request.data}")
        return data_pb2.Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    data_grpc.add_ModuleAServicer_to_server(ModuleAServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{MODULE_A_HOST.split(':')[1]}")
    server.start()
    logger.debug(f"Server initialized and listening on {MODULE_A_HOST}")
    logger.info(f"Server listening on {MODULE_A_HOST}")
    server.wait_for_termination()

def run_client():
    logger.debug("Starting client connection to Module B")
    with grpc.insecure_channel(MODULE_B_HOST) as channel:
        stub = data_grpc.ModuleBStub(channel)
        
        # Track messages sent in the client
        messages_sent = 0
        MAX_MESSAGES = 10
        
        # Send exactly 10 messages
        while messages_sent < MAX_MESSAGES and event_extractor.active:  
            data_dict = event_extractor.extract_event()
            logger.debug(f"Preparing to send events: {data_dict}")
            logger.info(f"Sending events {messages_sent + 1}")
            try:
                ack = stub.ProcessFromA(data_pb2.DictionaryData(data=data_dict))
                logger.debug(f"Received acknowledgment from B: success: {ack.success}, message: {ack.message}")
                logger.info(f"Got acknowledgment from B")
                messages_sent += 1
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                
    stats = event_extractor.get_extraction_stats()
    logger.debug(f"Client finished sending messages. Stats: {stats}")
    logger.info(f"Finished sending {messages_sent} messages. Server remains active to receive responses.")

if __name__ == "__main__":
    # Start server in a separate thread
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    
    # Run client in main thread
    run_client()
    
    # Keep the main thread alive to maintain the server
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Module A...")
import logging
from concurrent import futures
import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
import grpc
from scripts.discovery_utils import (
    get_env_var, 
    get_service_endpoint_from_discovery, 
    start_grpc_server_with_discovery
)
from proto import data_pb2, data_pb2_grpc
from module_b.event_to_text import EventToText
# from module_b.dummy_event_to_text import EventToText
import threading
import time
from queue import Queue
import json

# Service configuration
logging.basicConfig(level=logging.INFO, format="[Module B] %(asctime)s - %(levelname)s - %(message)s")
SERVICE_NAME = "module_b"
MODULE_B_HOST = get_env_var("MODULE_B_HOST", "0.0.0.0:50052")
MODULE_C_HOST = get_env_var("MODULE_C_HOST") or get_service_endpoint_from_discovery("module_c")

# ------------------------- MAIN CODE ------------------------------------ #
class ModuleBServicer(data_pb2_grpc.ModuleBServicer):
    """Receives events from Module A, accumulates them, and periodically generates commentary."""

    def __init__(self, batch_interval_seconds=10):
        # Create a single channel to Module C for reuse
        self._c_channel = grpc.insecure_channel(MODULE_C_HOST)
        self._c_stub = data_pb2_grpc.ModuleCStub(self._c_channel)
        logging.info(f"✅ Initialized connection to Module C at {MODULE_C_HOST}")

        # Processing component – heavy NLP, can tune delays
        self.eventToText = EventToText()

        # Event accumulation system
        self.event_queue = Queue()
        self.batch_interval = batch_interval_seconds
        self.processing_thread = None
        self.stop_processing = threading.Event()
        self.last_batch_id = 0
        
        # Start the periodic processing thread
        self._start_processing_thread()

    def _start_processing_thread(self):
        """Start the background thread that processes events periodically."""
        self.processing_thread = threading.Thread(target=self._process_events_periodically, daemon=True)
        self.processing_thread.start()
        logging.info(f"🔄 Started periodic processing thread (interval: {self.batch_interval}s)")

    def _process_events_periodically(self):
        """Background thread that processes accumulated events every N seconds."""
        while not self.stop_processing.is_set():
            # Wait for the specified interval
            if self.stop_processing.wait(self.batch_interval):
                break  # Stop signal received
            
            # Collect all events from the queue
            events = []
            while not self.event_queue.empty():
                try:
                    event = self.event_queue.get_nowait()
                    events.append(event)
                except:
                    break
            
            # Process events if we have any
            if events:
                self._process_event_batch(events)

    def _process_start_of_match_event(self, event):
        """Process the special start_of_match event immediately."""
        try:
            # Generate opening commentary
            text = self.eventToText.process_start_of_match(event)
            
            if text and text.strip():
                logging.info(f"➡️  Forwarding opening commentary (id={event.id}) to Module C")
                
                # Send to Module C
                response_c = self._c_stub.TextToSpeech(
                    data_pb2.Comment(id=event.id, text=text)
                )
                
                if response_c.success:
                    logging.info(f"✅ Successfully sent opening commentary to Module C")
                else:
                    logging.warning(f"⚠️  Module C reported issue with opening commentary: {response_c.message}")
            else:
                logging.info(f"📝 No opening commentary generated")
                
        except grpc.RpcError as exc:
            error_msg = f"❌ Failed to forward opening commentary to Module C: {exc.details()}"
            logging.error(error_msg)
        except Exception as exc:
            error_msg = f"❌ Error processing opening commentary: {str(exc)}"
            logging.error(error_msg)

    def _process_event_batch(self, events):
        """Process a batch of events and send the result to Module C."""
        self.last_batch_id += 1
        batch_id = f"batch_{self.last_batch_id}"
        
        logging.info(f"🎯 Processing batch {batch_id} with {len(events)} events")
        
        try:
            # Generate commentary for the batch of events
            text = self.eventToText.process_batch(events)
            
            if text and text.strip():  # Only send if there's actual content
                logging.info(f"➡️  Forwarding batch commentary (id={batch_id}) to Module C")
                
                # Send to Module C
                response_c = self._c_stub.TextToSpeech(
                    data_pb2.Comment(id=batch_id, text=text)
                )
                
                if response_c.success:
                    logging.info(f"✅ Successfully sent batch {batch_id} to Module C")
                else:
                    logging.warning(f"⚠️  Module C reported issue with batch {batch_id}: {response_c.message}")
            else:
                logging.info(f"📝 No commentary generated for batch {batch_id}")
                
        except grpc.RpcError as exc:
            error_msg = f"❌ Failed to forward batch {batch_id} to Module C: {exc.details()}"
            logging.error(error_msg)
        except Exception as exc:
            error_msg = f"❌ Error processing batch {batch_id}: {str(exc)}"
            logging.error(error_msg)

    def ProcessEvent(self, request: data_pb2.Event, context):  # noqa: N802 (grpc naming)
        """Receive an event and add it to the processing queue."""
        
        # Check if this is the start_of_match event for special handling
        event_data = json.loads(request.data)
        if event_data.get("type") == "start_of_match":
            logging.info(f"📥 Received START_OF_MATCH event (id={request.id}) - processing immediately")
            self._process_start_of_match_event(request)
        else:
            logging.info(f"📥 Received event (id={request.id}) - added to queue")
            # Add event to queue for batch processing
            self.event_queue.put(request)
        
        # Return immediate acknowledgment
        return data_pb2.BasicResponse(
            id=request.id, 
            success=True, 
            message="Event processed" if event_data.get("type") == "start_of_match" else "Event queued for batch processing"
        )

    def shutdown(self):
        """Gracefully shutdown the processing thread."""
        logging.info("🛑 Shutting down event processor...")
        self.stop_processing.set()
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        self._c_channel.close()

def serve():
    servicer = ModuleBServicer(batch_interval_seconds=8)  # Configurable interval
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    data_pb2_grpc.add_ModuleBServicer_to_server(servicer, server)
    
    try:
        # Start server with discovery registration and graceful shutdown
        start_grpc_server_with_discovery(
            server=server,
            service_name=SERVICE_NAME,
            host_address=MODULE_B_HOST,
            metadata={
                "version": "1.0.0",
                "type": "event_processor",
                "description": "Converts batched events to text"
            }
        )
    except KeyboardInterrupt:
        logging.info("🛑 Received shutdown signal")
    finally:
        servicer.shutdown()

if __name__ == "__main__":
    serve()
    
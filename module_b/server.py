import logging
from concurrent import futures
import os
import socket
import netifaces
os.environ["GRPC_VERBOSITY"] = "DEBUG"  # Enable verbose gRPC logging
import grpc
from grpc_interceptor import ServerInterceptor
from scripts.utils import get_env_var
from proto import data_pb2, data_pb2_grpc
from module_b.dummy_event_to_text import EventToText
# from module_b.event_to_text import EventToText

logging.basicConfig(level=logging.DEBUG, format="[Module B] %(asctime)s - %(levelname)s - %(message)s")

def get_ip_address():
    """Get the IP address that can be reached from other machines."""
    # Try to get the IP from the eth0 interface first
    try:
        addrs = netifaces.ifaddresses('eth0')
        if netifaces.AF_INET in addrs:
            ip = addrs[netifaces.AF_INET][0]['addr']
            logging.info(f"Using eth0 IP address: {ip}")
            return ip
    except (ValueError, KeyError):
        pass

    # Fallback: try all interfaces
    for interface in netifaces.interfaces():
        try:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    # Skip localhost
                    if not ip.startswith('127.'):
                        logging.info(f"Using IP address from {interface}: {ip}")
                        return ip
        except ValueError:
            continue
    
    # Last resort: use 0.0.0.0
    logging.warning("Could not find specific IP address, using 0.0.0.0")
    return "0.0.0.0"

SERVER_IP = get_ip_address()
MODULE_B_HOST = f"{SERVER_IP}:50051"
MODULE_C_HOST = get_env_var("MODULE_C_HOST", "0.0.0.0:50052")

class ConnectionLoggingInterceptor(ServerInterceptor):
    def intercept(self, method, request, context, method_name):
        peer = context.peer()
        logging.info(f"🔌 New connection from {peer} calling method {method_name}")
        try:
            result = method(request, context)
            logging.info(f"✅ Successfully handled {method_name} from {peer}")
            return result
        except Exception as e:
            logging.error(f"❌ Error handling {method_name} from {peer}: {str(e)}")
            raise

class ModuleBServicer(data_pb2_grpc.ModuleBServicer):
    """Receives events from Module A and forwards text to Module C."""

    def __init__(self):
        # Log all available methods
        methods = [method for method in dir(self) if not method.startswith('_')]
        logging.info("ModuleBServicer initialized with methods: %s", methods)
        
        # Log protobuf service info
        service = data_pb2.DESCRIPTOR.services_by_name['ModuleB']
        logging.info("ModuleB service methods from proto:")
        for method in service.methods:
            logging.info(f"  - {method.name}: {method.input_type.name} -> {method.output_type.name}")
        
        # Create a single channel to Module C for reuse
        channel_options = [
            ('grpc.enable_http_proxy', 0),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', 1),
        ]
        self._c_channel = grpc.insecure_channel(MODULE_C_HOST, options=channel_options)
        self._c_stub = data_pb2_grpc.ModuleCStub(self._c_channel)
        logging.info(f"Initialized connection to Module C at {MODULE_C_HOST}")

        # Processing component – heavy NLP, can tune delays
        self._processor = EventToText(min_delay=40.0, max_delay=60.0)

    def ProcessEvent(self, request: data_pb2.Event, context):  # noqa: N802 (grpc naming)
        logging.info(f"ProcessEvent called with request type: {type(request)}")
        logging.info(f"Request details: id={request.id}, data={request.data}")
        logging.info(f"📥 Processing event (id={request.id})")
        
        text = self._processor.process(request)
        logging.info(f"➡️  Forwarding text (id={request.id}) to Module C")
        try:
            response_c = self._c_stub.TextToSpeech(
                data_pb2.TextRequest(id=request.id, text=text)
            )
            success = response_c.success
            msg = response_c.message
            logging.info(f"✅ Successfully forwarded text to Module C: {msg}")
        except grpc.RpcError as exc:
            success = False
            msg = f"❌ Failed to forward text to Module C: {exc.details()}"
            logging.error(msg)
            logging.error(f"  Status code: {exc.code()}")
            logging.error(f"  Debug error string: {exc.debug_error_string()}")
        return data_pb2.BasicResponse(id=request.id, success=success, message=msg)


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[ConnectionLoggingInterceptor()],
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
            ('grpc.enable_http_proxy', 0),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', 1),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.max_pings_without_data', 0),
        ]
    )
    data_pb2_grpc.add_ModuleBServicer_to_server(ModuleBServicer(), server)
    server.add_insecure_port(MODULE_B_HOST)
    server.start()
    logging.info(f"📡 Module B gRPC server listening on {MODULE_B_HOST}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve() 
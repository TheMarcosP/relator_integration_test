import grpc
import asyncio
from concurrent import futures
import sys
import os

# Add the proto directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import data_pb2, data_pb2_grpc
from scripts.utils import get_env_var

class ModuleBServicer(data_pb2_grpc.ModuleBServicer):
    def __init__(self):
        self.module_c_host = get_env_var('MODULE_C_HOST', 'localhost:50052')
        self.channel = grpc.aio.insecure_channel(self.module_c_host)
        self.stub = data_pb2_grpc.ModuleCStub(self.channel)

    async def eventToTextRequest(self, request, context):
        try:
            print(f"Received request with universal_id: {request.universal_id}")
            print(f"Request data: {request.data}")
            
            # Convert dictionary to text (dummy implementation)
            text_data = " ".join([f"{k}: {v}" for k, v in request.data.items()])
            print(f"Converted to text: {text_data}")
            
            # Create text request for Module C
            text_request = data_pb2.TextData(
                data=text_data,
                universal_id=request.universal_id
            )
            
            # Forward to Module C
            response = await self.stub.textToSpeechRequest(text_request)
            print(f"Response from Module C: {response.message}")
            return response
        except Exception as e:
            print(f"Error in Module B: {str(e)}")
            return data_pb2.Ack(success=False, message=str(e), universal_id=request.universal_id)

async def serve():
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
        ]
    )
    
    # Add the servicer to the server
    data_pb2_grpc.add_ModuleBServicer_to_server(ModuleBServicer(), server)
    
    port = int(get_env_var('MODULE_B_PORT', '50051'))
    server.add_insecure_port(f'[::]:{port}')
    await server.start()
    print(f"Module B server started on port {port}")
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve()) 
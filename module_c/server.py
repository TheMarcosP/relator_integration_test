import grpc
import asyncio
from concurrent import futures
import sys
import os

# Add the proto directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import data_pb2, data_pb2_grpc
from scripts.utils import get_env_var

class ModuleCServicer(data_pb2_grpc.ModuleCServicer):
    def __init__(self):
        self.module_d_host = get_env_var('MODULE_D_HOST', 'localhost:50053')
        self.channel = grpc.aio.insecure_channel(self.module_d_host)
        self.stub = data_pb2_grpc.ModuleDStub(self.channel)

    async def textToSpeechRequest(self, request, context):
        try:
            # Dummy text-to-speech conversion
            speech_data = f"SPEECH_{request.data}"
            
            # Create speech request for Module D
            speech_request = data_pb2.SpeechData(
                data=speech_data,
                universal_id=request.universal_id
            )
            
            # Forward to Module D
            response = await self.stub.ReproduceSpeechRequest(speech_request)
            return response
        except Exception as e:
            return data_pb2.Ack(success=False, message=str(e), universal_id=request.universal_id)

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    data_pb2_grpc.add_ModuleCServicer_to_server(ModuleCServicer(), server)
    
    port = int(get_env_var('MODULE_C_PORT', '50052'))
    server.add_insecure_port(f'[::]:{port}')
    await server.start()
    print(f"Module C server started on port {port}")
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve()) 
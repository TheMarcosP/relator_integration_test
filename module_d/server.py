import grpc
import asyncio
from concurrent import futures
import sys
import os

# Add the proto directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import data_pb2, data_pb2_grpc
from scripts.utils import get_env_var

class ModuleDServicer(data_pb2_grpc.ModuleDServicer):
    async def ReproduceSpeechRequest(self, request, context):
        try:
            # Dummy speech reproduction
            print(f"Reproducing speech: {request.data}")
            
            # Simulate some processing time
            await asyncio.sleep(0.5)
            
            return data_pb2.Ack(
                success=True,
                message="Speech reproduced successfully",
                universal_id=request.universal_id
            )
        except Exception as e:
            return data_pb2.Ack(
                success=False,
                message=str(e),
                universal_id=request.universal_id
            )

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    data_pb2_grpc.add_ModuleDServicer_to_server(ModuleDServicer(), server)
    
    port = int(get_env_var('MODULE_D_PORT', '50053'))
    server.add_insecure_port(f'[::]:{port}')
    await server.start()
    print(f"Module D server started on port {port}")
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve()) 
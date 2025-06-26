"""
RelatorDiscovery MVP - Service Discovery Server
A simple FastAPI-based service registry for the Relator pipeline modules.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[Discovery] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class ServiceInfo(BaseModel):
    name: str
    host: str
    port: int
    health_endpoint: Optional[str] = "/health"
    metadata: Optional[Dict[str, str]] = {}


class ServiceRegistration(ServiceInfo):
    pass


class ServiceResponse(ServiceInfo):
    service_id: str
    registered_at: datetime
    last_heartbeat: datetime
    status: str = "healthy"


class HealthCheck(BaseModel):
    service_id: str
    status: str = "healthy"


# In-memory service registry (for MVP)
class ServiceRegistry:
    def __init__(self):
        self.services: Dict[str, ServiceResponse] = {}
        self.name_to_id: Dict[str, str] = {}  # service_name -> service_id mapping
        
    def register_service(self, service: ServiceRegistration) -> str:
        """Register a new service and return service_id"""
        service_id = f"{service.name}_{int(time.time())}"
        now = datetime.now()
        
        # If service with same name exists, update the mapping
        if service.name in self.name_to_id:
            old_service_id = self.name_to_id[service.name]
            if old_service_id in self.services:
                del self.services[old_service_id]
        
        # Create service response object
        service_response = ServiceResponse(
            service_id=service_id,
            name=service.name,
            host=service.host,
            port=service.port,
            health_endpoint=service.health_endpoint,
            metadata=service.metadata,
            registered_at=now,
            last_heartbeat=now,
            status="healthy"
        )
        
        # Store in registry
        self.services[service_id] = service_response
        self.name_to_id[service.name] = service_id
        
        logger.info(f"✅ Registered service: {service.name} at {service.host}:{service.port} (id: {service_id})")
        return service_id
    
    def get_service_by_name(self, name: str) -> Optional[ServiceResponse]:
        """Get service by name"""
        if name in self.name_to_id:
            service_id = self.name_to_id[name]
            return self.services.get(service_id)
        return None
    
    def get_service_by_id(self, service_id: str) -> Optional[ServiceResponse]:
        """Get service by service_id"""
        return self.services.get(service_id)
    
    def get_all_services(self) -> List[ServiceResponse]:
        """Get all registered services"""
        return list(self.services.values())
    
    def update_heartbeat(self, service_id: str) -> bool:
        """Update service heartbeat"""
        if service_id in self.services:
            self.services[service_id].last_heartbeat = datetime.now()
            self.services[service_id].status = "healthy"
            return True
        return False
    
    def mark_unhealthy(self, service_id: str) -> bool:
        """Mark service as unhealthy"""
        if service_id in self.services:
            self.services[service_id].status = "unhealthy"
            return True
        return False
    
    def cleanup_stale_services(self, timeout_minutes: int = 5):
        """Remove services that haven't sent heartbeat for timeout_minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        stale_services = []
        
        for service_id, service in self.services.items():
            if service.last_heartbeat < cutoff_time:
                stale_services.append(service_id)
        
        for service_id in stale_services:
            service = self.services[service_id]
            logger.warning(f"🧹 Removing stale service: {service.name} (id: {service_id})")
            
            # Remove from name mapping if it points to this service_id
            if service.name in self.name_to_id and self.name_to_id[service.name] == service_id:
                del self.name_to_id[service.name]
            
            del self.services[service_id]


# Initialize FastAPI app and registry
app = FastAPI(
    title="RelatorDiscovery",
    description="Service Discovery for Relator Pipeline",
    version="1.0.0"
)

registry = ServiceRegistry()


# Background task for cleanup
async def cleanup_stale_services():
    """Background task to cleanup stale services"""
    registry.cleanup_stale_services()


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "RelatorDiscovery",
        "status": "healthy",
        "total_services": len(registry.services)
    }


@app.post("/register", response_model=Dict[str, str])
async def register_service(service: ServiceRegistration):
    """Register a new service"""
    try:
        service_id = registry.register_service(service)
        return {
            "service_id": service_id,
            "message": f"Service {service.name} registered successfully",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"❌ Failed to register service {service.name}: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.get("/discover/{service_name}", response_model=ServiceResponse)
async def discover_service(service_name: str):
    """Discover a service by name"""
    service = registry.get_service_by_name(service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    logger.info(f"🔍 Service discovery request for {service_name} -> {service.host}:{service.port}")
    return service


@app.get("/services", response_model=List[ServiceResponse])
async def list_services():
    """List all registered services"""
    return registry.get_all_services()


@app.post("/heartbeat/{service_id}")
async def heartbeat(service_id: str, background_tasks: BackgroundTasks):
    """Service heartbeat endpoint"""
    if not registry.update_heartbeat(service_id):
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    
    # Schedule cleanup in background
    background_tasks.add_task(cleanup_stale_services)
    
    return {"status": "success", "message": "Heartbeat updated"}


@app.delete("/unregister/{service_id}")
async def unregister_service(service_id: str):
    """Unregister a service"""
    service = registry.get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    
    # Remove from name mapping if it points to this service_id
    if service.name in registry.name_to_id and registry.name_to_id[service.name] == service_id:
        del registry.name_to_id[service.name]
    
    del registry.services[service_id]
    logger.info(f"🗑️ Unregistered service: {service.name} (id: {service_id})")
    
    return {"status": "success", "message": f"Service {service_id} unregistered"}


# Relator-specific convenience endpoints
@app.get("/pipeline/next/{current_module}")
async def get_next_module(current_module: str):
    """Get the next module in the pipeline chain"""
    pipeline_order = {
        "module_a": "module_b",
        "module_b": "module_c", 
        "module_c": "module_d"
    }
    
    next_module = pipeline_order.get(current_module.lower())
    if not next_module:
        raise HTTPException(status_code=400, detail=f"Unknown module or end of pipeline: {current_module}")
    
    service = registry.get_service_by_name(next_module)
    if not service:
        raise HTTPException(status_code=404, detail=f"Next module {next_module} not found")
    
    return {
        "current_module": current_module,
        "next_module": next_module,
        "next_service": service
    }


def main():
    """Run the discovery server"""
    logger.info("🚀 Starting RelatorDiscovery server...")
    uvicorn.run(
        "discovery.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main() 
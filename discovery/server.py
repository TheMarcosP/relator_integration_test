"""
Discovery Server MVP - FastAPI-based service registry
Acts as an online dictionary where modules can register and discover each other
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Optional
import uvicorn
from scripts.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger("Discovery Server")

app = FastAPI(title="Relator Discovery Service", version="1.0.0")

# Simple in-memory dictionary to store service information
services_registry: Dict[str, dict] = {}

class ServiceInfo(BaseModel):
    """Service information model"""
    host: str
    port: int
    metadata: Optional[dict] = None

class ServiceRegistration(BaseModel):
    """Service registration request model"""
    service_name: str
    host: str
    port: int
    metadata: Optional[dict] = None

@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "Discovery Service is running", "registered_services": len(services_registry)}

@app.post("/register")
def register_service(registration: ServiceRegistration):
    """
    Register a service in the discovery registry
    
    Args:
        registration: Service registration information
    
    Returns:
        Success message with registration details
    """
    service_info = {
        "host": registration.host,
        "port": registration.port,
        "metadata": registration.metadata or {},
        "endpoint": f"{registration.host}:{registration.port}"
    }
    
    services_registry[registration.service_name] = service_info
    
    logger.info(f"✅ Registered service '{registration.service_name}' at {service_info['endpoint']}")
    
    return {
        "message": f"Service '{registration.service_name}' registered successfully",
        "service_name": registration.service_name,
        "endpoint": service_info["endpoint"]
    }

@app.get("/discover/{service_name}")
def discover_service(service_name: str):
    """
    Discover a service by name
    
    Args:
        service_name: Name of the service to discover
    
    Returns:
        Service information including host, port, and metadata
    
    Raises:
        HTTPException: If service is not found
    """
    if service_name not in services_registry:
        logger.warning(f"❌ Service '{service_name}' not found in registry")
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    service_info = services_registry[service_name]
    logger.info(f"🔍 Service '{service_name}' discovered at {service_info['endpoint']}")
    
    return {
        "service_name": service_name,
        **service_info
    }

@app.get("/services")
def list_services():
    """
    List all registered services
    
    Returns:
        Dictionary of all registered services
    """
    logger.info(f"📋 Listed all services: {list(services_registry.keys())}")
    return {
        "services": services_registry,
        "count": len(services_registry)
    }

@app.delete("/unregister/{service_name}")
def unregister_service(service_name: str):
    """
    Unregister a service from the registry
    
    Args:
        service_name: Name of the service to unregister
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If service is not found
    """
    if service_name not in services_registry:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    del services_registry[service_name]
    logger.info(f"🗑️  Unregistered service '{service_name}'")
    
    return {"message": f"Service '{service_name}' unregistered successfully"}

def main():
    """Run the discovery server"""
    uvicorn.run(
        "discovery.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 
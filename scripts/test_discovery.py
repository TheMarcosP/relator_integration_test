#!/usr/bin/env python3
"""
Test script for RelatorDiscovery server
"""

import sys
import os
import time
import requests
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from discovery.client import DiscoveryClient


def test_discovery_server():
    """Test the discovery server functionality"""
    print("🧪 Testing RelatorDiscovery server...")
    
    # Test basic health check
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Health check: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test service registration
    client = DiscoveryClient()
    
    # Register test services
    test_services = [
        {"name": "module_b", "port": 50052},
        {"name": "module_c", "port": 50053},
        {"name": "module_d", "port": 50054}
    ]
    
    for service in test_services:
        success = client.register_service(
            name=service["name"],
            port=service["port"],
            metadata={"version": "1.0.0", "environment": "test"}
        )
        if success:
            print(f"✅ Registered {service['name']}")
        else:
            print(f"❌ Failed to register {service['name']}")
    
    time.sleep(1)  # Give some time for registration
    
    # Test service discovery
    for service in test_services:
        discovered = client.discover_service(service["name"])
        if discovered:
            print(f"✅ Discovered {service['name']}: {discovered['host']}:{discovered['port']}")
        else:
            print(f"❌ Failed to discover {service['name']}")
    
    # Test pipeline chain discovery
    pipeline_chain = ["module_a", "module_b", "module_c"]
    for current in pipeline_chain:
        next_address = client.get_next_service_address(current)
        if next_address:
            print(f"✅ Pipeline: {current} -> {next_address}")
        else:
            print(f"❌ Failed to get next service for {current}")
    
    # Test list all services
    try:
        response = requests.get("http://localhost:8000/services", timeout=5)
        services = response.json()
        print(f"✅ Listed {len(services)} services:")
        for service in services:
            print(f"   - {service['name']} at {service['host']}:{service['port']}")
    except Exception as e:
        print(f"❌ Failed to list services: {e}")
    
    # Cleanup - unregister test service
    if client.service_id:
        success = client.unregister_service()
        if success:
            print("✅ Unregistered test service")
        else:
            print("❌ Failed to unregister test service")
    
    print("\n🎉 Discovery server test completed!")
    return True


if __name__ == "__main__":
    test_discovery_server() 
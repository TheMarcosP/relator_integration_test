#!/usr/bin/env python3
"""
RelatorDiscovery Deployment Configuration Examples

This script shows how to configure the system for different deployment scenarios.
"""

import os


def show_deployment_configurations():
    """Show configuration examples for different deployment scenarios"""
    
    print("🚀 RelatorDiscovery Deployment Configuration Examples")
    print("=" * 60)
    
    print("\n1️⃣ SAME MACHINE DEPLOYMENT")
    print("-" * 30)
    print("All modules running on the same machine/WSL instance")
    print("Environment variables:")
    print("   DISCOVERY_HOST=localhost:8000")
    print("   DEPLOYMENT_MODE=localhost")
    print("   # Services will register as 127.0.0.1")
    
    print("\n2️⃣ LAN DEPLOYMENT")
    print("-" * 30)
    print("Modules running on different machines in the same LAN")
    print("Environment variables:")
    print("   DISCOVERY_HOST=192.168.1.100:8000  # Discovery server IP")
    print("   DEPLOYMENT_MODE=lan")
    print("   # Services will auto-detect their LAN IP")
    
    print("\n3️⃣ WAN/INTERNET DEPLOYMENT")
    print("-" * 30)
    print("Modules running across different networks/internet")
    print("Environment variables:")
    print("   DISCOVERY_HOST=discovery.yourdomain.com:8000")
    print("   DEPLOYMENT_MODE=wan")
    print("   # Services will detect their public IP")
    
    print("\n4️⃣ CONTAINER/DOCKER DEPLOYMENT")
    print("-" * 30)
    print("Modules running in containers")
    print("Environment variables:")
    print("   DISCOVERY_HOST=discovery-service:8000")
    print("   DEPLOYMENT_MODE=container")
    print("   # Services will use container hostname IP")
    
    print("\n5️⃣ EXPLICIT IP CONFIGURATION")
    print("-" * 30)
    print("Manually specify the IP for each service")
    print("Environment variables:")
    print("   DISCOVERY_HOST=192.168.1.100:8000")
    print("   SERVICE_IP=192.168.1.101  # Force this specific IP")
    print("   # Overrides all auto-detection")
    
    print("\n6️⃣ MIXED ENVIRONMENT")
    print("-" * 30)
    print("Auto-detection based on discovery server location")
    print("Environment variables:")
    print("   DISCOVERY_HOST=<discovery-server>:8000")
    print("   DEPLOYMENT_MODE=auto  # (default)")
    print("   # System will auto-detect best IP strategy")
    

def create_env_file(deployment_type: str, discovery_host: str = "localhost:8000", service_ip: str = None):
    """Create a .env file for a specific deployment type"""
    
    env_content = f"# RelatorDiscovery Configuration\n"
    env_content += f"# Deployment Type: {deployment_type.upper()}\n\n"
    env_content += f"DISCOVERY_HOST={discovery_host}\n"
    
    if deployment_type == "same_machine":
        env_content += "DEPLOYMENT_MODE=localhost\n"
    elif deployment_type == "lan":
        env_content += "DEPLOYMENT_MODE=lan\n"
    elif deployment_type == "wan":
        env_content += "DEPLOYMENT_MODE=wan\n"
    elif deployment_type == "container":
        env_content += "DEPLOYMENT_MODE=container\n"
    elif deployment_type == "explicit":
        env_content += f"SERVICE_IP={service_ip or '192.168.1.101'}\n"
    else:
        env_content += "DEPLOYMENT_MODE=auto\n"
    
    env_content += "\n# Optional: Override specific module hosts (legacy mode)\n"
    env_content += "# MODULE_B_HOST=localhost:50052\n"
    env_content += "# MODULE_C_HOST=localhost:50053\n"
    env_content += "# MODULE_D_HOST=localhost:50054\n"
    
    filename = f".env.{deployment_type}"
    with open(filename, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created {filename}")
    return filename


def test_network_connectivity(discovery_host: str):
    """Test connectivity to discovery server"""
    import requests
    
    try:
        response = requests.get(f"http://{discovery_host}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Successfully connected to discovery server at {discovery_host}")
            result = response.json()
            print(f"   Status: {result.get('status')}")
            print(f"   Total services: {result.get('total_services')}")
            return True
        else:
            print(f"❌ Discovery server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to discovery server at {discovery_host}: {e}")
        return False


def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        show_deployment_configurations()
        print(f"\n💡 Usage:")
        print(f"  {sys.argv[0]} create <type> [discovery_host] [service_ip]")
        print(f"  {sys.argv[0]} test <discovery_host>")
        print(f"\nTypes: same_machine, lan, wan, container, explicit, auto")
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        if len(sys.argv) < 3:
            print("❌ Please specify deployment type")
            return
        
        deployment_type = sys.argv[2].lower()
        discovery_host = sys.argv[3] if len(sys.argv) > 3 else "localhost:8000"
        service_ip = sys.argv[4] if len(sys.argv) > 4 else None
        
        env_file = create_env_file(deployment_type, discovery_host, service_ip)
        print(f"\n💡 To use this configuration:")
        print(f"   cp {env_file} .env")
        
    elif command == "test":
        if len(sys.argv) < 3:
            print("❌ Please specify discovery host")
            return
        
        discovery_host = sys.argv[2]
        test_network_connectivity(discovery_host)
    
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main() 
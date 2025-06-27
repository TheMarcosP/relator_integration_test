#!/usr/bin/env python3
"""
Discovery Service CLI Tool
Simple command-line interface for testing and interacting with the discovery service
"""

import argparse
import json
import sys
from discovery.client import (
    register_service,
    discover_service,
    get_service_endpoint,
    list_all_services,
    unregister_service,
    DiscoveryError
)
from scripts.discovery_utils import get_local_ip

def cmd_register(args):
    """Register a service"""
    try:
        result = register_service(
            discovery_host=args.discovery_host,
            service_name=args.name,
            service_host=args.host or get_local_ip(),
            service_port=args.port,
            metadata=json.loads(args.metadata) if args.metadata else None,
            discovery_port=args.discovery_port
        )
        print(f"✅ {result['message']}")
        print(f"   Endpoint: {result['endpoint']}")
    except DiscoveryError as e:
        print(f"❌ Registration failed: {e}")
        sys.exit(1)

def cmd_discover(args):
    """Discover a service"""
    try:
        result = discover_service(
            discovery_host=args.discovery_host,
            service_name=args.name,
            discovery_port=args.discovery_port
        )
        print(f"🔍 Service '{args.name}' found:")
        print(f"   Endpoint: {result['endpoint']}")
        print(f"   Host: {result['host']}")
        print(f"   Port: {result['port']}")
        if result.get('metadata'):
            print(f"   Metadata: {json.dumps(result['metadata'], indent=2)}")
    except DiscoveryError as e:
        print(f"❌ Discovery failed: {e}")
        sys.exit(1)

def cmd_endpoint(args):
    """Get service endpoint"""
    try:
        endpoint = get_service_endpoint(
            discovery_host=args.discovery_host,
            service_name=args.name,
            discovery_port=args.discovery_port
        )
        print(endpoint)
    except DiscoveryError as e:
        print(f"❌ Failed to get endpoint: {e}")
        sys.exit(1)

def cmd_list(args):
    """List all services"""
    try:
        result = list_all_services(
            discovery_host=args.discovery_host,
            discovery_port=args.discovery_port
        )
        print(f"📋 Found {result['count']} registered services:")
        if result['services']:
            for name, info in result['services'].items():
                print(f"   {name}: {info['endpoint']}")
                if info.get('metadata'):
                    print(f"     Metadata: {json.dumps(info['metadata'], indent=4)}")
        else:
            print("   No services registered")
    except DiscoveryError as e:
        print(f"❌ Failed to list services: {e}")
        sys.exit(1)

def cmd_unregister(args):
    """Unregister a service"""
    try:
        result = unregister_service(
            discovery_host=args.discovery_host,
            service_name=args.name,
            discovery_port=args.discovery_port
        )
        print(f"🗑️  {result['message']}")
    except DiscoveryError as e:
        print(f"❌ Unregistration failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Discovery Service CLI Tool")
    parser.add_argument(
        "--discovery-host", 
        default="localhost", 
        help="Discovery server host (default: localhost)"
    )
    parser.add_argument(
        "--discovery-port", 
        type=int, 
        default=8000, 
        help="Discovery server port (default: 8000)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Register command
    register_parser = subparsers.add_parser("register", help="Register a service")
    register_parser.add_argument("name", help="Service name")
    register_parser.add_argument("port", type=int, help="Service port")
    register_parser.add_argument("--host", help="Service host (auto-detected if not provided)")
    register_parser.add_argument("--metadata", help="Service metadata as JSON string")
    register_parser.set_defaults(func=cmd_register)
    
    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover a service")
    discover_parser.add_argument("name", help="Service name")
    discover_parser.set_defaults(func=cmd_discover)
    
    # Endpoint command
    endpoint_parser = subparsers.add_parser("endpoint", help="Get service endpoint")
    endpoint_parser.add_argument("name", help="Service name")
    endpoint_parser.set_defaults(func=cmd_endpoint)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all services")
    list_parser.set_defaults(func=cmd_list)
    
    # Unregister command
    unregister_parser = subparsers.add_parser("unregister", help="Unregister a service")
    unregister_parser.add_argument("name", help="Service name")
    unregister_parser.set_defaults(func=cmd_unregister)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)

if __name__ == "__main__":
    main() 
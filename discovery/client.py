"""
RelatorDiscovery Client SDK
Simple client for service registration and discovery.
"""

import logging
import socket
import time
import threading
import os
from typing import Dict, Optional, Any, List
import requests
from scripts.utils import get_env_var

logger = logging.getLogger(__name__)


class DiscoveryClient:
    """Client for service registration and discovery"""
    
    def __init__(self, discovery_host: Optional[str] = None):
        self.discovery_host = discovery_host or get_env_var("DISCOVERY_HOST", "localhost:8000")
        self.base_url = f"http://{self.discovery_host}"
        self.service_id: Optional[str] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.heartbeat_interval = 30  # seconds
        self.stop_heartbeat = threading.Event()
        
    def register_service(
        self, 
        name: str, 
        port: int, 
        host: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Register this service with the discovery server
        
        Args:
            name: Service name (e.g., 'module_b')
            port: Service port
            host: Service host (auto-detected if None)
            metadata: Additional service metadata
            
        Returns:
            True if registration successful, False otherwise
        """
        if host is None:
            host = self._get_service_ip()
        
        registration_data = {
            "name": name,
            "host": host,
            "port": port,
            "metadata": metadata or {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/register",
                json=registration_data,
                timeout=10  # Increased timeout for remote servers
            )
            response.raise_for_status()
            
            result = response.json()
            self.service_id = result["service_id"]
            
            logger.info(f"✅ Registered service {name} with discovery server at {self.discovery_host} (id: {self.service_id})")
            logger.info(f"🏠 Service address: {host}:{port}")
            
            # Start heartbeat
            self._start_heartbeat()
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"❌ Failed to register service {name} with discovery server {self.discovery_host}: {e}")
            return False
    
    def discover_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Discover a service by name
        
        Args:
            service_name: Name of service to discover
            
        Returns:
            Service information dict or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/discover/{service_name}",
                timeout=10  # Increased timeout for remote servers
            )
            response.raise_for_status()
            
            service_info = response.json()
            logger.info(f"🔍 Discovered service {service_name} at {service_info['host']}:{service_info['port']}")
            return service_info
            
        except requests.RequestException as e:
            logger.error(f"❌ Failed to discover service {service_name} from {self.discovery_host}: {e}")
            return None
    
    def get_service_address(self, service_name: str) -> Optional[str]:
        """
        Get service address in host:port format
        
        Args:
            service_name: Name of service
            
        Returns:
            Address string in format "host:port" or None if not found
        """
        service_info = self.discover_service(service_name)
        if service_info:
            return f"{service_info['host']}:{service_info['port']}"
        return None
    
    def get_next_service_address(self, current_module: str) -> Optional[str]:
        """
        Get the next service in the pipeline chain
        
        Args:
            current_module: Current module name
            
        Returns:
            Next service address in format "host:port" or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/pipeline/next/{current_module}",
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            next_service = result["next_service"]
            address = f"{next_service['host']}:{next_service['port']}"
            
            logger.info(f"🔗 Next service for {current_module}: {result['next_module']} at {address}")
            return address
            
        except requests.RequestException as e:
            logger.error(f"❌ Failed to get next service for {current_module}: {e}")
            return None
    
    def unregister_service(self) -> bool:
        """
        Unregister this service
        
        Returns:
            True if successful, False otherwise
        """
        if not self.service_id:
            logger.warning("⚠️ No service_id to unregister")
            return False
        
        # Stop heartbeat first
        self._stop_heartbeat()
        
        try:
            response = requests.delete(
                f"{self.base_url}/unregister/{self.service_id}",
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"🗑️ Unregistered service (id: {self.service_id})")
            self.service_id = None
            return True
            
        except requests.RequestException as e:
            logger.error(f"❌ Failed to unregister service: {e}")
            return False
    
    def _get_service_ip(self) -> str:
        """
        Get the IP address this service should register with.
        Uses multiple strategies based on environment configuration.
        """
        # Strategy 1: Explicit configuration via environment variable
        explicit_ip = get_env_var("SERVICE_IP", None)
        if explicit_ip:
            logger.info(f"🎯 Using explicit SERVICE_IP: {explicit_ip}")
            return explicit_ip
        
        # Strategy 2: Check if we're in a container/special environment
        deployment_mode = get_env_var("DEPLOYMENT_MODE", "auto").lower()
        
        if deployment_mode == "localhost":
            logger.info("🏠 Using localhost mode")
            return "127.0.0.1"
        elif deployment_mode == "container":
            logger.info("🐳 Using container mode")
            return self._get_container_ip()
        elif deployment_mode == "lan":
            logger.info("🌐 Using LAN mode")
            return self._get_lan_ip()
        elif deployment_mode == "wan":
            logger.info("🌍 Using WAN mode")
            return self._get_wan_ip()
        else:
            # Auto-detect mode
            logger.info("🔍 Auto-detecting network configuration")
            return self._auto_detect_ip()
    
    def _auto_detect_ip(self) -> str:
        """Auto-detect the best IP to use"""
        # Try to reach the discovery server and see what interface we use
        try:
            # Parse discovery host to get IP
            discovery_ip = self.discovery_host.split(':')[0]
            
            # If discovery is localhost, use localhost
            if discovery_ip in ['localhost', '127.0.0.1']:
                return "127.0.0.1"
            
            # Try to determine what interface would be used to reach discovery server
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.connect((discovery_ip, 80))
            local_ip = test_socket.getsockname()[0]
            test_socket.close()
            
            logger.info(f"🔍 Auto-detected IP {local_ip} (route to discovery server {discovery_ip})")
            return local_ip
            
        except Exception as e:
            logger.warning(f"⚠️ Auto-detection failed: {e}, falling back to LAN IP")
            return self._get_lan_ip()
    
    def _get_container_ip(self) -> str:
        """Get IP for container environments"""
        try:
            # Try to get hostname IP (works in many container setups)
            hostname = socket.gethostname()
            container_ip = socket.gethostbyname(hostname)
            if not container_ip.startswith('127.'):
                return container_ip
        except Exception:
            pass
        
        # Fallback to LAN IP
        return self._get_lan_ip()
    
    def _get_lan_ip(self) -> str:
        """Get LAN IP address"""
        try:
            # Connect to a well-known address to determine our local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Use Google DNS as target (won't actually connect)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def _get_wan_ip(self) -> str:
        """Get WAN/public IP address"""
        try:
            # Try multiple public IP services
            services = [
                "https://ipv4.icanhazip.com",
                "https://api.ipify.org",
                "https://checkip.amazonaws.com"
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        public_ip = response.text.strip()
                        logger.info(f"🌍 Detected public IP: {public_ip}")
                        return public_ip
                except Exception:
                    continue
            
            logger.warning("⚠️ Could not determine public IP, falling back to LAN IP")
            return self._get_lan_ip()
            
        except Exception:
            return self._get_lan_ip()
    
    def _get_all_network_interfaces(self) -> List[str]:
        """Get all available network interface IPs"""
        interfaces = []
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ip not in interfaces and not ip.startswith('127.'):
                    interfaces.append(ip)
        except Exception:
            pass
        return interfaces
    
    def _start_heartbeat(self):
        """Start heartbeat thread"""
        if not self.service_id:
            return
        
        self.stop_heartbeat.clear()
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        logger.info(f"💓 Started heartbeat for service {self.service_id}")
    
    def _stop_heartbeat(self):
        """Stop heartbeat thread"""
        self.stop_heartbeat.set()
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)
            logger.info("💔 Stopped heartbeat")
    
    def _heartbeat_loop(self):
        """Heartbeat loop with retry logic"""
        consecutive_failures = 0
        max_failures = 3
        
        while not self.stop_heartbeat.wait(self.heartbeat_interval):
            if not self.service_id:
                break
                
            try:
                response = requests.post(
                    f"{self.base_url}/heartbeat/{self.service_id}",
                    timeout=10
                )
                response.raise_for_status()
                consecutive_failures = 0  # Reset failure counter
                logger.debug(f"💓 Heartbeat sent for service {self.service_id}")
                
            except requests.RequestException as e:
                consecutive_failures += 1
                logger.error(f"❌ Heartbeat failed for service {self.service_id}: {e} (failure {consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    logger.error(f"💔 Too many heartbeat failures ({consecutive_failures}), stopping heartbeat")
                    break
    
    def __del__(self):
        """Cleanup on deletion"""
        self._stop_heartbeat()


# Global discovery client instance
_discovery_client: Optional[DiscoveryClient] = None


def get_discovery_client() -> DiscoveryClient:
    """Get or create global discovery client instance"""
    global _discovery_client
    if _discovery_client is None:
        _discovery_client = DiscoveryClient()
    return _discovery_client 
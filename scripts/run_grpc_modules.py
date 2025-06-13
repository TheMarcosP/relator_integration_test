#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import signal
import time
from scripts.logging_config import setup_logger

# print working directory
print("WORKING DIRECTORY: ", os.getcwd())

# Setup logger
logger = setup_logger('run_grpc_modules')

def start_module(module_name):
    module_path = os.path.join(os.getcwd(), f"module_{module_name}", f"module_{module_name}_server.py")
    if not os.path.exists(module_path):
        logger.error(f"Module {module_name} not found at {module_path}")
        return None
    
    logger.info(f"Starting Module {module_name.upper()}...")
    # Use python -m to run the module
    process = subprocess.Popen(
        [sys.executable, "-m", f"module_{module_name}.module_{module_name}_server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def main():
    parser = argparse.ArgumentParser(description='Run gRPC modules')
    parser.add_argument('modules', nargs='+', choices=['a', 'b', 'c'], help='Modules to run (a, b, c)')
    args = parser.parse_args()

    processes = []
    try:
        logger.info(f"Starting modules: {', '.join(args.modules)}")
        for module in args.modules:
            process = start_module(module)
            if process:
                processes.append(process)
                time.sleep(1)  # Give each module time to start up

        logger.info("All modules started. Press Ctrl+C to stop all modules.")
        
        # Monitor processes
        while True:
            for process in processes:
                if process.poll() is not None:
                    logger.error("A module has stopped unexpectedly. Stopping all modules...")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping all modules...")
        for process in processes:
            if process.poll() is None:  # If process is still running
                process.terminate()
                process.wait()
        logger.info("All modules stopped.")

if __name__ == "__main__":
    main() 
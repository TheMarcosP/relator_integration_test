#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import signal
import time
from logging_config import setup_logger

def run_module(module_name):
    """Run a specific module and return its process."""
    module_path = f"module_{module_name}/module_{module_name}_server.py"
    if not os.path.exists(module_path):
        logger.error(f"Module {module_name} not found at {module_path}")
        sys.exit(1)
    
    logger.info(f"Starting Module {module_name.upper()}...")
    process = subprocess.Popen([sys.executable, module_path],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             universal_newlines=True)
    return process

def main():
    parser = argparse.ArgumentParser(description='Run gRPC modules A, B, and C')
    parser.add_argument('modules', nargs='+', choices=['a', 'b', 'c'],
                      help='Modules to run (a, b, c)')
    args = parser.parse_args()

    # Setup logger for the run script
    global logger
    logger = setup_logger('run_script')
    logger.info(f"Starting modules: {', '.join(args.modules)}")

    processes = []
    try:
        # Start each module
        for module in args.modules:
            process = run_module(module)
            processes.append(process)
            # Give each module time to start up
            time.sleep(2)

        logger.info("All modules started. Press Ctrl+C to stop all modules.")
        
        # Monitor output from all processes
        while True:
            for process in processes:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
            
            # Check if any process has ended
            for process in processes:
                if process.poll() is not None:
                    logger.error("A module has stopped unexpectedly. Stopping all modules...")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        logger.info("Stopping all modules...")
        for process in processes:
            if process.poll() is None:  # If process is still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        logger.info("All modules stopped.")

if __name__ == "__main__":
    main() 
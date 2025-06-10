import argparse
import subprocess
import os
from dotenv import load_dotenv
load_dotenv()

def require_env(var):
    try:
        return os.environ[var]
    except KeyError:
        raise RuntimeError(f"Missing required environment variable: {var}")

MODULES = {
    'a': {
        'dir': '.',
        'main': 'module_a.main:app',
        'port_var': 'MODULE_A_PORT',
        'desc': 'Module A (calls Module B)',
        'required_env': ['MODULE_A_PORT', 'MODULE_B_URL']
    },
    'b': {
        'dir': '.',
        'main': 'module_b.main:app',
        'port_var': 'MODULE_B_PORT',
        'desc': 'Module B (calls Module C)',
        'required_env': ['MODULE_B_PORT', 'MODULE_C_URL']
    },
    'c': {
        'dir': '.',
        'main': 'module_c.main:app',
        'port_var': 'MODULE_C_PORT',
        'desc': 'Module C (returns result)',
        'required_env': ['MODULE_C_PORT']
    }
}

def run_module(key):
    mod = MODULES[key]
    # Check required env vars
    for var in mod['required_env']:
        require_env(var)
    port = os.environ[mod['port_var']]
    print(f"Starting {mod['desc']} on port {port}...")
    subprocess.Popen([
        "uvicorn", mod['main'], "--host", "0.0.0.0", "--port", port, "--reload"
    ], cwd=mod['dir'], env=os.environ.copy())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run selected FastAPI modules.")
    parser.add_argument(
        "-m", "--modules",
        nargs='+',
        choices=['a', 'b', 'c'],
        required=True,
        help="Which modules to run (choose any of: a, b, c)"
    )
    args = parser.parse_args()

    print("Using environment variables:")
    for key in args.modules:
        for var in MODULES[key]['required_env']:
            print(f"  {var}: {os.environ.get(var)}")
    print()

    for key in args.modules:
        run_module(key)

    print("All selected modules started. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down.") 
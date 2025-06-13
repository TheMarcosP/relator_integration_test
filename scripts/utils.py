import os
from dotenv import load_dotenv

def get_env_var(name, default):
    """
    Get an environment variable with a default value.
    Reloads environment variables from .env file each time.
    """
    load_dotenv(override=True)  # Reload environment variables
    return os.getenv(name, default) 
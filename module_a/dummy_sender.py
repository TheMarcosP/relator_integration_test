import random
import sys
import os
from datetime import datetime
import time

# Ensure module_a package and project root are on the path
ROOT_DIR = os.path.join(os.path.dirname(__file__), '..')
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from module_a.sender_client import ModuleASenderSync

def generate_event() -> dict:
    """Generate a new random event dictionary each time."""
    event_types = ["user_action", "system_event", "error_log", "status_update"]
    actions = ["button_click", "page_view", "form_submit", "api_call"]
    time.sleep(random.randint(1, 5))
    return {
        "event_type": random.choice(event_types),
        "timestamp": datetime.now().isoformat(),
        "user_id": f"user_{random.randint(1000, 9999)}",
        "action": random.choice(actions),
        "value": str(random.randint(1, 100))
    }

def main():
    print("Starting dummy sender (synchronous)...")

    try:

        with ModuleASenderSync() as sender:
            while True:
                event_dict = generate_event()
                print("\nGenerated event:", event_dict)
                response = sender.send_event(event_dict)
                if response:
                    print("Ack from Module B:", response.message)
                # Sleep 1 second before next iteration
                time.sleep(1)
   
    except KeyboardInterrupt:
        print("\nStopping dummy sender...")

if __name__ == '__main__':
    main() 
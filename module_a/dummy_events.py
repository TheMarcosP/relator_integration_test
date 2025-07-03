"""
Dummy Event Generator for Module A
---------------------------------
Replaces the original `dummy_play_game.py` so you can test the rest of the
pipeline without `gfootball`.  It connects to Module B over gRPC and keeps
pushing simple, randomly‑generated match events once per second.

Run it exactly the same way you used to launch the old sender:

    python -m module_a.dummy_events

(Make sure Module B, C, and D are already running.)
"""

import logging
import os
import signal
import sys
import time
import uuid
from pathlib import Path

import grpc
import json

# Local helpers / stubs -------------------------------------------------------
from scripts.utils import get_env_var  # reloads .env each call
from proto import data_pb2, data_pb2_grpc


# ---------------------------------------------------------------------------
MODULE_B_HOST = get_env_var("MODULE_B_HOST", "localhost:50052")
EVENTS_DIR = Path("./module_a/dummy_events")


def load_events_from_folder() -> list:
    """Load all event JSON files from the events folder."""
    if not EVENTS_DIR.exists():
        raise FileNotFoundError(f"Events directory '{EVENTS_DIR}' not found")
    
    events = []
    json_files = sorted(EVENTS_DIR.glob("*.json"))
    
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in '{EVENTS_DIR}'")
    
    logging.info(f"📁 Loading {len(json_files)} events from {EVENTS_DIR}/")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                event_data = json.load(f)
                
                # Handle case where JSON file contains a JSON string (double-encoded)
                if isinstance(event_data, str):
                    event_data = json.loads(event_data)
                
                # Ensure we have a dictionary
                if not isinstance(event_data, dict):
                    logging.warning(f"⚠️  {json_file.name} doesn't contain a JSON object: {type(event_data)}")
                    continue
                
                events.append(event_data)
                logging.debug(f"✅ Loaded {json_file.name}")
        except Exception as e:
            logging.warning(f"⚠️  Could not load {json_file.name}: {e}")
    
    logging.info(f"🎉 Successfully loaded {len(events)} events")
    return events

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[Module A] %(asctime)s - %(levelname)s - %(message)s",
    )

    logging.info("🔌 Connecting to Module B at %s…", MODULE_B_HOST)
    channel = grpc.insecure_channel(MODULE_B_HOST)
    stub = data_pb2_grpc.ModuleBStub(channel)

    # Graceful Ctrl‑C shutdown ------------------------------------------------
    def _sigint_handler(sig, frame):
        logging.info("👋 Dummy event generator stopped – bye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint_handler)
    
    # Load events from folder
    try:
        events = load_events_from_folder()
    except Exception as e:
        logging.error(f"❌ Failed to load events: {e}")
        sys.exit(1)
    
    event_index = 0
    # Main loop --------------------------------------------------------------
    while True:
        # Get current event (cycle through all events)
        current_event = events[event_index % len(events)]
        json_str = json.dumps(current_event, ensure_ascii=False)

        evt = data_pb2.Event(
            id   = str(uuid.uuid4()),
            data = json_str
        )
        # Show abbreviated event info for cleaner logs
        event_type = current_event.get("type", "unknown")
        match_time = current_event.get("match_time", "??:??")
        logging.info("⚽ Sending event %d/%d [%s at %s] » %s", 
                    event_index + 1, len(events), event_type, match_time, evt.id)
        try:
            response = stub.ProcessEvent(evt)  # BasicResponse is ignored
            status = getattr(response, "status", "ok")
            logging.info("✅ Module B ack: %s", status)
        except grpc.RpcError as exc:
            logging.error("❌ gRPC error to Module B: %s", exc)
        event_index += 1
        time.sleep(3.0)  # Only when using dummy events (for testing) 


if __name__ == "__main__":
    main()

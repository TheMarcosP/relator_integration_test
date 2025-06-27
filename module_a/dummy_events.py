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
import random
import signal
import sys
import time
import uuid

import grpc

# Local helpers / stubs -------------------------------------------------------
from scripts.utils import get_env_var  # reloads .env each call
from proto import data_pb2, data_pb2_grpc

# ---------------------------------------------------------------------------
MODULE_B_HOST = get_env_var("MODULE_B_HOST", "localhost:50052")

# A small pool of plausible football actions for the dummy feed
ACTIONS = [
    "pase",
    "disparo_al_arco",
    "disparo_desviado",
    "gol",
    "falta",
    "tarjeta_amarilla",
    "tarjeta_roja",
    "corner",
    "saque_de_banda",
    "saque_de_arco",
]


def build_event() -> data_pb2.Event:
    """Create a synthetic `pipeline.Event` message."""
    now_sec = int(time.time())
    minute = (now_sec // 5) % 90  # ≈ 1 match‑minute every 5 real seconds

    return data_pb2.Event(
        id=str(uuid.uuid4()),
        data={
            "minuto": str(minute),
            "equipo": random.choice(["casa", "afuera"]),
            "jugador": f"Jugador {random.randint(1, 11)}",
            "accion": random.choice(ACTIONS),
        },
    )


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

    # Main loop --------------------------------------------------------------
    while True:
        evt = build_event()
        logging.info("⚽ Sending event %s » %s", evt.id, dict(evt.data))
        try:
            response = stub.ProcessEvent(evt)  # BasicResponse is ignored
            status = getattr(response, "status", "ok")
            logging.info("✅ Module B ack: %s", status)
        except grpc.RpcError as exc:
            logging.error("❌ gRPC error to Module B: %s", exc)

        time.sleep(10.0)  # 1 event per second


if __name__ == "__main__":
    main()
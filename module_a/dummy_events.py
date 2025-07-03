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
import json

# Local helpers / stubs -------------------------------------------------------
from scripts.utils import get_env_var  # reloads .env each call
from proto import data_pb2, data_pb2_grpc
from google.protobuf.struct_pb2 import Struct


# ---------------------------------------------------------------------------
MODULE_B_HOST = get_env_var("MODULE_B_HOST", "localhost:50052")


events = [{
    "event_id": 1,
    "match_time": "00:00",
    "type": "start_of_match",
    "match_metadata": {
        "date": "2022-12-18",
        "time": "12:00",
        "stadium": "Lusail Stadium",
        "city": "Lusail",
        "country": "Qatar",
        "competition": "FIFA World Cup Final",
        "weather": {
            "temperature": "25\u00b0C",
            "humidity": "60%",
            "condition": "Clear"
        },
        "referee": {
            "name": "Sandro Ricci",
            "country": "Brazil",
            "assistant_referees": [
                "Marcelo Van Gasse (Brazil)",
                "Anderson Daronco (Brazil)"
            ],
            "fourth_official": "Abdulrahman Al-Jassim (Qatar)",
            "video_assistant_referee": "Massimiliano Irrati (Italy)"
        },
        "left_team": {
            "name": "Argentina",
            "short_name": "ARG",
            "colors": "blue and white",
            "formation": "4-3-3",
            "coach": "Lionel Scaloni",
            "captain": "Lionel Messi",
            "nickname": "La Albiceleste",
            "players": [
                {
                    "first_name": "Emiliano",
                    "last_name": "Martinez",
                    "nickname": "Dibu",
                    "number": 23,
                    "short_position": "GK",
                    "position": "Goalkeeper"
                },
                {
                    "first_name": "Nicolas",
                    "last_name": "Tagliafico",
                    "nickname": "Nico",
                    "number": 3,
                    "short_position": "LB",
                    "position": "Left Back"
                },
                {
                    "first_name": "Cristian",
                    "last_name": "Romero",
                    "nickname": "Cuti",
                    "number": 13,
                    "short_position": "CB",
                    "position": "Centre Back"
                },
                {
                    "first_name": "Nicolas",
                    "last_name": "Otamendi",
                    "nickname": "General",
                    "number": 19,
                    "short_position": "CB",
                    "position": "Centre Back"
                },
                {
                    "first_name": "Nahuel",
                    "last_name": "Molina",
                    "nickname": "Nahuel",
                    "number": 26,
                    "short_position": "RB",
                    "position": "Right Back"
                },
                {
                    "first_name": "Alexis",
                    "last_name": "Mac Allister",
                    "nickname": "Alexis",
                    "number": 20,
                    "short_position": "CM",
                    "position": "Central Midfielder"
                },
                {
                    "first_name": "Enzo",
                    "last_name": "Fernandez",
                    "nickname": "Enzo",
                    "number": 24,
                    "short_position": "CM",
                    "position": "Central Midfielder"
                },
                {
                    "first_name": "Rodrigo",
                    "last_name": "De Paul",
                    "nickname": "Rodri",
                    "number": 7,
                    "short_position": "CM",
                    "position": "Central Midfielder"
                },
                {
                    "first_name": "Angel",
                    "last_name": "Di Maria",
                    "nickname": "Fideo",
                    "number": 11,
                    "short_position": "LM",
                    "position": "Left Midfielder"
                },
                {
                    "first_name": "Julian",
                    "last_name": "Alvarez",
                    "nickname": "Ara\u00f1a",
                    "number": 9,
                    "short_position": "CF",
                    "position": "Centre Forward"
                },
                {
                    "first_name": "Lionel",
                    "last_name": "Messi",
                    "nickname": "La Pulga",
                    "number": 10,
                    "short_position": "RM",
                    "position": "Right Midfielder"
                }
            ]
        },
        "right_team": {
            "name": "France",
            "short_name": "FRA",
            "colors": "blue, white and red",
            "formation": "4-2-3-1",
            "coach": "Didier Deschamps",
            "captain": "Hugo Lloris",
            "nickname": "Les Bleus",
            "players": [
                {
                    "first_name": "Hugo",
                    "last_name": "Lloris",
                    "nickname": "Hugo",
                    "number": 1,
                    "short_position": "GK",
                    "position": "Goalkeeper"
                },
                {
                    "first_name": "Theo",
                    "last_name": "Hernandez",
                    "nickname": "Theo",
                    "number": 22,
                    "short_position": "LB",
                    "position": "Left Back"
                },
                {
                    "first_name": "Raphael",
                    "last_name": "Varane",
                    "nickname": "Rapha",
                    "number": 4,
                    "short_position": "CB",
                    "position": "Centre Back"
                },
                {
                    "first_name": "Dayot",
                    "last_name": "Upamecano",
                    "nickname": "Upa",
                    "number": 18,
                    "short_position": "CB",
                    "position": "Centre Back"
                },
                {
                    "first_name": "Jules",
                    "last_name": "Kounde",
                    "nickname": "Jules",
                    "number": 5,
                    "short_position": "RB",
                    "position": "Right Back"
                },
                {
                    "first_name": "Aurelien",
                    "last_name": "Tchouameni",
                    "nickname": "Tchou",
                    "number": 8,
                    "short_position": "CM",
                    "position": "Central Midfielder"
                },
                {
                    "first_name": "Adrien",
                    "last_name": "Rabiot",
                    "nickname": "Adrien",
                    "number": 14,
                    "short_position": "CM",
                    "position": "Central Midfielder"
                },
                {
                    "first_name": "Antoine",
                    "last_name": "Griezmann",
                    "nickname": "Grizi",
                    "number": 7,
                    "short_position": "CM",
                    "position": "Central Midfielder"
                },
                {
                    "first_name": "Kylian",
                    "last_name": "Mbappe",
                    "nickname": "Kyky",
                    "number": 10,
                    "short_position": "LM",
                    "position": "Left Midfielder"
                },
                {
                    "first_name": "Olivier",
                    "last_name": "Giroud",
                    "nickname": "Oli",
                    "number": 9,
                    "short_position": "CF",
                    "position": "Centre Forward"
                },
                {
                    "first_name": "Ousmane",
                    "last_name": "Dembele",
                    "nickname": "Dembouz",
                    "number": 11,
                    "short_position": "RM",
                    "position": "Right Midfielder"
                }
            ]
        }
    }
},{
    "event_id": 2,
    "match_time": "01:17",
    "type": "ball_possession_change",
    "subtype": "different_team",
    "current_team": "France",
    "previous_team": "Argentina",
    "current_player": {
        "first_name": "Kylian",
        "last_name": "Mbappe",
        "nickname": "Kyky",
        "number": 10,
        "short_position": "LM",
        "position": "Left Midfielder"
    },
    "previous_player": {
        "first_name": "Nicolas",
        "last_name": "Tagliafico",
        "nickname": "Nico",
        "number": 3,
        "short_position": "LB",
        "position": "Left Back"
    },
    "location": "center_middle"
},
{
    "event_id": 3,
    "match_time": "01:44",
    "type": "ball_possession_change",
    "subtype": "same_team",
    "current_team": "France",
    "previous_team": "France",
    "current_player": {
        "first_name": "Ousmane",
        "last_name": "Dembele",
        "nickname": "Dembouz",
        "number": 11,
        "short_position": "RM",
        "position": "Right Midfielder"
    },
    "previous_player": {
        "first_name": "Kylian",
        "last_name": "Mbappe",
        "nickname": "Kyky",
        "number": 10,
        "short_position": "LM",
        "position": "Left Midfielder"
    },
    "location": "center_middle"
},{
    "event_id": 4,
    "match_time": "02:46",
    "type": "ball_possession_change",
    "subtype": "different_team",
    "current_team": "Argentina",
    "previous_team": "France",
    "current_player": {
        "first_name": "Angel",
        "last_name": "Di Maria",
        "nickname": "Fideo",
        "number": 11,
        "short_position": "LM",
        "position": "Left Midfielder"
    },
    "previous_player": {
        "first_name": "Ousmane",
        "last_name": "Dembele",
        "nickname": "Dembouz",
        "number": 11,
        "short_position": "RM",
        "position": "Right Midfielder"
    },
    "location": "right_bottom"
}]

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
    num_events = 0
    # Main loop --------------------------------------------------------------
    while True:
        # evt = str(events[0])
        json_str = json.dumps(events[num_events % len(events)], ensure_ascii=False)

        evt = data_pb2.Event(
            id   = str(uuid.uuid4()),
            data = json_str
        )
        logging.info("⚽ Sending event %s » %s", evt.id, evt.data)
        try:
            response = stub.ProcessEvent(evt)  # BasicResponse is ignored
            status = getattr(response, "status", "ok")
            logging.info("✅ Module B ack: %s", status)
        except grpc.RpcError as exc:
            logging.error("❌ gRPC error to Module B: %s", exc)
        num_events += 1
        time.sleep(3.0)  # 1 event per second


if __name__ == "__main__":
    main()

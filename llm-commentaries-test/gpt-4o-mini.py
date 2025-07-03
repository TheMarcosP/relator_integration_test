from openai import AzureOpenAI
import asyncio
import random
import time
from fetch_api_keys import parse_settings

# ─── CONFIG ──────────────────────────────────────────────────
API_KEYS_TXT = "llm-commentaries-test/api_keys_azure.txt"
cfg = parse_settings(API_KEYS_TXT)
API_KEY     = cfg["API_KEY"]
ENDPOINT    = cfg["ENDPOINT"]
DEPLOYMENT = "gpt-4o-mini-ignacio"

azure_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=ENDPOINT,
    api_key=API_KEY
)

# -------------------------------------
# 2) Define mock-feed of football events
# -------------------------------------
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

def build_event():
    """Create a synthetic Event dict."""
    now_sec = int(time.time())
    minuto = (now_sec // 5) % 90  # ~1 match-min every 5s
    return {
        "minuto": str(minuto),
        "equipo": random.choice(["casa", "afuera"]),
        "jugador": f"Jugador {random.randint(1, 11)}",
        "accion": random.choice(ACTIONS),
    }

# -------------------------------------
# 3) System prompt: live football commentator
# -------------------------------------
system_prompt = (
    "Eres un comentarista de fútbol EN TIEMPO REAL. "
    "Tu tarea es generar comentarios CORTOS y PRECISOS basados en cada evento recibido, "
    "con un estilo auténticamente argentino (como Mariano Closs). "
    "Siempre responde en español."
)

# -------------------------------------
# 4) Stream events and get LLM replies
# -------------------------------------
max_comments = 10  # Limit to avoid infinite loop in this example
total_time = 0.0
while True:
    # 4.1 build a new mock event
    evt = build_event()
    
    user_msg = (
        f"Minuto {evt['minuto']}, "
        f"el {evt['jugador']} del equipo {evt['equipo']} "
        f"realiza un {evt['accion']}. Comenta:"
    )
    print(f"[Evento] {user_msg}")
    start = time.time()
    # 4.2 call the model
    response = azure_client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=50,
        temperature=0.7,
        top_p=0.9,
    )
    end = time.time()
    # 4.3 print event + commentary
    comment = response.choices[0].message.content.strip()
    time_taken = end - start
    total_time += time_taken
    print(f"[Comentarista] {comment}\n")
    print(f"Tiempo de respuesta: {time_taken:.2f} segundos")
    print(f"Tokens generados: {response.usage.total_tokens}")

    print("-" * 80)
    # 4.4 delay to simulate real-time
    max_comments -= 1
    if max_comments <= 0:
        break

    time.sleep(3.0)

print(f"Tiempo total de generación: {total_time:.2f} segundos")
print(f"Comentarios generados: {10 - max_comments}")
print(f"Tiempo promedio por comentario: {total_time / (10 - max_comments):.2f} segundos")
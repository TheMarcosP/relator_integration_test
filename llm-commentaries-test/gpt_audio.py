import time
import base64
import os
from openai import AzureOpenAI
from fetch_api_keys import parse_settings

# ─── CONFIG ──────────────────────────────────────────────────
API_KEYS_TXT = "llm-commentaries-test/api_keys_azure.txt"
cfg = parse_settings(API_KEYS_TXT)
API_KEY     = cfg["API_KEY"]
ENDPOINT    = cfg["ENDPOINT"]
DEPLOYMENT  = "gpt-4o-mini-audio-preview"
API_VERSION = "2025-01-01-preview"

print(
    f"Using API_KEY: {API_KEY[:5]}… (truncated)\n"
    f"Using ENDPOINT: {ENDPOINT}\n"
    f"Using MODEL: {DEPLOYMENT}\n"
)

# https://football-commentator.openai.azure.com/openai/realtime?api-version=2024-10-01-preview&deployment=gpt-4o-mini-realtime-preview

# System prompt for all calls
SYSTEM_PROMPT = (
    "Eres un comentarista de fútbol EN TIEMPO REAL. "
    "Tu tarea es relatar comentarios CORTOS y PRECISOS basados en cada comentario recibido, "
    "con un estilo auténticamente argentino (como Mariano Closs). "
    "NO tenes que alterar nada de los comentarios que te llegan, solo debes generar un audio con el comentario y responder lo más rápido posible en tiempo real. "
    "El audio debe durar menos de 15 segundos. "
    "Siempre responde en español."
)

# Your list of raw commentaries
commentaries = [
    "¡Saque de banda para el equipo de casa! El 10 se la da con toda la confianza, busca reactivar el juego. Vamos a ver si logra conectar con un compañero y generar algo de peligro. ¡Atención!",
    # "¡Saque de arco para el equipo! El Jugador 6 se prepara, busca el despeje y tiene que ser preciso. ¡Vamos a ver si puede encontrar a sus compañeros en el medio!",
    # "¡Foul clarísimo del 6! Llegó tarde y se llevó puesto al rival. El árbitro no dudó, tarjeta amarilla en camino. Esto se calienta, hay que tener cuidado...",
    # "¡Corner para el equipo local! El Jugador 7 se prepara para ejecutar. ¡Atención! Puede ser una buena oportunidad para abrir el marcador. ¡Vamos a ver qué sucede!",
    # "¡Qué buen remate del Jugador 4! Se animó desde fuera del área, la colgó de un ángulo, pero el arquero se estiró como un gato y la sacó del ángulo. ¡Gran respuesta!",
    # "¡Y ahí va! Tarjeta amarilla para el Jugador 6 del equipo afuera. Un foul innecesario, le deja al árbitro sin opción. Se le complica el partido, ¡hay que tener cuidado!",
    # "¡Faulazo del Jugador 2! Se pasó de rosca y le dejó un regalito al rival. Tarjeta amarilla en camino, esto se calienta.",
    # "¡Saque de arco para el equipo local! El Jugador 7 se prepara, hay que aprovechar este momento para reorganizarse. ¡Vamos a ver si logra encontrar a un compañero!",
    # "¡Uy! El 10 se animó y sacó un bombazo, pero se fue desviado. Tenía el arco a su disposición, le faltó puntería. ¡Hay que seguir buscando!"
]

# ─── CLIENT SETUP ───────────────────────────────────────────
client = AzureOpenAI(
    api_key=API_KEY,
    azure_endpoint=ENDPOINT,
    api_version=API_VERSION
)

# ─── LOOP & MEASURE LATENCY ─────────────────────────────────
latencies = []

for idx, text in enumerate(commentaries, start=1):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": text}
    ]
    start = time.perf_counter()
    completion = client.chat.completions.create(
        model=DEPLOYMENT,
        modalities=["text","audio"],
        audio={"voice":"fable","format":"wav"},
        messages=messages
    )
    elapsed = time.perf_counter() - start

    # record latency
    latencies.append(elapsed)
    print(f"Commentary #{idx} took {elapsed*1000:.0f} ms")

    # decode and save audio
    audio_b64 = completion.choices[0].message.audio.data
    wav = base64.b64decode(audio_b64)
    out_fname = f"llm-commentaries-test/ouput_audio/commentary_{idx:02d}n.wav"
    with open(out_fname, "wb") as f:
        f.write(wav)

# ─── SUMMARY ─────────────────────────────────────────────────
print("\nAll done!")
for i, t in enumerate(latencies, start=1):
    print(f"  #{i}: {t*1000:.0f} ms")

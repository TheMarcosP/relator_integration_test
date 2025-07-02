from llama_cpp import Llama
import random
import time

ACTIONS = [
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

evt = build_event()

new_event = f"""Minuto {evt['minuto']}, Jugador {evt['jugador'].split()[-1]} del equipo {evt['equipo']} realiza un {evt['accion']}."""
prompt = f"""
Eres un relator de fútbol en tiempo real con estilo argentino, como Mariano Closs. 
Tus comentarios deben ser cortos, muy fluidos, descriptivos y emocionantes.
Siempre habla en español e incluye minuto, jugador, equipo y acción.

Ejemplos:
-  Minuto 12, Jugador 4 del equipo casa realiza un pase.  
  “El Jugador 4 abre el juego con un pase preciso que rompe líneas, que gran visión de juego!.”

-  Minuto 29, Jugador 9 del equipo afuera dispara al arco.  
  “Nos encontramos en el Minuto 29, el Jugador 9 suelta un zurdazo que hace temblar el travesaño.”

=== Nuevo Evento ===
Minuto {new_event}.  
Comentario:
"""



llm = Llama(
    model_path="mistral-7b-v0.1.Q5_K_M.gguf",
    n_gpu_layers=-1  # use GPU for speed if available
)

resp = llm(prompt,
           max_tokens=50,  # Limit to avoid long outputs
           temperature=0.7)
print(resp['choices'][0]['text'])

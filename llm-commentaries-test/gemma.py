from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import time
import random
from fetch_api_keys import parse_settings

TOKEN_TXT = "llm-commentaries-test/token_hugging-face.txt"
cfg = parse_settings(TOKEN_TXT)
TOKEN = cfg["TOKEN"]

tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b", use_auth_token=TOKEN)
model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-2b",
    device_map="cuda",
    torch_dtype=torch.bfloat16,
    use_auth_token=TOKEN,
)


# -------------------------------------
# 2) Define mock-feed of football events
# -------------------------------------
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
input_text = prompt
inputs = tokenizer(input_text, return_tensors="pt").to("cuda")

_ = model.generate(**inputs, max_new_tokens=1)


start_time = time.time()
out = model.generate(
    **inputs,
    max_new_tokens=30,   # <-- was 50
    do_sample=True,
    temperature=0.7,
    top_p=0.9,
)
end_time = time.time()

print(f"Generation took {end_time - start_time:.2f} seconds")
print(f"Generated tokens: {out[0].shape[0] - inputs.input_ids.shape[1]}")
text = tokenizer.decode(out[0], skip_special_tokens=True)
comment = text.split("Comentario:")[-1].strip()
print(f"[Evento] {new_event}")
print(f"[Comentarista] {comment}")
import time
import random
import torch
from fetch_api_keys import parse_settings
from transformers import (
    BitsAndBytesConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline
)

# ----------------------------
# 1) Setup your local Mistral 7B
# ----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
if device == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

# Gated “instruct” weights (if you have access) or swap in an open fork:
model_id      = "mistral-7b-v0.1.Q4_K_M.gguf"
sharded_model = "TheBloke/Mistral-7B-v0.1-GGUF"


TOKEN_TXT = "llm-commentaries-test/token_hugging-face.txt"
cfg = parse_settings(TOKEN_TXT)
TOKEN = cfg["TOKEN"]

tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    trust_remote_code=True,
    use_auth_token=TOKEN
)
model = AutoModelForCausalLM.from_pretrained(
    sharded_model,
    trust_remote_code   = True,
    quantization_config = bnb,
    device_map          = "auto",
    use_auth_token      = TOKEN
)

text_gen = pipeline(
    "text-generation",
    model               = model,
    tokenizer           = tokenizer,
    max_new_tokens      = 50,
    temperature         = 0.7,
    top_p               = 0.9,
    repetition_penalty  = 1.1,
    eos_token_id        = tokenizer.eos_token_id,
    pad_token_id        = tokenizer.eos_token_id,
    device_map          = "auto",
)

# Warm-up so first call isn’t slow
_ = text_gen("¡Hola!")

# ----------------------------
# 2) Mock-feed of football events
# ----------------------------
ACTIONS = [
    "pase","disparo_al_arco","disparo_desviado","gol","falta",
    "tarjeta_amarilla","tarjeta_roja","corner","saque_de_banda","saque_de_arco",
]

def build_event():
    now = int(time.time())
    return {
        "minuto": str((now // 5) % 90),
        "equipo": random.choice(["casa","afuera"]),
        "jugador": f"Jugador {random.randint(1,11)}",
        "accion": random.choice(ACTIONS),
    }

# ----------------------------
# 3) System prompt
# ----------------------------
system_prompt = (
    "Eres un comentarista de fútbol EN TIEMPO REAL. "
    "Tu tarea es generar comentarios CORTOS y PRECISOS basados en cada evento recibido, "
    "con un estilo auténticamente argentino (como Mariano Closs). "
    "Siempre responde en español."
)

# ----------------------------
# 4) Stream events with Mistral
# ----------------------------
max_comments = 10
while max_comments:
    evt = build_event()
    user_msg = (
        f"Minuto {evt['minuto']}, el {evt['jugador']} del equipo {evt['equipo']} "
        f"realiza un {evt['accion']}. Comenta:"
    )
    print(f"[Evento]    {user_msg}")

    # build a single prompt combining system + user
    prompt = f"{system_prompt}\n\n{user_msg}"

    # measure
    start = time.time()
    outputs = text_gen(prompt, return_full_text=False)
    latency = time.time() - start

    comment = outputs[0]["generated_text"].strip().split("\n")[0]

    print(f"[Comentarista] {comment}")
    print(f"Tiempo de respuesta: {latency:.2f} s")
    print("-" * 60)

    max_comments -= 1
    time.sleep(1.0)

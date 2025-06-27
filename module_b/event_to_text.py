import os
import time
import logging
from openai import AzureOpenAI
from proto import data_pb2  # type: ignore

logger = logging.getLogger(__name__)

class EventToText:
    """NLP processing: converts events to a comment about the game"""

    def __init__(self,
                 api_key: str = None,
                 endpoint: str = None,
                 deployment: str = None,
                 max_tokens: int = 50,
                 temperature: float = 0.7,
                 top_p: float = 0.9):
        # Load configuration from env if not provided
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p

        if not all([self.api_key, self.endpoint, self.deployment]):
            raise ValueError("Azure OpenAI API key, endpoint, and deployment must be set")

        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version="2024-12-01-preview"
        )

        # System prompt to guide the model
        self.system_prompt = (
            "Eres un comentarista de fútbol EN TIEMPO REAL. "
            "Tu tarea es generar comentarios CORTOS y PRECISOS basados en cada evento recibido, "
            "con un estilo auténticamente argentino (como Mariano Closs). "
            "Siempre responde en español."
        )

    def process(self, event: data_pb2.Event) -> str:
        """Process incoming Event and return commentary string."""
        # Extract event fields
        data = event.data
        minuto = data.get("minuto", "?") # Default to "?" if not present
        equipo = data.get("equipo", "?")
        jugador = data.get("jugador", "?")
        accion = data.get("accion", "?")

        # Build user message
        user_msg = (
            f"Minuto {minuto}, el {jugador} del equipo {equipo} "
            f"realiza un {accion}. Comenta:"
        )

        # Call Azure OpenAI
        start = time.time()
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        latency = time.time() - start

        # Extract comment
        comment = response.choices[0].message.content.strip()

        # Log metrics
        logger.debug(
            "[Module B] Processed event %s in %.2f s (tokens: %s)",
            event.id,
            latency,
            getattr(response.usage, 'total_tokens', None)
        )

        return comment
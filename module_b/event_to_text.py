import os
import time
import logging
from openai import AzureOpenAI
from proto import data_pb2  # type: ignore
from typing import List

logger = logging.getLogger(__name__)

class EventToText:
    """NLP processing: converts batches of events to game commentary"""

    def __init__(self,
                 api_key: str = None,
                 endpoint: str = None,
                 deployment: str = None,
                 max_tokens: int = 150,  # Increased for batch processing
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

        # System prompt for batch processing
        self.system_prompt = (
            "Eres un comentarista de fútbol EN TIEMPO REAL con estilo argentino como Mariano Closs. "
            "Recibirás varios eventos del juego que ocurrieron en los últimos segundos. "
            "Tu tarea es crear un relato FLUIDO y NATURAL que conecte estos eventos, "
            "contando la historia de lo que está pasando en el partido. "
            "Genera un comentario CORTO pero EMOCIONANTE (máximo 2-3 oraciones). "
            "Siempre responde en español y mantén el ritmo dinámico del fútbol."
        )

    def process_batch(self, events: List[data_pb2.Event]) -> str:
        """Process a batch of events and return a cohesive commentary string."""
        if not events:
            return ""

        # Sort events by timestamp if available, or by order received
        # For now, we'll process them in the order received
        
        # Build the context from all events
        event_descriptions = []
        for event in events:
            data = event.data
            minuto = data.get("minuto", "?")
            equipo = data.get("equipo", "?") 
            jugador = data.get("jugador", "?")
            accion = data.get("accion", "?")
            
            event_desc = f"Minuto {minuto}: {jugador} ({equipo}) - {accion}"
            event_descriptions.append(event_desc)

        # Create user message with all events
        if len(events) == 1:
            user_msg = (
                f"Evento del juego:\n{event_descriptions[0]}\n\n"
                "Genera un comentario dinámico sobre esta acción:"
            )
        else:
            events_text = "\n".join(event_descriptions)
            user_msg = (
                f"Secuencia de eventos del juego:\n{events_text}\n\n"
                f"Genera un relato fluido que conecte estos {len(events)} eventos "
                "y capture la emoción del momento:"
            )

        # Call Azure OpenAI
        start = time.time()
        try:
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
            logger.info(
                "[Module B] Processed batch of %d events in %.2f s (tokens: %s)",
                len(events),
                latency,
                getattr(response.usage, 'total_tokens', None)
            )

            return comment

        except Exception as e:
            logger.error(f"Error processing batch of {len(events)} events: {str(e)}")
            return ""

    def process(self, event: data_pb2.Event) -> str:
        """Legacy method - process single event (kept for compatibility)."""
        return self.process_batch([event])
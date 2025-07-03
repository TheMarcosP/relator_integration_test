import os
import time
import logging
import json
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
                 max_tokens: int = 50,  # Increased for batch processing
                 temperature: float = 0.7,
                 top_p: float = 0.9):
        # Load configuration from env if not provided
        self.api_key = api_key or os.getenv("API_KEY")
        self.endpoint = endpoint or os.getenv("ENDPOINT")
        self.deployment = deployment or os.getenv("DEPLOYMENT")
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
            "Recibirás eventos del juego en formato JSON. "
            "Tu tarea es crear un pequeño relato FLUIDO y NATURAL que conecte estos eventos, "
            "contando la brevemente de lo que está sucediendo en el partido. "
            "Genera un comentario MUY MUY MUY CORTO pero EMOCIONANTE (máximo 1 oración). "
            "Siempre responde en español y mantén el ritmo dinámico del fútbol."
        )

        # Special system prompt for match start
        self.start_match_prompt = (
            "Eres un comentarista de fútbol profesional con estilo argentino como Mariano Closs. "
            "Recibirás los metadatos de inicio de un partido de fútbol en formato JSON. "
            "Tu tarea es hacer una PRESENTACIÓN EMOCIONANTE del partido que está por comenzar. "
            "Incluye: saludo inicial, presentación de los equipos, estadio, competición, y algún dato relevante. "
            "Genera una introducción CAUTIVANTE pero MUY MUY MUY CORTA (máximo 2-3 oraciones). "
            "Usa un tono profesional pero apasionado, típico del fútbol argentino. "
            "Siempre responde en español."
        )

    def process_start_of_match(self, event: data_pb2.Event) -> str:
        """Process the special start_of_match event with detailed introduction."""
        # Convert the event data to JSON string for the LLM
        event_json = json.loads(event.data)
        
        user_msg = (
            "Datos del partido que está por comenzar:\n\n"
            f"{event_json}\n\n"
            "Genera una presentación emocionante para el inicio de este partido de fútbol:"
        )

        # Call Azure OpenAI with special prompt
        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.start_match_prompt},
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
                "[Module B] Processed start_of_match event in %.2f s (tokens: %s)",
                latency,
                getattr(response.usage, 'total_tokens', None)
            )

            return comment

        except Exception as e:
            logger.error(f"Error processing start_of_match event: {str(e)}")
            return ""

    def process_batch(self, events: List[data_pb2.Event]) -> str:
        """Process a batch of events and return a cohesive commentary string."""
        if not events:
            return ""

        # Convert events to JSON strings instead of parsing them
        events_json_list = []
        for event in events:
            # event_json = json.loads(event.data)
            events_json_list.append(event.data)

        # Create user message with raw JSON events
        if len(events) == 1:
            user_msg = (
                f"Evento del juego:\n\n{events_json_list[0]}\n\n"
                "Genera un comentario dinámico sobre esta acción:"
            )
        else:
            events_text = "\n\n---\n\n".join(events_json_list)
            user_msg = (
                f"Secuencia de {len(events)} eventos del juego:\n\n{events_text}\n\n"
                "Genera un relato fluido que conecte estos eventos y capture la emoción del momento:"
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
            # Log prompt
            
            return comment

        except Exception as e:
            logger.error(f"Error processing batch of {len(events)} events: {str(e)}")
            return ""

    def process(self, event: data_pb2.Event) -> str:
        """Legacy method - process single event (kept for compatibility)."""
        return self.process_batch([event])
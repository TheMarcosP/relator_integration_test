import os
import time
import logging
import json
from datetime import datetime
from pathlib import Path
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

        # Conversation history - keep last 5 exchanges (10 messages)
        self.conversation_history = []
        self.max_history_exchanges = 5

        # Debug logging setup
        self.debug_dir = Path("debug_llm_calls")
        self.debug_dir.mkdir(exist_ok=True)
        self.call_counter = 0

        # System prompt for batch processing
        self.system_prompt = (
            "Eres un comentarista de fútbol EN TIEMPO REAL con estilo argentino como Mariano Closs. "
            "Recibirás eventos del juego en formato JSON. "
            "Tu tarea es crear un pequeño relato FLUIDO y NATURAL que conecte estos eventos, "
            "Genera un comentario MUY MUY MUY CORTO pero EMOCIONANTE de lo más importante que ocurrió en los ultimos eventos (máximo 1 oración breve). "
            "Siempre responde en español y mantén el ritmo dinámico del fútbol. "
            "Variar entre usar el last_name y el nickname del jugador."
            "Cuando no ocurre nada, nombrar al jugador que tiene la pelota. Como por ejemplo: 'La tiene Messi', o simplemente 'Messi'." 
            "No repetirse con los comentarios de eventos anteriores."
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

    def _add_to_conversation(self, user_message: str, assistant_message: str):
        """Add a user-assistant exchange to conversation history."""
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        # Keep only last N exchanges (N*2 messages)
        max_messages = self.max_history_exchanges * 2
        if len(self.conversation_history) > max_messages:
            self.conversation_history = self.conversation_history[-max_messages:]

    def _build_messages(self, system_prompt: str, user_message: str) -> List[dict]:
        """Build the complete message list with system prompt and conversation history."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_message})
        return messages

    def _save_debug_call(self, call_type: str, messages: List[dict], response_content: str, latency: float):
        """Save LLM call details to debug file."""
        self.call_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llm_call_{self.call_counter:03d}_{call_type}.json"
        
        # Process messages to make embedded JSON readable
        readable_messages = []
        for msg in messages:
            readable_msg = msg.copy()
            if msg["role"] == "user" and ("evento del juego:" in msg["content"].lower() or "eventos del juego:" in msg["content"].lower()):
                readable_msg["content_formatted"] = self._format_user_content(msg["content"])
            readable_messages.append(readable_msg)
        
        debug_data = {
            "timestamp": timestamp,
            "call_number": self.call_counter,
            "call_type": call_type,
            "latency_seconds": latency,
            "messages_sent": readable_messages,
            "response_content": response_content,
            "conversation_history_length": len(self.conversation_history)
        }
        
        debug_file = self.debug_dir / filename
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"💾 Saved debug call to {filename}")

    def _format_user_content(self, content: str) -> dict:
        """Format user content to make embedded JSON events readable."""
        try:
            lines = content.split('\n')
            formatted_content = {
                "instruction": "",
                "events": [],
                "request": ""
            }
            
            current_section = "instruction"
            current_event_json = ""
            
            for line in lines:
                if line.strip().startswith('{"event_id"'):
                    if current_event_json:
                        # Parse previous event
                        try:
                            event_data = json.loads(current_event_json)
                            formatted_content["events"].append(event_data)
                        except:
                            formatted_content["events"].append({"raw": current_event_json})
                    current_event_json = line.strip()
                    current_section = "events"
                elif line.strip() == "---":
                    if current_event_json:
                        # Parse current event
                        try:
                            event_data = json.loads(current_event_json)
                            formatted_content["events"].append(event_data)
                        except:
                            formatted_content["events"].append({"raw": current_event_json})
                        current_event_json = ""
                elif line.strip().startswith("Genera un relato"):
                    if current_event_json:
                        # Parse last event
                        try:
                            event_data = json.loads(current_event_json)
                            formatted_content["events"].append(event_data)
                        except:
                            formatted_content["events"].append({"raw": current_event_json})
                        current_event_json = ""
                    formatted_content["request"] = line.strip()
                    current_section = "request"
                elif current_section == "instruction":
                    formatted_content["instruction"] += line + "\n"
            
            # Handle last event if exists
            if current_event_json:
                try:
                    event_data = json.loads(current_event_json)
                    formatted_content["events"].append(event_data)
                except:
                    formatted_content["events"].append({"raw": current_event_json})
            
            formatted_content["instruction"] = formatted_content["instruction"].strip()
            return formatted_content
            
        except Exception as e:
            return {"error": f"Failed to format content: {e}", "raw_content": content}

    def process_start_of_match(self, event: data_pb2.Event) -> str:
        """Process the special start_of_match event with detailed introduction."""
        # Convert the event data to JSON string for the LLM
        event_json = json.loads(event.data)
        
        user_msg = (
            "Datos del partido que está por comenzar:\n\n"
            f"{event_json}\n\n"
            "Genera una presentación emocionante para el inicio de este partido de fútbol:"
        )

        # Call Azure OpenAI with special prompt and conversation history
        start = time.time()
        try:
            messages = self._build_messages(self.start_match_prompt, user_msg)
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            latency = time.time() - start

            # Extract comment
            comment = response.choices[0].message.content.strip()

            # Add to conversation history
            self._add_to_conversation(user_msg, comment)

            # Save debug information
            self._save_debug_call("start_match", messages, comment, latency)

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
                # "Genera un comentario dinámico sobre esta acción"
            )
        else:
            events_text = "\n\n---\n\n".join(events_json_list)
            user_msg = (
                f"Secuencia de {len(events)} eventos del juego:\n\n{events_text}\n\n"
                # f"Comenta uno de los siguientes {len(events)} eventos del juego (máximo 10 palabras):\n\n{events_text}\n\n"
            )

        # Call Azure OpenAI with conversation history
        start = time.time()
        try:
            messages = self._build_messages(self.system_prompt, user_msg)
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            latency = time.time() - start

            # Extract comment
            comment = response.choices[0].message.content.strip()

            # Add to conversation history
            self._add_to_conversation(user_msg, comment)

            # Save debug information
            self._save_debug_call(f"", messages, comment, latency)

            # Log metrics
            logger.info(
                "[Module B] Processed batch of %d events in %.2f s (tokens: %s)",
                len(events),
                latency,
                getattr(response.usage, 'total_tokens', None)
            )
            # Log prompt
            logger.info(f'  Comment:\n{comment}')
            return comment

        except Exception as e:
            logger.error(f"Error processing batch of {len(events)} events: {str(e)}")
            return ""

    def process(self, event: data_pb2.Event) -> str:
        """Legacy method - process single event (kept for compatibility)."""
        return self.process_batch([event])
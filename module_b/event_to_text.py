import logging
import random
import time
from proto import data_pb2  # type: ignore

logger = logging.getLogger(__name__)

class EventToText:
    """NLP processing: converts events to a comment about the game"""

    def __init__(self):
        # state to keep the client, chat and so on
        pass

    def process(self, event: data_pb2.Event) -> str:
        """Process incoming Event and return text string."""

        return "text" 
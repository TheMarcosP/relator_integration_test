import logging
import random
import time
from proto import data_pb2  # type: ignore

logger = logging.getLogger(__name__)

# Create a similar class for the actual implementation
# Then update the import in the server.py file
class EventToText:
    """Simulates heavy NLP processing, converts event to text.
    This is a dummy implementation for testing purposes.
    """

    def __init__(self, min_delay: float = 0.5, max_delay: float = 2.0):
        self.min_delay = min_delay
        self.max_delay = max_delay

    def process(self, event: data_pb2.Event) -> str:
        """Process incoming Event and return text string."""
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.info(f"🛠️  Processing Event (id={event.id}) for {delay:.2f}s…")
        time.sleep(delay)
        # Simple conversion: join map key/values
        text = ", ".join(f"{k} is {v}" for k, v in event.data.items())
        logger.info(f"✅ Processed Event (id={event.id}) text:\n'{text[:90]}…'")
        return text 
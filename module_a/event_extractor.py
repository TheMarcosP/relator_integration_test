import time
import logging
import random
logger = logging.getLogger('module_a')

class EventExtractor:
    def __init__(self):
        self.message_count = 0
        self.start_time = time.time()
        self.last_event_time = None
        self.event_history = []
        self.active = True
        self.extraction_patterns = {
            "timestamp": lambda: str(time.time()),
            "sequence": lambda: str(self.message_count),
            "status": lambda: "active",
            "source": lambda: "Module A"
        }
        logger.debug("EventExtractor initialized")

    def extract_event(self):
        # add random delay
        # time.sleep(random.uniform(0.1, 0.5))
        self.message_count += 1
        current_time = time.time()
        self.last_event_time = current_time
        
        event = {
            f"key_{self.message_count}": f"value_{self.message_count}",
            "timestamp": self.extraction_patterns["timestamp"](),
            "status": self.extraction_patterns["status"](),
            "source": self.extraction_patterns["source"](),
            "sequence": self.extraction_patterns["sequence"](),
            "runtime": str(current_time - self.start_time),
            "time_since_last": str(current_time - (self.last_event_time or current_time))
        }
        
        self.event_history.append(event)
        logger.debug(f"Extracted event {self.message_count}: {event}")
        return event

    def get_extraction_stats(self):
        return {
            "total_events": self.message_count,
            "runtime": time.time() - self.start_time,
            "average_interval": sum(float(e["time_since_last"]) for e in self.event_history) / len(self.event_history) if self.event_history else 0
        } 
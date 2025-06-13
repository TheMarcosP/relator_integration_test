import time
import logging
import random

logger = logging.getLogger('module_c')

class TextToSpeech:
    def __init__(self):
        self.processed_count = 0
        self.validation_errors = 0
        self.processing_history = []
        self.last_processed = None
        self.speech_patterns = {
            "prefix": "(Processed by C) (",
            "suffix": ")",
            "min_length": 10
        }
        logger.debug("TextToSpeech initialized")

    def process_text(self, input_string):
        # time.sleep(random.uniform(0.1, 5))
        self.processed_count += 1
        
        # Validate the text
        if not self.validate_text(input_string):
            self.validation_errors += 1
            raise ValueError("Invalid input string")
        
        # Process the text
        result = f"{self.speech_patterns['prefix']}{input_string}{self.speech_patterns['suffix']}"
        
        self.processing_history.append({
            "input": input_string,
            "output": result,
            "timestamp": time.time()
        })
        self.last_processed = result
        
        logger.debug(f"Processed text: {str(result)}")
        return result

    def validate_text(self, input_string):
        return bool(input_string and len(input_string) >= self.speech_patterns['min_length'])

    def get_processing_stats(self):
        return {
            "total_processed": self.processed_count,
            "validation_errors": self.validation_errors,
            "last_processed": self.last_processed,
            "processing_history": self.processing_history
        } 
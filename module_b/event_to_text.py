import time
import logging
import random

logger = logging.getLogger('module_b')

class EventToText:
    def __init__(self):
        self.processed_count = 0
        self.processing_times = []
        self.last_processed = None
        self.error_count = 0
        self.text_templates = {
            "prefix": "(Processed by B) (",
            "suffix": ")",
            "separator": " | "
        }
        logger.debug("EventToText initialized")

    def convert_to_text(self, data_dict):
        # time.sleep(random.uniform(1, 10))

        try:
            start_time = time.time()
            self.processed_count += 1
            
            # Add processing metadata
            data_dict = dict(data_dict)  # Create a copy to avoid modifying the original
            data_dict["processed_by"] = "Module B"
            data_dict["processing_time"] = str(time.time())
            data_dict["processing_sequence"] = str(self.processed_count)
            
            # Convert all values to strings and create text items
            items = []
            for key, value in data_dict.items():
                try:
                    # Convert value to string if it's not already
                    str_value = str(value)
                    items.append(f"{key}: {str_value}")
                except Exception as e:
                    logger.error(f"Error converting value for key {key}: {e}")
                    items.append(f"{key}: [conversion_error]")
            
            # Join items and create final text
            text = f"{self.text_templates['prefix']}{self.text_templates['separator'].join(items)}{self.text_templates['suffix']}"
            
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            self.last_processed = text
            
            logger.debug(f"Converted events to text: {text}")
            return text
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error in convert_to_text: {e}")
            raise

    def get_conversion_stats(self):
        return {
            "total_processed": self.processed_count,
            "average_processing_time": sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0,
            "error_count": self.error_count,
            "last_processed": self.last_processed
        } 
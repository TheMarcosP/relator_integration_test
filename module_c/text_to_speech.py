import logging
import os
import random
import time
import subprocess
import tempfile
from proto import data_pb2  # type: ignore

logger = logging.getLogger(__name__)

class TextToAudio:
    """TTS model wrapper to synthesize audio from text comment about the game"""

    def process(self, text_request: data_pb2.TextRequest) -> bytes:
        """Return raw bytes of a short WAV clip bundled with the module."""

        return audio_bytes
    
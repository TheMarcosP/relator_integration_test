"""module_c.text_to_speech
---------------------------------
A Kokoro wrapper that **accepts a local model directory** (via the env‑var
`KOKORO_REPO_DIR`) *or* falls back to HuggingFace (`hexgrad/Kokoro-82M`).

* Works with Kokoro 0.7.x (iterator‑only API) and newer 0.9 wheels.
* Streams every chunk; if we get only the short 6 k‑sample probe we re‑try
  with forced newlines to coax a full sentence.
* Saves 16‑bit PCM WAV.
"""

from io import BytesIO
import logging
import os
from pathlib import Path
from typing import List

import numpy as np
import soundfile as sf
import torch
from kokoro import KPipeline

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# -----------------------------------------------------------------------------
# Where to look for a local Kokoro repo, e.g. module_c/Kokoro-82M
LOCAL_DIR = Path(os.getenv("KOKORO_REPO_DIR", Path(__file__).parent / "Kokoro-82M")).expanduser()
VOICE_DEFAULT = "em_alex"
SAMPLE_RATE = 24_000
# -----------------------------------------------------------------------------

class TextToAudio:
    """Turn Spanish commentary into 16‑bit PCM WAV bytes."""

    def __init__(self, voice: str = VOICE_DEFAULT, sample_rate: int = SAMPLE_RATE):
        self.voice = voice
        self.sample_rate = sample_rate

        if LOCAL_DIR.is_dir():
            # HuggingFace needs a *valid* repo_id string; we pass the default
            # one but tell it to look in our local folder only.
            repo_id = "hexgrad/Kokoro-82M"
            cache_dir = str(LOCAL_DIR)
                        # Kokoro 0.7.x' KPipeline doesn't accept cache_dir/local_files_only.
            # Instead we trick HF into treating LOCAL_DIR as its cache by
            # pointing HF_HOME there and forcing offline mode.
            os.environ["HF_HOME"] = str(LOCAL_DIR)
            os.environ["HF_HUB_OFFLINE"] = "1"
            self.pipe = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M", device="cuda")
            logger.info("📦 Loaded Kokoro from local dir %s", cache_dir)
            # Use absolute path to voice file so load_voice skips HF download
            voice_path = LOCAL_DIR / "voices" / f"{voice}.pt"
            if voice_path.exists():
                self.voice_file = str(voice_path)
            else:
                self.voice_file = voice  # fallback to hub
        else:
            # No local copy – pull from hub
            self.pipe = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M", device="cuda")
            self.voice_file = voice
            logger.info("🌐 Using Kokoro from HuggingFace hub")

    # ------------------------------------------------------------------
    @staticmethod
    def _to_np(chunk):
        if isinstance(chunk, torch.Tensor):
            return chunk.detach().cpu().numpy().astype(np.float32, copy=False)
        if isinstance(chunk, np.ndarray):
            return chunk.astype(np.float32, copy=False)
        raise TypeError(type(chunk))

    def _collect(self, text: str) -> np.ndarray:
        chunks: List[np.ndarray] = []
        for idx, (*_, ch) in enumerate(
            self.pipe(text, voice=self.voice_file, speed=1.0, split_pattern="\n+")
        ):
            arr = self._to_np(ch)
            chunks.append(arr)
            logger.debug("    chunk %-2d shape=%s", idx, arr.shape)
        return np.concatenate(chunks) if chunks else np.empty(0, np.float32)

    # ------------------------------------------------------------------
    def process(self, request) -> bytes:
        text = request.text if hasattr(request, "text") else str(request)
        if not text.endswith((".", "!", "?", "\n")):
            text += "\n"

        logger.info("🗣️  Synthesising | %s…", text[:70])
        audio = self._collect(text)

        # Probe‑only heuristic: retry with forced newlines if too short
        if audio.size and audio.shape[0] <= 7000:
            logger.warning("↩️  Only probe chunk (%.0f ms). Retrying…",
                           1000 * audio.shape[0] / self.sample_rate)
            text_retry = "\n".join(text[i:i+80] for i in range(0, len(text), 80)) + "\n"
            audio = self._collect(text_retry)

        if audio.size == 0 or audio.shape[0] <= 7000:
            raise RuntimeError("Kokoro produced no usable audio")

        duration = audio.shape[0] / self.sample_rate
        logger.info("✅ Final audio %.2f s (%d bytes)", duration, audio.nbytes)

        buf = BytesIO()
        sf.write(buf, audio, self.sample_rate, format="WAV", subtype="PCM_16")
        return buf.getvalue()

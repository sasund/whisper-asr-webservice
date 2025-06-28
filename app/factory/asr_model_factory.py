from typing import Union

from app.asr_models.asr_model import ASRModel
from app.asr_models.faster_whisper_engine import FasterWhisperASR
from app.asr_models.mbain_whisperx_engine import WhisperXASR
from app.asr_models.openai_whisper_engine import OpenAIWhisperASR
from app.config import CONFIG
from app.exceptions import UnsupportedEngineError
from app.nbailab_whisper import core as nbailab_core


class NbAiLabWhisperASR(ASRModel):
    def load_model(self):
        # Ingen eksplisitt lasting nødvendig for HuggingFace pipeline
        pass

    def transcribe(
        self,
        audio,
        task: Union[str, None],
        language: Union[str, None],
        initial_prompt: Union[str, None],
        vad_filter: Union[bool, None],
        word_timestamps: Union[bool, None],
        options: Union[dict, None],
        output,
    ):
        return nbailab_core.transcribe(audio, task, language, initial_prompt, vad_filter, word_timestamps, output)

    def language_detection(self, audio):
        return nbailab_core.language_detection(audio)


class ASRModelFactory:
    @staticmethod
    def create_asr_model() -> ASRModel:
        """Create an ASR model instance based on configuration."""
        if CONFIG.ASR_ENGINE == "openai_whisper":
            return OpenAIWhisperASR()
        elif CONFIG.ASR_ENGINE == "faster_whisper":
            return FasterWhisperASR()
        elif CONFIG.ASR_ENGINE == "whisperx":
            return WhisperXASR()
        elif CONFIG.ASR_ENGINE == "nbailab_whisper":
            return NbAiLabWhisperASR()
        else:
            raise UnsupportedEngineError(f"Unsupported ASR engine: {CONFIG.ASR_ENGINE}")

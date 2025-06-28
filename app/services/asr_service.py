from typing import Union
from urllib.parse import quote

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from app.asr_models.asr_model import ASRModel
from app.config import CONFIG
from app.exceptions import AudioLoadError, TranscriptionError
from app.utils import load_audio


class ASRService:
    """Service class for ASR operations with dependency injection."""

    def __init__(self, asr_model: ASRModel):
        self.asr_model = asr_model

    async def transcribe_audio(
        self,
        audio_file: UploadFile,
        task: Union[str, None] = "transcribe",
        language: Union[str, None] = None,
        initial_prompt: Union[str, None] = None,
        vad_filter: bool = False,
        word_timestamps: bool = False,
        diarize: bool = False,
        min_speakers: Union[int, None] = None,
        max_speakers: Union[int, None] = None,
        output: Union[str, None] = "txt",
        encode: bool = True,
    ) -> StreamingResponse:
        """Transcribe audio file and return streaming response."""
        try:
            # Load and process audio
            audio_data = load_audio(audio_file.file, encode)

            # Prepare options for diarization
            options = {
                "diarize": diarize,
                "min_speakers": min_speakers,
                "max_speakers": max_speakers,
            }

            # Perform transcription
            result = self.asr_model.transcribe(
                audio_data,
                task,
                language,
                initial_prompt,
                vad_filter,
                word_timestamps,
                options,
                output,
            )

            # Ensure we have a valid result
            if result is None:
                raise TranscriptionError("Transcription returned no result")

            filename = audio_file.filename or "audio"
            output_ext = output or "txt"

            return StreamingResponse(
                result,
                media_type="text/plain",
                headers={
                    "Asr-Engine": CONFIG.ASR_ENGINE,
                    "Content-Disposition": f'attachment; filename="{quote(filename)}.{output_ext}"',
                },
            )

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}") from e

    async def detect_language(
        self,
        audio_file: UploadFile,
        encode: bool = True,
    ) -> dict:
        """Detect language of audio file."""
        try:
            audio_data = load_audio(audio_file.file, encode)
            result = self.asr_model.language_detection(audio_data)

            # Handle different return types from different ASR engines
            if isinstance(result, tuple) and len(result) == 2:
                detected_lang_code, confidence = result
            else:
                # Fallback for engines that don't return confidence
                detected_lang_code = str(result) if result is not None else "en"
                confidence = 1.0

            from whisper import tokenizer

            return {
                "detected_language": tokenizer.LANGUAGES.get(detected_lang_code, "Unknown"),
                "language_code": detected_lang_code,
                "confidence": confidence,
            }

        except Exception as e:
            raise AudioLoadError(f"Language detection failed: {str(e)}") from e

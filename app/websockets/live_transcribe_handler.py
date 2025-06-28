import logging
from typing import Optional
import time

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from app.asr_models.asr_model import ASRModel
from app.exceptions import TranscriptionError
from app.config import CONFIG

logger = logging.getLogger(__name__)


class LiveTranscribeHandler:
    """Handles live transcription via WebSocket connections."""

    def __init__(self, asr_model: ASRModel):
        self.asr_model = asr_model
        self.SAMPLE_RATE = 16000
        self.CHUNK_SIZE = CONFIG.LIVE_CHUNK_SIZE  # Use configurable chunk size
        self.OVERLAP_SIZE = CONFIG.LIVE_OVERLAP_SIZE  # Overlap for better context
        self.audio_buffer = bytearray()
        self.last_processed_position = 0

    async def handle_connection(self, websocket: WebSocket, language: Optional[str] = None):
        """Handle a WebSocket connection for live transcription."""
        await websocket.accept()
        self.audio_buffer = bytearray()
        self.last_processed_position = 0

        logger.info(f"Live transcription started - Language: {language or 'auto-detect'}")

        try:
            chunk_count = 0
            while True:
                chunk = await websocket.receive_bytes()
                chunk_count += 1
                self.audio_buffer.extend(chunk)

                logger.debug(
                    f"Received chunk {chunk_count}, size: {len(chunk)} bytes, total buffer: {len(self.audio_buffer)} bytes"
                )

                # Process when we have enough new data (considering overlap)
                new_data_size = len(self.audio_buffer) - self.last_processed_position
                if new_data_size >= self.CHUNK_SIZE:
                    await self._process_audio_chunk(websocket, language)
                    
                    # Keep overlap for context, but advance the processing position
                    if CONFIG.LIVE_OVERLAP_CHUNKS:
                        # Keep last 0.5 seconds for overlap
                        keep_size = self.OVERLAP_SIZE
                        if len(self.audio_buffer) > keep_size:
                            self.audio_buffer = self.audio_buffer[-keep_size:]
                            self.last_processed_position = 0
                        else:
                            self.last_processed_position = len(self.audio_buffer)
                    else:
                        # Clear buffer completely
                        self.audio_buffer = bytearray()
                        self.last_processed_position = 0
                else:
                    # Send confirmation that we received data
                    await websocket.send_text("[BUFFERING]")

        except WebSocketDisconnect:
            logger.info("WebSocket connection closed by client")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
            try:
                await websocket.send_text(f"[ERROR] {str(e)}")
            except Exception:
                pass  # Connection might already be closed

    async def _process_audio_chunk(self, websocket: WebSocket, language: Optional[str]):
        """Process an audio chunk and send transcription result."""
        logger.debug(f"Processing audio buffer of size: {len(self.audio_buffer)} bytes")

        # Convert to numpy array
        audio_np = np.frombuffer(self.audio_buffer, np.int16).astype(np.float32) / 32768.0
        logger.debug(f"Audio array shape: {audio_np.shape}, min: {audio_np.min()}, max: {audio_np.max()}")

        # Check if there's audio in the data
        if np.abs(audio_np).max() < 0.01:
            logger.debug("Audio seems to be silence, skipping transcription")
            await websocket.send_text("[SILENCE]")
            return

        try:
            # For NbAiLab models, don't use initial_prompt as it's not supported by HuggingFace pipeline
            # The language parameter is sufficient for good quality
            initial_prompt = None

            # Call existing transcribe function with improved parameters for better synchronization
            result_file = self.asr_model.transcribe(
                audio_np,
                task="transcribe",
                language=language,
                initial_prompt=initial_prompt,
                vad_filter=CONFIG.LIVE_VAD_FILTER,  # Use configurable VAD setting
                word_timestamps=CONFIG.LIVE_WORD_TIMESTAMPS,  # Use configurable word timestamps
                options=None,
                output=CONFIG.LIVE_OUTPUT_FORMAT,  # Use configurable output format
            )

            if result_file is not None and hasattr(result_file, "getvalue"):
                transcription_data = result_file.getvalue().strip()
                logger.debug(f"Transcription result: '{transcription_data}'")

                if transcription_data:
                    # Add timing information to the response
                    if CONFIG.LIVE_OUTPUT_FORMAT == "json":
                        try:
                            import json
                            result_json = json.loads(transcription_data)
                            
                            # Add processing timestamp and chunk information
                            result_json["processing_timestamp"] = time.time()
                            result_json["chunk_duration"] = len(audio_np) / self.SAMPLE_RATE
                            result_json["buffer_size"] = len(self.audio_buffer)
                            
                            # Adjust timestamps if we have overlap
                            if CONFIG.LIVE_OVERLAP_CHUNKS and self.last_processed_position > 0:
                                overlap_duration = self.last_processed_position / (self.SAMPLE_RATE * 2)  # 2 bytes per sample
                                if "segments" in result_json:
                                    for segment in result_json["segments"]:
                                        if "start" in segment:
                                            segment["start"] += overlap_duration
                                        if "end" in segment:
                                            segment["end"] += overlap_duration
                            
                            transcription_data = json.dumps(result_json, ensure_ascii=False)
                        except json.JSONDecodeError:
                            # If JSON parsing fails, send as is
                            pass
                    
                    # Send transcription data with timing information
                    await websocket.send_text(transcription_data)
                else:
                    await websocket.send_text("[NO_SPEECH]")
            else:
                logger.error("Transcription failed - no result file")
                await websocket.send_text("[ERROR] Transcription failed.")

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise TranscriptionError(f"Transcription failed: {str(e)}") from e

    def _get_initial_prompt(self, language: Optional[str]) -> str:
        """Get language-specific initial prompt."""
        prompts = {
            "en": "This is English speech. Transcribe accurately what is said.",
            "sv": "Detta är svenska tal. Transkribera exakt vad som sägs.",
            "da": "Dette er dansk tale. Transkriber nøjagtigt det der siges.",
            "no": "Dette er norsk radio eller podcast. Transkriber nøyaktig det som sies, inkludert navn, stedsnavn og tekniske termer.",
        }

        # Return language-specific prompt or neutral prompt for auto-detect
        return prompts.get(language or "", "Transcribe accurately what is said.")

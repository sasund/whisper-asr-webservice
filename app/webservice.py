import importlib.metadata
import os
from os import path
from typing import Annotated, Optional, Union
from urllib.parse import quote

import click
import uvicorn
from fastapi import FastAPI, File, Query, UploadFile, applications, WebSocket, WebSocketDisconnect
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from whisper import tokenizer
import numpy as np

from app.config import CONFIG
from app.factory.asr_model_factory import ASRModelFactory
from app.utils import load_audio

asr_model = ASRModelFactory.create_asr_model()
asr_model.load_model()

LANGUAGE_CODES = sorted(tokenizer.LANGUAGES.keys())

projectMetadata = importlib.metadata.metadata("whisper-asr-webservice")
app = FastAPI(
    title=projectMetadata["Name"].title().replace("-", " "),
    description=projectMetadata["Summary"],
    version=projectMetadata["Version"],
    contact={"url": projectMetadata["Home-page"]},
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    license_info={"name": "MIT License", "url": projectMetadata["License"]},
)

assets_path = os.getcwd() + "/swagger-ui-assets"
if path.exists(assets_path + "/swagger-ui.css") and path.exists(assets_path + "/swagger-ui-bundle.js"):
    app.mount("/assets", StaticFiles(directory=assets_path), name="static")

    def swagger_monkey_patch(*args, **kwargs):
        return get_swagger_ui_html(
            *args,
            **kwargs,
            swagger_favicon_url="",
            swagger_css_url="/assets/swagger-ui.css",
            swagger_js_url="/assets/swagger-ui-bundle.js",
        )

    applications.get_swagger_ui_html = swagger_monkey_patch

# Serve static files for live player
static_path = os.getcwd() + "/static"
if path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static_files")


@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def index():
    return "/docs"


@app.post("/asr", tags=["Endpoints"])
async def asr(
    audio_file: UploadFile = File(...),  # noqa: B008
    encode: bool = Query(default=True, description="Encode audio first through ffmpeg"),
    task: Union[str, None] = Query(default="transcribe", enum=["transcribe", "translate"]),
    language: Union[str, None] = Query(default=None, enum=LANGUAGE_CODES),
    initial_prompt: Union[str, None] = Query(default=None),
    vad_filter: Annotated[
        bool | None,
        Query(
            description="Enable the voice activity detection (VAD) to filter out parts of the audio without speech",
            include_in_schema=(True if CONFIG.ASR_ENGINE == "faster_whisper" else False),
        ),
    ] = False,
    word_timestamps: bool = Query(
        default=False,
        description="Word level timestamps",
        include_in_schema=(True if CONFIG.ASR_ENGINE == "faster_whisper" else False),
    ),
    diarize: bool = Query(
        default=False,
        description="Diarize the input",
        include_in_schema=(True if CONFIG.ASR_ENGINE == "whisperx" and CONFIG.HF_TOKEN != "" else False),
    ),
    min_speakers: Union[int, None] = Query(
        default=None,
        description="Min speakers in this file",
        include_in_schema=(True if CONFIG.ASR_ENGINE == "whisperx" else False),
    ),
    max_speakers: Union[int, None] = Query(
        default=None,
        description="Max speakers in this file",
        include_in_schema=(True if CONFIG.ASR_ENGINE == "whisperx" else False),
    ),
    output: Union[str, None] = Query(default="txt", enum=["txt", "vtt", "srt", "tsv", "json"]),
):
    result = asr_model.transcribe(
        load_audio(audio_file.file, encode),
        task,
        language,
        initial_prompt,
        vad_filter,
        word_timestamps,
        {"diarize": diarize, "min_speakers": min_speakers, "max_speakers": max_speakers},
        output,
    )
    return StreamingResponse(
        result,
        media_type="text/plain",
        headers={
            "Asr-Engine": CONFIG.ASR_ENGINE,
            "Content-Disposition": f'attachment; filename="{quote(audio_file.filename)}.{output}"',
        },
    )


@app.post("/detect-language", tags=["Endpoints"])
async def detect_language(
    audio_file: UploadFile = File(...),  # noqa: B008
    encode: bool = Query(default=True, description="Encode audio first through FFmpeg"),
):
    detected_lang_code, confidence = asr_model.language_detection(load_audio(audio_file.file, encode))
    return {
        "detected_language": tokenizer.LANGUAGES[detected_lang_code],
        "language_code": detected_lang_code,
        "confidence": confidence,
    }


@app.websocket("/ws/live-transcribe")
async def websocket_live_transcribe(websocket: WebSocket, language: str = None):
    await websocket.accept()
    audio_buffer = bytearray()
    SAMPLE_RATE = 16000  # Kan evt. hentes fra CONFIG
    CHUNK_SIZE = 64000  # Økt til 2 sekunder ved 16kHz, 16bit mono for bedre kontekst
    
    print(f"Live transcription started - Language: {language or 'auto-detect'}")
    
    try:
        chunk_count = 0
        while True:
            chunk = await websocket.receive_bytes()
            chunk_count += 1
            audio_buffer.extend(chunk)
            
            print(f"Received chunk {chunk_count}, size: {len(chunk)} bytes, total buffer: {len(audio_buffer)} bytes")
            
            # Vent til vi har nok data
            if len(audio_buffer) >= CHUNK_SIZE:
                print(f"Processing audio buffer of size: {len(audio_buffer)} bytes")
                # Konverter til numpy array
                audio_np = np.frombuffer(audio_buffer, np.int16).astype(np.float32) / 32768.0
                print(f"Audio array shape: {audio_np.shape}, min: {audio_np.min()}, max: {audio_np.max()}")
                
                # Sjekk om det er lyd i data
                if np.abs(audio_np).max() < 0.01:
                    print("Audio seems to be silence, skipping transcription")
                    audio_buffer = bytearray()
                    continue
                
                try:
                    # Forbedret initial prompt for norsk
                    initial_prompt = "Dette er norsk tale. Transkriber nøyaktig det som sies."
                    if language == "en":
                        initial_prompt = "This is English speech. Transcribe accurately what is said."
                    elif language == "sv":
                        initial_prompt = "Detta är svenska tal. Transkribera exakt vad som sägs."
                    elif language == "da":
                        initial_prompt = "Dette er dansk tale. Transkriber nøjagtigt det der siges."
                    
                    # Kall eksisterende transcribe-funksjon med forbedrede parametere
                    result_file = asr_model.transcribe(
                        audio_np, 
                        task="transcribe", 
                        language=language, 
                        initial_prompt=initial_prompt,
                        vad_filter=True,  # Aktiver VAD for bedre kvalitet
                        word_timestamps=False, 
                        options=None, 
                        output="txt"
                    )
                    
                    if result_file is not None and hasattr(result_file, "getvalue"):
                        transcription_text = result_file.getvalue().strip()
                        print(f"Transcription result: '{transcription_text}'")
                        if transcription_text:
                            await websocket.send_text(transcription_text)
                        else:
                            await websocket.send_text("[NO_SPEECH]")
                    else:
                        print("Transcription failed - no result file")
                        await websocket.send_text("[ERROR] Transcription failed.")
                        
                except Exception as e:
                    print(f"Error during transcription: {e}")
                    await websocket.send_text(f"[ERROR] {str(e)}")
                
                audio_buffer = bytearray()  # Tøm buffer
            else:
                # Send en bekreftelse at vi mottok data
                if chunk_count == 1:
                    await websocket.send_text("[BUFFERING] Collecting audio data...")
                
    except WebSocketDisconnect:
        # Klienten koblet fra - ikke prøv å lukke forbindelsen igjen
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass  # Ignorer hvis forbindelsen allerede er lukket


@click.command()
@click.option(
    "-h",
    "--host",
    metavar="HOST",
    default="0.0.0.0",
    help="Host for the webservice (default: 0.0.0.0)",
)
@click.option(
    "-p",
    "--port",
    metavar="PORT",
    default=9000,
    help="Port for the webservice (default: 9000)",
)
@click.version_option(version=projectMetadata["Version"])
def start(host: str, port: Optional[int] = None):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start()

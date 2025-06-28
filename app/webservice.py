import importlib.metadata
import os
from os import path
from typing import Annotated, Optional, Union

import click
import uvicorn
from fastapi import FastAPI, File, Query, UploadFile, WebSocket
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from whisper import tokenizer

from app.config import CONFIG
from app.factory.asr_model_factory import ASRModelFactory
from app.services.asr_service import ASRService
from app.websockets.live_transcribe_handler import LiveTranscribeHandler

# Initialize ASR model and service
asr_model = ASRModelFactory.create_asr_model()
asr_model.load_model()
asr_service = ASRService(asr_model)
live_transcribe_handler = LiveTranscribeHandler(asr_model)

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

# Serve static files for Swagger UI
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

    # Monkey patch the swagger UI function
    import fastapi.openapi.docs

    fastapi.openapi.docs.get_swagger_ui_html = swagger_monkey_patch

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
        bool,
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
    """Transcribe audio file using the configured ASR engine."""
    return await asr_service.transcribe_audio(
        audio_file=audio_file,
        task=task,
        language=language,
        initial_prompt=initial_prompt,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
        diarize=diarize,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
        output=output,
        encode=encode,
    )


@app.post("/detect-language", tags=["Endpoints"])
async def detect_language(
    audio_file: UploadFile = File(...),  # noqa: B008
    encode: bool = Query(default=True, description="Encode audio first through FFmpeg"),
):
    """Detect the language of the audio file."""
    return await asr_service.detect_language(audio_file=audio_file, encode=encode)


@app.websocket("/ws/live-transcribe")
async def websocket_live_transcribe(websocket: WebSocket, language: Optional[str] = None):
    """WebSocket endpoint for live transcription."""
    await live_transcribe_handler.handle_connection(websocket, language)


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
    """Start the ASR webservice."""
    uvicorn.run(
        "app.webservice:app",
        host=host,
        port=port or 9000,
        log_level="info",
    )


if __name__ == "__main__":
    start()

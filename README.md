![Release](https://img.shields.io/github/v/release/sasund/whisper-asr-webservice.svg)
![Docker Pulls](https://img.shields.io/docker/pulls/sasund/whisper-asr-webservice.svg)
![Build](https://img.shields.io/github/actions/workflow/status/sasund/whisper-asr-webservice/docker-publish.yml.svg)
![Licence](https://img.shields.io/github/license/sasund/whisper-asr-webservice.svg)

# Whisper ASR Box

Whisper ASR Box is a general-purpose speech recognition toolkit. Whisper Models are trained on a large dataset of diverse audio and is also a multitask model that can perform multilingual speech recognition as well as speech translation and language identification.

## Features

Current release (v1.9.0-dev) supports following whisper models:

- [openai/whisper](https://github.com/openai/whisper)@[v20240930](https://github.com/openai/whisper/releases/tag/v20240930)
- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)@[v1.1.0](https://github.com/SYSTRAN/faster-whisper/releases/tag/v1.1.0)
- [whisperX](https://github.com/m-bain/whisperX)@[v3.1.1](https://github.com/m-bain/whisperX/releases/tag/v3.1.1)
- [NbAiLab Whisper (via HuggingFace)](https://huggingface.co/NbAiLab) (f.eks. `NbAiLab/nb-whisper-large`, `NbAiLab/nb-whisper-small`)

## Quick Usage

### CPU (NbAiLab Whisper - Default for Norwegian)

```shell
docker run -d -p 9000:9000 \
  -e ASR_MODEL=NbAiLab/nb-whisper-large \
  -e ASR_ENGINE=nbailab_whisper \
  sasund/whisper-asr-webservice:latest
```

### CPU (OpenAI/NbAiLab)

```shell
docker run -d -p 9000:9000 \
  -e ASR_MODEL=base \
  -e ASR_ENGINE=openai_whisper \
  sasund/whisper-asr-webservice:latest
```

### CPU (NbAiLab Whisper via HuggingFace)

```sh
docker run -d -p 9000:9000 -e ASR_MODEL=NbAiLab/nb-whisper-large -e ASR_ENGINE=nbailab_whisper sasund/whisper-asr-webservice:latest
```

### GPU (NbAiLab Whisper - Default for Norwegian)

Alle støttede modeller, inkludert NbAiLab Whisper-modeller, kan kjøres på GPU dersom du bruker en Docker-image med GPU-støtte og har riktig PyTorch-installasjon.

```shell
docker run -d --gpus all -p 9000:9000 \
  -e ASR_MODEL=NbAiLab/nb-whisper-large \
  -e ASR_ENGINE=nbailab_whisper \
  sasund/whisper-asr-webservice:latest-gpu
```

### GPU (OpenAI/NbAiLab)

```shell
docker run -d --gpus all -p 9000:9000 \
  -e ASR_MODEL=base \
  -e ASR_ENGINE=openai_whisper \
  sasund/whisper-asr-webservice:latest-gpu
```

#### Cache

To reduce container startup time by avoiding repeated downloads, you can persist the cache directory:

```shell
docker run -d -p 9000:9000 \
  -v $PWD/cache:/root/.cache/ \
  sasund/whisper-asr-webservice:latest
```

#### GPU med NbAiLab Whisper

```sh
docker run -d --gpus all -p 9000:9000 -e ASR_MODEL=NbAiLab/nb-whisper-large -e ASR_ENGINE=nbailab_whisper sasund/whisper-asr-webservice:latest-gpu
```

## Development & Testing

### Project Structure
The project follows a modular architecture:
- `app/asr_models/` - ASR engine implementations
- `app/factory/` - Factory pattern for ASR models  
- `app/services/` - Business logic layer
- `app/websockets/` - WebSocket handlers
- `app/output/` - Output formatters
- `app/exceptions/` - Custom exceptions

### Running Tests
```bash
# Install dev dependencies
poetry install --with dev

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## NbAiLab Whisper Models

When using `ASR_ENGINE=nbailab_whisper`, you have access to a wide range of Norwegian-optimized models:

### Standard Models (Recommended)
- `NbAiLab/nb-whisper-tiny` - Fastest, smallest model
- `NbAiLab/nb-whisper-base` - Good balance of speed and accuracy  
- `NbAiLab/nb-whisper-small` - Better accuracy than base
- `NbAiLab/nb-whisper-medium` - High accuracy, moderate speed
- `NbAiLab/nb-whisper-large` - Best accuracy, slower inference

### Beta Models (Latest versions)
- `NbAiLab/nb-whisper-tiny-beta` - Latest tiny model
- `NbAiLab/nb-whisper-base-beta` - Latest base model
- `NbAiLab/nb-whisper-small-beta` - Latest small model
- `NbAiLab/nb-whisper-medium-beta` - Latest medium model
- `NbAiLab/nb-whisper-large-beta` - Latest large model

### Verbatim Models (Preserves exact pronunciation)
- `NbAiLab/nb-whisper-tiny-verbatim` - Preserves pronunciation details
- `NbAiLab/nb-whisper-base-verbatim` - Preserves pronunciation details
- `NbAiLab/nb-whisper-small-verbatim` - Preserves pronunciation details
- `NbAiLab/nb-whisper-medium-verbatim` - Preserves pronunciation details
- `NbAiLab/nb-whisper-large-verbatim` - Preserves pronunciation details

### Semantic Models (Better understanding of context)
- `NbAiLab/nb-whisper-tiny-semantic` - Better context understanding
- `NbAiLab/nb-whisper-base-semantic` - Better context understanding
- `NbAiLab/nb-whisper-small-semantic` - Better context understanding
- `NbAiLab/nb-whisper-medium-semantic` - Better context understanding
- `NbAiLab/nb-whisper-large-semantic` - Better context understanding

### Example Usage
```bash
# For production use (recommended)
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-large

# For faster inference
export ASR_MODEL=NbAiLab/nb-whisper-base

# For latest beta version
export ASR_MODEL=NbAiLab/nb-whisper-large-beta

# For preserving exact pronunciation
export ASR_MODEL=NbAiLab/nb-whisper-large-verbatim
```

## Key Features

- Multiple ASR engines support (OpenAI Whisper, Faster Whisper, WhisperX, NbAiLab Whisper)
- Multiple output formats (text, JSON, VTT, SRT, TSV)
- Word-level timestamps support
- Voice activity detection (VAD) filtering
- Speaker diarization (with WhisperX)
- FFmpeg integration for broad audio/video format support
- GPU acceleration support
- Configurable model loading/unloading
- REST API with Swagger documentation
- **Live transcription via WebSocket** (new!)
- **Optimized Norwegian language support** with NbAiLab models

## Recent Improvements (v1.9.0-dev)

### Norwegian Language Quality Fixes
- **Fixed NbAiLab Whisper implementation**: Corrected HuggingFace pipeline usage for optimal Norwegian transcription
- **Improved language detection**: Enhanced Norwegian language detection with proper confidence scoring
- **Fixed result formatting**: Resolved compatibility issues with output writers for NbAiLab models
- **Removed unsupported parameters**: Cleaned up initial_prompt handling for HuggingFace compatibility
- **Warning suppression**: Eliminated transformers warnings for cleaner logs

### Quality Improvements
- **Better Norwegian transcription**: NbAiLab models now provide significantly better quality for Norwegian speech
- **Stable live transcription**: Fixed WebSocket implementation for reliable real-time transcription
- **Proper error handling**: Improved error messages and exception handling
- **Memory optimization**: Better model loading and caching for HuggingFace models

### Recommended Configuration for Norwegian
```bash
# For best Norwegian transcription quality
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-large

# For faster processing with good quality
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-medium
```

## Live Transcription

The service now supports real-time transcription via WebSocket. This allows you to send audio chunks and receive transcription results in real-time.

### WebSocket Endpoint
```
ws://localhost:9000/ws/live-transcribe
```

### Demo Client
A demo client is included to test live transcription:

```bash
# Install websockets if not already installed
pip install websockets

# Run demo with a WAV file
python demo_live_transcribe.py path/to/your/audio.wav

# Run demo with an MP3 file (automatic conversion)
python demo_live_transcribe.py path/to/your/audio.mp3

# With language specification
python demo_live_transcribe.py audio.wav --language no

# Custom options
python demo_live_transcribe.py audio.wav --host localhost --port 9000 --chunk-duration 1.0 --language en
```

### Audio Requirements
- **Supported formats**: MP3, WAV, and all formats supported by FFmpeg
- **Automatic conversion**: Non-WAV files are automatically converted to WAV format
- **Recommended settings**: 16kHz, mono, 16-bit (automatic with conversion)
- **FFmpeg required**: For MP3 and other format support

### Language Support
You can specify the language for live transcription:
- **Auto-detect** (default): Let the model detect the language automatically
- **Norwegian**: `--language no`
- **English**: `--language en`
- **Swedish**: `--language sv`
- **Danish**: `--language da`
- And all other languages supported by Whisper

### Usage Example
```python
import asyncio
import websockets

async def live_transcribe():
    # With language specification
    uri = "ws://localhost:9000/ws/live-transcribe?language=no"
    async with websockets.connect(uri) as websocket:
        # Send audio chunks
        await websocket.send(audio_chunk)
        
        # Receive transcription
        transcription = await websocket.recv()
        print(f"Transcription: {transcription}")

asyncio.run(live_transcribe())
```

## Live Player

A web-based live transcription player is included with Video.js integration:

### Access Live Player
```
http://localhost:9000/static/live_player.html
```

### Audio Player med Live Transcription
For å spille av lydfiler med live transcription:
```
http://localhost:9000/static/audio_player.html
```

### Features
- **Real-time microphone transcription** via WebSocket
- **Audio file playback with transcription** via WebSocket
- **Video.js player** for media playback
- **Language selection** (Norwegian, English, Swedish, etc.)
- **Live captions** with timestamps
- **Responsive design** for desktop and mobile
- **Audio processing** with noise suppression and echo cancellation
- **Drag & drop file upload** for audio files
- **Progress tracking** for audio playback

### Usage
1. Start the whisper-asr-webservice
2. Open `http://localhost:9000/static/live_player.html` in your browser
3. Allow microphone access when prompted
4. Click "Start Live Transcription" to begin
5. Speak into your microphone and see real-time transcription

### Browser Requirements
- Modern browser with WebSocket support
- Microphone access permission
- HTTPS required for microphone access in production

## Environment Variables

Key configuration options:

- `ASR_ENGINE`: Engine selection (openai_whisper, faster_whisper, whisperx, nbailab_whisper)
- `ASR_MODEL`: Model selection (tiny, base, small, medium, large-v3, etc.)
- `ASR_MODEL_PATH`: Custom path to store/load models
- `ASR_DEVICE`: Device selection (cuda, cpu)
- `MODEL_IDLE_TIMEOUT`: Timeout for model unloading

## Documentation

For complete documentation, visit:
[https://ahmetoner.github.io/whisper-asr-webservice](https://ahmetoner.github.io/whisper-asr-webservice)

## Development

```shell
# Install poetry
pip3 install poetry

# Install dependencies
poetry install

# Run service
poetry run whisper-asr-webservice --host 0.0.0.0 --port 9000
```

After starting the service, visit `http://localhost:9000` or `http://0.0.0.0:9000` in your browser to access the Swagger UI documentation and try out the API endpoints.

## Credits

- This software uses libraries from the [FFmpeg](http://ffmpeg.org) project under the [LGPLv2.1](http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html)
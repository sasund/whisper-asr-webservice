# English Transcription Issue and Solutions

## Problem Description

When using the ASR endpoint with `task=transcribe` on English audio files, you may get Norwegian text instead of English. This happens because:

1. The default ASR engine is `nbailab_whisper` which uses the `NbAiLab/nb-whisper-large` model
2. This model is specifically trained for Norwegian language and has a strong bias towards Norwegian
3. **IMPORTANT**: NbAiLab Whisper models do NOT support the `language` parameter - it will be ignored
4. When no language is specified, the model assumes Norwegian by default

## Solutions

### Solution 1: Switch to Faster Whisper (Recommended)

Faster Whisper supports the `language` parameter properly:

```bash
export ASR_ENGINE=faster_whisper
export ASR_MODEL=base  # or small, medium, large
```

Then restart the service and use:

```bash
curl -X POST -F "audio_file=@audio/king_16k.wav" \
  "http://localhost:9000/asr?task=transcribe&language=en&output=json"
```

### Solution 2: Switch to OpenAI Whisper

Original OpenAI Whisper also supports language parameter:

```bash
export ASR_ENGINE=openai_whisper
export ASR_MODEL=base  # or small, medium, large
```

### Solution 3: Use WhisperX

WhisperX with enhanced features:

```bash
export ASR_ENGINE=whisperx
export ASR_MODEL=base
export HF_TOKEN=your_huggingface_token  # Required for diarization
```

### Solution 4: Use a different NbAiLab model

For NbAiLab engine, try a different model (but language parameter still won't work):

```bash
export ASR_MODEL=openai/whisper-base  # or other OpenAI models
```

## Why NbAiLab Models Don't Support Language Parameter

NbAiLab Whisper models use HuggingFace's `AutomaticSpeechRecognitionPipeline` which:
- Does not support `forced_decoder_ids` for language forcing
- Automatically detects language based on the model's training
- Ignores the `language` parameter completely

## Testing

Use the provided test script to verify English transcription:

```bash
./test_english_transcription.sh
```

Or run the full test suite:

```bash
./run_tests.sh
```

## Expected Behavior

- **NbAiLab models**: Will ignore `language=en` and transcribe in Norwegian
- **Faster Whisper**: Will respect `language=en` and transcribe in English
- **OpenAI Whisper**: Will respect `language=en` and transcribe in English
- **WhisperX**: Will respect `language=en` and transcribe in English

## Quick Fix

To immediately fix the issue, run:

```bash
# Stop the current service
# Then set environment variables
export ASR_ENGINE=faster_whisper
export ASR_MODEL=base

# Restart the service
make serve
```

Then test with:

```bash
curl -X POST -F "audio_file=@audio/king_16k.wav" \
  "http://localhost:9000/asr?language=en&output=json"
```

## Configuration

The current default configuration in `app/config.py`:

```python
ASR_ENGINE = os.getenv("ASR_ENGINE", "nbailab_whisper")
MODEL_NAME = os.getenv("ASR_MODEL", "NbAiLab/nb-whisper-large")
```

## Supported ASR Engines

1. **nbailab_whisper** (default) - Norwegian-optimized, **does NOT support language parameter**
2. **faster_whisper** - Fast, multi-language, **supports language parameter**
3. **openai_whisper** - Original OpenAI Whisper, **supports language parameter**
4. **whisperx** - Enhanced with diarization, **supports language parameter**

## Language Codes

Common language codes:
- `en` - English
- `no` - Norwegian
- `auto` - Auto-detect (may not work well with Norwegian-biased models) 
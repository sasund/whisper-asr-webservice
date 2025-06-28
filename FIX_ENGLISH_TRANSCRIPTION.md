# Quick Fix: English Transcription Issue

## Problem
When using `language=en` with NbAiLab Whisper, you still get Norwegian text because NbAiLab models ignore the language parameter.

## Solution: Switch to Faster Whisper

### Step 1: Stop the current service
```bash
# If running with make
make stop

# Or if running with docker
docker-compose down
```

### Step 2: Set environment variables
```bash
export ASR_ENGINE=faster_whisper
export ASR_MODEL=base
```

### Step 3: Restart the service
```bash
make serve
```

### Step 4: Test the fix
```bash
curl -X POST -F "audio_file=@audio/king_16k.wav" \
  "http://localhost:9000/asr?language=en&output=json"
```

## Alternative: Use OpenAI Whisper
```bash
export ASR_ENGINE=openai_whisper
export ASR_MODEL=base
```

## Why This Happens
- NbAiLab Whisper uses HuggingFace pipeline
- HuggingFace pipeline doesn't support `forced_decoder_ids` for language forcing
- The `language` parameter is completely ignored
- Model always assumes Norwegian due to training bias

## Test Scripts
- `./test_english_transcription.sh` - Test if language parameter works
- `./test_nbailab_language_issue.sh` - Demonstrate the issue
- `./run_tests.sh` - Full test suite

## Expected Result
After switching to Faster Whisper or OpenAI Whisper:
- `language=en` should produce English text
- `language=no` should produce Norwegian text
- Auto-detect should work correctly 
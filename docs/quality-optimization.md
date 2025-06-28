# Quality Optimization for ASR

## Environment Variables for Better Quality

### 1. **Use Larger Model**
```bash
# For best quality (slower)
export ASR_MODEL=large

# For good balance (medium)
export ASR_MODEL=medium

# For fast transcription (lower quality)
export ASR_MODEL=base
```

### 2. **Optimize Quantization**
```bash
# For best quality on GPU
export ASR_QUANTIZATION=float32

# For good balance on GPU
export ASR_QUANTIZATION=float16

# For fastest on CPU (lowest quality)
export ASR_QUANTIZATION=int8
```

### 3. **Use NbAiLab Models for Norwegian**
```bash
# Best quality for Norwegian
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-large

# Good balance
export ASR_MODEL=NbAiLab/nb-whisper-medium

# Fast transcription
export ASR_MODEL=NbAiLab/nb-whisper-base
```

### 4. **Enable VAD for Better Quality**
```bash
# In API call, set vad_filter=true
curl -X POST "http://localhost:9000/asr?vad_filter=true" \
  -F "audio_file=@radio.mp3"
```

## Recommended Configurations

### For Best Quality (radio/podcast):
```bash
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-large
export ASR_QUANTIZATION=float32
export ASR_DEVICE=cuda  # If GPU available
```

### For Good Balance:
```bash
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-medium
export ASR_QUANTIZATION=float16
```

### For Live Transcription:
```bash
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-base
export ASR_QUANTIZATION=float16
```

## API Parameters for Better Quality

### High-Quality Transcription:
```bash
curl -X POST "http://localhost:9000/asr" \
  -F "audio_file=@radio.mp3" \
  -F "language=no" \
  -F "initial_prompt=This is Norwegian radio. Transcribe exactly what is said." \
  -F "vad_filter=true" \
  -F "word_timestamps=false"
```

### Live Transcription with Improved Quality:
```bash
# In WebSocket call, specify language
ws://localhost:9000/ws/live-transcribe?language=no
```

## Troubleshooting

### If Quality is Still Poor:
1. **Check Audio Quality** - Radio files should be 16kHz, mono
2. **Use initial_prompt** - Provide context about the content
3. **Enable VAD** - Filter out noise
4. **Specify Language** - Don't use auto-detect for Norwegian radio

### Performance Optimization:
1. **GPU Usage** - Use CUDA if available
2. **Model Caching** - Keep model in memory
3. **Batch Processing** - Process multiple files simultaneously 
# Kvalitetsoptimalisering for ASR

## Miljøvariabler for bedre kvalitet

### 1. **Bruk større modell**
```bash
# For beste kvalitet (langsommere)
export ASR_MODEL=large

# For god balanse (medium)
export ASR_MODEL=medium

# For rask transkribering (mindre kvalitet)
export ASR_MODEL=base
```

### 2. **Optimaliser kvantisering**
```bash
# For beste kvalitet på GPU
export ASR_QUANTIZATION=float32

# For god balanse på GPU
export ASR_QUANTIZATION=float16

# For raskest på CPU (minst kvalitet)
export ASR_QUANTIZATION=int8
```

### 3. **Bruk NbAiLab modeller for norsk**
```bash
# Beste kvalitet for norsk
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-large

# God balanse
export ASR_MODEL=NbAiLab/nb-whisper-medium

# Rask transkribering
export ASR_MODEL=NbAiLab/nb-whisper-base
```

### 4. **Aktiver VAD for bedre kvalitet**
```bash
# I API-kallet, sett vad_filter=true
curl -X POST "http://localhost:9000/asr?vad_filter=true" \
  -F "audio_file=@radio.mp3"
```

## Anbefalte konfigurasjoner

### For beste kvalitet (radio/podcast):
```bash
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-large
export ASR_QUANTIZATION=float32
export ASR_DEVICE=cuda  # Hvis GPU tilgjengelig
```

### For god balanse:
```bash
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-medium
export ASR_QUANTIZATION=float16
```

### For live transkribering:
```bash
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-base
export ASR_QUANTIZATION=float16
```

## API-parametere for bedre kvalitet

### Transkribering med høy kvalitet:
```bash
curl -X POST "http://localhost:9000/asr" \
  -F "audio_file=@radio.mp3" \
  -F "language=no" \
  -F "initial_prompt=Dette er norsk radio. Transkriber nøyaktig det som sies." \
  -F "vad_filter=true" \
  -F "word_timestamps=false"
```

### Live transkribering med forbedret kvalitet:
```bash
# I WebSocket-kallet, spesifiser språk
ws://localhost:9000/ws/live-transcribe?language=no
```

## Feilsøking

### Hvis kvaliteten fortsatt er dårlig:
1. **Sjekk lydkvaliteten** - Radio-filer bør være 16kHz, mono
2. **Bruk initial_prompt** - Gi kontekst om innholdet
3. **Aktiver VAD** - Filtrer ut støy
4. **Spesifiser språk** - Ikke bruk auto-detect for norsk radio

### Ytelsesoptimalisering:
1. **GPU-bruk** - Bruk CUDA hvis tilgjengelig
2. **Modell-caching** - La modellen forbli i minnet
3. **Batch-processing** - Behandle flere filer samtidig 
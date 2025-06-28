# TESTPLAN.md

## Testoppsett

### Forutsetninger

- Python 3.10+ og Poetry installert
- (Valgfritt) Node.js fjernet, kun Python/Poetry brukes
- Alle nødvendige modeller lastes ned automatisk ved første kjøring
- Test-lydfiler finnes i `audio/` og `tests/fixtures/audio_samples/`

### Installasjon

```bash
# Installer avhengigheter
poetry install --with dev

# (Valgfritt) Aktiver venv
poetry shell
```

### Miljøvariabler

Sett relevante miljøvariabler for å teste ulike motorer og modeller:

```bash
# Eksempel for WhisperX
export ASR_ENGINE=whisperx
export ASR_MODEL=large-v2

# Eksempel for Faster Whisper
export ASR_ENGINE=faster_whisper
export ASR_MODEL=large-v2

# Eksempel for OpenAI Whisper
export ASR_ENGINE=openai_whisper
export ASR_MODEL=large-v2

# Eksempel for NbAiLab Whisper
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-large
```

## Test Cases

### 1. REST API: `/asr` (transkribering)

| Modell              | Engine             | Kommandoeksempel                                                                                  | Forventet resultat                |
|---------------------|--------------------|---------------------------------------------------------------------------------------------------|-----------------------------------|
| OpenAI Whisper      | openai_whisper     | `curl -F "audio_file=@audio/king_16k.wav" "localhost:9000/asr?output=json"`                      | JSON med tekst og segmenter       |
| Faster Whisper      | faster_whisper     | `curl -F "audio_file=@audio/king_16k.wav" "localhost:9000/asr?output=srt"`                       | SRT-fil med undertekster          |
| WhisperX            | whisperx           | `curl -F "audio_file=@audio/king_16k.wav" "localhost:9000/asr?output=vtt&diarize=true"`          | VTT-fil, evt. med speaker labels  |
| NbAiLab Whisper     | nbailab_whisper    | `curl -F "audio_file=@audio/king_16k.wav" "localhost:9000/asr?output=txt"`                       | Ren tekst                        |

**Test også:**
- Ulike språk (`?language=no`, `?language=en`)
- Ulike output-formater (`txt`, `json`, `vtt`, `srt`, `tsv`)
- Med/uten VAD (`vad_filter=true`)
- Med/uten word timestamps (`word_timestamps=true`)
- Med/uten diarization (`diarize=true`, `min_speakers`, `max_speakers`)

### 2. REST API: `/detect-language` (språkdeteksjon)

```bash
curl -F "audio_file=@audio/king_16k.wav" "localhost:9000/detect-language"
```
- Forventet: JSON med korrekt språkkode (f.eks. `"no"` for norsk)

### 3. WebSocket: Live Transkribering

- Åpne `static/live_player.html` eller bruk websockets direkte:
```python
import asyncio
import websockets

async def test_ws():
    uri = "ws://localhost:9000/ws/live-transcribe?language=no"
    async with websockets.connect(uri) as websocket:
        with open("audio/king_16k.wav", "rb") as f:
            chunk = f.read(4096)
            await websocket.send(chunk)
            response = await websocket.recv()
            print(response)

asyncio.run(test_ws())
```
- Forventet: Løpende transkripsjon mottas over websocket

### 4. Feilhåndtering

- Prøv å sende ugyldig filformat
- Prøv å sende tom fil
- Prøv å bruke ugyldig modellnavn
- Prøv å bruke ugyldig output-format

Forventet: API returnerer meningsfulle feilmeldinger.

---

## Automatiserte tester

Kjør alle enhetstester og integrasjonstester:

```bash
poetry run pytest tests/
```

---

## Sjekkliste for dekning

- [ ] Alle motorer (engines) testet
- [ ] Alle output-formater testet
- [ ] Språkdeteksjon testet
- [ ] Diarisering testet (WhisperX)
- [ ] VAD og word timestamps testet (Faster Whisper)
- [ ] WebSocket live-transkribering testet
- [ ] Feilhåndtering testet

---

Dette gir deg et komplett testgrunnlag for å verifisere at alle hovedfunksjoner og alle modeller fungerer som forventet! 
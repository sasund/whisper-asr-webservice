import logging
import os
import warnings
from io import StringIO
from threading import Lock
from typing import TextIO, Union

import torch
from transformers.pipelines import pipeline

# Suppress FutureWarning from transformers
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

# Modellnavn og eventuelt cache path
model_name = os.getenv("ASR_MODEL", "NbAiLab/nb-whisper-large")
model_path = os.getenv("ASR_MODEL_PATH", os.path.join(os.path.expanduser("~"), ".cache", "whisper"))

# Bestem device automatisk: CUDA > MPS > CPU
if torch.cuda.is_available():
    device = 0
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = -1

logging.basicConfig(level=logging.INFO)
logging.info(f"[NbAiLab Whisper] Using model: {model_name} (device: {device})")

# Initialiser HuggingFace pipeline
asr_pipeline = None
model_lock = Lock()


def load_model():
    """Load the HuggingFace pipeline if not already loaded."""
    global asr_pipeline
    if asr_pipeline is None:
        with model_lock:
            if asr_pipeline is None:
                logging.info(f"Loading model: {model_name}")
                asr_pipeline = pipeline(
                    "automatic-speech-recognition",
                    model=model_name,
                    device=device,
                    model_kwargs={"cache_dir": model_path},
                )
                logging.info("Model loaded successfully")


def transcribe(
    audio,
    task: Union[str, None],
    language: Union[str, None],
    initial_prompt: Union[str, None],
    vad_filter: Union[bool, None],
    word_timestamps: Union[bool, None],
    output,
):
    """Transcribe audio using NbAiLab Whisper model."""
    load_model()

    if asr_pipeline is None:
        raise RuntimeError("Model failed to load")

    # Forbered transcribe options
    kwargs = {}

    # Language og task parametere støttes ikke av HuggingFace pipeline for NbAiLab modeller
    # Pipeline håndterer språk automatisk basert på modellen
    # Vi logger språket for debugging
    if language:
        logging.info(f"Language specified: {language} (note: NbAiLab model may ignore this parameter)")

    # initial_prompt støttes ikke av HuggingFace pipeline for NbAiLab modeller
    # Så vi hopper over det

    # Sett word timestamps hvis spesifisert
    if word_timestamps:
        kwargs["return_timestamps"] = "word"
    else:
        kwargs["return_timestamps"] = True

    # VAD filter støttes ikke direkte i transformers pipeline

    with model_lock:
        result = asr_pipeline(audio, **kwargs)

    # Konverter til Whisper-format for write_result
    text = result.get("text", "") if isinstance(result, dict) else ""

    # Håndter segments basert på resultatet fra HuggingFace pipeline
    if isinstance(result, dict) and "chunks" in result:
        # HuggingFace pipeline returnerer chunks med timestamps
        segments = []
        chunks = result.get("chunks", [])
        if isinstance(chunks, list):
            for chunk in chunks:
                if isinstance(chunk, dict):
                    segment = {
                        "text": chunk.get("text", ""),
                        "start": chunk.get("timestamp", [0, 0])[0] if isinstance(chunk.get("timestamp"), list) else 0,
                        "end": chunk.get("timestamp", [0, 0])[1] if isinstance(chunk.get("timestamp"), list) else 0,
                    }
                    segments.append(segment)
                else:
                    segments.append({"text": str(chunk), "start": 0, "end": 0})
        else:
            segments = [{"text": text, "start": 0, "end": 0}]
    else:
        # Fallback til enkelt segment
        segments = [{"text": text, "start": 0, "end": 0}]

    whisper_result = {"text": text, "segments": segments}

    output_file = StringIO()
    write_result(whisper_result, output_file, output)
    output_file.seek(0)
    return output_file


def language_detection(audio):
    """Detect language using Whisper model."""
    load_model()

    if asr_pipeline is None:
        raise RuntimeError("Model failed to load")

    # For HuggingFace pipeline, bruk en enkel språkgjenkjenning
    # eller returner norsk som standard for NbAiLab modeller
    try:
        # Prøv å gjøre en kort transkribering for språkgjenkjenning
        with model_lock:
            result = asr_pipeline(audio, return_timestamps=True)

        # Sjekk om resultatet inneholder norske ord
        if isinstance(result, dict):
            text = result.get("text", "").lower()
        else:
            text = str(result).lower()

        norwegian_words = ["er", "og", "i", "til", "av", "på", "som", "det", "at", "en", "et"]

        if any(word in text for word in norwegian_words):
            return "no", 0.9
        else:
            return "en", 0.7  # Fallback til engelsk

    except Exception as e:
        logging.warning(f"Language detection failed: {e}")
        return "no", 0.8  # Standard til norsk for NbAiLab modeller


def write_result(result: dict, file: TextIO, output: Union[str, None]):
    """Write transcription result to file in specified format."""
    if output == "txt":
        # Enkel tekst output
        for segment in result["segments"]:
            if isinstance(segment, dict):
                text = segment.get("text", "")
            else:
                text = str(segment)
            print(text.strip(), file=file, flush=True)
    elif output == "json":
        # JSON output
        import json

        json.dump(result, file, ensure_ascii=False, indent=2)
    elif output == "srt":
        # SRT format
        for i, segment in enumerate(result["segments"], start=1):
            if isinstance(segment, dict):
                text = segment.get("text", "")
                start = segment.get("start", 0)
                end = segment.get("end", 0)
            else:
                text = str(segment)
                start = 0
                end = 0

            # Format timestamps
            start_str = (
                f"{int(start//3600):02d}:{int((start%3600)//60):02d}:{int(start%60):02d},{int((start%1)*1000):03d}"
            )
            end_str = f"{int(end//3600):02d}:{int((end%3600)//60):02d}:{int(end%60):02d},{int((end%1)*1000):03d}"

            print(f"{i}\n{start_str} --> {end_str}\n{text.strip()}\n", file=file, flush=True)
    elif output == "vtt":
        # VTT format
        print("WEBVTT\n", file=file)
        for segment in result["segments"]:
            if isinstance(segment, dict):
                text = segment.get("text", "")
                start = segment.get("start", 0)
                end = segment.get("end", 0)
            else:
                text = str(segment)
                start = 0
                end = 0

            # Format timestamps
            start_str = (
                f"{int(start//3600):02d}:{int((start%3600)//60):02d}:{int(start%60):02d}.{int((start%1)*1000):03d}"
            )
            end_str = f"{int(end//3600):02d}:{int((end%3600)//60):02d}:{int(end%60):02d}.{int((end%1)*1000):03d}"

            print(f"{start_str} --> {end_str}\n{text.strip()}\n", file=file, flush=True)
    elif output == "tsv":
        # TSV format
        print("start\tend\ttext", file=file)
        for segment in result["segments"]:
            if isinstance(segment, dict):
                text = segment.get("text", "")
                start = segment.get("start", 0)
                end = segment.get("end", 0)
            else:
                text = str(segment)
                start = 0
                end = 0

            print(f"{int(start*1000)}\t{int(end*1000)}\t{text.strip()}", file=file, flush=True)
    else:
        return "Please select an output method!"

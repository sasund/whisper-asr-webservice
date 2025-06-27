import os
from io import StringIO
from threading import Lock
from typing import Union, TextIO
import logging

import torch
from transformers.pipelines import pipeline

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
asr_pipeline = pipeline(
    "automatic-speech-recognition",
    model=model_name,
    device=device,
    model_kwargs={"cache_dir": model_path},
)
model_lock = Lock()


def transcribe(
    audio,
    task: Union[str, None],
    language: Union[str, None],
    initial_prompt: Union[str, None],
    vad_filter: Union[bool, None],
    word_timestamps: Union[bool, None],
    output,
):
    # transformers pipeline tar filsti eller np.array
    kwargs = {}
    if language:
        kwargs["generate_kwargs"] = {"language": language}
    if task:
        if "generate_kwargs" not in kwargs:
            kwargs["generate_kwargs"] = {}
        kwargs["generate_kwargs"]["task"] = task
    if word_timestamps:
        kwargs["return_timestamps"] = "word"
    else:
        kwargs["return_timestamps"] = True
    # initial_prompt og vad_filter støttes ikke direkte
    with model_lock:
        result = asr_pipeline(audio, **kwargs)

    # Konverter til Whisper-format for write_result
    text = result.get("text", "") if isinstance(result, dict) else ""
    segments = result.get("chunks") if isinstance(result, dict) and "chunks" in result else [{"text": text}]
    whisper_result = {"text": text, "segments": segments}

    output_file = StringIO()
    write_result(whisper_result, output_file, output)
    output_file.seek(0)
    return output_file


def language_detection(audio):
    # transformers pipeline støtter ikke direkte språkgjenkjenning
    return "no"


def write_result(result: dict, file: TextIO, output: Union[str, None]):
    # Gjenbruker samme format som openai_whisper
    # NB: Krever at OpenAI Whisper er installert (pip install openai-whisper)
    from whisper.utils import WriteJSON, WriteSRT, WriteTSV, WriteTXT, WriteVTT
    options = {"max_line_width": 1000, "max_line_count": 10, "highlight_words": False}
    # NB: WriteSRT() osv. brukes kun for filobjekt, ikke for disk
    if output == "srt":
        WriteSRT("").write_result(result, file=file, options=options)
    elif output == "vtt":
        WriteVTT("").write_result(result, file=file, options=options)
    elif output == "tsv":
        WriteTSV("").write_result(result, file=file, options=options)
    elif output == "json":
        WriteJSON("").write_result(result, file=file, options=options)
    elif output == "txt":
        WriteTXT("").write_result(result, file=file, options=options)
    else:
        return "Please select an output method!" 
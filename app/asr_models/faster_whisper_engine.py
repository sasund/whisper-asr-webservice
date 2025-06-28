import time
from io import StringIO
from threading import Thread
from typing import TextIO, Union

from faster_whisper import WhisperModel

from app.asr_models.asr_model import ASRModel
from app.config import CONFIG
from app.output.result_writers import WriteJSON, WriteSRT, WriteTSV, WriteTXT, WriteVTT


class FasterWhisperASR(ASRModel):

    def load_model(self):

        self.model = WhisperModel(
            model_size_or_path=CONFIG.MODEL_NAME,
            device=CONFIG.DEVICE,
            compute_type=CONFIG.MODEL_QUANTIZATION,
            download_root=CONFIG.MODEL_PATH,
        )

        Thread(target=self.monitor_idleness, daemon=True).start()

    def transcribe(
        self,
        audio,
        task: Union[str, None],
        language: Union[str, None],
        initial_prompt: Union[str, None],
        vad_filter: Union[bool, None],
        word_timestamps: Union[bool, None],
        options: Union[dict, None],
        output,
    ):
        self.last_activity_time = time.time()

        with self.model_lock:
            if self.model is None:
                self.load_model()

        options_dict = {}
        if task:
            options_dict["task"] = task
        if language:
            options_dict["language"] = language
        if initial_prompt:
            options_dict["initial_prompt"] = initial_prompt
        if vad_filter:
            options_dict["vad_filter"] = True
        if word_timestamps:
            options_dict["word_timestamps"] = True

        with self.model_lock:
            segments = []
            text = ""
            segment_generator, info = self.model.transcribe(audio, beam_size=5, **options_dict)
            for segment in segment_generator:
                segments.append(segment)
                text = text + segment.text
            result = {"language": options_dict.get("language", info.language), "segments": segments, "text": text}

        output_file = StringIO()
        self.write_result(result, output_file, output)
        output_file.seek(0)

        return output_file

    def language_detection(self, audio):

        self.last_activity_time = time.time()

        with self.model_lock:
            if self.model is None:
                self.load_model()

        # detect the spoken language
        with self.model_lock:
            segments, info = self.model.transcribe(audio, beam_size=5)
            detected_lang_code = info.language
            detected_language_confidence = info.language_probability

        return detected_lang_code, detected_language_confidence

    def write_result(self, result: dict, file: TextIO, output: Union[str, None]):
        if output == "srt":
            writer = WriteSRT("")
            writer.write_result(result, file=file)
        elif output == "vtt":
            writer = WriteVTT("")
            writer.write_result(result, file=file)
        elif output == "tsv":
            writer = WriteTSV("")
            writer.write_result(result, file=file)
        elif output == "json":
            writer = WriteJSON("")
            writer.write_result(result, file=file)
        else:
            writer = WriteTXT("")
            writer.write_result(result, file=file)

import pytest

from app.asr_models.faster_whisper_engine import FasterWhisperASR
from app.asr_models.mbain_whisperx_engine import WhisperXASR
from app.asr_models.openai_whisper_engine import OpenAIWhisperASR
from app.config import CONFIG
from app.exceptions import UnsupportedEngineError
from app.factory.asr_model_factory import ASRModelFactory, NbAiLabWhisperASR


def test_factory_returns_openai_whisper(monkeypatch):
    monkeypatch.setattr(CONFIG, "ASR_ENGINE", "openai_whisper")
    model = ASRModelFactory.create_asr_model()
    assert isinstance(model, OpenAIWhisperASR)


def test_factory_returns_faster_whisper(monkeypatch):
    monkeypatch.setattr(CONFIG, "ASR_ENGINE", "faster_whisper")
    model = ASRModelFactory.create_asr_model()
    assert isinstance(model, FasterWhisperASR)


def test_factory_returns_whisperx(monkeypatch):
    monkeypatch.setattr(CONFIG, "ASR_ENGINE", "whisperx")
    model = ASRModelFactory.create_asr_model()
    assert isinstance(model, WhisperXASR)


def test_factory_returns_nbailab_whisper(monkeypatch):
    monkeypatch.setattr(CONFIG, "ASR_ENGINE", "nbailab_whisper")
    model = ASRModelFactory.create_asr_model()
    assert isinstance(model, NbAiLabWhisperASR)


def test_factory_raises_on_invalid_engine(monkeypatch):
    monkeypatch.setattr(CONFIG, "ASR_ENGINE", "invalid_engine")
    with pytest.raises(UnsupportedEngineError):
        ASRModelFactory.create_asr_model()

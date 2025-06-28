import os
import tempfile
from unittest.mock import Mock

import numpy as np
import pytest

from app.asr_models.asr_model import ASRModel
from app.services.asr_service import ASRService


@pytest.fixture
def mock_asr_model():
    """Create a mock ASR model for testing."""
    model = Mock(spec=ASRModel)
    model.transcribe.return_value = Mock()
    model.language_detection.return_value = ("en", 0.95)
    return model


@pytest.fixture
def asr_service(mock_asr_model):
    """Create an ASR service with a mock model."""
    return ASRService(mock_asr_model)


@pytest.fixture
def sample_audio_data():
    """Create sample audio data for testing."""
    # Generate 1 second of 16kHz sine wave
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0  # A4 note

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)

    return audio_data


@pytest.fixture
def temp_audio_file(sample_audio_data):
    """Create a temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Write as 16-bit PCM
        audio_int16 = (sample_audio_data * 32767).astype(np.int16)
        f.write(audio_int16.tobytes())
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing."""
    mock_file = Mock()
    mock_file.filename = "test_audio.wav"
    mock_file.file = Mock()
    mock_file.file.read.return_value = b"fake_audio_data"
    return mock_file

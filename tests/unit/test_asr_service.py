from unittest.mock import patch

import pytest


@pytest.mark.asyncio
@patch('app.services.asr_service.load_audio', return_value=[0.0, 0.1, 0.2])
async def test_transcribe_audio_calls_model_transcribe(mock_load_audio, asr_service, mock_upload_file):
    response = await asr_service.transcribe_audio(audio_file=mock_upload_file)
    # Should return a StreamingResponse
    from fastapi.responses import StreamingResponse

    assert isinstance(response, StreamingResponse)


@pytest.mark.asyncio
@patch('app.services.asr_service.load_audio', return_value=[0.0, 0.1, 0.2])
async def test_detect_language_returns_expected_dict(mock_load_audio, asr_service, mock_upload_file):
    result = await asr_service.detect_language(audio_file=mock_upload_file)
    assert isinstance(result, dict)
    assert result["language_code"] == "en"
    assert result["confidence"] == 0.95

class ASRException(Exception):
    """Base exception for ASR-related errors."""

    pass


class ModelLoadError(ASRException):
    """Raised when there's an error loading the ASR model."""

    pass


class TranscriptionError(ASRException):
    """Raised when there's an error during transcription."""

    pass


class AudioLoadError(ASRException):
    """Raised when there's an error loading audio files."""

    pass


class UnsupportedEngineError(ASRException):
    """Raised when an unsupported ASR engine is requested."""

    pass


class ConfigurationError(ASRException):
    """Raised when there's a configuration error."""

    pass


class WebSocketError(ASRException):
    """Raised when there's an error in WebSocket communication."""

    pass

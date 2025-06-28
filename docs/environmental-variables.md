### Configuring the `Engine`

=== ":octicons-file-code-16: `openai_whisper`"

    ```shell
    export ASR_ENGINE=openai_whisper
    ```

=== ":octicons-file-code-16: `faster_whisper`"

    ```shell
    export ASR_ENGINE=faster_whisper
    ```
=== ":octicons-file-code-16: `nbailab_whisper`"
    ```sh
    export ASR_ENGINE=nbailab_whisper
    export ASR_MODEL=NbAiLab/nb-whisper-large  # or other model from https://huggingface.co/NbAiLab
    ```

=== ":octicons-file-code-16: `whisperx`"

    ```shell
    export ASR_ENGINE=whisperx
    ```

### Configuring the `Model`

```shell
export ASR_MODEL=base
```

Available ASR_MODELs are:

- Standard models: `tiny`, `base`, `small`, `medium`, `large-v1`, `large-v2`, `large-v3` (or `large`), `large-v3-turbo` (or `turbo`)
- English-optimized models: `tiny.en`, `base.en`, `small.en`, `medium.en`
- Distilled models: `distil-large-v2`, `distil-medium.en`, `distil-small.en`, `distil-large-v3` (only for whisperx and faster-whisper)

For English-only applications, the `.en` models tend to perform better, especially for the `tiny.en` and `base.en`
models. We observed that the difference becomes less significant for the `small.en` and `medium.en` models.

The distilled models offer improved inference speed while maintaining good accuracy.

### NbAiLab Whisper Models

When using `ASR_ENGINE=nbailab_whisper`, you can use any of the following Norwegian-optimized models:

#### Standard Models (Recommended)
- `NbAiLab/nb-whisper-tiny` - Fastest, smallest model
- `NbAiLab/nb-whisper-base` - Good balance of speed and accuracy
- `NbAiLab/nb-whisper-small` - Better accuracy than base
- `NbAiLab/nb-whisper-medium` - High accuracy, moderate speed
- `NbAiLab/nb-whisper-large` - Best accuracy, slower inference

#### Beta Models (Latest versions)
- `NbAiLab/nb-whisper-tiny-beta` - Latest tiny model
- `NbAiLab/nb-whisper-base-beta` - Latest base model
- `NbAiLab/nb-whisper-small-beta` - Latest small model
- `NbAiLab/nb-whisper-medium-beta` - Latest medium model
- `NbAiLab/nb-whisper-large-beta` - Latest large model

#### Verbatim Models (Preserves exact pronunciation)
- `NbAiLab/nb-whisper-tiny-verbatim` - Preserves pronunciation details
- `NbAiLab/nb-whisper-base-verbatim` - Preserves pronunciation details
- `NbAiLab/nb-whisper-small-verbatim` - Preserves pronunciation details
- `NbAiLab/nb-whisper-medium-verbatim` - Preserves pronunciation details
- `NbAiLab/nb-whisper-large-verbatim` - Preserves pronunciation details

#### Semantic Models (Better understanding of context)
- `NbAiLab/nb-whisper-tiny-semantic` - Better context understanding
- `NbAiLab/nb-whisper-base-semantic` - Better context understanding
- `NbAiLab/nb-whisper-small-semantic` - Better context understanding
- `NbAiLab/nb-whisper-medium-semantic` - Better context understanding
- `NbAiLab/nb-whisper-large-semantic` - Better context understanding

#### Specialized Models
- `NbAiLab/nb-whisper-large-distil-turbo-beta` - Fast large model
- `NbAiLab/nb-whisper-large-v0.8` - Legacy large model
- `NbAiLabBeta/nb-whisper-large-des23` - Specialized model

#### Example Usage
```bash
# For production use (recommended)
export ASR_ENGINE=nbailab_whisper
export ASR_MODEL=NbAiLab/nb-whisper-large

# For faster inference
export ASR_MODEL=NbAiLab/nb-whisper-base

# For latest beta version
export ASR_MODEL=NbAiLab/nb-whisper-large-beta

# For preserving exact pronunciation
export ASR_MODEL=NbAiLab/nb-whisper-large-verbatim
```

For English-only applications, the `.en` models tend to perform better, especially for the `tiny.en` and `base.en`
models. We observed that the difference becomes less significant for the `small.en` and `medium.en` models.

The distilled models offer improved inference speed while maintaining good accuracy.

### Configuring the `Model Path`

```shell
export ASR_MODEL_PATH=/data/whisper
```

### Configuring the `Model Unloading Timeout`

```shell
export MODEL_IDLE_TIMEOUT=300
```

Defaults to `0`. After no activity for this period (in seconds), unload the model until it is requested again. Setting
`0` disables the timeout, keeping the model loaded indefinitely.

### Configuring the `SAMPLE_RATE`

```shell
export SAMPLE_RATE=16000
```

Defaults to `16000`. Default sample rate for audio input. `16 kHz` is commonly used in `speech-to-text` tasks.

### Configuring Device and Quantization

```shell
export ASR_DEVICE=cuda  # or 'cpu'
export ASR_QUANTIZATION=float32  # or 'float16', 'int8'
```

The `ASR_DEVICE` defaults to `cuda` if GPU is available, otherwise `cpu`. 

The `ASR_QUANTIZATION` defines the precision for model weights:

- `float32`: 32-bit floating-point precision (higher precision, slower inference)
- `float16`: 16-bit floating-point precision (lower precision, faster inference)
- `int8`: 8-bit integer precision (lowest precision, fastest inference)

Defaults to `float32` for GPU, `int8` for CPU.

### Configuring Subtitle Options (WhisperX)

```shell
export SUBTITLE_MAX_LINE_WIDTH=1000
export SUBTITLE_MAX_LINE_COUNT=2
export SUBTITLE_HIGHLIGHT_WORDS=false
```

These options only apply when using the WhisperX engine:

- `SUBTITLE_MAX_LINE_WIDTH`: Maximum width of subtitle lines (default: 1000)
- `SUBTITLE_MAX_LINE_COUNT`: Maximum number of lines per subtitle (default: 2)
- `SUBTITLE_HIGHLIGHT_WORDS`: Enable word highlighting in subtitles (default: false)

### Hugging Face Token

```shell
export HF_TOKEN=your_token_here
```

Required when using the WhisperX engine to download the diarization model.

# Klok Audio Processing Pipeline

A comprehensive audio processing pipeline that separates vocals from audio files and generates MIDI using multiple methods.

## Features

🎤 **Vocal Separation**: Uses Demucs to separate vocals from music tracks  
🎹 **Pitch-based MIDI**: Generates MIDI using librosa pitch analysis  
🤖 **Neural Network MIDI**: Generates MIDI using Basic Pitch neural network  
⚡ **Batch Processing**: Process multiple files efficiently  
🔧 **Customizable**: Configure models, devices, and output formats  

## Quick Start

### Installation

```bash
# Install dependencies using uv
uv sync

# Or install specific packages with uv if needed
uv add demucs librosa matplotlib mido onnxruntime pretty-midi torch numpy scipy
```

### Basic Usage

```python
from audio_pipeline import process_audio_file

# Process a single audio file
results = process_audio_file("my_song.mp3")

# Results contain paths to generated files:
# - vocals_path: separated vocals
# - pitch_midi_path: MIDI from pitch analysis  
# - basic_pitch_midi_path: MIDI from neural network
```

### Command Line Usage

```bash
# Process an audio file
python audio_pipeline.py my_song.mp3

# Specify output directory
python audio_pipeline.py my_song.mp3 -o output/

# Use different Demucs model
python audio_pipeline.py my_song.mp3 -m htdemucs

# Force CPU processing
python audio_pipeline.py my_song.mp3 -d cpu

# Skip certain MIDI generation methods
python audio_pipeline.py my_song.mp3 --no-basic-pitch
```

## Requirements

- Python 3.8+
- PyTorch, Demucs, librosa, ONNX Runtime
- Audio file formats: MP3, WAV, M4A, etc.

## Pipeline Steps

1. **Input**: Audio file → 2. **Vocal Separation** → 3. **MIDI Generation** → 4. **Output Files**

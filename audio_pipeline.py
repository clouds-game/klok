#!/usr/bin/env python3
# %%
"""
Audio Processing Pipeline

This module provides a complete pipeline for processing audio files:
1. Separates vocals from the input audio using Demucs
2. Generates MIDI using both pitch analysis (librosa) and Basic Pitch (neural network)
3. Outputs the separated vocals and generated MIDI files
"""

import sys
from pathlib import Path
import platform
import time
import numpy as np

workspace_dir = Path(__file__).parent
sys.path.append(str(workspace_dir / "analysis"))

from analysis.vocal_separation import separate_audio
from analysis.pitch import get_audio_pitches, pitch_to_midi_notes, notes_to_midi
from analysis.basic_pitch.inference import transform_to_midi

# %%
class AudioPipeline:
    """
    A pipeline for processing audio files to extract vocals and generate MIDI.
    """

    def __init__(self,
                 model_name: str = "mdx_extra",
                 device: str | None = None,
                 output_ext: str = "mp3",
                 hop_length: int = 512):
        """
        Initialize the audio pipeline.

        Args:
            model_name: Demucs model name for vocal separation
            device: Device to use ("cpu", "cuda", "mps"). Auto-detected if None.
            output_ext: Extension for separated audio files
            hop_length: Hop length for pitch analysis (default: 512)
        """
        self.model_name = model_name
        self.output_ext = output_ext
        self.hop_length = hop_length

        if device is None:
            # Auto-detect device
            if platform.system() == "Darwin":
                self.device = "mps"  # Metal Performance Shaders for macOS
            else:
                self.device = "cuda"  # CUDA for Linux/Windows
        else:
            self.device = device

    def process_audio(self,
                     audio_path: Path,
                     output_dir: Path | None = None,
                     generate_pitch_midi: bool = True,
                     generate_basic_pitch_midi: bool = True) -> dict:
        """
        Complete audio processing pipeline.

        Args:
            audio_path: Path to input audio file
            output_dir: Directory for output files. Uses audio file directory if None.
            generate_pitch_midi: Whether to generate MIDI using pitch analysis
            generate_basic_pitch_midi: Whether to generate MIDI using Basic Pitch

        Returns:
            Dictionary containing paths to generated files:
            {
                'vocals_path': Path to separated vocals,
                'pitch_midi_path': Path to pitch-based MIDI (if generated),
                'basic_pitch_midi_path': Path to Basic Pitch MIDI (if generated)
            }
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        output_dir = output_dir or audio_path.parent
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = audio_path.stem
        results = {}

        print(f"🎵 Processing audio file: {audio_path.name}")

        # Step 1: Vocal separation
        print("🎤 Separating vocals...")
        start_time = time.time()
        try:
            separate_audio(
                audio_path,
                model_name=self.model_name,
                device=self.device,
                out_dir=output_dir,
                ext=self.output_ext
            )

            vocals_path = output_dir / f"{base_name}_vocals.{self.output_ext}"
            results['vocals_path'] = vocals_path
            elapsed = time.time() - start_time
            print(f"✅ Vocals saved to: {vocals_path} (took {elapsed:.2f}s)")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Vocal separation failed: {e} (took {elapsed:.2f}s)")
            raise

        # Step 2: Generate MIDI using pitch analysis
        if generate_pitch_midi:
            print("🎹 Generating MIDI using pitch analysis...")
            start_time = time.time()
            try:
                pitch_midi_path = self._generate_pitch_midi(vocals_path, output_dir)
                results['pitch_midi_path'] = pitch_midi_path
                elapsed = time.time() - start_time
                print(f"✅ Pitch MIDI saved to: {pitch_midi_path} (took {elapsed:.2f}s)")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"⚠️ Pitch MIDI generation failed: {e} (took {elapsed:.2f}s)")
                results['pitch_midi_path'] = None

        # Step 3: Generate MIDI using Basic Pitch
        if generate_basic_pitch_midi:
            print("🤖 Generating MIDI using Basic Pitch...")
            start_time = time.time()
            try:
                basic_pitch_midi_path = self._generate_basic_pitch_midi(vocals_path, output_dir)
                results['basic_pitch_midi_path'] = basic_pitch_midi_path
                elapsed = time.time() - start_time
                print(f"✅ Basic Pitch MIDI saved to: {basic_pitch_midi_path} (took {elapsed:.2f}s)")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"⚠️ Basic Pitch MIDI generation failed: {e} (took {elapsed:.2f}s)")
                results['basic_pitch_midi_path'] = None

        print("🎉 Pipeline completed successfully!")
        return results

    def _generate_pitch_midi(self, vocals_path: Path, output_dir: Path) -> Path:
        """Generate MIDI using pitch analysis (librosa)."""
        import librosa
        import numpy as np

        # Load audio
        y, sr = librosa.load(str(vocals_path), sr=None)

        # Extract pitch information
        pitches, voiced_flag, voiced_prob, rms = get_audio_pitches(
            y, sr, hop_length=self.hop_length, audio_path=vocals_path
        )

        # Convert to MIDI notes
        notes = pitch_to_midi_notes(pitches, rms, sr, hop_length=self.hop_length)

        # Save MIDI file
        midi_path = output_dir / f"{vocals_path.stem}_pitch.mid"
        notes_to_midi(notes, midi_path)

        return midi_path

    def _generate_basic_pitch_midi(self, vocals_path: Path, output_dir: Path) -> Path:
        """Generate MIDI using Basic Pitch neural network."""
        midi_path = output_dir / f"{vocals_path.stem}_basic_pitch.mid"
        transform_to_midi(vocals_path, midi_path)
        return midi_path


def process_audio_file(audio_path: str,
                      output_dir: Path | None = None,
                      model_name: str = "mdx_extra",
                      device: str | None = None) -> dict:
    """
    Convenience function to process a single audio file.

    Args:
        audio_path: Path to audio file
        output_dir: Output directory (optional)
        model_name: Demucs model name
        device: Processing device (auto-detected if None)

    Returns:
        Dictionary with paths to generated files
    """
    pipeline = AudioPipeline(model_name=model_name, device=device)
    return pipeline.process_audio(
        Path(audio_path),
        Path(output_dir) if output_dir else None
    )


def main():
    """Command line interface for the audio pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Audio processing pipeline: vocal separation + MIDI generation"
    )
    parser.add_argument("audio_path", help="Path to input audio file")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-m", "--model", default="mdx_extra",
                       help="Demucs model name (default: mdx_extra)")
    parser.add_argument("-d", "--device", help="Device (cpu/cuda/mps)")
    parser.add_argument("--no-pitch", action="store_true",
                       help="Skip pitch-based MIDI generation")
    parser.add_argument("--no-basic-pitch", action="store_true",
                       help="Skip Basic Pitch MIDI generation")

    args = parser.parse_args()

    pipeline = AudioPipeline(model_name=args.model, device=args.device)

    try:
        results = pipeline.process_audio(
            Path(args.audio_path),
            Path(args.output) if args.output else None,
            generate_pitch_midi=not args.no_pitch,
            generate_basic_pitch_midi=not args.no_basic_pitch
        )

        print("\n📁 Generated files:")
        for key, path in results.items():
            if path:
                print(f"  {key}: {path}")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

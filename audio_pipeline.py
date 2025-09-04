#!/usr/bin/env python3
"""
Audio Processing Pipeline

This module provides a complete pipeline for processing audio files:
1. Separates vocals from the input audio using Demucs
2. Generates MIDI using both pitch analysis (librosa) and Basic Pitch (neural network)
3. Outputs the separated vocals and generated MIDI files
"""

import sys
from pathlib import Path
from typing import Optional, Tuple, List
import platform
import time
import numpy as np

# Add analysis directory to path for imports
sys.path.append(str(Path(__file__).parent / "analysis"))

# Import functions with graceful fallback for missing dependencies
def import_with_fallback():
    """Import analysis modules with fallback for missing dependencies."""
    try:
        from analysis.vocal_separation import separate_audio
        from analysis.pitch import get_audio_info, pitch_to_midi_notes, notes_to_midi
        from analysis.basic_pitch.inference import transform_to_midi
        return separate_audio, get_audio_info, pitch_to_midi_notes, notes_to_midi, transform_to_midi
    except ImportError:
        try:
            # Fallback imports for when running from analysis directory
            from vocal_separation import separate_audio
            from pitch import get_audio_info, pitch_to_midi_notes, notes_to_midi
            from basic_pitch.inference import transform_to_midi
            return separate_audio, get_audio_info, pitch_to_midi_notes, notes_to_midi, transform_to_midi
        except ImportError as e:
            # Return None values if dependencies are missing
            return None, None, None, None, None


# Global variables for imported functions
separate_audio = None
get_audio_info = None
pitch_to_midi_notes = None
notes_to_midi = None
transform_to_midi = None


class AudioPipeline:
    """
    A pipeline for processing audio files to extract vocals and generate MIDI.
    """
    
    def __init__(self, 
                 model_name: str = "mdx_extra",
                 device: Optional[str] = None,
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
        
        # Check if dependencies are available
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        # Initialize imports if not already done
        global separate_audio, get_audio_info, pitch_to_midi_notes, notes_to_midi, transform_to_midi
        if separate_audio is None:
            import_result = import_with_fallback()
            separate_audio, get_audio_info, pitch_to_midi_notes, notes_to_midi, transform_to_midi = import_result
        
        missing_deps = []
        
        if separate_audio is None:
            missing_deps.extend(["demucs", "librosa"])
        if get_audio_info is None:
            missing_deps.extend(["librosa", "matplotlib", "mido"])
        if transform_to_midi is None:
            missing_deps.extend(["onnxruntime", "pretty-midi"])
        
        if missing_deps:
            self._missing_deps = list(set(missing_deps))
        else:
            self._missing_deps = None
    
    def _raise_if_missing_deps(self, operation: str):
        """Raise informative error if dependencies are missing."""
        if self._missing_deps:
            deps_str = ", ".join(self._missing_deps)
            raise ImportError(
                f"Cannot perform {operation} - missing dependencies: {deps_str}\n"
                f"Install with: pip install {deps_str}"
            )
    
    def process_audio(self, 
                     audio_path: Path,
                     output_dir: Optional[Path] = None,
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
        self._raise_if_missing_deps("audio processing")
        
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
            # Check for cached sources
            cache_path = output_dir / f"{base_name}_sources.npz"
            
            sources = separate_audio(
                audio_path,
                model_name=self.model_name,
                device=self.device,
                out_dir=output_dir,
                ext=self.output_ext
            )
            
            # Cache sources to npz
            if hasattr(sources, 'cpu'):
                # If sources is a tensor, convert to numpy and cache
                sources_np = sources.cpu().numpy()
                np.savez_compressed(cache_path, sources=sources_np)
                print(f"💾 Cached sources to: {cache_path}")
            
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
        pitches, voiced_flag, voiced_prob, rms = get_audio_info(
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
                      output_dir: Optional[str] = None,
                      model_name: str = "mdx_extra",
                      device: Optional[str] = None) -> dict:
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
    # Initialize imported functions when run as script
    import_result = import_with_fallback()
    separate_audio, get_audio_info, pitch_to_midi_notes, notes_to_midi, transform_to_midi = import_result
    
    main()
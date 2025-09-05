#!/usr/bin/env python3
"""
Example usage of the audio processing pipeline.

This script demonstrates how to use the audio pipeline to process audio files.
"""

from pathlib import Path
from audio_pipeline import AudioPipeline, process_audio_file


def example_basic_usage():
    """Example of basic pipeline usage."""
    print("🎵 Basic Usage Example")
    print("-" * 30)
    
    # Path to sample audio
    audio_path = Path("res/我的一个道姑朋友.m4a")
    
    if not audio_path.exists():
        print(f"❌ Sample audio not found: {audio_path}")
        print("💡 Please place an audio file at the above path or change the path.")
        return
    
    # Simple function call
    try:
        results = process_audio_file(str(audio_path))
        
        print("✅ Processing completed!")
        print("📁 Generated files:")
        for key, path in results.items():
            print(f"  {key}: {path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_advanced_usage():
    """Example of advanced pipeline usage with custom options."""
    print("\n🎵 Advanced Usage Example")
    print("-" * 30)
    
    audio_path = Path("res/我的一个道姑朋友.m4a")
    
    if not audio_path.exists():
        print(f"❌ Sample audio not found: {audio_path}")
        return
    
    # Create custom output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Create pipeline with custom settings
    pipeline = AudioPipeline(
        model_name="mdx_extra",  # Demucs model
        device="cpu",            # Force CPU (for compatibility)
        output_ext="wav"         # Use WAV for separated audio
    )
    
    try:
        results = pipeline.process_audio(
            audio_path,
            output_dir=output_dir,
            generate_pitch_midi=True,      # Generate librosa-based MIDI
            generate_basic_pitch_midi=True # Generate neural network MIDI
        )
        
        print("✅ Advanced processing completed!")
        print("📁 Generated files:")
        for key, path in results.items():
            if path:
                print(f"  {key}: {path}")
                print(f"    Size: {path.stat().st_size} bytes")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_midi_only():
    """Example of generating MIDI from pre-separated vocals."""
    print("\n🎵 MIDI-Only Example")
    print("-" * 30)
    
    # Check if vocals already exist
    vocals_path = Path("res/我的一个道姑朋友_vocals.mp3")
    
    if vocals_path.exists():
        print(f"📁 Found existing vocals: {vocals_path}")
        
        pipeline = AudioPipeline()
        
        try:
            # Generate only MIDI files from existing vocals
            output_dir = vocals_path.parent
            
            print("🎹 Generating pitch-based MIDI...")
            pitch_midi = pipeline._generate_pitch_midi(vocals_path, output_dir)
            print(f"✅ Saved: {pitch_midi}")
            
            print("🤖 Generating Basic Pitch MIDI...")
            basic_midi = pipeline._generate_basic_pitch_midi(vocals_path, output_dir)
            print(f"✅ Saved: {basic_midi}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print(f"❌ No pre-separated vocals found at: {vocals_path}")
        print("💡 Run the full pipeline first to generate vocals.")


def main():
    """Run all examples."""
    print("🎼 Klok Audio Pipeline Examples")
    print("=" * 40)
    
    try:
        # Run examples
        example_basic_usage()
        example_advanced_usage()
        example_midi_only()
        
    except ImportError as e:
        print(f"\n⚠️  Missing dependencies: {e}")
        print("💡 Please install required packages:")
        print("   pip install demucs librosa matplotlib mido onnxruntime pretty-midi torch")
        print("\n📝 Or install using the project dependencies:")
        print("   pip install -e .")
    
    print("\n" + "=" * 40)
    print("🎯 Next steps:")
    print("  1. Install dependencies if needed")
    print("  2. Place your audio files in the res/ directory")
    print("  3. Run: python audio_pipeline.py your_audio.mp3")
    print("  4. Check the generated vocals and MIDI files!")


if __name__ == "__main__":
    main()
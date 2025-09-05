def main():
    """
    Main entry point for the Klok audio processing application.
    Processes audio files with vocal separation and MIDI generation.
    """
    import argparse
    from pathlib import Path
    from audio_pipeline import AudioPipeline
    
    parser = argparse.ArgumentParser(
        description="Klok Audio Processing Pipeline: vocal separation + MIDI generation"
    )
    parser.add_argument("audio_path", nargs="?", 
                       help="Path to input audio file (.m4a, .mp3, .wav, etc.)")
    parser.add_argument("-o", "--output", 
                       help="Output directory for generated files")
    parser.add_argument("-m", "--model", default="mdx_extra", 
                       help="Demucs model name (default: mdx_extra)")
    parser.add_argument("-d", "--device", 
                       help="Device (cpu/cuda/mps, auto-detected if not specified)")
    parser.add_argument("--no-pitch", action="store_true", 
                       help="Skip pitch-based MIDI generation")
    parser.add_argument("--no-basic-pitch", action="store_true", 
                       help="Skip Basic Pitch neural network MIDI generation")
    
    args = parser.parse_args()
    
    print("🎵 Welcome to Klok Audio Processing Pipeline!")
    print("=" * 50)
    
    # Determine input audio file
    if args.audio_path:
        audio_path = Path(args.audio_path)
        if not audio_path.exists():
            print(f"❌ Audio file not found: {audio_path}")
            return 1
    else:
        # Default to sample audio in res/ folder
        audio_path = Path("res/我的一个道姑朋友.m4a")
        if not audio_path.exists():
            print("📂 No audio file specified and no sample audio found in res/")
            print("💡 Usage examples:")
            print("   python main.py audio_file.m4a")
            print("   python main.py audio_file.mp3 -o output_directory")
            print("   python main.py  # (uses sample audio in res/ directory)")
            return 1
        print(f"📁 Using sample audio: {audio_path}")
    
    print(f"🎵 Processing: {audio_path}")
    
    # Create pipeline with specified options
    pipeline = AudioPipeline(model_name=args.model, device=args.device)
    
    try:
        print("\n🚀 Starting audio processing pipeline...")
        results = pipeline.process_audio(
            audio_path,
            Path(args.output) if args.output else None,
            generate_pitch_midi=not args.no_pitch,
            generate_basic_pitch_midi=not args.no_basic_pitch
        )
        
        print("\n✅ Processing completed successfully!")
        print("\n📁 Generated files:")
        for key, path in results.items():
            if path and path.exists():
                print(f"  📄 {key}: {path}")
                
    except ImportError as e:
        print(f"⚠️  Missing dependencies: {e}")
        print("💡 Please install required packages with uv:")
        print("   uv sync")
        return 1
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        print("\n💡 You can also run the pipeline manually:")
        print(f"   python audio_pipeline.py \"{audio_path}\"")
        return 1
    
    print("\n" + "=" * 50)
    print("🎼 Pipeline features used:")
    print("  🎤 Vocal separation using Demucs")
    if not args.no_pitch:
        print("  🎹 MIDI generation using pitch analysis (librosa)")
    if not args.no_basic_pitch:
        print("  🤖 MIDI generation using Basic Pitch neural network")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

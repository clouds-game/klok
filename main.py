def main():
    """
    Main entry point for the Klok audio processing application.
    Demonstrates the audio pipeline functionality.
    """
    from pathlib import Path
    from audio_pipeline import AudioPipeline
    
    print("🎵 Welcome to Klok Audio Processing Pipeline!")
    print("=" * 50)
    
    # Check for sample audio file
    sample_audio = Path("res/我的一个道姑朋友.m4a")
    
    if sample_audio.exists():
        print(f"📁 Found sample audio: {sample_audio}")
        
        # Create pipeline
        pipeline = AudioPipeline()
        
        try:
            print("\n🚀 Starting audio processing pipeline...")
            results = pipeline.process_audio(sample_audio)
            
            print("\n✅ Processing completed successfully!")
            print("\n📁 Generated files:")
            for key, path in results.items():
                if path and path.exists():
                    print(f"  📄 {key}: {path}")
                    
        except ImportError as e:
            print(f"⚠️  Missing dependencies: {e}")
            print("💡 Please install required packages:")
            print("   pip install demucs librosa matplotlib mido onnxruntime pretty-midi torch")
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            print("\n💡 You can also run the pipeline manually:")
            print(f"   python audio_pipeline.py \"{sample_audio}\"")
    else:
        print("📂 No sample audio found.")
        print("💡 Usage examples:")
        print("   python audio_pipeline.py your_audio_file.mp3")
        print("   python audio_pipeline.py your_audio_file.wav -o output_directory")
        print("   python main.py  # (with sample audio in res/ directory)")
    
    print("\n" + "=" * 50)
    print("🎼 Pipeline features:")
    print("  🎤 Vocal separation using Demucs")
    print("  🎹 MIDI generation using pitch analysis (librosa)")
    print("  🤖 MIDI generation using Basic Pitch neural network")


if __name__ == "__main__":
    main()

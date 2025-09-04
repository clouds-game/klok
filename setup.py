#!/usr/bin/env python3
"""
Setup script for Klok Audio Pipeline.

Helps users install dependencies and verify the installation.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description="", check=True):
    """Run a command and handle errors."""
    print(f"🔧 {description}")
    print(f"   Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("   ✅ Python version is compatible")
        return True
    else:
        print("   ❌ Python 3.8+ required")
        return False


def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    # Core dependencies for the pipeline
    deps = [
        "demucs>=4.0.1",
        "librosa>=0.11.0", 
        "matplotlib>=3.10.6",
        "mido>=1.3.3",
        "onnxruntime>=1.22.1",
        "numpy>=1.20.0",
        "scipy>=1.7.0",
    ]
    
    # Install PyTorch first (might need special handling)
    print("   Installing PyTorch...")
    if not run_command([sys.executable, "-m", "pip", "install", "torch"], check=False):
        print("   ⚠️  PyTorch installation failed, continuing anyway...")
    
    # Install pretty-midi from git (as specified in pyproject.toml)
    print("   Installing pretty-midi from git...")
    if not run_command([
        sys.executable, "-m", "pip", "install", 
        "git+https://github.com/craffel/pretty-midi.git"
    ], check=False):
        print("   ⚠️  pretty-midi installation failed, trying PyPI version...")
        run_command([sys.executable, "-m", "pip", "install", "pretty-midi"], check=False)
    
    # Install other dependencies
    for dep in deps:
        print(f"   Installing {dep}...")
        if not run_command([sys.executable, "-m", "pip", "install", dep], check=False):
            print(f"   ⚠️  {dep} installation failed")
    
    print("✅ Dependency installation completed")


def verify_installation():
    """Verify that the pipeline can be imported and used."""
    print("\n🔍 Verifying installation...")
    
    try:
        # Test basic imports
        print("   Testing imports...")
        import librosa
        import demucs
        import onnxruntime
        import mido
        import pretty_midi
        print("   ✅ All core dependencies imported successfully")
        
        # Test pipeline import
        print("   Testing pipeline import...")
        sys.path.insert(0, str(Path(__file__).parent))
        from audio_pipeline import AudioPipeline
        
        pipeline = AudioPipeline()
        if hasattr(pipeline, '_missing_deps') and pipeline._missing_deps:
            print(f"   ⚠️  Some dependencies still missing: {pipeline._missing_deps}")
        else:
            print("   ✅ Pipeline ready to use!")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False


def show_usage_examples():
    """Show usage examples."""
    print("\n🎼 Usage Examples:")
    print("   # Basic usage")
    print("   python audio_pipeline.py your_song.mp3")
    print()
    print("   # With custom output directory") 
    print("   python audio_pipeline.py your_song.mp3 -o output/")
    print()
    print("   # Use CPU only")
    print("   python audio_pipeline.py your_song.mp3 -d cpu")
    print()
    print("   # Skip neural network MIDI generation")
    print("   python audio_pipeline.py your_song.mp3 --no-basic-pitch")
    print()
    print("   # Run examples")
    print("   python example_usage.py")
    print()
    print("   # Run main demo")
    print("   python main.py")


def main():
    """Main setup function."""
    print("🎵 Klok Audio Pipeline Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        sys.exit(1)
    
    # Ask user what to do
    print("\n🛠️  Setup Options:")
    print("1. Install dependencies")
    print("2. Verify installation") 
    print("3. Both (recommended)")
    print("4. Show usage examples")
    
    try:
        choice = input("\nEnter choice (1-4) [3]: ").strip() or "3"
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
    
    if choice in ["1", "3"]:
        install_dependencies()
    
    if choice in ["2", "3"]:
        success = verify_installation()
        if not success:
            print("\n⚠️  Installation verification failed.")
            print("You may need to install dependencies manually:")
            print("pip install demucs librosa matplotlib mido onnxruntime pretty-midi torch")
    
    if choice == "4" or choice in ["3"]:
        show_usage_examples()
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed!")
    print("💡 Next steps:")
    print("   1. Place an audio file in the res/ directory")
    print("   2. Run: python audio_pipeline.py your_audio.mp3")
    print("   3. Check the generated vocals and MIDI files!")


if __name__ == "__main__":
    main()
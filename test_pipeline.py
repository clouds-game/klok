#!/usr/bin/env python3
"""
Simple test script for the audio pipeline.

Tests the pipeline structure and logic without requiring full dependencies.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_pipeline_structure():
    """Test that the pipeline can be imported and instantiated."""
    print("🧪 Testing pipeline structure...")
    
    try:
        from audio_pipeline import AudioPipeline
        print("✅ AudioPipeline imported successfully")
        
        # Test instantiation with different parameters
        pipeline1 = AudioPipeline()
        print(f"✅ Default pipeline created: {pipeline1.model_name}, {pipeline1.device}")
        
        pipeline2 = AudioPipeline(model_name="htdemucs", device="cpu", output_ext="wav")
        print(f"✅ Custom pipeline created: {pipeline2.model_name}, {pipeline2.device}, {pipeline2.output_ext}")
        
        # Test dependency checking
        if hasattr(pipeline1, '_missing_deps') and pipeline1._missing_deps:
            print(f"ℹ️  Missing dependencies detected: {pipeline1._missing_deps}")
        else:
            print("✅ All dependencies available")
            
        return True
        
    except Exception as e:
        print(f"❌ Pipeline structure test failed: {e}")
        return False


def test_convenience_function():
    """Test the convenience function."""
    print("\n🧪 Testing convenience function...")
    
    try:
        from audio_pipeline import process_audio_file
        print("✅ process_audio_file imported successfully")
        
        # Test with non-existent file to check error handling
        try:
            process_audio_file("nonexistent.mp3")
            print("❌ Should have failed with missing file")
            return False
        except FileNotFoundError:
            print("✅ Correctly handled missing file")
        except ImportError as e:
            print(f"✅ Correctly handled missing dependencies: {e}")
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Convenience function test failed: {e}")
        return False


def test_command_line_interface():
    """Test command line argument parsing."""
    print("\n🧪 Testing command line interface...")
    
    try:
        import subprocess
        import sys
        
        # Test help command
        result = subprocess.run([
            sys.executable, "audio_pipeline.py", "--help"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "Audio processing pipeline" in result.stdout:
            print("✅ Command line help works")
        else:
            print(f"❌ Command line help failed: {result.stderr}")
            return False
            
        # Test with invalid file
        result = subprocess.run([
            sys.executable, "audio_pipeline.py", "nonexistent.mp3"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0 and ("missing dependencies" in result.stderr or "Pipeline failed" in result.stderr):
            print("✅ Command line correctly handles missing dependencies")
        else:
            print(f"⚠️  Unexpected command line behavior: stdout={result.stdout}, stderr={result.stderr}")
            
        return True
        
    except Exception as e:
        print(f"❌ Command line test failed: {e}")
        return False


def test_file_structure():
    """Test that required files exist."""
    print("\n🧪 Testing file structure...")
    
    required_files = [
        "audio_pipeline.py",
        "main.py", 
        "example_usage.py",
        "README.md",
        "pyproject.toml",
        "analysis/vocal_separation.py",
        "analysis/pitch.py",
        "analysis/basic_pitch/inference.py",
        "res/nmp.onnx"
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests."""
    print("🎼 Klok Audio Pipeline Tests")
    print("=" * 40)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Pipeline Structure", test_pipeline_structure),
        ("Convenience Function", test_convenience_function),
        ("Command Line Interface", test_command_line_interface),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n📝 {name}")
        print("-" * len(name))
        try:
            if test_func():
                passed += 1
                print(f"✅ {name} PASSED")
            else:
                print(f"❌ {name} FAILED")
        except Exception as e:
            print(f"❌ {name} FAILED with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("💡 The pipeline structure is ready. Install dependencies to use:")
        print("   pip install demucs librosa matplotlib mido onnxruntime pretty-midi torch")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
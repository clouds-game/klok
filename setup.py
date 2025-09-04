#!/usr/bin/env python3
"""
Setup helper for Klok Audio Pipeline.

This project uses uv for dependency management. 
For package building and dependency installation, use uv instead of setup.py.
"""

import sys


def main():
    """Show setup instructions using uv."""
    print("🎵 Klok Audio Pipeline Setup")
    print("=" * 40)
    print()
    print("This project uses uv for dependency management.")
    print("Please use the following commands:")
    print()
    print("📦 Install dependencies:")
    print("   uv sync")
    print()
    print("🏃 Run the pipeline:")
    print("   uv run python main.py")
    print("   uv run python main.py your_audio.m4a")
    print("   uv run python audio_pipeline.py your_audio.mp3 -o output/")
    print()
    print("🧪 Run tests:")
    print("   uv run python test_pipeline.py")
    print()
    print("📚 More examples:")
    print("   uv run python example_usage.py")
    print()
    print("💡 If you don't have uv installed:")
    print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("   # or")
    print("   pip install uv")
    print()
    print("=" * 40)
    print("🎼 Pipeline features:")
    print("  🎤 Vocal separation using Demucs")
    print("  🎹 MIDI generation using pitch analysis (librosa)")
    print("  🤖 MIDI generation using Basic Pitch neural network")


if __name__ == "__main__":
    main()
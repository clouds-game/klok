# %%
using SampledSignals
using Plots

# %%
using PortAudio: PortAudioStream
# stream = PortAudioStream(1, 0, samplerate=44100) # input_channels=1, output_channels=0
# buf = read(stream, 10s)[:, 1]

# %%
using FileIO
using MP3Codec
buf = load("res/我的一个道姑朋友_vocals.mp3")

# %%
using MusicProcessing
using DSP
# _spec = spectrogram(mono(buf), 2048)
# heatmap(spec.time, spec.freq, pow2db.(mel * spec.power); yflip=true, xlabel="Time (s)", ylabel="Frequency (Hz)", title="Mel Spectrogram")

spec = melspectrogram(mono(buf), 2048; nmels=64, fmin=0f0, fmax=8000f0)
heatmap(spec.time, spec.mels, pow2db.(spec.power); xlabel="Time (s)", ylabel="Frequency (Hz)", title="Mel Spectrogram")

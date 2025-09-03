# %%
# 人声分离
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
import demucs.separate
from demucs.pretrained import get_model
from demucs.apply import apply_model
# %%
audio_path = Path(__file__).parent.parent.joinpath("res/我的一个道姑朋友.mp3")
human_audio_path = audio_path.parent.joinpath("res/我的一个道姑朋友_human.wav")

output_dir = audio_path.parent.joinpath(audio_path.name)

y, sr = librosa.load(audio_path, sr=None)
print(f"音频加载完成 - 采样率: {sr} Hz, 时长: {librosa.get_duration(y=y, sr=sr):.2f} 秒")

# %%
# demucs.separate.main(["--mp3", "--two-stems", "vocals", "-n", "mdx_extra", f"{str(audio_path)}"])
# %%
import matplotlib.pyplot as plt


def show(audio_path: Path):
  y, sr = librosa.load(audio_path, sr=None)

  S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
  S_dB = librosa.power_to_db(S, ref=np.max)

  # 显示 Mel 频谱图
  plt.figure(figsize=(10, 4))
  librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel', fmax=8000)
  plt.colorbar(format='%+2.0f dB')
  plt.title('Mel Spectrogram')
  plt.tight_layout()
  plt.show()
#%%
human = Path(__file__).parent / "separated/mdx_extra/我的一个道姑朋友/vocals.mp3"
show(human)
#%%
show(audio_path)
# %%
# print(f"加载模型: {model_name}")
# model = get_model(model_name)

# # 读取音频文件
# print(f"读取音频文件: {input_path}")
# with AudioFile(input_path) as f:
# wav = f.read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)

# # 确保音频是立体声道
# wav = wav.mean(0) if wav.ndim == 3 else wav

# # 应用模型进行分离
# print("开始分离音频...")
# sources = apply_model(model, wav[None], device="cpu", progress=True)[0]

# # 获取分离后的各个音轨
# track_names = model.sources
# print(f"分离完成，获得音轨: {track_names}")

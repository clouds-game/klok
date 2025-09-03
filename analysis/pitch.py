# %%
# 音高分析
import librosa
import numpy as np
from pathlib import Path
# %%
audio_path = Path(__file__).parent.parent.joinpath("res/我的一个道姑朋友.mp3")
y, sr = librosa.load(audio_path)
duration = librosa.get_duration(y=y, sr=sr)
# %%
pitches, voiced_flag, voiced_prob = librosa.pyin(
    y,
    fmin=librosa.note_to_hz('C2'),  # 最低检测音高
    fmax=librosa.note_to_hz('C6'),  # 最高检测音高
    sr=sr,
    hop_length=512
)

# %%


def load_pitch_analysis(audio_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
  data = np.load(audio_path.with_suffix('.npz'))
  return data['pitches'], data['voiced_flag'], data['voiced_prob']


def save_pitch_analysis(pitches: np.ndarray, voiced_flag: np.ndarray, voiced_prob: np.ndarray, audio_path: Path):
  np.savez(audio_path.with_suffix('.npz'), pitches=pitches,
           voiced_flag=voiced_flag, voiced_prob=voiced_prob)


# %%
pitches, voiced_flag, voiced_prob = load_pitch_analysis(audio_path)
valid_pitches = np.where(voiced_flag, pitches, np.nan)
times = librosa.times_like(pitches, sr=sr)

# %%
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'SimHei'
fig, ax = plt.subplots(figsize=(12, 8))
plt.subplots_adjust(bottom=0.25)  # 留出滑块空间

# 绘制音高曲线
ax.plot(times, valid_pitches, 'b-', linewidth=1.5, alpha=0.8)

# 设置坐标轴
ax.set_ylim(librosa.note_to_hz('C2') * 0.9, librosa.note_to_hz('C6') * 1.1)
ax.set_xlim(0, max(20, duration))  # 初始显示20秒或整首歌（取较小值）
ax.set_ylabel('音高 (Hz)')
ax.set_xlabel('时间 (秒)')
ax.set_title(f'歌曲音高展示')
ax.grid(True, alpha=0.4)

# plt.show()
note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# 添加音符参考线（C4到B5）
for octave in range(4, 6):
  for i, note in enumerate(note_names):
    hz = librosa.note_to_hz(f"{note}{octave}")
    ax.axhline(y=hz, color='lightgray', linestyle='--', alpha=0.5)
    # 在右侧显示音符名称
    ax.text(ax.get_xlim()[1] * 1.01, hz, f"{note}{octave}",
            verticalalignment='center', color='gray', alpha=0.7)

plt.show()
# %%

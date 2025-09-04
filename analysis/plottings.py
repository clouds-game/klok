import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ArrayLike = np.ndarray | list[float]

# PROMPT: fix missing from font(s) DejaVu Sans.
# Prefer fonts that contain CJK glyphs to avoid "missing glyphs in DejaVu Sans" warnings.
# This sets a fallback list; matplotlib will use the first available on the system.
plt.rcParams['font.sans-serif'] = [
  'SimHei',            # common on many systems
  'PingFang SC',       # macOS modern Chinese font
  'Heiti SC',
  'Noto Sans CJK SC',  # Google Noto CJK
  'Arial Unicode MS',
  'DejaVu Sans'
]
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False


def _mmss(x, pos=None):
  m = int(x) // 60
  s = int(x) % 60
  return f"{m:02d}:{s:02d}"

def plot_y_time(y: ArrayLike, sr: int, name: str = None):
  # PROMPT: making a plot, x is time (considering sr), y is y
  # PROMPT: now x is seconds from zero, please use `mm:ss``
  # plot with time on x-axis (seconds), formatted as mm:ss

  times = np.arange(len(y)) / sr
  fig, ax = plt.subplots(figsize=(12, 3))
  ax.plot(times, y, linewidth=0.5)
  ax.set_xlabel('Time')
  ax.set_ylabel('Amplitude')
  ax.set_title(f'Waveform - {name} (sr={sr})')

  ax.xaxis.set_major_formatter(FuncFormatter(_mmss))
  fig.tight_layout()

def show_pitch(pitches: np.ndarray, sr: int, max_duration: float | None = None):
  import librosa
  fig, ax = plt.subplots(figsize=(12, 8))
  plt.subplots_adjust(bottom=0.25)  # 留出滑块空间

  times = np.arange(len(pitches)) / sr
  duration = librosa.get_duration(y=pitches, sr=sr)
  # 绘制音高曲线
  ax.plot(times, pitches, 'b-', linewidth=1.5, alpha=0.8)

  # 设置坐标轴
  ax.set_ylim(librosa.note_to_hz('C2') * 0.9, librosa.note_to_hz('C6') * 1.1)
  if max_duration:
    ax.set_xlim(0, max(max_duration, duration))  # 初始显示20秒或整首歌（取较小值）
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
  ax.xaxis.set_major_formatter(FuncFormatter(_mmss))

  fig.tight_layout()

def show_mel(y: ArrayLike, sr: int, name: str = None):
  import librosa

  if not isinstance(y, np.ndarray):
    y = np.array(y)
  S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
  S_dB = librosa.power_to_db(S, ref=np.max)

  # 显示 Mel 频谱图
  fig, ax = plt.subplots(figsize=(12, 5))
  img = librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel', fmax=8000, ax=ax)
  fig.colorbar(img, format='%+2.0f dB')
  ax.set_title('Mel Spectrogram')

  fig.tight_layout()

def plot_notes(notes: list, sr: int, title: str | None = None) -> None:
  """用 matplotlib 绘制音高时间线：每个音符为一条水平线（start->end），y 轴为 midi note number。"""
  notes = list(notes)
  if not notes:
    print('No notes to plot')
    return

  fig, ax = plt.subplots(figsize=(10, 4))

  for n in notes:
    ax.hlines(n.note, n.start / sr, (n.start + n.duration) / sr, linewidth=3, color='C0')
    # 在段中点标注名称
    # mid_t = (n.start + n.start + n.duration) / 2
    # ax.text(mid_t, n.note + 0.15, n.name, fontsize=8, ha='center', va='bottom')

  ax.set_xlabel('Time (s)')
  ax.set_ylabel('MIDI Note Number')
  if title:
    ax.set_title(title)
  ax.grid(True, axis='x', linestyle='--', alpha=0.4)
  ax.xaxis.set_major_formatter(FuncFormatter(_mmss))
  fig.tight_layout()

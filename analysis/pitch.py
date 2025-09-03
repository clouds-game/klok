# %%
# 音高分析
import librosa
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from mido import MidiFile, MidiTrack, Message
import mido
# %%


# %%

# 获取音频信息


def _load_pitch_analysis(cache_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
  data = np.load(cache_path)
  return data['pitches'], data['voiced_flag'], data['voiced_prob']


def _save_pitch_analysis(pitches: np.ndarray, voiced_flag: np.ndarray, voiced_prob: np.ndarray, cache_path: Path):
  np.savez(cache_path, pitches=pitches,
           voiced_flag=voiced_flag, voiced_prob=voiced_prob)


def get_audio_info(audio_path: Path) -> tuple[np.ndarray, float, float]:
  y, sr = librosa.load(audio_path)
  cache_path = audio_path.with_suffix('.npz')
  if cache_path.exists():
    pitches, voiced_flag, voiced_prob = _load_pitch_analysis(cache_path)
  else:
    pitches, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('C2'),  # 最低检测音高
        fmax=librosa.note_to_hz('C6'),  # 最高检测音高
        sr=sr,
    )
    _save_pitch_analysis(pitches, voiced_flag, voiced_prob, cache_path)

  duration = librosa.get_duration(y=y, sr=sr)
  # return sr so times_like can compute correct time axis
  return pitches, sr, duration


# %%


def pitch_to_midi_notes(pitches: np.ndarray, sr: int, hop_length: int = 512):
  """
  将帧级别的频率数组转换为带持续时间的 MIDI 音符列表。
  返回值列表项为 (start_time, end_time, midi_note)
  """
  notes = []
  times = librosa.times_like(pitches, sr=sr, hop_length=hop_length)

  cur_note = None
  cur_start = None

  for t, pitch in zip(times, pitches):
    if np.isnan(pitch):
      # 遇到无声帧：若有正在进行的音符，结束它
      if cur_note is not None:
        notes.append((cur_start, t, cur_note))
        cur_note = None
        cur_start = None
      continue

    midi_note = int(round(librosa.hz_to_midi(pitch)))
    if not (21 <= midi_note <= 108):
      if cur_note is not None:
        notes.append((cur_start, t, cur_note))
        cur_note = None
        cur_start = None
      continue

    if cur_note is None:
      cur_note = midi_note
      cur_start = t
    elif midi_note != cur_note:
      # 音高变化，结束上一个音符并开始新的
      notes.append((cur_start, t, cur_note))
      cur_note = midi_note
      cur_start = t

  # 文件结尾处收尾
  if cur_note is not None:
    notes.append((cur_start, times[-1], cur_note))

  return notes


def notes_to_midi(notes: list[tuple[float, float, int]], output_path: Path, bpm=120):
  """将音符列表转换为MIDI文件"""
  mid = MidiFile()
  track = MidiTrack()
  mid.tracks.append(track)

  # 设置速度 (微秒/拍)
  track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
  track.append(Message('program_change', program=0, time=0))  # 0 = 钢琴音色

  prev_time = 0.0
  tempo_us = mido.bpm2tempo(bpm)
  for start, end, note in notes:
    # delta from previous event to this note_on (in seconds)
    delta = max(0.0, start - prev_time)
    ticks = int(mido.second2tick(delta, mid.ticks_per_beat, tempo_us))

    # note_on
    track.append(Message('note_on', note=note, velocity=64, time=ticks))

    # note_off after duration
    duration = max(0.0, end - start)
    off_ticks = int(mido.second2tick(duration, mid.ticks_per_beat, tempo_us))
    # ensure at least 1 tick for audible note
    if off_ticks <= 0:
      off_ticks = 1
    track.append(Message('note_off', note=note, velocity=64, time=off_ticks))

    prev_time = end

  mid.save(output_path)
  return output_path


# %%


def show_pitch(pitch: np.ndarray, duration: float):
  plt.rcParams['font.family'] = 'SimHei'
  fig, ax = plt.subplots(figsize=(12, 8))
  plt.subplots_adjust(bottom=0.25)  # 留出滑块空间

  times = librosa.times_like(pitch)
  # 绘制音高曲线
  ax.plot(times, pitch, 'b-', linewidth=1.5, alpha=0.8)

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
def mp3_to_midi(audio_path: Path):
  pitches, sr, duration = get_audio_info(audio_path)
  notes = pitch_to_midi_notes(pitches, sr)
  midi_path = audio_path.with_suffix('.mid')
  notes_to_midi(notes, midi_path)

# %%
audio_path = Path(__file__).parent.parent.joinpath("res/vocals.mp3")
pitches, sr, duration = get_audio_info(audio_path)
notes = pitch_to_midi_notes(pitches, sr)
midi_path = audio_path.with_suffix('.mid')
notes_to_midi(notes, midi_path)
# %%

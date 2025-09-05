# %%
# 音高分析
import librosa
import numpy as np
from pathlib import Path
from mido import MidiFile, MidiTrack, Message
import mido

try:
  from plottings import plot_y_time, show_pitch
except ImportError:
  from .plottings import plot_y_time, show_pitch

# %%
# 获取音频信息


def _load_pitch_analysis(cache_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
  data = np.load(cache_path)
  # older caches may not contain rms; provide zeros in that case
  pitches = data['pitches']
  voiced_flag = data['voiced_flag']
  voiced_prob = data['voiced_prob']
  rms = data['rms'] if 'rms' in data else np.zeros_like(pitches)
  return pitches, voiced_flag, voiced_prob, rms


def _save_pitch_analysis(pitches: np.ndarray, voiced_flag: np.ndarray, voiced_prob: np.ndarray, rms: np.ndarray, cache_path: Path):
  np.savez(cache_path, pitches=pitches,
           voiced_flag=voiced_flag, voiced_prob=voiced_prob, rms=rms)


def get_audio_pitches(y: np.ndarray, sr: int, hop_length: int = 512, audio_path: Path | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
  """
  返回 (pitches, voiced_flag, voiced_prob, rms, sr, duration)
  pitches: 每帧频率(Hz)或 NaN
  voiced_flag: 每帧是否判定为有声音
  voiced_prob: 每帧为音高的置信度
  rms: 每帧能量（可用作 velocity 来源），与 pitches 对齐
  sr: 采样率
  duration: 音频总时长（秒）
  """
  cache_path = audio_path and audio_path.with_name(audio_path.stem + "_pyin.npz")
  if cache_path and cache_path.exists():
    pitches, voiced_flag, voiced_prob, rms = _load_pitch_analysis(cache_path)
  else:
    pitches, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('C2'),  # 最低检测音高
        fmax=librosa.note_to_hz('C6'),  # 最高检测音高
        sr=sr,
        hop_length=hop_length,
    )
    # 计算与 frames 对齐的 rms（使用相同 hop_length）
    rms = librosa.feature.rms(y=y, hop_length=hop_length).flatten()
    _save_pitch_analysis(pitches, voiced_flag, voiced_prob, rms, cache_path)

  plot_y_time(pitches, sr=sr/hop_length, name="音高 (Hz)")
  plot_y_time(voiced_prob, sr=sr/hop_length, name="音高置信度")
  plot_y_time(rms, sr=sr/hop_length, name="RMS 能量")
  return pitches, voiced_flag, voiced_prob, rms


# %%


def pitch_to_midi_notes(pitches: np.ndarray, rms: np.ndarray, sr: int, hop_length: int = 512):
  """
  将帧级别的频率数组转换为带持续时间和 velocity 的 MIDI 音符列表。
  返回列表项为 (start_time, end_time, midi_note, velocity)

  """
  notes: list[tuple[float, float, int, int]] = []
  times = librosa.times_like(pitches, sr=sr, hop_length=hop_length)
  frame_duration = hop_length / sr

  for t, pitch, r in zip(times, pitches, rms):
    if np.isnan(pitch):
      continue

    midi_note = int(round(librosa.hz_to_midi(pitch)))
    if not (21 <= midi_note <= 108):
      continue

    # 以 rms 作为 velocity 的估计（映射到 1-127）
    # 先使用 r / rms_scale 再裁剪到 [0,1]
    try:
      r_val = 0.0 if r is None or np.isnan(r) else float(r)
    except Exception:
      r_val = 0.0
    normalized = float(r_val)
    normalized = np.clip(normalized, 0.0, 1.0)
    vel = int(np.clip(round(normalized * 127), 1, 127))

    start = t
    end = t + frame_duration

    # 不合并相邻帧，直接作为单独的 note 记录（每帧一个 note）
    notes.append((start, end, midi_note, vel))

  return notes


def notes_to_midi(notes: list[tuple[float, float, int, int]], output_path: Path, tempo=500000):
  """将音符列表（包含 velocity）转换为MIDI文件

  notes 项可为 (start, end, note) 或 (start, end, note, velocity)
  """
  mid = MidiFile()
  track = MidiTrack()
  mid.tracks.append(track)

  # 设置速度 (微秒/拍)
  track.append(mido.MetaMessage('set_tempo', tempo=tempo))
  track.append(Message('program_change', program=0, time=0))  # 0 = 钢琴音色

  prev_time = 0.0
  for item in notes:
    # 支持两种格式: (start,end,note) 或 (start,end,note,velocity)
    if len(item) == 3:
      start, end, note = item
      velocity = 64
    else:
      start, end, note, velocity = item

    # delta from previous event to this note_on (in seconds)
    delta = max(0.0, start - prev_time)
    ticks = int(mido.second2tick(delta, mid.ticks_per_beat, tempo))

    # note_on
    track.append(Message('note_on', note=int(note), velocity=int(velocity), time=ticks))

    # note_off after duration
    duration = max(0.0, end - start)
    off_ticks = int(mido.second2tick(duration, mid.ticks_per_beat, tempo))
    # ensure at least 1 tick for audible note
    if off_ticks <= 0:
      off_ticks = 1
    track.append(Message('note_off', note=int(note), velocity=int(velocity), time=off_ticks))

    prev_time = end

  mid.save(output_path)
  return output_path

def mp3_to_midi(audio_path: Path):
  y, sr = librosa.load(str(audio_path), sr=None)
  pitches, _, _, rms = get_audio_pitches(y, sr, name=audio_path.name)
  notes = pitch_to_midi_notes(pitches, rms, sr)
  midi_path = audio_path.with_suffix('.mid')
  notes_to_midi(notes, midi_path)

if __name__ == "__main__":
  workspace_dir = Path(__file__).parent.parent
  audio_base_name = "我的一个道姑朋友"
  audio_vocals_path = workspace_dir / f"res/{audio_base_name}_vocals.mp3"
  # Demo/testing code when run as script
  y, sr = librosa.load(str(audio_vocals_path), sr=None)
  print(f"音频加载完成 - 采样率: {sr} Hz, 时长: {librosa.get_duration(y=y, sr=sr):.2f} 秒")

  plot_y_time(y, sr=sr, name=audio_vocals_path.name)

  # Get audio info for demo
  pitches, voiced_flag, voiced_prob, rms = get_audio_pitches(y, sr, audio_path=audio_vocals_path)
  hop_length = 512

  show_pitch(pitches, sr=sr/hop_length)

  notes = pitch_to_midi_notes(pitches, rms, sr)
  midi_path = audio_vocals_path.with_suffix('.mid')
  notes_to_midi(notes, midi_path)

# %%

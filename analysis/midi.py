# %%
"""解析 MIDI 文件并按时间段提取与展示音高的工具。
"""

from typing import Dict, Iterable, List, Optional
from pathlib import Path

import mido
import matplotlib.pyplot as plt

# %%


def note_number_to_name(n: int) -> str:
  """将 MIDI 音符编号转换为名称，例如 60 -> C4。"""
  names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
  octave = (n // 12) - 1
  name = names[n % 12]
  return f"{name}{octave}"


def extract_notes(midi_path: Path, start_sec: Optional[float] = None, end_sec: Optional[float] = None) -> List[Dict]:
  """解析 MIDI，返回在时间段内的音符列表。

  每个音符用 dict 表示：{'note': int, 'name': str, 'start': float, 'end': float, 'velocity': int, 'channel': int}

  算法：
  - 将所有 track 的消息展开为 (abs_tick, msg)
  - 按 abs_tick 排序，并在遍历时使用当前 tempo 动态将 tick 转为秒
  - 跟踪正在按下的 note (channel, note) 对，遇到 note_off 或 note_on with vel==0 则结束该 note
  """
  mid = mido.MidiFile(midi_path)
  ticks_per_beat = mid.ticks_per_beat

  events: List[tuple[int, mido.Message]] = []
  for track in mid.tracks:
    abs_tick = 0
    for msg in track:
      abs_tick += msg.time
      events.append((abs_tick, msg))

  # 按绝对 tick 排序，确保多 track 的消息按时间线性处理
  events.sort(key=lambda x: x[0])

  notes: List[Dict] = []
  ongoing: Dict[tuple[int, int], Dict] = {}  # (channel, note) -> {'start': float, 'velocity': int}

  last_tick = 0
  current_time = 0.0
  tempo = 500000  # 默认微秒/四分音符

  for abs_tick, msg in events:
    delta_ticks = abs_tick - last_tick
    if delta_ticks:
      seconds = mido.tick2second(delta_ticks, ticks_per_beat, tempo)
      current_time += seconds
      last_tick = abs_tick

    if msg.is_meta and msg.type == 'set_tempo':
      tempo = msg.tempo
      continue

    # 只关心 note_on / note_off
    if not hasattr(msg, 'type'):
      continue

    if msg.type == 'note_on' and msg.velocity > 0:
      key = (getattr(msg, 'channel', 0), msg.note)
      # 如果该 note 已经存在（重叠按新开始覆盖）
      ongoing[key] = {'start': current_time, 'velocity': msg.velocity}

    elif msg.type == 'note_off' or (msg.type == 'note_on' and getattr(msg, 'velocity', 0) == 0):
      key = (getattr(msg, 'channel', 0), msg.note)
      info = ongoing.pop(key, None)
      if info is None:
        # 未发现对应的开始，跳过
        continue
      note = {
          'note': msg.note,
          'name': note_number_to_name(msg.note),
          'start': info['start'],
          'end': current_time,
          'velocity': info.get('velocity', 0),
          'channel': key[0],
      }
      notes.append(note)

  # 过滤时间段
  if start_sec is None and end_sec is None:
    filtered = notes
  else:
    s = start_sec if start_sec is not None else -float('inf')
    e = end_sec if end_sec is not None else float('inf')
    # 保留与区间有重叠的音符
    filtered = [n for n in notes if (n['start'] < e and n['end'] > s)]

  # 按开始时间排序
  filtered.sort(key=lambda x: x['start'])
  return filtered


def plot_pitch_timeline(notes: Iterable[Dict], title: Optional[str] = None) -> None:
  """用 matplotlib 绘制音高时间线：每个音符为一条水平线（start->end），y 轴为 midi note number。"""
  notes = list(notes)
  if not notes:
    print('No notes to plot')
    return

  fig, ax = plt.subplots(figsize=(10, 4))

  for n in notes:
    ax.hlines(n['note'], n['start'], n['end'], linewidth=4, color='C0')
    # 在段中点标注名称
    mid_t = (n['start'] + n['end']) / 2
    ax.text(mid_t, n['note'] + 0.15, n['name'], fontsize=8, ha='center', va='bottom')

  ax.set_xlabel('Time (s)')
  ax.set_ylabel('MIDI Note Number')
  if title:
    ax.set_title(title)
  ax.grid(True, axis='x', linestyle='--', alpha=0.4)
  plt.tight_layout()
  plt.show()

# %%


midi_path = Path("D:/tmp/AnyConv.com__vocals.midi")
midi_path2 = Path("D:/WorkSpace/klok/res/vocals.mid")
# notes = extract_notes(midi_path)

# plot_pitch_timeline(notes, title=f"Pitches")

# %%
mid = mido.MidiFile(midi_path)
mid2 = mido.MidiFile(midi_path2)
print(mid.ticks_per_beat)
print(mid2.ticks_per_beat)
print(mid.tracks[0])
print(mid2.tracks[0])

# %%

# %%
"""解析 MIDI 文件并按时间段提取与展示音高的工具。
"""

from dataclasses import dataclass
from plottings import plot_notes

import mido
import matplotlib.pyplot as plt

TEMPO = 500000  # 默认微秒/四分音符
# %%
@dataclass
class Note:
  note: int
  name: str
  start: int # tick
  duration: int # tick
  velocity: int
  channel: int

def note_number_to_name(n: int) -> str:
  """将 MIDI 音符编号转换为名称，例如 60 -> C4。"""
  names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
  octave = (n // 12) - 1
  name = names[n % 12]
  return f"{name}{octave}"


def extract_notes(mid: mido.MidiFile, start_sec: float | None = None, end_sec: float | None = None) -> list[Note]:
  """解析 MIDI，返回在时间段内的音符列表。

  每个音符用 dict 表示：{'note': int, 'name': str, 'start': float, 'end': float, 'velocity': int, 'channel': int}

  算法：
  - 将所有 track 的消息展开为 (abs_tick, msg)
  - 按 abs_tick 排序，并在遍历时使用当前 tempo 动态将 tick 转为秒
  - 跟踪正在按下的 note (channel, note) 对，遇到 note_off 或 note_on with vel==0 则结束该 note
  """
  ticks_per_beat = mid.ticks_per_beat

  events: list[tuple[int, mido.Message]] = []
  for track in mid.tracks:
    abs_tick = 0
    for msg in track:
      abs_tick += msg.time
      events.append((abs_tick, msg))

  # 按绝对 tick 排序，确保多 track 的消息按时间线性处理
  events.sort(key=lambda x: x[0])

  notes: list[Note] = []
  ongoing: list[tuple[int, int], dict] = {}  # (channel, note) -> {'start': float, 'velocity': int}

  last_tick = 0
  current_tick = 0
  tempo = 500000  # 默认微秒/四分音符

  for abs_tick, msg in events:
    delta_ticks = abs_tick - last_tick
    if delta_ticks:
      seconds = mido.tick2second(delta_ticks, ticks_per_beat, tempo)
      current_tick += delta_ticks
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
      ongoing[key] = {'start': current_tick, 'velocity': msg.velocity}

    elif msg.type == 'note_off' or (msg.type == 'note_on' and getattr(msg, 'velocity', 0) == 0):
      key = (getattr(msg, 'channel', 0), msg.note)
      info = ongoing.pop(key, None)
      if info is None:
        # 未发现对应的开始，跳过
        continue
      note = Note(
          note=msg.note,
          name=note_number_to_name(msg.note),
          start=info['start'],
          duration=current_tick-info['start'],
          velocity=info.get('velocity', 0),
          channel=key[0],
      )
      notes.append(note)

  # 过滤时间段
  if start_sec is None and end_sec is None:
    filtered = notes
  else:
    s = start_sec if start_sec is not None else -float('inf')
    e = end_sec if end_sec is not None else float('inf')
    # 保留与区间有重叠的音符
    filtered = [n for n in notes if (n.start < e and n.end > s)]

  # 按开始时间排序
  filtered.sort(key=lambda x: x.start)
  return filtered


def hist_notes(mid: list[Note]) -> dict[int, int]:
  """统计 MIDI 文件中每个音符出现的次数，返回 {note_number: count}。"""
  counts: dict[int, int] = {}
  for n in mid:
    counts[n.note] = counts.get(n.note, 0) + n.duration
  plt.figure()
  plt.hist(list(counts.keys()), weights=list(counts.values()), align='left', rwidth=0.8, )
  plt.xlabel('MIDI Note Number')
  plt.ylabel('Count')
  plt.title('MIDI Note Histogram')
  plt.grid(axis='y', linestyle='--', alpha=0.7)
  plt.show()

# %%
if __name__ == "__main__":
  from pathlib import Path

  workspace_dir = Path(__file__).parent.parent
  base_name = "我的一个道姑朋友"
  midi_path = workspace_dir / f"res/{base_name}_vocals.mid"
  mid = mido.MidiFile(midi_path)
  notes = extract_notes(mid)

  plot_notes(notes, mid.ticks_per_beat / TEMPO * 1e6, title=base_name)
  hist_notes(notes)

# %%

# %%
from pathlib import Path
workspace_dir = Path(__file__).parent.parent

import sounddevice as sd
import numpy as np
import queue

# %%
RATE = 44100
CHANNELS = 1
CHUNK = 4096
BUFFER_MILLISECONDS = 1000

class AudioStream:
  def __init__(self, samplerate=RATE, channels=CHANNELS, buffer_milliseconds=BUFFER_MILLISECONDS, downsample=10, blocksize=CHUNK):
    self.buffer_len = int(samplerate * buffer_milliseconds / (1000 * downsample))
    self._ring_buffer = np.zeros((channels, self.buffer_len), dtype='float32')
    self.samplerate = samplerate
    self.channels = channels
    self.blocksize = blocksize
    self.downsample = downsample
    self.q = queue.Queue()

  def sync_ring_buffer(self):
    # print("sync_ring_buffer", self.q.qsize(), self.q.empty())
    while not self.q.empty():
      try:
        data = self.q.get_nowait() # type: np.ndarray
      except queue.Empty:
        break
      shift = data.shape[1]
      # print("sync_ring_buffer got data:", describe_np(data), "shift:", shift)
      if shift >= self.buffer_len:
        # assert False, "Unexpected large shift"
        self._ring_buffer = data[:, -self.buffer_len:]
      else:
        self._ring_buffer = np.roll(self._ring_buffer, -shift, axis=1)
        self._ring_buffer[:, -shift:] = data

  @property
  def ring_buffer(self):
    self.sync_ring_buffer()
    return self._ring_buffer

  def __enter__(self):
    def audio_callback(indata: np.ndarray, frames_count, time_info, status):
      # print("callback", indata.shape, describe_np(indata))
      if status:
        print('Audio status:', status)
      self.q.put(indata[::self.downsample, :].T)
    self.stream = sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype='float32', callback=audio_callback)
    self.stream.__enter__()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.stream.__exit__(exc_type, exc_value, traceback)


def describe_np(array: np.ndarray) -> str:
  return f"shape: {array.shape}, dtype: {array.dtype}, min: {np.min(array)}, max: {np.max(array)}, mean: {np.mean(array):.4f}, std: {np.std(array):.4f}"

# %%

import matplotlib
# matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.axes import Axes
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

class Plotting:
  def __init__(self, stream: AudioStream):
    fig, axes = plt.subplots(2, 1)
    self.figure = fig
    self.axes = axes # type: Axes
    self.lines = Plotting.plot_line(axes[0], stream.ring_buffer)
    self.figure.tight_layout(pad=0)
    self.stream = stream

  @staticmethod
  def plot_line(ax: Axes, plotdata: np.ndarray):
    lines = ax.plot(*list(plotdata))
    ax.axis((0, plotdata.shape[1], -1, 1))
    ax.set_yticks([0])
    ax.yaxis.grid(True)
    ax.tick_params(bottom=False, top=False, labelbottom=False,
              right=False, left=False, labelleft=False)
    return lines

  def update_line(self):
    for (line, data) in zip(self.lines, self.stream.ring_buffer):
      line.set_ydata(data[-len(line.get_ydata()):])

  def update_plot(self, frames):
    print("update_plot", describe_np(self.stream.ring_buffer))
    self.update_line()
    return self.axes

if __name__ == "__main__":
  device_info = sd.query_devices(None, 'input')
  print("device_info:", device_info)
  samplerate = device_info['default_samplerate']
  stream = AudioStream(samplerate=samplerate)
  plots = Plotting(stream)
  # fig.tight_layout(pad=0)

  ani = FuncAnimation(plots.figure, lambda f: plots.update_plot(f), interval=50, blit=True)
  with stream:
    print("Initial ring_buffer:", describe_np(stream.ring_buffer))
    plt.show()

# %%

# %%
from pathlib import Path
workspace_dir = Path(__file__).parent.parent

import sounddevice as sd
import numpy as np
import queue
import threading

# %%
RATE = 44100
CHANNELS = 1
CHUNK = 4096
BUFFER_MILLISECONDS = 10000

class AudioStream:
  def __init__(self, samplerate=RATE, channels=CHANNELS, buffer_milliseconds=BUFFER_MILLISECONDS, downsample=1, blocksize=CHUNK):
    self.buffer_len = int(samplerate * buffer_milliseconds / (1000 * downsample))
    self.ring_buffer_lock = threading.Lock()
    self._ring_buffer = np.zeros((channels, self.buffer_len), dtype='float32')
    self.samplerate = samplerate
    self.channels = channels
    self.blocksize = blocksize
    self.downsample = downsample
    self.q = queue.Queue()

  def _sync_ring_buffer(self):
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
  def sr(self):
    return self.samplerate / self.downsample

  @property
  def ring_buffer(self):
    with self.ring_buffer_lock:
      self._sync_ring_buffer()
      return self._ring_buffer

  def get_buffer(self, duration_ms: int) -> np.ndarray:
    """Get the most recent audio buffer of specified duration in milliseconds."""
    with self.ring_buffer_lock:
      self._sync_ring_buffer()
      num_samples = int(self.samplerate * duration_ms / (1000 * self.downsample))
      num_samples = min(num_samples, self._ring_buffer.shape[1])
      return self._ring_buffer[:, -num_samples:]

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
import time
class AudioStreamInfo:
  def __init__(self, stream: AudioStream, duration_ms=5000, resample=882, n_mels=64, max_freq=8000):
    self.stream = stream
    self.duration_ms = duration_ms
    self.resample = resample
    self.n_mels = n_mels
    self.max_freq = max_freq
    self.last_update = 0
    self.update()

  def _update(self):
    if time.time() - self.last_update > 1:
      self.update()

  def update(self):
    sr = self.stream.sr
    self._buffer = self.stream.get_buffer(self.duration_ms)
    print(self._buffer.shape)

    if self.resample:
      self._y = librosa.resample(self._buffer, orig_sr=sr, target_sr=self.resample, axis=1)
    else:
      self._y = None

    self._S = librosa.feature.melspectrogram(y=self._buffer, sr=sr, n_mels=self.n_mels, fmax=self.max_freq)
    self._S_dB = librosa.power_to_db(self._S, ref=np.max)
    self.last_update = time.time()

  @property
  def sr(self):
    return self.stream.sr

  @property
  def y_sr(self):
    return self.resample or self.stream.sr

  @property
  def buffer(self):
    return self._update() or self._buffer

  @property
  def y(self):
    return self._update() or (self._y if self._y is not None else self._buffer)

  @property
  def S(self):
    return self._update() or self._S.mean(0)

  @property
  def S_dB(self):
    return self._update() or self._S_dB.mean(0)

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

# lazy import to avoid hard dependency at module import time
import librosa
import librosa.display

class Plotting:
  def __init__(self, stream: AudioStreamInfo):
    self.stream = stream

    fig, axes = plt.subplots(2, 1)
    self.figure = fig
    self.axes = axes # type: Axes
    self.lines = Plotting.plot_line(axes[0], self.stream.y, sr=stream.y_sr)
    # Mel spectrogram image artist (initialize with current buffer)
    self.mel_im = Plotting.plot_mel(axes[1], self.stream.S_dB, sr=stream.sr)
    self.figure.tight_layout(pad=0)

  @staticmethod
  def plot_line(ax: Axes, plotdata: np.ndarray, sr: int):
    lines = ax.plot(*list(plotdata))
    ax.axis((0, plotdata.shape[1], -0.3, 0.3))
    ax.set_yticks([0])
    ax.yaxis.grid(True)
    ax.tick_params(bottom=False, top=False, labelbottom=False,
              right=False, left=False, labelleft=False)
    return lines

  @staticmethod
  def plot_mel(ax: Axes, S_dB: np.ndarray, sr: int):
    """Create an initial mel-spectrogram image on ax from plotdata.

    Returns the AxesImage so it can be updated later via set_data.
    """
    # display with imshow for easy updates
    img = ax.imshow(S_dB, aspect='auto', origin='lower', interpolation='nearest')
    ax.set_ylabel('Mel bin')
    ax.set_xlabel('Frame')
    ax.set_title('Mel Spectrogram')
    return img

  def update_line(self):
    for (line, data) in zip(self.lines, self.stream.y):
      line.set_ydata(data[-len(line.get_ydata()):])
    return self.lines

  def update_mel(self):
    S_dB = self.stream.S_dB

    # update the image data and rescale color limits
    try:
      self.mel_im.set_data(S_dB)
      self.mel_im.set_clim(vmin=S_dB.min(), vmax=S_dB.max())
    except Exception:
      # If the image artist was not created for any reason, recreate it on the axes
      ax = self.axes[1] # type: Axes
      ax.clear()
      self.mel_im = Plotting.plot_mel(ax, S_dB, sr=self.stream.sr)
    return [self.mel_im]

  def update_plot(self, frames):
    self.stream.update()
    print("update_plot", describe_np(self.stream.buffer))
    artists = []
    artists.extend(self.update_line())
    artists.extend(self.update_mel())
    # return artists for blitting: lines and mel image
    return artists

if __name__ == "__main__":
  device_info = sd.query_devices(None, 'input')
  print("device_info:", device_info)
  samplerate = device_info['default_samplerate']
  stream = AudioStream(samplerate=samplerate)
  info = AudioStreamInfo(stream=stream, duration_ms=5000, resample=882, n_mels=64, max_freq=8000)
  plots = Plotting(info)
  # fig.tight_layout(pad=0)

  ani = FuncAnimation(plots.figure, plots.update_plot, interval=50, blit=True)
  with stream:
    print("Initial ring_buffer:", describe_np(stream.ring_buffer))
    plt.show()

# %%

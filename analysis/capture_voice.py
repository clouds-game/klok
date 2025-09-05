# %%
import sounddevice as sd
import time
import numpy as np
import librosa
import threading

# %%
CHANNELS = 1
RATE = 44100  # 采样率
CHUNK = 1024  # 每次读取的音频块大小
RECORD_SECONDS = 0  # 0表示无限录制

# %%
latest_pitch_data = None
is_running = True
pitch_lock = threading.Lock()

# %%


def detect_pitch(audio_data: np.ndarray, sr=RATE) -> float | None:
  max_abs = np.max(np.abs(audio_data))
  if max_abs == 0:
    return None
  audio_data = audio_data / max_abs
  f0, _, _ = librosa.pyin(
      audio_data,
      fmin=librosa.note_to_hz('C2'),  # 最低检测音高 65hz value=36
      fmax=librosa.note_to_hz('C7'),  # 最高检测音高 2093hz value=96
      sr=sr
  )
  if f0 is not None:
    valid_f0 = f0[~np.isnan(f0)]
    if len(valid_f0) > 0:
      return np.mean(valid_f0)
  return None


def hz_to_note(frequency: float) -> str:
  """将频率转换为音符"""
  if frequency <= 0:
    return "无效频率"

  a4 = 440.0
  semitones = 12 * np.log2(frequency / a4)
  semitones_rounded = round(semitones)

  note_names = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
  octave = 4 + (semitones_rounded + 9) // 12
  note_index = (semitones_rounded + 9) % 12
  return f"{note_names[note_index]}{octave} {semitones_rounded + 9} ({frequency:.1f} Hz)"

def describe_np(array: np.ndarray) -> str:
  return f"shape: {array.shape}, dtype: {array.dtype}, min: {np.min(array)}, max: {np.max(array)}, mean: {np.mean(array):.4f}, std: {np.std(array):.4f}"

def handle_frame(stream: sd.InputStream):
  # read returns (frames, overflow)
  frames, overflow = stream.read(CHUNK)
  if overflow:
    # overflow is a boolean array or flag; if True, skip this block
    # print("缓冲区溢出，跳过此帧", frames)
    return None
  print(describe_np(frames))
  # frames shape: (CHUNK, CHANNELS) -> squeeze to 1D for mono
  audio_data = np.squeeze(np.array(frames, dtype=np.float32))
  # 检测音高
  pitch = detect_pitch(audio_data)
  # 显示结果
  if pitch:
    midi = librosa.hz_to_midi(pitch)
    note = librosa.hz_to_note(pitch)
    print(f"当前音高: {midi:.2f} MIDI, {note}")
    pitch_data = {
        "midi": midi,
        "note": note,
        "pitch": pitch,
    }
    global latest_pitch_data
    with pitch_lock:
      latest_pitch_data = pitch_data
  else:
    print("未检测到有效音高...")

def audio_processing_thread():
  start_time = time.time()
  print("开始检测音高, start_time:", start_time)
  try:
    # Use sounddevice InputStream which is usually easier to install on macOS
    with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='float32', blocksize=CHUNK) as stream:
      while is_running:
        handle_frame(stream)
        # 短暂延迟，减少CPU占用
        time.sleep(0.05)
  except Exception as e:
    print(f"检测已停止: {e}")
  finally:
    print("音频处理线程已退出")
# %%
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/pitch', methods=['GET'])
def get_pitch():
  with pitch_lock:
    pitch_data = latest_pitch_data
  return jsonify({'status': 'success', 'data': pitch_data if pitch_data else {}})

def run_http_server(port=8000, host='localhost'):
  """启动Flask HTTP服务器"""
  print(f"HTTP服务器已启动, 监听端口 {port}")
  print(f"可用接口: http://localhost:{port}/pitch")
  try:
    # use_reloader=False to avoid spawning child processes which can duplicate audio threads
    app.run(host=host, port=port, debug=True, threaded=True, use_reloader=False)
  except KeyboardInterrupt:
    pass
  finally:
    print("HTTP服务器已停止")

# %%
def main():
  audio_thread = threading.Thread(target=audio_processing_thread, daemon=True)
  audio_thread.start()

  # 等待音频线程初始化
  time.sleep(1)
  try:
    run_http_server(port=8000)
  except KeyboardInterrupt:
    print("\n收到停止信号")
  finally:
    # 停止音频处理线程
    global is_running
    is_running = False
    audio_thread.join()
    print("程序已退出")

# %%
if __name__ == '__main__':
  main()

# %%

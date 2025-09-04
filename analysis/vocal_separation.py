# %%
# 人声分离
# TODO: source - vocals?
# TODO: other model? why mdx_extra?

import librosa
import numpy as np
from pathlib import Path

workspace_dir = Path(__file__).parent.parent

# %%
audio_base_name = "我的一个道姑朋友"
audio_path = workspace_dir / f"res/{audio_base_name}.m4a"

# output_dir = audio_path.parent.joinpath(audio_path.name)

# str is needed on PosixPath: AttributeError: 'PosixPath' object has no attribute 'encode'
y, sr = librosa.load(str(audio_path), sr=None)
print(f"音频加载完成 - 采样率: {sr} Hz, 时长: {librosa.get_duration(y=y, sr=sr):.2f} 秒")

# %%
def separate_audio(audio_path: Path,
                   model_name: str = "mdx_extra",
                   device: str = "cpu",
                   two_stems: bool = True,
                   out_dir: Path | None = None,
                   ext: str = "mp3"
):

  from demucs.separate import load_track
  from demucs.pretrained import get_model
  from demucs.apply import apply_model
  from demucs.audio import save_audio
  """Separate stems using Demucs model (inlined minimal flow).

  This uses demucs.get_model + demucs.apply.apply_model to perform separation
  and writes each source to disk under outdir / <base_name>_<source>.<ext>
  """
  model = get_model(model_name)
  # model.sources == ['drums', 'bass', 'other', 'vocals']
  wav = load_track(audio_path, model.audio_channels, model.samplerate)
  ref_wav = wav.mean(0)
  wav -= ref_wav.mean()
  wav /= ref_wav.std()

  # run model (batch dimension)
  sources = apply_model(model, wav[None], device=device, progress=True)[0]

  vocals_idx = model.sources.index("vocals")
  if two_stems:
    output_sources = {
      "vocals": sources[vocals_idx],
      "non_vocals": sources[[i for i in range(len(sources)) if i != vocals_idx]].sum(0),
    }
  else:
    output_sources = {source: sources[i] for i, source in enumerate(model.sources)}

  base_name = audio_path.stem
  out_dir = out_dir or audio_path.parent
  out_dir.mkdir(parents=True, exist_ok=True)
  kwargs = {
    'samplerate': model.samplerate,
    # 'bitrate': args.mp3_bitrate,
    # 'preset': args.mp3_preset,
    # 'clip': args.clip_mode,
    # 'as_float': args.float32,
    # 'bits_per_sample': 24 if args.int24 else 16,
  }
  for k, v in output_sources.items():
    filename = out_dir / f"{base_name}_{k}.{ext}"
    save_audio(v, filename, **kwargs)
    print(f"wrote: {filename}")
  return sources

# call the inlined separation (replaces demucs.separate.main invocation)
sources = separate_audio(audio_path, model_name="mdx_extra", device="mps")

# %%
import matplotlib.pyplot as plt

def show(audio_path: Path):
  y, sr = librosa.load(str(audio_path), sr=None)

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
vocals_path = workspace_dir / f"res/{audio_base_name}_vocals.mp3"

show(audio_path)
show(vocals_path)

#%%

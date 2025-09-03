# %%

from pathlib import Path


# %%


def uc2mp3(uc_file_path, mp3_file_path):
  uc_file = Path(uc_file_path)
  with open(uc_file, 'rb') as f:
    uc_data = f.read()

  arr = bytearray(uc_data)
  for i in range(len(arr)):
    arr[i] ^= 0xa3

  with open(mp3_file_path, 'wb') as f:
    f.write(arr)


# %%
# uc_file = Path(
#     "C:/Users/breezing/AppData/Local/NetEase/CloudMusic/Cache/Cache/1367452194-320-7eb893efed67a2071a2a958d9752923f.uc")
# mp3_file = Path("test.mp3")
# uc2mp3(uc_file, mp3_file)
# %%

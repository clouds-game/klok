# %%
# 从网易云音乐搜索并下载歌曲
from dataclasses import dataclass
from pathlib import Path
import requests
# %%


@dataclass
class Song:
  id: int
  name: str
  artists: list[str]
  album: str
  duration: int
  copyrightId: int

  def __str__(self):
    return f"{self.name} ({self.id})"
# %%


def get_lrc_url(songid: int) -> str:
  lrc_url = f"https://music.163.com/api/song/lyric?id={songid}&lv=1&kv=1&tv=-1"
  return lrc_url


def song_detail_url(songid: int) -> str:
  return f"https://music.163.com/#/song?id={songid}"


def get_mp3url(songid: int) -> str:
  return f"http://music.163.com/song/media/outer/url?id={songid}.mp3"


def parse_song_info(data: dict) -> Song:
  song = Song(
      id=int(data['id']),
      name=data['name'],
      artists=[artist['name'] for artist in data['artists']],
      album=data['album'].get('name', ''),
      duration=int(data['duration']),
      copyrightId=int(data['copyrightId'])
  )
  return song


def search_song(content: str, limit: int = 10) -> list[Song]:
  search_url = f'https://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&s={content}&type=1&offset=0&total=true&limit={limit}'
  response = requests.get(search_url)
  data = response.json()
  songs_data = data['result']['songs']
  songs = [parse_song_info(data) for data in songs_data]
  return songs

# %%


def download_song(song: Song, path: Path):
  if song.copyrightId != 0:
    print(f"Song '{song}' is not available for download due to copyright restrictions.")
    return
  mp3_url = get_mp3url(song.id)
  response = requests.get(mp3_url)
  path.parent.mkdir(parents=True, exist_ok=True)
  with open(path, 'wb') as f:
    f.write(response.content)


def download_lyric(song: Song, path: Path):
  lrc_url = get_lrc_url(song.id)
  response = requests.get(lrc_url)
  data = response.json()
  if 'lrc' in data and 'lyric' in data['lrc']:
    lyric = data['lrc']['lyric']
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
      f.write(lyric)
  else:
    print(f"No lyrics found for song: {song}")


# %%
# RES_DIR = Path(__file__).parent.parent / "res/songs"
# # %%
# songs = search_song("普通朋友")
# song = songs[1]
# download_song(song, RES_DIR.joinpath(f"{song.name}-{song.id}.mp3"))
# download_lyric(song, RES_DIR.joinpath(f"{song.name}-{song.id}.lrc"))


# %%

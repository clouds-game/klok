import { invoke } from "@tauri-apps/api/core"

export function getAudioMimeType(url: string): string {
  const ext = url.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'mp3':
      return 'audio/mpeg'
    case 'wav':
      return 'audio/wav'
    case 'ogg':
      return 'audio/ogg'
    case 'flac':
      return 'audio/flac'
    case 'm4a':
    case 'mp4':
    case 'aac':
      return 'audio/mp4'
    default:
      return 'application/octet-stream' // fallback binary type
  }
}

export async function loadAudioContent(url: string) {
  const data = await invoke('load_audio', { path: url }) as ArrayBuffer
  console.log("loadAudioContent data:", data)
  const mimeType = getAudioMimeType(url)
  const blob = new Blob([data], { type: mimeType })
  return URL.createObjectURL(blob)
}

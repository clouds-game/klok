import { invoke } from '@tauri-apps/api/core'
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { base64ToDataUrl } from './time'

// MIDI note representation (matches Rust `Note` returned from `load_midi`)
type MidiNote = {
  note: number
  start: number
  duration: number
  velocity: number
  channel: number
  confidence?: number | null
}

export const useAppState = defineStore('app', () => {
  const fileUrl = ref<string | null>(null)
  const _title = ref<string | null>(null)
  const streamUrl = ref<string | null>(null)
  const isPlaying = ref(false)
  const duration = ref(1)
  const currentTime = ref(0)
  const volume = ref(1)
  const metadata = ref<Metadata | null>(null)
  const notes = ref<MidiNote[] | null>(null)

  const lyrics = computed(() => Array.from(metadata.value?.lyrics || []))

  const title = computed(() => _title.value || 'No Title')
  const setTitle = (newTitle: string) => {
    _title.value = newTitle
  }

  const reset = () => {
    _title.value = null
    streamUrl.value = null
    duration.value = 1
    currentTime.value = 0
    metadata.value = null
  }

  const loadMetadata = async (newUrl: string) => {
    try {
      // fetch metadata
      const md = await invoke('get_metadata', { path: newUrl })
      metadata.value = md as Metadata
      if (metadata.value?.duration) {
        duration.value = metadata.value.duration
      }
      if (metadata.value?.title) {
        _title.value = metadata.value.title
      }
    } catch (e) {
      // ignore, optional
      console.warn('get_metadata failed', e)
    }
  }

  const loadAudio = async (newUrl: string) => {
    // fetch audio content from rust backend as data URL for bundled resource
    // store it in `streamUrl` so we don't overwrite any user-selected `fileUrl`
    try {
      const data = await invoke('load_audio', { path: newUrl }) as string
      if (data.startsWith("data:")) {
        streamUrl.value = base64ToDataUrl(data)
      } else {
        streamUrl.value = data
      }
    } catch (e) {
      // fallback: keep using builtin file name
      console.warn('load_audio failed', e)
    }
  }

  const loadMidi = async (newUrl: string) => {
    try {
      const res = await invoke('load_midi', { path: newUrl })
      notes.value = res as MidiNote[]
    } catch (e) {
      console.warn('load_midi failed', e)
      notes.value = null
    }
  }

  watch(fileUrl, async (newUrl) => {
    reset()
    if (newUrl) {
      _title.value = 'Loading...'
    } else {
      return
    }
    await loadMetadata(newUrl)
    await loadAudio(newUrl)
    await loadMidi(newUrl)
  })

  const activeIndex = computed(() => {
    const t = currentTime.value
    for (let i = lyrics.value.length - 1; i >= 0; i--) {
      if (t >= lyrics.value[i].time) return i
    }
    return 0
  })

  const activeLeftTime = computed(() => {
    return lyrics.value[activeIndex.value]?.time || 0
  })
  const activeRightTime = computed(() => {
    if (activeIndex.value + 1 < lyrics.value.length) {
      return (lyrics.value[activeIndex.value + 1]?.time || duration.value)
    }
    return duration.value
  })

  const togglePlay = (b?: boolean) => { isPlaying.value = b !== undefined ? b : !isPlaying.value }
  const seekTo = (v: number) => { console.log("seekTo", v); currentTime.value = v }
  const setVolume = (v: number) => { volume.value = v }
  const setDuration = (v: number) => { duration.value = v }

  return {
    title,
    fileUrl,
    streamUrl,
    isPlaying,
    duration,
    currentTime,
    volume,
    metadata,
    notes,
    lyrics,
    activeIndex,
    activeLeftTime,
    activeRightTime,
    setTitle,
    loadMetadata,
    loadAudio,
    loadMidi,
    togglePlay,
    seekTo,
    setVolume,
    setDuration,
  }
})

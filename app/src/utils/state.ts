import { invoke } from '@tauri-apps/api/core'
import { defineStore } from 'pinia'
import { ref, computed, watch, nextTick } from 'vue'
import { fetchCurrentPitch, loadAudioContent, pitchData} from './api'


// MIDI note representation (matches Rust `Note` returned from `load_midi`)
type MidiNote = {
  note: number
  start: number
  duration: number
  velocity: number
  channel: number
  confidence?: number | null
}

export type PlayListItem = {
  title: string
  artist?: string
  url: string
}

export const useAppState = defineStore('app', () => {
  const playList = ref<PlayListItem[]>([])
  const fileUrl = ref<string | null>(null)
  const _title = ref<string | null>(null)
  const streamUrl = ref<string | null>(null)
  const vocalUrl = ref<string | null>(null)
  const isPlaying = ref(false)
  const duration = ref(1)
  const currentTime = ref(0)
  const volume = ref(1)
  const metadata = ref<Metadata | null>(null)
  const notes = ref<MidiNote[] | null>(null)
  // realtime pitch detection state (Hz)
  const currentPitchData = ref<pitchData | null>(null)
  // history of detected pitches: { time: number, midi: number }
  const pitchHistory = ref<pitchData[]>([])
  // polling handle
  let pitchPollTimer: number | null = null

  // Keep original lyrics exactly as provided by metadata
  const originalLyrics = computed(() => Array.from(metadata.value?.lyrics || []))

  // Ad-hoc per-lyric time deltas (index -> seconds). This lets the UI adjust lyric timing
  // without mutating the underlying `metadata.lyrics` array.
  // Note: using index-based keys is simple and suitable for ad-hoc adjustments.
  const lyricsTimeDelta = ref<Record<number, number>>({})

  // Global delta applied to all lyrics (seconds). Useful for shifting entire lyric track.
  const lyricsGlobalDelta = ref<number>(0)

  // Computed adjusted lyrics view which applies any time deltas to the original lyrics.
  const lyrics = computed(() =>
    originalLyrics.value.map((l, i) => ({
      ...l,
      time: l.time + (lyricsGlobalDelta.value || 0) + (lyricsTimeDelta.value[i] || 0),
    }))
  )

  const title = computed(() => _title.value || 'No Title')
  const setTitle = (newTitle: string) => {
    _title.value = newTitle
  }

  const reset = () => {
    _title.value = null
    setStreamUrl(null)
    setVocalUrl(null)
    duration.value = 1
    currentTime.value = 0
    metadata.value = null
    // stop pitch polling and clear pitch state
    if (pitchPollTimer) {
      clearInterval(pitchPollTimer)
      pitchPollTimer = null
    }
    currentPitchData.value = null
    pitchHistory.value = []
  }

  const loadPlaylist = async () => {
    try {
      const pl = await invoke('load_playlist') as PlayListItem[]
      playList.value = pl
    } catch (e) {
      // ignore, optional
      console.warn('load_playlist failed', e)
    }
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

  const setVocalUrl = (url: string | null) => {
    const oldVocalUrl = vocalUrl.value
    nextTick(() => {
      if (oldVocalUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(oldVocalUrl)
      }
    })
    vocalUrl.value = url
  }

  const setStreamUrl = (url: string | null) => {
    const oldStreamUrl = streamUrl.value
    nextTick(() => {
      if (oldStreamUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(oldStreamUrl)
      }
    })
    streamUrl.value = url
  }

  const loadAudio = async (newUrl: string) => {
    // fetch audio content from rust backend as data URL for bundled resource
    // store it in `streamUrl` so we don't overwrite any user-selected `fileUrl`
    try {
      const name = newUrl.split(".")[0]

      const vocalUrl = await loadAudioContent(`${name}_vocals.mp3`)
      const backgroundUrl = await loadAudioContent(`${name}_non_vocals.mp3`)

      setVocalUrl(vocalUrl)
      setStreamUrl(backgroundUrl)
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
  const seekTo = (v: number) => { currentTime.value = v }
  const setVolume = (v: number) => { volume.value = v }
  const setDuration = (v: number) => { duration.value = v }

  // Adjust a lyric's time by an ad-hoc delta (seconds). Passing 0 clears the per-line delta.
  const setLyricLineDelta = (index: number, delta: number) => {
    if (delta === 0) {
      if (index in lyricsTimeDelta.value) {
        // remove key immutably so Vue picks up change
        const copy = { ...lyricsTimeDelta.value }
        delete copy[index]
        lyricsTimeDelta.value = copy
      }
    } else {
      lyricsTimeDelta.value = { ...lyricsTimeDelta.value, [index]: delta }
    }
  }

  // Set a global delta (seconds) applied to all lyric lines. Passing 0 clears it.
  const setLyricDelta = (delta: number) => {
    lyricsGlobalDelta.value = delta
  }

  // Clear a specific delta or all deltas when index is omitted
  const clearLyricTimeDelta = (index?: number) => {
    if (index === undefined) {
      lyricsTimeDelta.value = {}
    } else if (index in lyricsTimeDelta.value) {
      const copy = { ...lyricsTimeDelta.value }
      delete copy[index]
      lyricsTimeDelta.value = copy
    }
  }

  const switchToSong = (url: string) => {
    isPlaying.value = false
    fileUrl.value = url
  }

  // Start polling pitch endpoint every 500ms. Will replace existing timer.
  const startPitchPolling = (endpoint?: string) => {
    if (pitchPollTimer) clearInterval(pitchPollTimer)
    pitchPollTimer = window.setInterval(async () => {
      const data = await fetchCurrentPitch()
      if (data) {
        currentPitchData.value = data
        pitchHistory.value = [...pitchHistory.value, data].slice(-500)
      } else {
        console.warn('fetchCurrentPitch returned no data')
      }

    }, 500)
  }

  const stopPitchPolling = () => {
    if (pitchPollTimer) {
      clearInterval(pitchPollTimer)
      pitchPollTimer = null
    }
  }

  return {
    playList,
    title,
    fileUrl,
    streamUrl,
    vocalUrl,
    isPlaying,
    duration,
    currentTime,
    volume,
    metadata,
    notes,
    lyrics,
    // original unmodified lyrics and per-index deltas
    originalLyrics,
    lyricsTimeDelta,
    lyricsGlobalDelta,
    activeIndex,
    activeLeftTime,
    activeRightTime,
    setTitle,
    loadPlaylist,
    loadMetadata,
    loadAudio,
    loadMidi,
    togglePlay,
    seekTo,
    setVolume,
    setDuration,
    setLyricLineDelta,
    setLyricDelta,
    clearLyricTimeDelta,
    switchToSong,
    // realtime pitch controls
    currentPitchData,
    pitchHistory,
    startPitchPolling,
    stopPitchPolling,
  }
})

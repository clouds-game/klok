<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'

type LyricLine = { time: number; text: string }

const audioRef = ref<HTMLAudioElement | null>(null)
const fileUrl = ref<string | null>(null)
const isPlaying = ref(false)
const duration = ref(0)
const currentTime = ref(0)
const volume = ref(1)

// Example lyrics (seconds)
const lyrics = ref<LyricLine[]>([
  { time: 0, text: '（Instrumental intro）' },
  { time: 6, text: '我 有 一 个 道 姑 朋 友' },
  { time: 12, text: '她 在 云 间 游 戏' },
  { time: 20, text: '轻 轻 唱 着 古 老 的 歌' },
  { time: 28, text: '风 吹 过 山 河' },
  { time: 36, text: '月 光 照 在 她 的 眉 间' },
])

const activeIndex = computed(() => {
  const t = currentTime.value
  for (let i = lyrics.value.length - 1; i >= 0; i--) {
    if (t >= lyrics.value[i].time) return i
  }
  return 0
})

function loadFile(e: Event) {
  const inp = e.target as HTMLInputElement
  if (!inp.files || inp.files.length === 0) return
  const file = inp.files[0]
  if (fileUrl.value) URL.revokeObjectURL(fileUrl.value)
  fileUrl.value = URL.createObjectURL(file)
  nextTick(() => {
    if (!audioRef.value) return
    audioRef.value.load()
    audioRef.value.volume = volume.value
    play()
  })
}

function onLoadedMetadata() {
  if (!audioRef.value) return
  duration.value = audioRef.value.duration || 0
}

function onTimeUpdate() {
  if (!audioRef.value) return
  currentTime.value = audioRef.value.currentTime
}

function play() {
  if (!audioRef.value) return
  audioRef.value.play()
  isPlaying.value = true
}

function pause() {
  if (!audioRef.value) return
  audioRef.value.pause()
  isPlaying.value = false
}

function togglePlay() {
  if (!audioRef.value) return
  if (isPlaying.value) pause()
  else play()
}

function seekTo(v: number) {
  if (!audioRef.value) return
  audioRef.value.currentTime = v
  currentTime.value = v
}

function setVolume(v: number) {
  volume.value = v
  if (audioRef.value) audioRef.value.volume = v
}

// Auto-scroll lyrics
const lyricsContainer = ref<HTMLElement | null>(null)
watch(activeIndex, async (idx) => {
  await nextTick()
  if (!lyricsContainer.value) return
  const el = lyricsContainer.value.querySelectorAll('.lyric-line')[idx] as HTMLElement | undefined
  if (el) {
    const container = lyricsContainer.value
    const offset = el.offsetTop - container.clientHeight / 2 + el.clientHeight / 2
    container.scrollTo({ top: offset, behavior: 'smooth' })
  }
})

onMounted(() => {
  // if there's a bundled resource, you could pre-load it here
})

function onEnded() {
  isPlaying.value = false
}

function formatTime(v: number | { value: number } | null | undefined) {
  const t = typeof v === 'number' ? v : (v && typeof (v as any).value === 'number' ? (v as any).value : 0)
  if (!isFinite(t) || t <= 0) return '0:00'
  const minutes = Math.floor(t / 60)
  const seconds = Math.floor(t % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}
</script>

<template>
  <main class="flex gap-6 p-6 min-h-screen bg-gradient-to-b from-bg1 to-bg2 text-text box-border">
    <section class="w-[360px] bg-panel p-4 rounded-lg shadow-[0_6px_18px_rgba(2,6,23,0.6)]">
      <div class="flex items-center justify-between gap-3">
        <label class="border border-muted px-3 py-2 rounded cursor-pointer inline-flex items-center">
          Load audio
          <input class="hidden" type="file" accept="audio/*" @change="loadFile" />
        </label>
        <div class="flex items-center gap-3">
          <button class="bg-primary text-white px-3 py-2 rounded" @click="togglePlay">{{ isPlaying ? 'Pause' : 'Play' }}</button>
          <div class="text-muted text-sm">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</div>
        </div>
      </div>

      <input class="w-full mt-3" type="range" min="0" :max="duration" step="0.01" :value="currentTime" @input="(e) => seekTo(Number((e.target as HTMLInputElement).value))" />

      <div class="mt-3 text-muted text-sm">
        <label>Volume <input type="range" min="0" max="1" step="0.01" :value="volume" @input="(e) => setVolume(Number((e.target as HTMLInputElement).value))" /></label>
      </div>

      <audio
        ref="audioRef"
        :src="fileUrl || '/res/我的一个道姑朋友.mp3'"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @ended="onEnded"
      ></audio>
    </section>

    <section class="flex-1 bg-[rgba(255,255,255,0.03)] p-4 rounded-lg overflow-auto" ref="lyricsContainer">
      <ul class="p-0 m-0 list-none">
        <li v-for="(line, i) in lyrics" :key="i" class="py-2 px-3 rounded flex gap-3 items-center" :class="i === activeIndex ? 'bg-gradient-to-r from-[rgba(255,107,107,0.12)] to-[rgba(255,107,107,0.04)] text-white font-semibold' : 'text-muted'">
          <span class="w-16 text-[12px]">{{ formatTime(line.time) }}</span>
          <span class="flex-1">{{ line.text }}</span>
        </li>
      </ul>
    </section>
  </main>
</template>

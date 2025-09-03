<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import Controller from './components/Controller.vue'
import Lyrics from './components/Lyrics.vue'
import Playlist from './components/Playlist.vue'
import { invoke } from '@tauri-apps/api/core'

const audioRef = ref<HTMLAudioElement | null>(null)
const fileUrl = ref<string | null>(null)
const isPlaying = ref(false)
const duration = ref(0)
const currentTime = ref(0)
const volume = ref(1)

const metadata = ref<Metadata | null>(null)

// Example lyrics (seconds)
const lyrics = computed(() => Array.from(metadata.value?.lyrics || []))

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

onMounted(() => {
  // if there's a bundled resource, you could pre-load it here
  ;(async () => {
    try {
      const md = await invoke('get_metadata', { path: fileUrl.value ?? "我的一个道姑朋友.m4a" })
      metadata.value = md as Metadata
      if (metadata.value?.duration) {
        duration.value = metadata.value.duration
      }
    } catch (e) {
      // ignore, optional
      console.warn('get_metadata failed', e)
    }
  })()
})

function onEnded() {
  isPlaying.value = false
}

</script>

<template>
  <main class="flex gap-6 p-6 min-h-screen bg-gradient-to-b from-bg1 to-bg2 text-text box-border">
    <section class="w-[360px] bg-panel p-4 rounded-lg shadow-[0_6px_18px_rgba(2,6,23,0.6)]">
      <Controller :isPlaying="isPlaying" :currentTime="currentTime" :duration="duration" :volume="volume"
        @toggle-play="togglePlay" @seek-to="seekTo" @set-volume="setVolume" @load-file="loadFile" />

      <audio
        ref="audioRef"
        :src="fileUrl || '我的一个道姑朋友.mp3'"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @ended="onEnded"
      ></audio>

      <div class="mt-4">
        <Playlist :items="[{ title: metadata?.title ?? '', artist: metadata?.artist, url: metadata?.url }]" />
      </div>
    </section>

    <section class="flex-1 bg-[rgba(255,255,255,0.03)] p-4 rounded-lg">
      <Lyrics :lyrics="lyrics" :activeIndex="activeIndex" />
    </section>
  </main>
</template>

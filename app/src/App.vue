<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import Controller from './components/Controller.vue'
import Lyrics from './components/Lyrics.vue'
import Playlist from './components/Playlist.vue'
import { invoke } from '@tauri-apps/api/core'

const fileUrl = ref<string | null>(null)
const streamUrl = ref<string | null>(null)
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
  // only revoke previous blob/object URLs
  if (fileUrl.value && fileUrl.value.startsWith('blob:')) URL.revokeObjectURL(fileUrl.value)
  fileUrl.value = URL.createObjectURL(file)
  nextTick(() => {
      // rely on media-player inside Controller (autoplay on selection if we set isPlaying)
      isPlaying.value = true
    })
}
function togglePlay() { isPlaying.value = !isPlaying.value }
function seekTo(v: number) { currentTime.value = v }
function setVolume(v: number) { volume.value = v }

onMounted(() => {
  // if there's a bundled resource, you could pre-load it here
  ;(async () => {
    try {
      // fetch metadata
      const md = await invoke('get_metadata', { path: fileUrl.value ?? "我的一个道姑朋友.m4a" })
      metadata.value = md as Metadata
      if (metadata.value?.duration) {
        duration.value = metadata.value.duration
      }
      // fetch audio content from rust backend as data URL for bundled resource
      // store it in `streamUrl` so we don't overwrite any user-selected `fileUrl`
      if (!streamUrl.value) {
        try {
          const dataUrl = await invoke('load_audio', { path: "我的一个道姑朋友.m4a" }) as string
          streamUrl.value = dataUrl
        } catch (e) {
          // fallback: keep using builtin file name
          console.warn('load_audio failed', e)
        }
      }
    } catch (e) {
      // ignore, optional
      console.warn('get_metadata failed', e)
    }
  })()
})

// ended event handled via play-state false when media ends (vidstack emits pause)

</script>

<template>
  <main class="flex gap-6 p-6 min-h-screen bg-gradient-to-b from-bg1 to-bg2 text-text box-border">
    <section class="w-[360px] bg-panel p-4 rounded-lg shadow-[0_6px_18px_rgba(2,6,23,0.6)]">
      <Controller :src="streamUrl || fileUrl || '我的一个道姑朋友.mp3'" :isPlaying="isPlaying" :currentTime="currentTime" :duration="duration" :volume="volume" :title="metadata?.title ?? 'Unknown'"
        @toggle-play="togglePlay" @seek-to="seekTo" @set-volume="setVolume"
        @time-update="t => currentTime = t"
        @loaded-metadata="d => duration = d"
        @play-state="p => isPlaying = p"
      />
      <label class="border border-muted px-3 py-2 rounded cursor-pointer inline-flex items-center">
        Load audio
        <input class="hidden" type="file" accept="audio/*" @change="loadFile" />
      </label>

  <!-- native <audio> removed; Controller's <media-player> handles playback -->

      <div class="mt-4">
        <Playlist :items="[{ title: metadata?.title ?? '', artist: metadata?.artist, url: metadata?.url }]" />
      </div>
    </section>

    <section class="flex-1 bg-[rgba(255,255,255,0.03)] p-4 rounded-lg">
      <Lyrics :lyrics="lyrics" :activeIndex="activeIndex" />
    </section>
  </main>
</template>

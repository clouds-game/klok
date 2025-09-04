<script setup lang="ts">
import { onMounted, nextTick } from 'vue'
import Controller from './components/Controller.vue'
import Lyrics from './components/Lyrics.vue'
import Playlist from './components/Playlist.vue'
import { invoke } from '@tauri-apps/api/core'
import { base64ToDataUrl } from './utils/time'
import { useAppState } from './utils/state'

const state = useAppState()

// store is used directly (Pinia store properties)

function loadFile(e: Event) {
  const inp = e.target as HTMLInputElement
  if (!inp.files || inp.files.length === 0) return
  const file = inp.files[0]
  // only revoke previous blob/object URLs
  if (state.fileUrl && state.fileUrl.startsWith('blob:')) URL.revokeObjectURL(state.fileUrl)
  state.fileUrl = URL.createObjectURL(file)
  nextTick(() => {
      // rely on media-player inside Controller (autoplay on selection if we set isPlaying)
      state.isPlaying = true
    })
}
function togglePlay() { state.isPlaying = !state.isPlaying }
function seekTo(v: number) { state.currentTime = v }
function setVolume(v: number) { state.volume = v }

onMounted(() => {
  // if there's a bundled resource, you could pre-load it here
  ;(async () => {
    try {
      // fetch metadata
      const md = await invoke('get_metadata', { path: state.fileUrl ?? "我的一个道姑朋友.m4a" })
      state.metadata = md as Metadata
      if (state.metadata?.duration) {
        state.duration = state.metadata.duration
      }
      // fetch audio content from rust backend as data URL for bundled resource
      // store it in `streamUrl` so we don't overwrite any user-selected `fileUrl`
      if (!state.streamUrl) {
        try {
          const dataUrl = await invoke('load_audio', { path: "我的一个道姑朋友.m4a" }) as string
          if (dataUrl.startsWith("data:")) {
            state.streamUrl = (dataUrl)
          } else {
            state.streamUrl = dataUrl
          }
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
      <Controller :src="state.streamUrl || state.fileUrl || '我的一个道姑朋友.mp3'" :isPlaying="state.isPlaying" :currentTime="state.currentTime" :duration="state.duration" :volume="state.volume" :title="state.metadata?.title ?? 'Unknown'"
        @toggle-play="togglePlay" @seek-to="seekTo" @set-volume="setVolume"
        @time-update="t => state.currentTime = t"
        @loaded-metadata="d => state.duration = d"
        @play-state="p => state.isPlaying = p"
      />
      <label class="border border-muted px-3 py-2 rounded cursor-pointer inline-flex items-center">
        Load audio
        <input class="hidden" type="file" accept="audio/*" @change="loadFile" />
      </label>

  <!-- native <audio> removed; Controller's <media-player> handles playback -->

      <div class="mt-4">
        <Playlist :items="[{ title: state.metadata?.title ?? '', artist: state.metadata?.artist, url: state.metadata?.url }]" />
      </div>
    </section>

    <section class="flex-1 bg-[rgba(255,255,255,0.03)] p-4 rounded-lg">
      <Lyrics :lyrics="state.lyrics" :activeIndex="state.activeIndex" />
    </section>
  </main>
</template>

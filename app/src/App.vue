<script setup lang="ts">
import { onMounted, nextTick } from 'vue'
import Controller from './components/Controller.vue'
import Lyrics from './components/Lyrics.vue'
import MidiView from './components/MidiView.vue'
import Playlist from './components/Playlist.vue'
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

onMounted(() => {
  // if there's a bundled resource, you could pre-load it here
  state.fileUrl = "我的一个道姑朋友.m4a"
})

// ended event handled via play-state false when media ends (vidstack emits pause)

</script>

<template>
  <main class="flex gap-6 p-6 min-h-screen bg-gradient-to-b from-bg1 to-bg2 text-text box-border">
    <section class="w-[360px] bg-panel p-4 rounded-lg shadow-[0_6px_18px_rgba(2,6,23,0.6)]">
      <Controller :src="state.streamUrl!" :isPlaying="state.isPlaying" :currentTime="state.currentTime" :duration="state.duration" :volume="state.volume" :title="state.title"
        @set-volume="state.setVolume"
        @seek-to="state.seekTo"
        @time-update="state.seekTo"
        @loaded-metadata="state.setDuration"
        @play-state="state.togglePlay"
      />
      <label class="border border-muted px-3 py-2 rounded cursor-pointer inline-flex items-center">
        Load audio
        <input class="hidden" type="file" accept="audio/*" @change="loadFile" />
      </label>

  <!-- native <audio> removed; Controller's <media-player> handles playback -->

      <div class="mt-4">
        <Playlist :items="[{ title: state.title, artist: state.metadata?.artist, url: state.metadata?.url }]" />
      </div>
    </section>

    <section class="flex flex-col flex-1 bg-[rgba(255,255,255,0.03)] p-4 rounded-lg">
      <div class="flex-1 h-[60vh]">
        <Lyrics :lyrics="state.lyrics" :activeIndex="state.activeIndex" />
      </div>
      <div class="flex-1 mt-4 h-[20vh]">
        <MidiView :notes="state.notes || []" />
      </div>
    </section>
  </main>
</template>

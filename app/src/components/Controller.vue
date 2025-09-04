<script setup lang="ts">
// register vidstack web components
import { MediaToggleButtonElement, type MediaPlayerElement } from 'vidstack/elements'
import 'vidstack/bundle'
import 'vidstack/icons'
import { defineEmits, defineProps, ref, watch } from 'vue'

const props = defineProps<{ title: string, src?: string, src2?: string, isPlaying: boolean; currentTime: number; duration: number; volume: number }>()
const emit = defineEmits<{
  (e: 'seek-to', v: number): void
  (e: 'set-volume', v: number): void
  // new automatic update events so parent doesn't need polling
  (e: 'time-update', t: number): void
  (e: 'loaded-metadata', d: number): void
  (e: 'play-state', playing: boolean): void
}>()

// underlying custom element <media-player>
const player = ref<MediaPlayerElement | null>(null)
const vocalAudio = ref<HTMLAudioElement | null>(null)
const toggleButton = ref<MediaToggleButtonElement | null>(null)
const playoriginal = ref<boolean>(true)

// volume slider not yet implemented inside this component (parent handles volume UI)

// media-player event handlers
function handleTimeUpdate() {
  console.log("Time update:", player.value?.currentTime)
  if (player.value?.currentTime == null) return
  // @ts-ignore custom element exposes currentTime
  const ct = player.value.currentTime
  emit('time-update', ct)
}

function handleSeeked() {
    console.log("Seeked:", player.value?.currentTime)
    if (player.value?.currentTime == null) return
    const ct = player.value.currentTime
    emit('seek-to', ct)
    if (vocalAudio.value)
      vocalAudio.value.currentTime = ct
}

function handleLoadedMetadata() {
  if (!player.value) return
  // @ts-ignore custom element exposes duration
  const d = (player.value as any).duration ?? 0
  emit('loaded-metadata', d)
}

function handlePlay(v: boolean) {
  if (v) {
    vocalAudio.value?.play()
  } else {
    vocalAudio.value?.pause()
  }
  emit('play-state', v)
}

function toggleOriginal() {
  playoriginal.value = toggleButton.value?.pressed ?? !playoriginal.value
  if (vocalAudio.value) {
    vocalAudio.value.muted = playoriginal.value
  }
}

// react to parent state changes
watch(() => props.isPlaying, (val) => {
  const el = player.value
  const a = vocalAudio.value
  if (!el || !a) return
  if (val && el.paused) {
    el.currentTime = props.currentTime // sync time before play
    a.currentTime = props.currentTime
    el.play?.()
    if (playoriginal.value) a.play?.()
  }
  else if (!val && !el.paused) {
    el.pause?.()
    a.pause?.()
  }
}, { immediate: true })

watch(() => props.volume, (v) => {
  const el = player.value
  const a = vocalAudio.value
  if (el) el.volume = v
  if (a) a.volume = v
}, { immediate: true })

</script>

<template>
  <div class="controller w-full select-none">
    <audio ref="vocalAudio" controls :src="props.src2" volume="0.5" preload="metadata"></audio>
    <media-player
      crossorigin
      playsinline
      :current-time="props.currentTime"
      ref="player"
      keep-alive
      @timeupdate="handleTimeUpdate"
      @progress="handleTimeUpdate"
      @loadedmetadata="handleLoadedMetadata"
      @play="handlePlay(true)"
      @pause="handlePlay(false)"
      @seeking="handleSeeked"
      @seeked="handleSeeked"
      class="block"
    >
      <!--@timeupdate and @progress would never emit -->
      <media-provider class="hidden" :src="props.src" type="audio/mp4">
        <source :src="props.src" type="audio/mp4" />
      </media-provider>
      <div class="flex items-center gap-4">
        <!-- Play / Pause -->
        <media-play-button class="vds-button group">
          <!-- See https://vidstack.io/docs/wc/player/components/buttons/play-button/?styling=tailwind-css -->
          <!-- group-data-[paused]:hidden is needed seems .vds-button[data-paused] not work -->
          <media-icon type="play" class="hidden play-icon vds-icon group-data-[paused]:block"></media-icon>
          <media-icon type="pause" class="pause-icon vds-icon group-data-[paused]:hidden"></media-icon>
        </media-play-button>

        <!-- Progress (click to seek) -->
        <media-time-slider class="vds-time-slider vds-slider" @value-change="handleTimeUpdate" @pointer-value-change="handleTimeUpdate">
          <!-- See https://vidstack.io/docs/wc/player/components/sliders/time-slider/?styling=default-theme -->
          <!-- only @pointer-value-change works, @value-change would not emit -->
          <div class="vds-slider-track"></div>
          <div class="vds-slider-track-fill vds-slider-track bg-white"></div>
          <div class="vds-slider-progress vds-slider-track bg-gray"></div>
          <div class="vds-slider-thumb"></div>
        </media-time-slider>

        <!-- Time Display -->
        <div class="vds-time-group">
          <!-- See https://vidstack.io/docs/wc/player/components/display/time/?styling=tailwind-css -->
          <media-time class="time" type="current"></media-time>
          <div class="vds-time-divider">/</div>
          <media-time class="time" type="duration"></media-time>
        </div>

        <!-- Volume (hover to show slider) -->
        <media-mute-button class="vds-button group">
          <!-- See https://vidstack.io/docs/wc/player/components/buttons/mute-button/?styling=tailwind-css -->
          <media-icon type="mute" class="mute-icon vds-icon hidden group-data-[state='muted']:block"></media-icon>
          <media-icon type="volume-low" class="volume-low-icon vds-icon hidden group-data-[state='low']:block"></media-icon>
          <media-icon type="volume-high" class="volume-high-icon vds-icon hidden group-data-[state='high']:block"></media-icon>
        </media-mute-button>
        <media-toggle-button class="vds-button group" :data-defaultPressed="playoriginal" ref="toggleButton" @click=toggleOriginal>
          <media-icon type="no-eye" class="vds-icon hidden group-data-[pressed]:block"></media-icon>
          <media-icon type="user" class="vds-icon block group-data-[pressed]:hidden"></media-icon>
        </media-toggle-button>
      </div>
    </media-player>
  </div>
</template>

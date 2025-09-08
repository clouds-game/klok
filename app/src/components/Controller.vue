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
const vocalsOn = ref<boolean>(true)

// volume slider not yet implemented inside this component (parent handles volume UI)

// media-player event handlers
function handleTimeUpdate() {
  // console.log("Time update:", player.value?.currentTime)
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
  const d = player.value.duration ?? 0
  emit('loaded-metadata', d)
}

function handlePlay(v: boolean) {
  emit('play-state', v)
}

function toggleOriginal() {
  vocalsOn.value = toggleButton.value?.pressed ?? !vocalsOn.value
}

function toPlay(el: HTMLMediaElement | MediaPlayerElement, play: boolean, time: number) {
  if (play && el.paused) {
    el.currentTime = time // sync time before play
    el.play?.()
  }
  else if (!play && !el.paused) {
    el.pause?.()
  }
}

// react to parent state changes
watch(() => props.isPlaying, (val) => {
  const el = player.value
  const a = vocalAudio.value
  if (el) {
    toPlay(el, val, props.currentTime)
  }
  if (a) {
    // if (playoriginal.value) {
    //   a.muted = true
    // } else {
    //   a.muted = false
    // }
    toPlay(a, val, props.currentTime)
  }
}, { immediate: true })

watch(toggleButton, (btn) => {
  if (!btn) return
    if (btn.pressed != vocalsOn.value) {
    console.log("click button")
    // dispatch a pointerup event so the custom toggle button receives a pointerup
    // see https://github.com/vidstack/player/blob/a8871648f2ae0022dc915bea6a4e72c4d49038ce/packages/vidstack/src/utils/dom.ts#L137
    btn?.dispatchEvent(new PointerEvent('pointerup', { bubbles: false, composed: true }))
  }
}, { immediate: true })

watch(() => props.volume, (v) => {
  const el = player.value
  const a = vocalAudio.value
  if (el) el.volume = v
  if (a) a.volume = v
}, { immediate: true })

watch(() => vocalsOn.value, (on) => {
  const a = vocalAudio.value
  if (a) {
    a.muted = !on
    console.log("Vocal audio muted:", a.muted)
  }
}, { immediate: true })

</script>

<template>
  <div class="controller w-full select-none">
    <audio ref="vocalAudio" :src="props.src2" volume="0.5" preload="metadata" v-if="props.src2"></audio>
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
      <media-provider class="hidden" :src="props.src" type="audio/mpeg">
        <source :src="props.src" type="audio/mpeg" />
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
        <media-mute-button class="vds-button group" v-if="props.src2">
          <!-- See https://vidstack.io/docs/wc/player/components/buttons/mute-button/?styling=tailwind-css -->
          <media-icon type="mute" class="mute-icon vds-icon hidden group-data-[state='muted']:block"></media-icon>
          <media-icon type="volume-low" class="volume-low-icon vds-icon hidden group-data-[state='low']:block"></media-icon>
          <media-icon type="volume-high" class="volume-high-icon vds-icon hidden group-data-[state='high']:block"></media-icon>
        </media-mute-button>
        <media-toggle-button class="vds-button group" :default-pressed="vocalsOn" ref="toggleButton" @click=toggleOriginal>
          <!-- See https://vidstack.io/docs/wc/player/components/buttons/toggle-button/?styling=default-theme -->
          <!-- default-pressed or `:default-pressed="vocalsOn ? '' as any : undefined"` doesn't works -->
          <!-- see also `watch(toggleButton, (btn) => ...)` -->
          <media-icon type="no-eye" slot="vocals-mute" class="vds-icon block group-data-[pressed]:hidden"></media-icon>
          <media-icon type="user" slot="vocals-unmute" class="vds-icon hidden group-data-[pressed]:block"></media-icon>
        </media-toggle-button>
      </div>
    </media-player>
  </div>
</template>

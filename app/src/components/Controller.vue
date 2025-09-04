<script setup lang="ts">
// register vidstack web components
import 'vidstack/bundle'
import 'vidstack/icons'
import { defineEmits, defineProps, ref, watch } from 'vue'

const props = defineProps<{ title: string, src: string, isPlaying: boolean; currentTime: number; duration: number; volume: number }>()
const emit = defineEmits<{
  (e: 'toggle-play'): void
  (e: 'seek-to', v: number): void
  (e: 'set-volume', v: number): void
  // new automatic update events so parent doesn't need polling
  (e: 'time-update', t: number): void
  (e: 'loaded-metadata', d: number): void
  (e: 'play-state', playing: boolean): void
}>()

// underlying custom element <media-player>
const player = ref<any | null>(null)

function onSeek(e: Event) {
  const t = e.target as HTMLInputElement
  const v = Number(t?.value ?? 0)
  const max = Number(t?.max ?? 1)
  const newTime = (props.duration || 0) * Math.max(0, Math.min(1, v / max))
  emit('seek-to', newTime)
}

// volume slider not yet implemented inside this component (parent handles volume UI)

// media-player event handlers
function handleTimeUpdate() {
  if (!player.value) return
  // @ts-ignore custom element exposes currentTime
  const ct = (player.value as any).currentTime ?? 0
  emit('time-update', ct)
}

function handleLoadedMetadata() {
  if (!player.value) return
  // @ts-ignore custom element exposes duration
  const d = (player.value as any).duration ?? 0
  emit('loaded-metadata', d)
}

function handlePlay() {
  emit('play-state', true)
}

function handlePause() {
  emit('play-state', false)
}

// react to parent state changes
watch(() => props.isPlaying, (val) => {
  const el: any = player.value
  if (!el) return
  if (val && el.paused) el.play?.()
  else if (!val && !el.paused) el.pause?.()
})

watch(() => props.volume, (v) => {
  const el: any = player.value
  if (el) el.volume = v
}, { immediate: true })

function onProgressClick(e: MouseEvent) {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  const newTime = (props.duration || 0) * Math.max(0, Math.min(1, ratio))
  emit('seek-to', newTime)
}
</script>

<template>
  <div class="controller w-full select-none">
    <media-player
      :src="props.src"
      crossorigin
      playsinline
      :current-time="props.currentTime"
      :ref="player"
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleLoadedMetadata"
      @play="handlePlay"
      @pause="handlePause"
      @seeking="onSeek"
      @seeked="onSeek"
      class="block"
    >
      <media-provider class="hidden" />
      <div class="flex items-center gap-4">
        <!-- Play / Pause -->
        <media-play-button class="vds-button group">
          <!-- See https://vidstack.io/docs/wc/player/components/buttons/play-button/?styling=tailwind-css -->
          <!-- group-data-[paused]:hidden is needed seems .vds-button[data-paused] not work -->
          <media-icon type="play" class="hidden play-icon vds-icon group-data-[paused]:block"></media-icon>
          <media-icon type="pause" class="pause-icon vds-icon group-data-[paused]:hidden"></media-icon>
        </media-play-button>

        <!-- Progress (click to seek) -->
        <media-time-slider class="vds-time-slider vds-slider" @click="onProgressClick">
          <!-- See https://vidstack.io/docs/wc/player/components/sliders/time-slider/?styling=default-theme -->
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
      </div>
    </media-player>
  </div>
</template>

<!-- formatTime imported from ../utils/time -->

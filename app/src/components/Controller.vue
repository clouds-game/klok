<script setup lang="ts">
import { computed, defineEmits, defineProps } from 'vue'
import { formatTime } from '../utils/time'

const props = defineProps<{ title: string, isPlaying: boolean; currentTime: number; duration: number; volume: number }>()
defineEmits<{
  (e: 'toggle-play'): void
  (e: 'seek-to', v: number): void
  (e: 'set-volume', v: number): void
}>()

// compute filled percent for the range input so we can paint the left side white
const percent = computed(() => {
  const d = props.duration || 0
  if (d <= 0) return 0
  return Math.min(100, Math.max(0, (props.currentTime / d) * 100))
})

const rangeStyle = computed(() => {
  // left (filled) - white, right (unfilled) - faint translucent white to keep visibility on dark backgrounds
  const p = `${percent.value}%`
  return {
    background: `linear-gradient(90deg, white 0%, white ${p}, rgba(255,255,255,0.18) ${p}, rgba(255,255,255,0.18) 100%)`
  }
})

</script>
<template>
  <div>
    <div class="flex items-center justify-between gap-3">
      <div p="x-3 y-2">
        {{ props.title }}
      </div>
      <div class="flex items-center gap-3">
        <button class="rounded" bg="primary" text="white" p="x-3 y-2" @click="$emit('toggle-play')">{{ props.isPlaying ? 'Pause' : 'Play' }}</button>
        <div text="muted sm">{{ formatTime(props.currentTime) }} / {{ formatTime(props.duration) }}</div>
      </div>
    </div>

    <div class="p1" :style="rangeStyle">
      <input class="w-full mt-3" bg="transparent" type="range" min="0" :max="props.duration" step="0.01" :value="props.currentTime" @input="$emit('seek-to', Number(( $event.target as HTMLInputElement).value))" />
    </div>

    <div class="mt-3" text="muted sm">
      <label>Volume <input type="range" min="0" max="1" step="0.01" :value="props.volume" @input="$emit('set-volume', Number(( $event.target as HTMLInputElement).value))" /></label>
    </div>
  </div>
</template>

<!-- formatTime imported from ../utils/time -->

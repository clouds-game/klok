<script setup lang="ts">
import { defineEmits, defineProps } from 'vue'
import { formatTime } from '../utils/time'

const props = defineProps<{ isPlaying: boolean; currentTime: number; duration: number; volume: number }>()
defineEmits<{
  (e: 'toggle-play'): void
  (e: 'seek-to', v: number): void
  (e: 'set-volume', v: number): void
  (e: 'load-file', ev: Event): void
}>()

</script>
<template>
  <div>
    <div class="flex items-center justify-between gap-3">
      <label class="border border-muted px-3 py-2 rounded cursor-pointer inline-flex items-center">
        Load audio
        <input class="hidden" type="file" accept="audio/*" @change="$emit('load-file', $event)" />
      </label>
      <div class="flex items-center gap-3">
        <button class="bg-primary text-white px-3 py-2 rounded" @click="$emit('toggle-play')">{{ props.isPlaying ? 'Pause' : 'Play' }}</button>
        <div class="text-muted text-sm">{{ formatTime(props.currentTime) }} / {{ formatTime(props.duration) }}</div>
      </div>
    </div>

    <input class="w-full mt-3" type="range" min="0" :max="props.duration" step="0.01" :value="props.currentTime" @input="$emit('seek-to', Number(( $event.target as HTMLInputElement).value))" />

    <div class="mt-3 text-muted text-sm">
      <label>Volume <input type="range" min="0" max="1" step="0.01" :value="props.volume" @input="$emit('set-volume', Number(( $event.target as HTMLInputElement).value))" /></label>
    </div>
  </div>
</template>

<!-- formatTime imported from ../utils/time -->

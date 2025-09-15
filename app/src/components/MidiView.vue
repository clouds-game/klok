<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useAppState } from '../utils/state'
import { drawNotes } from '../utils/draw'
import { MidiNote, SegNote } from '../utils/types';
import { usePitchStore } from '../utils/pitch';


const props = defineProps<{ notes: MidiNote[]; segNotes: SegNote[]; left_time?: number; right_time?: number }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const state = useAppState()
const pitchState = usePitchStore()

let raf = 0

const redraw = () => {
  const notes = props.notes
  const segNotes = props.segNotes

  drawNotes(canvas.value, notes, segNotes,{
    duration: state.duration,
    current_time: state.currentTime,
    left_time: props.left_time,
    right_time: props.right_time,
    min_note: 50,
    max_note: 80,
    pitch_history: pitchState.pitchHistory,
  })
}
const resizeObserver = new ResizeObserver(redraw)

watch(canvas, (el) => {
  if (el) resizeObserver.observe(el)
  nextTick(() => redraw())
})

onBeforeUnmount(() => {
  if (canvas.value) resizeObserver.unobserve(canvas.value)
  if (raf) cancelAnimationFrame(raf)
})

// redraw when notes prop or duration change
watch(() => props.notes, redraw, { deep: true })
watch(() => pitchState.currentSegNotes, redraw)
watch(() => state.isPlaying, (v) => { if (v) redraw() })
watch(() => [props.left_time, props.right_time], redraw)
watch(() => [state.currentTime, state.duration], redraw)
</script>

<template>
  <div class="w-full h-full bg-[#0b0b0b] rounded-md overflow-hidden">
    <canvas ref="canvas" class="w-full h-full block"></canvas>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useAppState } from '../utils/state'

type Note = {
  note: number
  start: number
  duration: number
  velocity: number
  channel: number
  confidence?: number | null
}

const props = defineProps<{ notes: Note[] }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const state = useAppState()

let raf = 0

const resizeObserver = new ResizeObserver(() => draw(canvas.value, props.notes))

function draw(canvas: HTMLCanvasElement | null, notes: Note[] | null) {
  const c = canvas
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return
  const dpr = window.devicePixelRatio || 1
  const cssWidth = Math.max(c.clientWidth, 800)
  const cssHeight = Math.max(c.clientHeight, 300)
  c.width = cssWidth
  c.height = cssHeight
  console.log(dpr, cssWidth, cssHeight, c.height, c.width)
  // c.width = Math.max(1, Math.floor(cssWidth * dpr))
  // c.height = Math.max(1, Math.floor(cssHeight * dpr))
  // c.style.width = cssWidth + 'px'
  // c.style.height = cssHeight + 'px'
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  // background
  ctx.fillStyle = '#0b0b0b'
  ctx.fillRect(0, 0, cssWidth, cssHeight)

  const ns = notes || []
  if (ns.length === 0) {
    ctx.fillStyle = '#666'
    ctx.font = '12px sans-serif'
    ctx.fillText('No MIDI notes', 8, 20)
    return
  }

  // determine note range
  let minNote = Infinity
  let maxNote = -Infinity
  for (const n of ns) {
    if (n.note < minNote) minNote = n.note
    if (n.note > maxNote) maxNote = n.note
  }
  if (!isFinite(minNote)) minNote = 21
  if (!isFinite(maxNote)) maxNote = 108
  minNote = Math.max(0, Math.floor(minNote) - 1)
  maxNote = Math.min(127, Math.ceil(maxNote) + 1)
  const noteRange = Math.max(1, maxNote - minNote)

  const totalTime = state.duration || (ns[ns.length - 1].start + ns[ns.length - 1].duration) || 1
  console.log(`minNote: ${minNote}, maxNote: ${maxNote}, noteRange: ${noteRange}, totalTime: ${totalTime}`)

  const clip = (value: number, min: number = 0, max: number = 1) => Math.min(Math.max(value, min), max)
  const timeToX = (t: number) => clip(t / totalTime) * cssWidth
  const noteToY = (m: number) => {
    const rel = (m - minNote) / noteRange
    return clip(1 - rel) * (cssHeight - 20) + 10
  }

  // grid lines for octaves
  ctx.strokeStyle = 'rgba(255,255,255,0.06)'
  ctx.lineWidth = 1
  for (let n = minNote; n <= maxNote; n++) {
    if (n % 12 === 0) {
      const y = noteToY(n)
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(cssWidth, y)
      ctx.stroke()
      console.log(0, y, cssWidth, y)
    }
  }

  // notes
  for (const n of ns) {
    const x = timeToX(n.start)
    const w = Math.max(1, timeToX(n.start + n.duration) - x)
    const y = noteToY(n.note)
    const h = Math.max(4, (cssHeight - 20) / noteRange)
    const alpha = Math.min(1, 0.25 + (n.velocity / 127) * 0.75)
    ctx.fillStyle = `rgba(40,200,255,${alpha})`
    ctx.fillRect(x, y - h / 2, w, h)
    ctx.strokeStyle = `rgba(0,0,0,0.25)`
    ctx.strokeRect(x + 0.5, y - h / 2 + 0.5, w - 1, h - 1)
  }

  // time ruler
  ctx.fillStyle = 'rgba(255,255,255,0.6)'
  ctx.font = '11px sans-serif'
  const step = Math.max(1, Math.pow(10, Math.floor(Math.log10(totalTime)) - 1))
  for (let t = 0; t <= totalTime; t += step) {
    const x = timeToX(t)
    ctx.fillRect(x, cssHeight - 8, 1, 6)
    ctx.fillText(t.toFixed(0), x + 4, cssHeight - 2)
  }

  // request next frame if playing to allow playhead animation later
  // if (state.isPlaying) {
  //   raf = requestAnimationFrame(() => draw(canvas, props.notes))
  // }
}

watch(canvas, (el) => {
  if (el) resizeObserver.observe(el)
  draw(el, props.notes)
})

onBeforeUnmount(() => {
  if (canvas.value) resizeObserver.unobserve(canvas.value)
  if (raf) cancelAnimationFrame(raf)
})

// redraw when notes prop or duration change
watch(() => props.notes, () => draw(canvas.value, props.notes), { deep: true })
watch(() => state.duration, () => draw(canvas.value, props.notes))
watch(() => state.isPlaying, (v) => { if (v) draw(canvas.value, props.notes) })
</script>

<template>
  <div class="w-full h-full bg-[#0b0b0b] rounded-md overflow-hidden">
    <canvas ref="canvas" class="w-full h-full block"></canvas>
  </div>
</template>

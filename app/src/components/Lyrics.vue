<script setup lang="ts">
import { ref, watch, nextTick, defineProps } from 'vue'
import { formatTime } from '../utils/time'

const props = defineProps<{ lyrics: LyricLine[]; activeIndex: number }>()
const emit = defineEmits<{
  (e: 'seek-to', t: number): void
}>()
const container = ref<HTMLElement | null>(null)

watch(() => props.activeIndex, async (idx) => {
  await nextTick()
  if (!container.value) return
  const nodes = container.value.querySelectorAll('.lyric-line')
  const el = nodes[idx] as HTMLElement | undefined
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
})

const jumpToTime = (t: number) => {
  emit('seek-to', t)
}

</script>
<template>
  <div class="h-full overflow-auto" ref="container">
    <ul class="p-0 m-0 list-none">
      <li v-for="(line, i) in props.lyrics" :key="i" class="lyric-line py-2 px-3 rounded flex gap-3 items-center" :class="{ 'bg-gradient-to-r from-[rgba(255,107,107,0.12)] to-[rgba(255,107,107,0.04)] font-semibold': i === props.activeIndex }" :text="i === props.activeIndex ? 'white' : 'muted'">
        <span class="w-16 text-[12px] select-none" @dblclick="jumpToTime(line.time)">{{ formatTime(line.time) }}</span>
        <span class="flex-1">{{ line.text }}</span>
      </li>
    </ul>
  </div>
</template>

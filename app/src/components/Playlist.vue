<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import { PlayListItem } from '../utils/state';
// accept an optional `current` prop (url of the currently playing item)
const props = defineProps<{ items: PlayListItem[], current_url?: string }>()
const emit = defineEmits<{
  (e: 'switch_song', v: string): void
}>()
function onItemClick(it: PlayListItem) {
  console.log("Switching to:", it.url)
  emit('switch_song', it.url)
}
</script>



<template>
  <div>
    <ul class="p-0 m-0 list-none">
      <li v-for="(it, i) in props.items" :key="i" @click="onItemClick(it)"
        :class="['py-2 px-3 rounded cursor-pointer hover:bg-[rgba(255,255,255,0.02)]', it.url === props.current_url ? 'bg-[rgba(255,255,0,0.4)] ring-1 ring-white/10' : '']">
        <div class="font-medium" text="sm">{{ it.title }}</div>
        <div text="muted xs">{{ it.artist }}</div>
      </li>
    </ul>
  </div>
</template>

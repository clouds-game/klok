<script setup lang="ts">
import { defineProps } from 'vue'
const props = defineProps<{ items: { title: string; artist?: string; url?: string }[] }>()
</script>

<template>
  <div>
    <ul class="p-0 m-0 list-none">
      <li v-for="(it, i) in props.items" :key="i" class="py-2 px-3 rounded hover:bg-[rgba(255,255,255,0.02)] cursor-pointer">
        <div class="font-medium" text="sm">{{ it.title }}</div>
        <div text="muted xs">{{ it.artist }}</div>
      </li>
    </ul>
  </div>
</template>

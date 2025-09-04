import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppState = defineStore('app', () => {
  const fileUrl = ref<string | null>(null)
  const streamUrl = ref<string | null>(null)
  const isPlaying = ref(false)
  const duration = ref(0)
  const currentTime = ref(0)
  const volume = ref(1)
  const metadata = ref<Metadata | null>(null)

  const lyrics = computed(() => Array.from(metadata.value?.lyrics || []))

  const activeIndex = computed(() => {
    const t = currentTime.value
    for (let i = lyrics.value.length - 1; i >= 0; i--) {
      if (t >= lyrics.value[i].time) return i
    }
    return 0
  })

  return {
    fileUrl,
    streamUrl,
    isPlaying,
    duration,
    currentTime,
    volume,
    metadata,
    lyrics,
    activeIndex,
  }
})

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { MidiNote, pitchData, SegNote } from "./types"
import { useAppState } from './state'
import { fetchCurrentPitch } from './api'


// 将notes按照是否重叠分割成多个多个groups
function GroupNotes(notes: MidiNote[]): MidiNote[][] {
  if (notes.length === 0) return []

  notes.sort((a, b) => a.start - b.start)
  const groups: MidiNote[][] = []
  let start: number = notes[0].start
  let end: number = notes[0].start + notes[0].duration
  let group: MidiNote[] = [notes[0]]
  for (const n of notes.slice(1)) {
    if (n.start <= end) {
      // 重叠，更新end
      end = Math.max(end, n.start + n.duration)
      group.push(n)
    } else {
      // 不重叠，保存当前组，开始新组
      groups.push(group)
      group = [n]
      start = n.start
      end = n.start + n.duration
    }
  }
  groups.push(group)
  return groups
}

// 将每个group生成不重叠的note片段
function _generateNoteSegments(group: MidiNote[]): SegNote[] {
  if (group.length === 0) return []
  let res: SegNote[] = []
  let times: number[] = group.map(n => [n.start, n.start + n.duration]).flat()
  times = Array.from(new Set(times)) // 去重
  times.sort((a, b) => a - b)
  // todo 考虑相邻时间点间隔过小的情况 通过abs(a-b) < threshold来去重
  for (let i = 0; i < times.length - 1; i++) {
    const segStart = times[i]
    const segEnd = times[i + 1]
    const segNote: SegNote = { start: segStart, end: segEnd }
    res.push(segNote)
  }
  return res
}

// 生成note片段
function generateNoteSegments(groups: MidiNote[][]): SegNote[] {
  const res: SegNote[] = []
  for (const group of groups) {
    const segs = _generateNoteSegments(group)
    res.push(...segs)
  }
  return res
}

// 将实际采集到的pitch数据填充到SegNote中
function fillPitchDataToSegNotes(segNotes: SegNote[], pitchHistory: pitchData[], margin: number = 0.1): SegNote[] {
  if (segNotes.length === 0 || pitchHistory.length === 0) return []
  const res: SegNote[] = []
  for (const seg of segNotes) {
    const start = seg.start - margin
    const end = seg.end + margin
    const pitchs = pitchHistory.filter(p => p.time >= start && p.time < end)
    const note = pitchs.length > 0 ? Math.round(pitchs.reduce((a, b) => a + b.midi, 0) / pitchs.length) : undefined
    res.push({ ...seg, note })
  }
  return res
}

export const usePitchStore = defineStore("pitch", () => {
  let pitchPollTimer: number | null = null

  const pitchHistory = ref<pitchData[]>([])
  const segNotes = computed(() => {
    const state = useAppState()
    const groups = GroupNotes(state.notes || [])
    const segs = generateNoteSegments(groups)
    return segs
  })
  const currentSegNotes = computed(() => {
    const state = useAppState()
    const segs = segNotes.value
    const current = segs.filter(seg => seg.end > state.activeLeftTime && seg.start < state.activeRightTime)
    const res = fillPitchDataToSegNotes(current, pitchHistory.value)
    return res || []
  })


  // Start polling pitch endpoint every 100ms. Will replace existing timer.
  const startPitchPolling = () => {
    if (pitchPollTimer) clearInterval(pitchPollTimer)
    const poll = async () => {
      const state = useAppState()
      if (!state.isPlaying) return
      const data = await fetchCurrentPitch(true)
      if (data) {
        data.time = state.currentTime
        pitchHistory.value.push(data)
      } else {
        console.warn('fetchCurrentPitch returned no data')
      }
    }
    pitchPollTimer = setInterval(poll, 200)
  }

  const stopPitchPolling = () => {
    if (pitchPollTimer) {
      clearInterval(pitchPollTimer)
      pitchPollTimer = null
    }
  }

  return {
    pitchHistory,
    segNotes,
    currentSegNotes,
    startPitchPolling,
    stopPitchPolling,
  }
})

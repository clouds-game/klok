export function formatTime(v: number | { value: number } | null | undefined) {
  const t = typeof v === 'number' ? v : (v && typeof (v as any).value === 'number' ? (v as any).value : 0)
  if (!isFinite(t) || t <= 0) return '0:00'
  const minutes = Math.floor(t / 60)
  const seconds = Math.floor(t % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

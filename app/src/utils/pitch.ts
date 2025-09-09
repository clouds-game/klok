import { pitchData } from "./api"

export type MidiNote = {
  note: number
  start: number
  duration: number
  velocity: number
  channel: number
  confidence?: number | null
}

type DrawOptions = {
  duration?: number
  current_time?: number
  left_time?: number
  right_time?: number
  min_note?: number
  max_note?: number
  alpha_threshold?: number
  // current detected pitch in Hz (optional)
  current_pitch_data?:  pitchData| null
  // history of detected pitches as array of {t: number, hz: number}
  pitch_history?: pitchData[] | null
}

function isValidNumber(v: any): v is number {
  return typeof v === 'number' && !Number.isNaN(v) && isFinite(v)
}

export function drawNotes(canvas: HTMLCanvasElement | null, notes: MidiNote[] | null, opts: DrawOptions = {}) {
  const c = canvas
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const cssWidth = Math.max(c.clientWidth, 800)
  const cssHeight = Math.max(c.clientHeight, 300)
  c.width = cssWidth
  c.height = cssHeight
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
  if (isValidNumber(opts.min_note)) minNote = opts.min_note
  if (isValidNumber(opts.max_note)) maxNote = opts.max_note
  minNote = Math.max(0, Math.floor(minNote) - 1)
  maxNote = Math.min(127, Math.ceil(maxNote) + 1)
  const noteRange = Math.max(1, maxNote - minNote)

  const rawTotal = (opts.duration !== undefined && !Number.isNaN(opts.duration))
    ? opts.duration
    : (ns.length > 0 ? (ns[ns.length - 1].start + ns[ns.length - 1].duration) : 1)

  const viewStart = isValidNumber(opts.left_time) ? opts.left_time : 0
  const viewEnd = isValidNumber(opts.right_time) ? opts.right_time : rawTotal
  const visibleDuration = Math.max(0.001, viewEnd - viewStart)

  const clip = (value: number, min: number = 0, max: number = 1) => Math.min(Math.max(value, min), max)
  const timeToX = (t: number) => clip((t - viewStart) / visibleDuration) * cssWidth
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
    }
  }

  // notes (cropped to view window)
  const visibleNotes = ns.filter(n => (n.start + n.duration) > viewStart && n.start < viewEnd)
  for (const n of visibleNotes) {
    const x = timeToX(n.start)
    const w = Math.max(1, timeToX(n.start + n.duration) - x)
    const y = noteToY(n.note)
    const h = Math.max(4, (cssHeight - 20) / noteRange)
    const alphaThreshold = opts.alpha_threshold || 0.3
    const alpha = Math.min(1, Math.max(n.velocity / 127 - alphaThreshold, 0) / (1 - alphaThreshold))
    ctx.fillStyle = `rgba(40,200,255,${alpha})`
    ctx.fillRect(x, y - h / 2, w, h)
    ctx.strokeStyle = `rgba(0,0,0,0.25)`
    ctx.strokeRect(x + 0.5, y - h / 2 + 0.5, w - 1, h - 1)
  }

  // time ruler
  ctx.fillStyle = 'rgba(255,255,255,0.6)'
  ctx.font = '11px sans-serif'
  const step = Math.max(1, Math.pow(10, Math.floor(Math.log10(visibleDuration)) - 1))
  for (let t = Math.ceil(viewStart); t <= Math.ceil(viewEnd); t += step) {
    const x = timeToX(t)
    ctx.fillRect(x, cssHeight - 8, 1, 6)
    ctx.fillText((t).toFixed(0), x + 4, cssHeight - 2)
  }

  // draw current time playhead if provided
  if (opts.current_time !== undefined && !Number.isNaN(opts.current_time)) {
    const ct = opts.current_time
    if (ct >= viewStart && ct <= viewEnd) {
      const x = timeToX(ct)
      // vertical line
      ctx.strokeStyle = 'rgba(255,60,60,0.95)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(x + 0.5, 0)
      ctx.lineTo(x + 0.5, cssHeight)
      ctx.stroke()

      // top triangular marker
      ctx.fillStyle = 'rgba(255,60,60,0.95)'
      ctx.beginPath()
      ctx.moveTo(x - 6, 6)
      ctx.lineTo(x + 6, 6)
      ctx.lineTo(x, 0)
      ctx.closePath()
      ctx.fill()

      // time label
      ctx.fillStyle = 'rgba(255,255,255,0.9)'
      ctx.font = '12px sans-serif'
      const label = ct.toFixed(2)
      const tx = Math.min(Math.max(6, x + 8), cssWidth - 40)
      ctx.fillText(label, tx, 14)
    }
  }
}

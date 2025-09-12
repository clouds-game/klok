export type MidiNote = {
  note: number
  start: number
  duration: number
  velocity: number
  channel: number
  confidence?: number | null
}

export type SegNote = {
  start: number
  end: number
  note?: number
}


export type PlayListItem = {
  title: string
  artist?: string
  url: string
}

export type pitchData = {
  pitch: number
  midi: number
  note: string
  time: number
}


export type DrawOptions = {
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

export type ScoreOptions = {
  // tolerance (semitones) where error==tolerance maps to zero score for that sample
  tolerance?: number
  // margin (seconds) added before/after a note when collecting pitch samples
  margin?: number
  // minimal samples to consider a note reliably detected (affects nothing except optional heuristics)
  minSamples?: number
  // whether to weight per-note scores by their duration when computing overall score
  weightByDuration?: boolean
}


export type NoteScore = {
  index: number
  note: number
  start: number
  duration: number
  // normalized score in range [0,1] (1 = perfect)
  score: number
  // mean absolute error in semitones between detected midi and target
  meanError: number | null
  // number of pitch samples used for this note
  samples: number
}


export type ScoreResult = {
  perNote: NoteScore[]
  overall: number
  // weights and options used for scoring
  options: {
    tolerance: number
    margin: number
    minSamples: number
    weightByDuration: boolean
  }
}

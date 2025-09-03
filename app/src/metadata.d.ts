
type LyricLine = { time: number; text: string }

type Metadata = {
  title: string
  artist: string
  url: string
  duration: number
  lyrics: Array<LyricLine>
}

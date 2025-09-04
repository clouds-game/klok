export function formatTime(v: number | { value: number } | null | undefined) {
  const t = typeof v === 'number' ? v : (v && typeof (v as any).value === 'number' ? (v as any).value : 0)
  if (!isFinite(t) || t <= 0) return '0:00'
  const minutes = Math.floor(t / 60)
  const seconds = Math.floor(t % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

/**
 * Converts a Base64 string to a temporary file URL.
 * @param dataUrl The full data URI string (e.g., "data:image/png;base64,...").
 * @returns The object URL for the file.
 */
export function base64ToDataUrl(dataUrl: string): string {
  // Extract the MIME type from the Data URI.
  const mimeMatch = dataUrl.match(/:(.*?);/)
  const mimeType = mimeMatch ? mimeMatch[1] : ''

  // Separate the Base64 data from the prefix.
  const base64Data = dataUrl.split(',')[1]
  // @ts-ignore
  const uint8Array: Uint8Array<ArrayBuffer> = Uint8Array.fromBase64(base64Data)

  // Create a Blob from the Uint8Array.
  const blob = new Blob([uint8Array], { type: mimeType })

  console.log(dataUrl.length, uint8Array.length, blob.type, blob.size)
  // Create and return the temporary object URL.
  return URL.createObjectURL(blob)
}

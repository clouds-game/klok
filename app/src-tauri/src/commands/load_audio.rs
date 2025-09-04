use crate::AppState;
use base64::Engine;
use std::path::Path;
use tauri::State;

pub fn read_audio_file(path: &Path) -> Result<String, String> {
  match std::fs::read(&path) {
    Ok(bytes) => {
      // choose mime based on extension; use generic m4a/mp4 audio type
      let mime = if path.ends_with(".mp3") {
        "audio/mpeg"
      } else if path.ends_with(".m4a") {
        "audio/mp4"
      } else if path.ends_with(".flac") {
        "audio/flac"
      } else {
        "application/octet-stream"
      };

      let encoded = base64::engine::general_purpose::STANDARD.encode(&bytes);
      let data_url = format!("data:{};base64,{}", mime, encoded);
      Ok(data_url)
    }
    Err(e) => Err(format!("failed to read {}: {}", path.display(), e)),
  }
}

/// Read a bundled resource file and return a data URL with base64-encoded content.
/// The frontend can set this as the `src` of an <audio> element.
#[tauri::command]
pub fn load_audio(state: State<'_, AppState>, path: String) -> Result<String, String> {
  if path.is_empty() {
    return Err("path argument is empty".to_string());
  }

  // Resolve path using app state (so bundle resources can be found)
  if let Some(resolved) = state.resolve(&path) {
    read_audio_file(&resolved)
  } else {
    Err(format!("resource not found: {}", path))
  }
}

use crate::AppState;
use std::path::Path;
use tauri::State;

pub fn read_audio_file(path: &Path) -> Result<Vec<u8>, String> {
  std::fs::read(&path).map_err(|e| format!("failed to read {}: {}", path.display(), e))
}

/// Read a bundled resource file and return a data URL with base64-encoded content.
/// The frontend can set this as the `src` of an <audio> element.
#[tauri::command]
pub fn load_audio(state: State<'_, AppState>, path: String) -> Result<Vec<u8> , String> {
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

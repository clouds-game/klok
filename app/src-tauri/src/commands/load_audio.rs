use crate::AppState;
use std::path::Path;
use tauri::State;
use tauri::ipc::Response;

pub fn read_audio_file(path: &Path) -> Result<Vec<u8>, String> {
  std::fs::read(&path).map_err(|e| format!("failed to read {}: {}", path.display(), e))
}

/// Read a bundled resource file and return binary audio bytes wrapped in an IPC Response.
/// The frontend can call the command via the Tauri IPC and receive a binary payload.
#[tauri::command]
pub fn load_audio(state: State<'_, AppState>, path: String) -> Result<Response, String> {
  if path.is_empty() {
    return Err("path argument is empty".to_string());
  }

  // Resolve path using app state (so bundle resources can be found)
  let resolved = state.resolve(&path).ok_or_else(|| format!("resource not found: {}", path))?;

  let bytes = read_audio_file(&resolved)?;
  Ok(Response::new(bytes))
}

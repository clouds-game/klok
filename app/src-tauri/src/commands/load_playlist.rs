use lofty::{AudioFile, Probe};
use serde::Serialize;
use tauri::State;

use crate::AppState;

#[derive(Serialize)]
pub struct PlaylistItem {
  pub title: String,
  pub url: String,
  pub artist: Option<String>,
}

const UNEXPECTED_SUFFIX: [&str; 2] = ["non_vocals", "vocals"];

/// Scan the state's res_dir for files matching extensions and return a playlist.
/// `extensions` is optional; when empty the DEFAULT_EXT list is used.
#[tauri::command]
pub fn load_playlist(state: State<'_, AppState>, extensions: Option<Vec<String>>) -> Result<Vec<PlaylistItem>, String> {
  let exts: Vec<String> = if let Some(v) = extensions {
    if v.is_empty() {
      super::COMMON_EXT.iter().map(|s| s.to_string()).collect()
    } else {
      v
    }
  } else {
    super::COMMON_EXT.iter().map(|s| s.to_string()).collect()
  };

  let mut items: Vec<PlaylistItem> = Vec::new();

  let dir = &state.res_dir;
  if !dir.exists() {
    return Err(format!("res_dir does not exist: {}", dir.display()));
  }

  // read top-level entries only
  let entries = match std::fs::read_dir(dir) {
    Ok(e) => e,
    Err(e) => return Err(format!("failed to read res_dir {}: {}", dir.display(), e)),
  };

  for entry in entries.flatten() {
    let path = entry.path();
    if path.is_file() {
      if let Some(os) = path.extension().and_then(|s| s.to_str()) {
        let dot_ext = format!(".{}", os);
        if exts.iter().any(|e| e == &dot_ext) {
          // build title and relative path
          let title = path.file_stem().and_then(|s| s.to_str()).unwrap_or("").to_string();

          // filter out unexpected suffixes (e.g. "vocals", "non_vocals")
          if UNEXPECTED_SUFFIX.iter().any(|sfx| title.ends_with(sfx)) {
            continue;
          }

          let url = path.file_name().and_then(|s| s.to_str()).unwrap_or("").to_string();
          items.push(PlaylistItem {
            title,
            url,
            artist: None,
          });
        }
      }
    }
  }

  Ok(items)
}

#[macro_use]
extern crate tracing;
use serde::{Serialize, Deserialize};
use std::path::Path;
use std::fs;
use tracing::instrument;
use tauri::{WindowEvent, Position, PhysicalPosition, LogicalPosition};
use std::env;
use std::path::PathBuf;


// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
  info!(%name, "greet called");
  format!("Hello, {}! You've been greeted from Rust!", name)
}

#[derive(Serialize)]
struct LyricLine {
  time: f64,
  text: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct WindowState {
  x: f64,
  y: f64,
}

#[derive(Serialize)]
struct Metadata {
  title: String,
  artist: String,
  url: String,
  duration: f64,
  lyrics: Vec<LyricLine>,
}

// Return a minimal Metadata object matching the frontend `Metadata` type.
#[tauri::command]
fn get_metadata(path: String) -> Result<Metadata, String> {
  debug!(%path, "get_metadata called");
  // use provided path, fallback to bundled resource when empty
  if path.is_empty() {
    warn!("empty path argument");
    return Err("path argument is empty".to_string());
  }
  let title = Path::new(&path)
    .file_stem()
    .and_then(|s| s.to_str())
    .map(|s| s.to_string())
    .ok_or_else(|| "failed to extract title from path".to_string())?;

  // Attempt to locate a corresponding .lrc file and parse lyrics from it.
  let mut lyrics: Vec<LyricLine> = Vec::new();

  // no longer using a helper closure here

  // Build candidate paths
  let mut candidates: Vec<String> = Vec::new();
  // If url looks like /res/name.mp3 or res/name.mp3, replace ext with .lrc
  if path.ends_with(".mp3") {
    if let Some(pos) = path.rfind('/') {
      let name = &path[pos + 1..];
      let lrc_name = name.trim_end_matches(".mp3").to_string() + ".lrc";
      candidates.push(format!("res/{}", lrc_name));
      candidates.push(lrc_name.clone());
      // relative up-one and up-two
      candidates.push(format!("../res/{}", lrc_name));
      candidates.push(format!("../../res/{}", lrc_name));
      // also try with leading slash removed from url replaced
      let no_lead = path.trim_start_matches('/').to_string();
      candidates.push(no_lead.trim_end_matches(".mp3").to_string() + ".lrc");
    } else {
      candidates.push(path.trim_end_matches(".mp3").to_string() + ".lrc");
    }
  }

  // If path argument looks like an .lrc, try it first
  if path.ends_with(".lrc") {
    candidates.insert(0, path.clone());
  }

  // Try to read any candidate; if a candidate exists but fails to read, return an error.
  let mut lrc_content: Option<String> = None;
  for c in &candidates {
    let pp = Path::new(c);
    if pp.exists() {
      match fs::read_to_string(pp) {
        Ok(s) => {
          info!(candidate = %c, "found lrc candidate and read successfully");
          lrc_content = Some(s);
          break;
        }
        Err(e) => {
          error!(candidate = %c, error = %e, "failed to read candidate");
          return Err(format!("failed to read {}: {}", c, e));
        }
      }
    }
  }

  if let Some(ref s) = lrc_content {
    lyrics = parse_lrc(s);
    info!(lines = lyrics.len(), "parsed lrc lines");
  }

  // If the caller explicitly passed an .lrc path and we couldn't find it, return error
  if path.ends_with(".lrc") && lrc_content.is_none() {
    return Err(format!(".lrc file not found for provided path: {}", path));
  }

  // If no lyrics found, fallback to small sample
  if lyrics.is_empty() {
    lyrics = vec![
      LyricLine { time: 0.0, text: title.to_string() },
      LyricLine { time: 1.0, text: "暂无歌词".to_string() },
    ];
  }

  Ok(Metadata { title, artist: "未知".to_string(), url: path, duration: 260.0, lyrics })
}

// Parse LRC content into a vector of LyricLine. Handles multiple timestamps per line.
#[instrument(level = "debug", skip(content))]
fn parse_lrc(content: &str) -> Vec<LyricLine> {
  let mut lyrics: Vec<LyricLine> = Vec::new();

  for raw_line in content.lines() {
    let line = raw_line.trim();
    if line.is_empty() {
      continue;
    }

    // collect timestamps at start like [mm:ss.xx][mm:ss.xx]Text
    let mut times: Vec<f64> = Vec::new();
    let mut rest = line;
    while rest.starts_with('[') {
      if let Some(idx) = rest.find(']') {
        let stamp = &rest[1..idx];
        // parse mm:ss.xx (allow seconds with decimals)
        if let Some(colon) = stamp.find(':') {
          let mm = &stamp[0..colon];
          let ss = &stamp[colon + 1..];
          let mmv: f64 = mm.parse::<f64>().unwrap_or(0.0);
          let ssv: f64 = ss.parse::<f64>().unwrap_or(0.0);
          let total = mmv * 60.0 + ssv;
          times.push(total);
        }
        // advance rest past this timestamp
        rest = &rest[idx + 1..];
      } else {
        break;
      }
    }

    let text = rest.trim().to_string();
    for t in times {
      lyrics.push(LyricLine { time: t, text: text.clone() });
    }
  }

  lyrics.sort_by(|a, b| a.time.partial_cmp(&b.time).unwrap_or(std::cmp::Ordering::Equal));
  lyrics
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tracing::info!("starting klok app");

  tauri::Builder::default()
    .plugin(tauri_plugin_opener::init())
    // restore saved window position when the page loads
    .on_page_load(|webview, _| {
      if let Ok(cwd) = env::current_dir() {
        let path: PathBuf = cwd.join("window_state.json");
        if path.exists() {
          if let Ok(s) = fs::read_to_string(&path) {
            if let Ok(ws) = serde_json::from_str::<WindowState>(&s) {
              info!("restoring window position: {:?}", ws);
              let _ = if cfg!(target_os = "macos") {
                webview.window().set_position(Position::Logical(LogicalPosition { x: ws.x as _, y: ws.y as _ }))
              } else {
                webview.window().set_position(Position::Physical(PhysicalPosition { x: ws.x as _, y: ws.y as _ }))
              };
            }
          }
        }
      }
    })
    // save the main window position on move/close
    .on_window_event(|window, event| {
      if window.label() != "main" {
        return;
      }
      match event {
        WindowEvent::Moved(_) | WindowEvent::CloseRequested { .. } => {
          if let Ok(cwd) = env::current_dir() {
            let _ = fs::create_dir_all(&cwd);
            if let Ok(pos) = window.outer_position() {
              let ws = if cfg!(target_os = "macos") {
                let pos = pos.to_logical::<f64>(window.scale_factor().unwrap_or(1.0));
                WindowState { x: pos.x as _, y: pos.y as _ }
              } else {
                WindowState { x: pos.x as _, y: pos.y as _ }
              };
              info!("saving window position: {:?}", ws);
              if let Ok(s) = serde_json::to_string(&ws) {
                let path = cwd.join("window_state.json");
                let _ = fs::write(path, s);
              }
            }
          }
        }
        _ => {}
      }
    })
    .invoke_handler(tauri::generate_handler![greet, get_metadata])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}

use std::path::Path;
use tauri::State;

use serde::Serialize;
use lofty::{Accessor, Probe, AudioFile, TaggedFileExt};

use crate::commands::with_extension;


#[derive(Serialize)]
struct LyricLine {
  time: f64,
  text: String,
}

#[derive(Serialize)]
pub struct Metadata {
  title: String,
  artist: String,
  url: String,
  duration: f64,
  lyrics: Vec<LyricLine>,
}

// Return a minimal Metadata object matching the frontend `Metadata` type.
#[tauri::command]
pub fn get_metadata(state: State<'_, crate::AppState>, path: String) -> Result<Metadata, String> {
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

  let lrc_path = with_extension(&path, ".lrc");

  // Build candidate paths
  let lrc_resolved_path = state.resolve(lrc_path);

  // Try to read any candidate; if a candidate exists but fails to read, return an error.
  let lrc_content = if let Some(lrc_resolved_path) = lrc_resolved_path {
    debug!(lrc_resolved_path = %lrc_resolved_path.display(), "resolved lrc path");
    match std::fs::read_to_string(&lrc_resolved_path) {
      Ok(s) => {
        Some(s)
      }
      Err(e) => {
        error!(lrc_resolved_path = %lrc_resolved_path.display(), error = %e, "failed to read candidate");
        return Err(format!("failed to read {}: {}", lrc_resolved_path.display(), e));
      }
    }
  } else {
    None
  };

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

  // Attempt to extract duration and tags from the audio file when possible.
  let mut duration_secs = lyrics.last().map(|l| l.time).unwrap_or(0.0) + 10.0;
  let mut artist = "未知".to_string();

  let mp3_path = state.resolve(&path);
  if let Some(mp3_path) = mp3_path {
    if let Some((d, a)) = get_duration_and_artist(&mp3_path) {
      duration_secs = d;
      artist = a;
    }
  }

  Ok(Metadata { title, artist, url: path, duration: duration_secs, lyrics })
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

// Probe audio candidates derived from `path` and return duration (secs) and artist when found.
fn get_duration_and_artist<P: AsRef<Path>>(path: P) -> Option<(f64, String)> {
  let path = path.as_ref();
  if path.exists() {
    match Probe::open(path) {
      Ok(probe) => match probe.read() {
        Ok(tagged) => {
          // duration from properties
          let props = tagged.properties();
          let d = props.duration().as_secs_f64();

          // try to get artist from primary tag (uses Accessor trait)
          let mut artist = "未知".to_string();
          if let Some(tag) = tagged.primary_tag() {
            if let Some(a) = tag.artist() {
              artist = a.to_string();
            }
          }

          Some((d, artist))
        }
        Err(e) => {
          // ignore and try next candidate
          error!(candidate = %path.display(), error = %e, "failed to read audio with lofty");
          return None;
        }
      },
      Err(e) => {
        error!(candidate = %path.display(), error = %e, "failed to open audio candidate");
        return None;
      }
    }
  } else {
    None
  }
}

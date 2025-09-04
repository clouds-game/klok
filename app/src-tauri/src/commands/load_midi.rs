use serde::Serialize;
use tauri::State;
use crate::AppState;
use std::collections::HashMap;

#[derive(Debug, Serialize)]
pub struct Note {
  pub note: i32,
  /// start time in seconds
  pub start: f64,
  /// duration in seconds
  pub duration: f64,
  pub velocity: f64,
  /// MIDI channel (0-15)
  pub channel: u8,
  pub confidence: Option<f64>,
}

/// Load a MIDI file (resolved via `AppState::resolve`) and return a list of notes.
#[tauri::command]
pub fn load_midi(state: State<'_, AppState>, path: String) -> Result<Vec<Note>, String> {
  if path.is_empty() {
    return Err("path argument is empty".to_string());
  }

  let resolved = state.resolve(&path).ok_or_else(|| format!("resource not found: {}", path))?;

  let bytes = std::fs::read(&resolved).map_err(|e| format!("failed to read {}: {}", resolved.display(), e))?;

  load_midi_from_memory(&bytes)
}

/// Parse MIDI content from any reader and return a list of notes.
pub fn load_midi_from_memory(content: &[u8]) -> Result<Vec<Note>, String> {
  // Parse MIDI using midly
  let smf = midly::Smf::parse(content).map_err(|e| format!("failed to parse midi: {}", e))?;

  // Only support metrical timing (ticks per quarter-note)
  let ticks_per_quarter = match smf.header.timing {
    midly::Timing::Metrical(t) => t.as_int() as u32,
    _ => return Err("SMPTE time formats are not supported".to_string()),
  };

  // Collect all events with absolute tick
  let mut events: Vec<(u64, midly::TrackEventKind)> = Vec::new();
  for track in &smf.tracks {
    let mut abs: u64 = 0;
    for ev in track {
      abs = abs.wrapping_add(ev.delta.as_int() as u64);
      events.push((abs, ev.kind.clone()));
    }
  }

  // Sort by absolute tick
  events.sort_by_key(|(t, _)| *t);

  // State while iterating events
  let mut last_tick: u64 = 0;
  let mut seconds: f64 = 0.0;
  let mut tempo_micro: u32 = 500_000; // default microseconds per quarter-note

  // ongoing notes keyed by (channel, note) -> (start_seconds, velocity)
  let mut ongoing: HashMap<(u8, u8), (f64, u8)> = HashMap::new();
  let mut notes: Vec<Note> = Vec::new();

  for (abs_tick, kind) in events {
    let delta_ticks = abs_tick.saturating_sub(last_tick);
    if delta_ticks != 0 {
      // convert ticks to seconds using current tempo
      seconds += (delta_ticks as f64) * (tempo_micro as f64) / (ticks_per_quarter as f64) / 1_000_000.0;
      last_tick = abs_tick;
    }

    match kind {
      midly::TrackEventKind::Meta(midly::MetaMessage::Tempo(t)) => {
        tempo_micro = t.into();
      }
      midly::TrackEventKind::Midi { channel, message } => {
        match message {
          midly::MidiMessage::NoteOn { key, vel } => {
            let k = key.as_int();
            let v = vel.as_int();
            let ch = channel.as_int();
            if v > 0 {
              ongoing.insert((ch, k), (seconds, v));
            } else {
              // velocity 0 note_on == note_off
              if let Some((start, vel0)) = ongoing.remove(&(ch, k)) {
                let dur = seconds - start;
                notes.push(Note { note: k as i32, start, duration: dur, velocity: vel0 as f64, channel: ch, confidence: None });
              }
            }
          }
          midly::MidiMessage::NoteOff { key, vel: _ } => {
            let k = key.as_int();
            let ch = channel.as_int();
            if let Some((start, vel0)) = ongoing.remove(&(ch, k)) {
              let dur = seconds - start;
              notes.push(Note { note: k as i32, start, duration: dur, velocity: vel0 as f64, channel: ch, confidence: None });
            }
          }
          _ => {}
        }
      }
      _ => {}
    }
  }

  // return notes sorted by start time
  notes.sort_by(|a, b| a.start.partial_cmp(&b.start).unwrap_or(std::cmp::Ordering::Equal));
  Ok(notes)
}

#[test]
pub fn test_midi() {
  let content = include_bytes!("../../../../res/我的一个道姑朋友_vocals.mid");

  let notes = load_midi_from_memory(content).expect("failed to parse midi from memory");
  println!("{:?}", notes.iter().take(10).collect::<Vec<_>>());
  assert_eq!(notes.len(), 18568);
}

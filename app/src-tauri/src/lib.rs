#[macro_use]
extern crate tracing;
use serde::{Serialize, Deserialize};
use tauri::{WindowEvent, Position, PhysicalPosition, LogicalPosition};
use std::env;
use std::path::PathBuf;

pub mod commands;
pub use commands::get_metadata::get_metadata;

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
  info!(%name, "greet called");
  format!("Hello, {}! You've been greeted from Rust!", name)
}

#[derive(Debug, Serialize, Deserialize)]
struct WindowState {
  x: f64,
  y: f64,
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
          if let Ok(s) = std::fs::read_to_string(&path) {
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
            let _ = std::fs::create_dir_all(&cwd);
            if let Ok(pos) = window.outer_position() {
              let ws = if cfg!(target_os = "macos") {
                let pos = pos.to_logical::<f64>(window.scale_factor().unwrap_or(1.0));
                WindowState { x: pos.x as _, y: pos.y as _ }
              } else {
                WindowState { x: pos.x as _, y: pos.y as _ }
              };
              debug!("saving window position: {:?}", ws);
              if let Ok(s) = serde_json::to_string(&ws) {
                let path = cwd.join("window_state.json");
                let _ = std::fs::write(path, s);
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

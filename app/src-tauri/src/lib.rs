// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

use serde::Serialize;
use std::path::Path;

#[derive(Serialize)]
struct LyricLine {
    time: f64,
    text: String,
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
fn get_metadata(path: Option<String>) -> Metadata {
    let url = path.unwrap_or_else(|| "/res/我的一个道姑朋友.mp3".to_string());
    let default_title = "我的一个道姑朋友".to_string();
    let title = Path::new(&url)
        .file_stem()
        .and_then(|s| s.to_str())
        .map(|s| s.to_string())
        .unwrap_or(default_title);

    // small sample of lyrics; frontend already has a richer set
    let lyrics = vec![
        LyricLine {
            time: 0.0,
            text: "我的一个道姑朋友".to_string(),
        },
        LyricLine {
            time: 1.74,
            text: "作词：陆菱纱".to_string(),
        },
        LyricLine {
            time: 27.12,
            text: "那年长街春意正浓".to_string(),
        },
    ];

    Metadata {
        title,
        artist: "未知".to_string(),
        url,
        duration: 260.0,
        lyrics,
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet, get_metadata])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

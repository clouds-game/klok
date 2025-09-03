// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
  // initialize tracing subscriber so logs from the library are captured
  let filter = tracing_subscriber::EnvFilter::try_from_default_env()
    .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info"));

  let _ = tracing_subscriber::fmt()
    .with_env_filter(filter)
    .with_target(false)
    .try_init();

  klok_app_lib::run()
}

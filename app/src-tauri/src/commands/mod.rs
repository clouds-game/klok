pub mod get_metadata;
pub mod load_audio;
pub mod load_midi;


const COMMON_EXT: [&str; 3] = [".mp3", ".m4a", ".flac"];

pub fn with_extension(filename: &str, extension: &str) -> String {
  if filename.ends_with(extension) {
    filename.to_string()
  } else {
    for ext in COMMON_EXT.iter() {
      if filename.ends_with(ext) {
        return format!("{}{}", &filename[..filename.len()-ext.len()], extension);
      }
    }
    format!("{}{}", filename, extension)
  }
}

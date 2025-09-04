
import os
import pathlib
import threading
from contextlib import contextmanager
from typing import Iterator, Union

TF_LOG_LEVEL_KEY = "TF_CPP_MIN_LOG_LEVEL"
TF_LOG_LEVEL_NO_WARNINGS_VALUE = "3"
DEFAULT_PRINT_INDENT = "  "

s_print_lock = threading.Lock()
OUTPUT_EMOJIS = {
    "MIDI": "💅",
    "MODEL_OUTPUT_NPZ": "💁‍♀️",
    "MIDI_SONIFICATION": "🎧",
    "NOTE_EVENTS": "🌸",
}


def generating_file_message(output_type: str) -> None:
  """Print a message that a file is being generated

  Args:
      output_type: string indicating which kind of file is being generated

  """
  print(f"\n\n{DEFAULT_PRINT_INDENT}Creating {output_type.replace('_', ' ').lower()}...")


def file_saved_confirmation(output_type: str, save_path: Union[pathlib.Path, str]) -> None:
  """Print a confirmation that the file was saved succesfully

  Args:
      output_type: The kind of file that is being generated.
      save_path: The path to output file.

  """
  emoji = OUTPUT_EMOJIS.get(output_type, "")
  print(f"{DEFAULT_PRINT_INDENT}{emoji} Saved to {save_path}")


def failed_to_save(output_type: str, save_path: Union[pathlib.Path, str]) -> None:
  """Print a failure to save message

  Args:
      output_type: The kind of file that is being generated.
      save_path: The path to output file.

  """
  print(f"\n🚨 Failed to save {output_type.replace('_', ' ').lower()} to {save_path} \n")


@contextmanager
def no_tf_warnings() -> Iterator[None]:
  """
  Supress tensorflow warnings in this context
  """
  tf_logging_level = os.environ.get(TF_LOG_LEVEL_KEY, TF_LOG_LEVEL_NO_WARNINGS_VALUE)
  os.environ[TF_LOG_LEVEL_KEY] = TF_LOG_LEVEL_NO_WARNINGS_VALUE
  try:
    yield
  finally:
    os.environ[TF_LOG_LEVEL_KEY] = tf_logging_level

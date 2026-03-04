"""Smart sound player: project-specific sounds first, fallback to global default."""
import sys, os, winsound

sound_name = sys.argv[1]  # e.g. start.wav
default_path = sys.argv[2]  # full path to fallback sound

local = os.path.join(".claude", "sounds", sound_name)
if os.path.isfile(local):
    winsound.PlaySound(os.path.abspath(local), winsound.SND_FILENAME)
else:
    winsound.PlaySound(default_path, winsound.SND_FILENAME)

"""Local diagnostic log shared with the panel: ~/Library/Logs/SoundSFXPaste.log, 'timestamp level [category] message',
rotated at ~5 MB to .1. Never write secrets, tokens or file contents; sound file NAMES only."""
import os, time, threading

_LOCK = threading.Lock()
MAX = 5 * 1024 * 1024


def path():
    return os.environ.get("SSFX_LOG") or os.path.join(os.path.expanduser("~"), "Library", "Logs", "SoundSFXPaste.log")


def write(level, cat, msg):
    p = path()
    try:
        with _LOCK:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if os.path.exists(p) and os.path.getsize(p) > MAX:
                os.replace(p, p + ".1")
            with open(p, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {level} [{cat}] {str(msg)[:400]}\n")
    except OSError:
        pass

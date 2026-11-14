"""SoundSFXPaste core: pure placement planning (no Resolve import, fully testable).
Frames: timeline absolute frames; intervals are [start, end) (end exclusive)."""
from dataclasses import dataclass
import re

AUDIO_EXT = {".wav", ".mp3", ".aif", ".aiff", ".aac", ".m4a", ".flac", ".ogg"}


def tc_to_frames(tc: str, fps: float) -> int:
    parts = [int(x) for x in re.split(r"[:;]", tc)]
    if len(parts) != 4:
        raise ValueError("bad timecode")
    h, m, s, f = parts
    return int((h * 3600 + m * 60 + s) * round(fps)) + f


def duration_frames(duration_tc: str, fps: float) -> int:
    n = tc_to_frames(duration_tc, fps)
    if n <= 0:
        raise ValueError("zero duration")
    return n


@dataclass
class Plan:
    ok: bool
    code: str = "OK"          # OK or ERR_* (UI localizes)
    track: int = 0
    start: int = 0
    end: int = 0              # exclusive
    detail: str = ""


def plan_placement(*, track, record_frame, length, track_count, locked, occupied):
    """Validate a single placement. `occupied`: list of (start,end) on that track."""
    if not isinstance(track, int) or track < 1 or track > track_count:
        return Plan(False, "ERR_TRACK_INVALID", track, detail=f"1..{track_count}")
    if track in locked:
        return Plan(False, "ERR_TRACK_LOCKED", track)
    if length <= 0:
        return Plan(False, "ERR_EMPTY_CLIP", track)
    start, end = record_frame, record_frame + length
    for s, e in occupied:
        if max(start, s) < min(end, e):
            return Plan(False, "ERR_TRACK_BUSY", track, start, end, f"{s}-{e}")
    return Plan(True, "OK", track, start, end)


def verify_result(plan: Plan, actual):
    """actual: list of (track,start,end) read back from timeline. Returns None if ok else code."""
    for t, s, e in actual:
        if t == plan.track and s == plan.start and e == plan.end:
            return None
    return "ERR_VERIFY_MISMATCH"


def plan_batch(requests, *, track_count, locked, occupied_by_track):
    """Plan many placements atomically: nothing executes if any fails.
    Placements in the same batch count as occupied for later ones."""
    occ = {t: list(v) for t, v in occupied_by_track.items()}
    plans = []
    for r in requests:
        p = plan_placement(track=r["track"], record_frame=r["record_frame"], length=r["length"],
                           track_count=track_count, locked=locked, occupied=occ.get(r["track"], []))
        plans.append(p)
        if p.ok:
            occ.setdefault(p.track, []).append((p.start, p.end))
    return plans, all(p.ok for p in plans)


# ---------------- v0.2: replace, markers, random fill (pure logic) ----------------
import json, random

TAG_PREFIX = "ssfx1:"


def encode_tags(tags):
    tags = [t.strip() for t in tags if t and t.strip()]
    return TAG_PREFIX + json.dumps({"tags": tags}, ensure_ascii=False) if tags else ""


def decode_tags(custom):
    if isinstance(custom, str) and custom.startswith(TAG_PREFIX):
        try:
            return [str(t) for t in json.loads(custom[len(TAG_PREFIX):]).get("tags", [])]
        except ValueError:
            return []
    return []


def pick_target_clip(candidates, playhead):
    """candidates: [{track,start,end,has_marker,locked}] -> best clip under playhead or None.
    Order (behaviour observed in the legacy panel, re-specified): unlocked only, clips with a marker first,
    then closest start to the playhead, then lowest track."""
    ok = [c for c in candidates if not c["locked"] and c["start"] <= playhead < c["end"]]
    if not ok:
        return None
    ok.sort(key=lambda c: (not c["has_marker"], abs(c["start"] - playhead), c["track"]))
    return ok[0]


def plan_replace(*, old, new_length, keep_new_length, locked, neighbours):
    """old: {track,start,end}; neighbours: [(s,e)] on the same track EXCLUDING the old clip.
    Default: the new sound is trimmed to the old clip's length (timing of the edit is preserved)."""
    if old["track"] in locked:
        return Plan(False, "ERR_TRACK_LOCKED", old["track"])
    old_len = old["end"] - old["start"]
    length = new_length if keep_new_length else min(new_length, old_len)
    if length <= 0:
        return Plan(False, "ERR_EMPTY_CLIP", old["track"])
    start, end = old["start"], old["start"] + length
    for s, e in neighbours:
        if max(start, s) < min(end, e):
            return Plan(False, "ERR_TRACK_BUSY", old["track"], start, end, f"{s}-{e}")
    return Plan(True, "OK", old["track"], start, end)


def plan_random_fill(markers, files, *, track, max_seconds=5.0, seed=None):
    """markers: [{frame(absolute)}]; files: [{path,duration}] -> requests; skips sounds longer than max_seconds."""
    pool = [f for f in files if f.get("duration") and 0 < f["duration"] <= max_seconds]
    if not pool:
        return []
    rng = random.Random(seed)
    return [{"path": rng.choice(pool)["path"], "track": track, "record_frame": m["frame"]} for m in markers]


def frames_to_tc(frame, fps):
    """Non-drop timecode (fps rounded). NOTE: only non-drop timelines are supported; callers refuse drop-frame."""
    r = int(round(fps)); f = frame % r; s = frame // r
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{f:02d}"

#!/usr/bin/env python3
"""Live probe: placement on 25/30 fps timelines and drop-frame refusal. Note: Resolve 21.2 refuses SetSetting for 29.97/drop-frame via the API, so the DF case stays at 24 fps here (DF is reported by deps() and refused by place(); live-unverified). Test project only; restores the original timeline."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "bridge"))
import resolve_adapter as ra
WAV = os.path.realpath(os.path.join(HERE, "..", "demo-audio", "Riser Short.wav"))  # 2.5 s
c0 = ra.Ctx()
if c0.project.GetName() != "SoundSFXPaste_TEST": sys.exit("REFUSED: not the test project")
proj, orig = c0.project, c0.timeline; out = []
def case(name, fps, drop):
    tl = proj.GetMediaPool().CreateEmptyTimeline(f"probe_{name}")
    if not tl: out.append({"case": name, "error": "create failed"}); return
    tl.SetSetting("useCustomSettings", "1"); tl.SetSetting("timelineFrameRate", str(fps))
    tl.SetSetting("timelineDropFrameTimecode", "1" if drop else "0")
    proj.SetCurrentTimeline(tl); c = ra.Ctx()
    r = {"case": name, "fps": c.fps, "drop": c.drop}
    while tl.GetTrackCount("audio") < 2: tl.AddTrack("audio")
    try:
        res = c.place({"path": WAV, "track": 1, "record_frame": c.start + 100, "project": c.project.GetName(), "timeline_id": tl.GetUniqueId()})
        r.update(res)
        if res.get("ok"): r["expected_frames"] = int(2.5 * c.fps)
    except RuntimeError as e: r["refused"] = str(e)
    out.append(r)
for n, f, d in (("25", 25, False), ("30", 30, False), ("2997df", 29.97, True)): case(n, f, d)
proj.SetCurrentTimeline(orig)
if '--keep' not in sys.argv:
    mp = proj.GetMediaPool(); mp.DeleteTimelines([t for t in (proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)) if t.GetName() in ('probe_25', 'probe_30', 'probe_2997df')])
print(json.dumps(out, indent=1))

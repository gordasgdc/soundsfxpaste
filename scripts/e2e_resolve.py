#!/usr/bin/env python3
"""End-to-end probe of the bridge against a LIVE Resolve. Refuses to run unless the open project is the dedicated test project.
Writes only to that project and cleans up after itself. Usage: python3 scripts/e2e_resolve.py <library_root_with_short_wavs> [report.json]"""
import os, sys, json, subprocess, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "bridge"))
import resolve_adapter as ra, core

LIB = os.path.realpath(sys.argv[1]); REPORT = sys.argv[2] if len(sys.argv) > 2 else None
TOKEN = "e2e-token"; res = []

def check(name, cond, extra=""):
    res.append({"test": name, "pass": bool(cond), "info": extra}); print(("PASS " if cond else "FAIL ") + name, extra)

c = ra.Ctx()
if c.project.GetName() != "SoundSFXPaste_TEST": sys.exit("REFUSED: open project is not SoundSFXPaste_TEST")
env = dict(os.environ, SSFX_TOKEN=TOKEN)
srv = subprocess.Popen([sys.executable, os.path.join(HERE, "..", "bridge", "server.py"), "0"], env=env, stdout=subprocess.PIPE, text=True)
port = json.loads(srv.stdout.readline())["port"]

def call(path, body=None):
    r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="POST" if body is not None else "GET",
                               headers={"X-SSFX-Token": TOKEN, "Content-Type": "application/json"}, data=json.dumps(body).encode() if body is not None else None)
    try: return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e: return json.load(e)

try:
    call("/library/set", {"roots": [LIB]})
    files = [f for f in call("/library/list", {"root": LIB})["files"] if (f["duration"] or 99) <= 5][:6]
    check("library lists short files with real header info", len(files) >= 2 and all(f["sr"] for f in files), f"{len(files)} files")
    st = call("/status"); ident = {"project": st["project"], "timeline_id": st["timeline_id"]}
    tl, S = c.timeline, c.start
    while tl.GetTrackCount("audio") < 7: tl.AddTrack("audio")
    tl.DeleteMarkersByColor("All")
    for r_ in (3000, 3100, 3200): tl.AddMarker(r_, "Blue", f"m{r_}", "", 1, "")
    ms = call("/markers")["markers"]; check("markers listed relative to timeline start", [m["frame"] for m in ms] == [3000, 3100, 3200])
    o = dict(ident, op="rename", frame=3000, name="hit"); check("rename marker", call("/markers/op", o)["ok"] and call("/markers")["markers"][0]["name"] == "hit")
    call("/markers/op", dict(ident, op="tags", frame=3100, tags=["whoosh", "deep"])); check("tags stored in customData", call("/markers")["markers"][1]["tags"] == ["whoosh", "deep"])
    check("trash_all needs confirm", call("/markers/op", dict(ident, op="trash_all"))["code"] == "ERR_CONFIRM_REQUIRED" and len(tl.GetMarkers()) == 3)
    check("identity mismatch refused", call("/markers/op", dict(op="delete", frame=3200, project="x", timeline_id="y"))["code"] == "ERR_IDENTITY_MISMATCH" and len(tl.GetMarkers()) == 3)
    # random fill (atomic batch) on A2 at marker positions
    pl = core.plan_random_fill([{"frame": S + m["frame"]} for m in ms], files, track=2, seed=7)
    b = call("/place_batch", dict(ident, items=pl)); check("random fill executes all", b["ok"] and b["executed"] == 3, str(b.get("executed")))
    got = [(i.GetStart() - S) for i in tl.GetItemListInTrack("audio", 2)]; check("clips landed at marker frames", sorted(got) == [3000, 3100, 3200], str(got))
    b2 = call("/place_batch", dict(ident, items=pl)); n_after = len(tl.GetItemListInTrack("audio", 2))
    check("repeat batch refused whole, nothing written", (not b2["ok"]) and b2["executed"] == 0 and n_after == 3)
    # locked track through the bridge
    tl.SetTrackLock("audio", 3, True); before = len(tl.GetItemListInTrack("audio", 3) or [])
    r1 = call("/place", dict(ident, path=files[0]["path"], track=3, record_frame=S + 5000)); tl.SetTrackLock("audio", 3, False)
    check("locked track refused, zero change", r1["code"] == "ERR_TRACK_LOCKED" and len(tl.GetItemListInTrack("audio", 3) or []) == before)
    # replace under playhead
    tl.SetCurrentTimecode(core.frames_to_tc(S + 3100 + 2, c.fps)); other = files[1]["path"] if files[1]["path"] != pl[1]["path"] else files[0]["path"]
    d = call("/replace", dict(ident, path=other, mode="playhead", dry_run=True)); check("replace dry-run plans target", d["ok"] and d["results"][0]["start"] == 3100, str(d["results"]))
    e = call("/replace", dict(ident, path=other, mode="playhead")); items = {i.GetStart() - S: i for i in tl.GetItemListInTrack("audio", 2)}
    name_other = os.path.basename(other); check("replace executed same start, verified", e["ok"] and 3100 in items and items[3100].GetName() == name_other, str(e.get("code")))
    # replace refused when no clip under playhead
    tl.SetCurrentTimecode(core.frames_to_tc(S + 9000, c.fps)); check("replace with no target refused", call("/replace", dict(ident, path=other, mode="playhead"))["code"] == "ERR_NO_TARGET")
    # playhead move
    check("playhead move", call("/playhead", dict(ident, frame=3200))["ok"] and c.playhead() == S + 3200)
    # bad track + add track
    check("invalid track refused", call("/place", dict(ident, path=files[0]["path"], track=40, record_frame=S + 6000))["code"] == "ERR_TRACK_INVALID")
    n0 = tl.GetTrackCount("audio"); check("add track", call("/track/add", ident)["ok"] and tl.GetTrackCount("audio") == n0 + 1)
    # file outside library
    check("outside library refused", call("/place", dict(ident, path="/etc/hosts", track=2))["code"] == "ERR_OUTSIDE_LIBRARY")
finally:
    try:
        for t in range(1, tl.GetTrackCount("audio") + 1):
            its = [i for i in (tl.GetItemListInTrack("audio", t) or []) if i.GetStart() - S >= 2900]
            if its: tl.DeleteClips(its)
        tl.DeleteMarkersByColor("All")
    finally:
        srv.terminate()
if REPORT: json.dump(res, open(REPORT, "w"), indent=1)
sys.exit(0 if all(r["pass"] for r in res) else 1)

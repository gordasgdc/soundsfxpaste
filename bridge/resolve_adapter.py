"""Thin Resolve adapter (official DaVinciResolveScript API). All decisions live in core.py.
Facts measured on Resolve Studio 21.2 / macOS (see evidence/): marker frames are RELATIVE to the timeline start,
clip positions are ABSOLUTE; AppendToTimeline.endFrame is exclusive; collisions and bad track indexes are silent."""
import os, sys, platform
import core

BIN = "SoundSFXPaste Imports"


def connect():
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        if platform.system() == "Darwin":
            sys.path.append("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules")
        else:
            sys.path.append(os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
                            "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules"))
        import DaVinciResolveScript as dvr
    return dvr.scriptapp("Resolve")


def deps():
    """Plain checks for the Dependencies panel. Never raises. Each item: id, ok, info."""
    out = [{"id": "python", "ok": True, "info": sys.version.split()[0] + " · " + sys.executable}]
    try:
        import DaVinciResolveScript as dvr  # noqa
        mod_ok = True
    except ImportError:
        mod_ok = False
        try:
            base = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
            if platform.system() != "Darwin":
                base = os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules")
            sys.path.append(base); import DaVinciResolveScript as dvr; mod_ok = True  # noqa
        except ImportError:
            pass
    out.append({"id": "module", "ok": mod_ok, "info": ""})
    if not mod_ok:
        return out
    try: r = dvr.scriptapp("Resolve")
    except Exception: r = None
    out.append({"id": "resolve", "ok": bool(r), "info": (r.GetVersionString() if r else "")})
    if not r:
        return out
    p = r.GetProjectManager().GetCurrentProject()
    out.append({"id": "project", "ok": bool(p), "info": p.GetName() if p else ""})
    t = p.GetCurrentTimeline() if p else None
    out.append({"id": "timeline", "ok": bool(t), "info": t.GetName() if t else ""})
    if t:
        fps = t.GetSetting("timelineFrameRate"); drop = str(t.GetSetting("timelineDropFrameTimecode")) == "1"
        out.append({"id": "tc", "ok": not drop, "info": f"{fps} fps" + (" DF" if drop else "")})
    return out


class Ctx:
    def __init__(self):
        self.resolve = connect()
        if not self.resolve: raise RuntimeError("ERR_NO_RESOLVE")
        self.project = self.resolve.GetProjectManager().GetCurrentProject()
        if not self.project: raise RuntimeError("ERR_NO_PROJECT")
        self.timeline = self.project.GetCurrentTimeline()
        if not self.timeline: raise RuntimeError("ERR_NO_TIMELINE")
        self.fps = float(self.timeline.GetSetting("timelineFrameRate") or 24)
        self.start = self.timeline.GetStartFrame()
        self.drop = str(self.timeline.GetSetting("timelineDropFrameTimecode")) == "1"

    # ---- identity / state ----
    def identity(self):
        return {"project": self.project.GetName(), "timeline": self.timeline.GetName(),
                "timeline_id": self.timeline.GetUniqueId()}

    def guard(self, req):
        """Refuse to write unless the user's expected project/timeline is still the active one."""
        if (req.get("project"), req.get("timeline_id")) != (self.project.GetName(), self.timeline.GetUniqueId()):
            raise RuntimeError("ERR_IDENTITY_MISMATCH")

    def _require_nondrop(self):
        if self.drop: raise RuntimeError("ERR_DROP_FRAME_UNSUPPORTED")

    def tracks(self):
        n = self.timeline.GetTrackCount("audio")
        return [{"index": i, "name": self.timeline.GetTrackName("audio", i),
                 "locked": bool(self.timeline.GetIsTrackLocked("audio", i))} for i in range(1, n + 1)]

    def playhead(self):
        return core.tc_to_frames(self.timeline.GetCurrentTimecode(), self.fps)

    def occupied(self, track):
        return [(i.GetStart(), i.GetEnd()) for i in (self.timeline.GetItemListInTrack("audio", track) or [])]

    def status(self):
        d = self.identity()
        d.update(drop_frame=self.drop, fps=self.fps, start=self.start, tracks=self.tracks(),
                 playhead=self.playhead(), playhead_tc=self.timeline.GetCurrentTimecode())
        return d

    def _rel(self, detail):
        """'a-b' absolute frames -> relative to timeline start (what the user sees)."""
        try:
            a, b = detail.split("-"); return f"{int(a) - self.start}-{int(b) - self.start}"
        except ValueError:
            return detail

    def add_track(self, req):
        self.guard(req); ok = bool(self.timeline.AddTrack("audio"))
        return {"ok": ok, "code": "OK" if ok else "ERR_RESOLVE_REFUSED", "tracks": self.timeline.GetTrackCount("audio")}

    def set_playhead(self, req):
        self.guard(req); self._require_nondrop()
        ok = bool(self.timeline.SetCurrentTimecode(core.frames_to_tc(self.start + int(req["frame"]), self.fps)))
        return {"ok": ok, "code": "OK" if ok else "ERR_RESOLVE_REFUSED"}

    # ---- media pool ----
    def _bin(self):
        mp = self.project.GetMediaPool(); root = mp.GetRootFolder()
        for f in root.GetSubFolderList():
            if f.GetName() == BIN: return mp, f
        return mp, mp.AddSubFolder(root, BIN)

    def _import(self, path):
        mp, b = self._bin()
        for c in b.GetClipList():
            if c.GetClipProperty("File Path") == path: return mp, c
        mp.SetCurrentFolder(b)
        items = mp.ImportMedia([path])
        if not items: raise RuntimeError("ERR_IMPORT_FAILED")
        return mp, items[0]

    def length_for(self, clip, in_sec, out_sec):
        """Returns (a, b, length): a/b are source frames at the CLIP's own fps (what AppendToTimeline expects),
        length is the resulting length in TIMELINE frames. Measured: for video Duration is a timecode at the clip fps; for audio-only clips at the timeline fps."""
        try: cf = float(clip.GetClipProperty("FPS") or 0) or self.fps
        except (TypeError, ValueError): cf = self.fps
        if in_sec is not None and out_sec is not None:
            a, b = int(round(in_sec * cf)), int(round(out_sec * cf))
        else:
            # Audio-only clips: "FPS" is the source rate (24) but "Duration" is a timecode at the TIMELINE fps (measured on 30 fps).
            df = self.fps if clip.GetClipProperty("Type") == "Audio" else cf
            a, b = 0, int(round(core.duration_frames(clip.GetClipProperty("Duration"), df) / df * cf))
        return a, b, max(1, int((b - a) / cf * self.fps + 1e-6))

    # ---- single placement ----
    def place(self, req, dry_run=False, _created=None):
        self.guard(req); self._require_nondrop()
        mp, clip = self._import(req["path"])  # import is needed to know the duration (also for dry runs)
        a, b, length = self.length_for(clip, req.get("in_sec"), req.get("out_sec"))
        rec = self.playhead() if req.get("record_frame") in (None, "playhead") else int(req["record_frame"])
        tr = int(req["track"]); n = self.timeline.GetTrackCount("audio")
        locked = {t["index"] for t in self.tracks() if t["locked"]}
        plan = core.plan_placement(track=tr, record_frame=rec, length=length, track_count=n, locked=locked,
                                   occupied=self.occupied(tr) if 1 <= tr <= n else [])
        out = {"ok": plan.ok, "code": plan.code, "track": plan.track,
               "start": (plan.start if plan.ok else rec) - self.start, "frames": length, "detail": self._rel(plan.detail)}
        if not plan.ok or dry_run: return out
        res = mp.AppendToTimeline([{"mediaPoolItem": clip, "mediaType": 2, "trackIndex": tr,
                                    "recordFrame": rec, "startFrame": a, "endFrame": b}])
        if not res:
            out.update(ok=False, code="ERR_RESOLVE_REFUSED"); return out
        if _created is not None: _created.extend(res)
        actual = [(tr, i.GetStart(), i.GetEnd()) for i in (self.timeline.GetItemListInTrack("audio", tr) or [])]
        bad = core.verify_result(plan, actual)
        if bad:
            self.timeline.DeleteClips(res)  # never leave a clip that differs from the plan
            if _created is not None: [_created.remove(x) for x in res if x in _created]
            out.update(ok=False, code=bad)
        return out

    def batch(self, req):
        """Plan everything first; execute only if every plan is ok; on any failure remove what this batch added."""
        self.guard(req); items = [dict(i, project=req.get("project"), timeline_id=req.get("timeline_id")) for i in req.get("items", [])]
        plans = [self.place(i, dry_run=True) for i in items]
        seen = {}
        for p in plans:
            if p["ok"]:
                for s_, e_ in seen.get(p["track"], []):
                    if max(p["start"], s_) < min(p["start"] + p["frames"], e_): p.update(ok=False, code="ERR_TRACK_BUSY")
                seen.setdefault(p["track"], []).append((p["start"], p["start"] + p["frames"]))
        if not all(p["ok"] for p in plans) or req.get("dry_run"):
            return {"ok": all(p["ok"] for p in plans), "executed": 0, "plans": plans}
        created, results = [], []
        for i in items:
            r = self.place(i, _created=created); results.append(r)
            if not r["ok"]:
                if created: self.timeline.DeleteClips(created)
                return {"ok": False, "executed": 0, "rolled_back": len(created), "plans": plans, "results": results}
        return {"ok": True, "executed": len(results), "plans": plans, "results": results}

    # ---- markers ----
    def markers(self):
        return [{"frame": int(fr), "name": m.get("name", ""), "color": m.get("color", "Blue"), "note": m.get("note", ""),
                 "duration": m.get("duration", 1), "tags": core.decode_tags(m.get("customData", ""))}
                for fr, m in sorted(self.timeline.GetMarkers().items())]

    def marker_op(self, req):
        self.guard(req); tl = self.timeline; op = req["op"]; cur = tl.GetMarkers(); fr = int(req.get("frame", -1))
        ok_ = lambda ok: {"ok": bool(ok), "code": "OK" if ok else "ERR_RESOLVE_REFUSED"}
        if op == "trash_all":
            if req.get("confirm") is not True: return {"ok": False, "code": "ERR_CONFIRM_REQUIRED"}
            n = len(cur); r = ok_(tl.DeleteMarkersByColor("All")); r["deleted"] = n; return r
        if fr not in cur: return {"ok": False, "code": "ERR_MARKER_GONE"}
        m = cur[fr]
        if op == "delete": return ok_(tl.DeleteMarkerAtFrame(fr))
        if op == "tags": return ok_(tl.UpdateMarkerCustomData(fr, core.encode_tags(req.get("tags", []))))
        if op == "rename":  # the API has no rename: delete + re-add with identical properties, restore on failure
            if not tl.DeleteMarkerAtFrame(fr): return {"ok": False, "code": "ERR_RESOLVE_REFUSED"}
            args = (fr, m.get("color", "Blue"), req["name"], m.get("note", ""), m.get("duration", 1), m.get("customData", ""))
            if tl.AddMarker(*args): return {"ok": True, "code": "OK"}
            tl.AddMarker(args[0], args[1], m.get("name", ""), *args[3:])
            return {"ok": False, "code": "ERR_RESOLVE_REFUSED"}
        return {"ok": False, "code": "ERR_INTERNAL"}

    # ---- replace ----
    def _clip_info(self, it, track):
        return {"track": track, "start": it.GetStart(), "end": it.GetEnd(), "has_marker": bool(it.GetMarkers()), "id": it.GetUniqueId()}

    def selected(self):
        ids = {i.GetUniqueId() for i in (self.timeline.GetSelectedClips() or [])}
        return [(it, t) for t in range(1, self.timeline.GetTrackCount("audio") + 1)
                for it in (self.timeline.GetItemListInTrack("audio", t) or []) if it.GetUniqueId() in ids]

    def under_playhead(self):
        ph = self.playhead(); locked = {t["index"] for t in self.tracks() if t["locked"]}
        cands = [(it, t, dict(self._clip_info(it, t), locked=t in locked))
                 for t in range(1, self.timeline.GetTrackCount("audio") + 1)
                 for it in (self.timeline.GetItemListInTrack("audio", t) or [])]
        best = core.pick_target_clip([c[2] for c in cands], ph)
        return [(c[0], c[1]) for c in cands if best and c[2]["id"] == best["id"]]

    def replace(self, req, dry_run=False):
        self.guard(req); self._require_nondrop()
        targets = self.selected() if req.get("mode") == "selected" else self.under_playhead()
        if not targets: return {"ok": False, "code": "ERR_NO_TARGET", "results": []}
        mp, clip = self._import(req["path"]); _, _, new_len = self.length_for(clip, None, None)
        locked = {t["index"] for t in self.tracks() if t["locked"]}; plans = []
        for it, tr in targets:
            nb = [(i.GetStart(), i.GetEnd()) for i in (self.timeline.GetItemListInTrack("audio", tr) or []) if i.GetUniqueId() != it.GetUniqueId()]
            plans.append((it, tr, core.plan_replace(old={"track": tr, "start": it.GetStart(), "end": it.GetEnd()}, new_length=new_len,
                                                    keep_new_length=bool(req.get("keep_length")), locked=locked, neighbours=nb)))
        view = [{"ok": p.ok, "code": p.code, "track": tr, "start": it.GetStart() - self.start, "frames": (p.end - p.start) if p.ok else 0,
                 "old": it.GetName(), "detail": self._rel(p.detail)} for it, tr, p in plans]
        good = all(v["ok"] for v in view)
        if not good or dry_run:
            return {"ok": good, "code": "OK" if good else next(v["code"] for v in view if not v["ok"]), "results": view}
        done = 0
        for (it, tr, p), v in zip(plans, view):
            snap = {"mpi": it.GetMediaPoolItem(), "start": it.GetStart(), "ss": it.GetSourceStartFrame(), "se": it.GetSourceEndFrame() + 1}
            deleted = bool(self.timeline.DeleteClips([it]))
            res = mp.AppendToTimeline([{"mediaPoolItem": clip, "mediaType": 2, "trackIndex": tr, "recordFrame": p.start,
                                        "startFrame": 0, "endFrame": p.end - p.start}]) if deleted else None
            got = [(tr, i.GetStart(), i.GetEnd()) for i in (self.timeline.GetItemListInTrack("audio", tr) or [])]
            if deleted and res and core.verify_result(p, got) is None:
                done += 1; v["done"] = True; continue
            if res: self.timeline.DeleteClips(list(res))
            restored = False
            if deleted and snap["mpi"]:
                restored = bool(mp.AppendToTimeline([{"mediaPoolItem": snap["mpi"], "mediaType": 2, "trackIndex": tr,
                                                      "recordFrame": snap["start"], "startFrame": snap["ss"], "endFrame": snap["se"]}]))
            v.update(ok=False, code="ERR_VERIFY_MISMATCH" if deleted else "ERR_RESOLVE_REFUSED", restored=restored)
            return {"ok": False, "code": v["code"], "results": view, "executed": done}
        return {"ok": True, "code": "OK", "results": view, "executed": done}

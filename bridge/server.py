"""Local bridge: 127.0.0.1 only, random port, per-session token, no CORS, library-root-confined file access."""
import os, sys, json, mimetypes, secrets, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import core, log
from audio_meta import header_info

TOKEN = os.environ.get("SSFX_TOKEN") or secrets.token_urlsafe(24)
ROOTS = []  # absolute real paths of user-chosen library folders
MAX_FILES = 5000


def within_roots(path):
    rp = os.path.realpath(path)
    return any(rp == r or rp.startswith(r + os.sep) for r in ROOTS) and os.path.isfile(rp)


def list_audio(root):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if not d.startswith("."))
        for f in sorted(fn):
            if os.path.splitext(f)[1].lower() in core.AUDIO_EXT and not f.startswith("."):
                p = os.path.join(dp, f)
                try: st = os.stat(p)
                except OSError: continue
                h = header_info(p)
                out.append({"path": p, "name": f, "rel": os.path.relpath(p, root), "size": st.st_size, "mtime": int(st.st_mtime),
                            "sr": h["sr"], "ch": h["ch"], "bits": h["bits"], "codec": h["codec"], "duration": h["duration"]})
                if len(out) >= MAX_FILES: return out
    return out


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def _auth(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        tok = self.headers.get("X-SSFX-Token") or (q.get("t") or [""])[0]
        host_ok = (self.headers.get("Host") or "").split(":")[0] in ("127.0.0.1", "localhost")
        if not host_ok or not secrets.compare_digest(tok, TOKEN):
            self._send(401, {"ok": False, "code": "ERR_UNAUTHORIZED"}); return False
        return True

    def _audio(self, p):
        size = os.path.getsize(p); start, end, code = 0, size - 1, 200
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            try:
                start = int(a) if a else max(0, size - int(b)); end = int(b) if (a and b) else size - 1
                end = min(end, size - 1); code = 206
            except ValueError:
                start, end, code = 0, size - 1, 200
        self.send_response(code)
        self.send_header("Content-Type", mimetypes.guess_type(p)[0] or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Length", str(end - start + 1))
        if code == 206: self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with open(p, "rb") as f:
            f.seek(start); left = end - start + 1
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk: break
                self.wfile.write(chunk); left -= len(chunk)

    def do_GET(self):
        if not self._auth(): return
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/audio":
                p = (q.get("path") or [""])[0]
                if not within_roots(p): return self._send(403, {"ok": False, "code": "ERR_OUTSIDE_LIBRARY"})
                return self._audio(os.path.realpath(p))
            import resolve_adapter as ra
            if u.path == "/deps": return self._send(200, {"ok": True, "items": ra.deps()})
            c = ra.Ctx()
            if u.path == "/status": return self._send(200, {"ok": True, **c.status()})
            if u.path == "/markers": return self._send(200, {"ok": True, "markers": c.markers(), **c.identity()})
            if u.path == "/selection":
                return self._send(200, {"ok": True, "clips": [{"track": t, "name": i.GetName(), "start": i.GetStart() - c.start,
                                                              "frames": i.GetDuration()} for i, t in c.selected()]})
            self._send(404, {"ok": False})
        except RuntimeError as e: self._send(200, {"ok": False, "code": str(e)})

    def do_POST(self):
        if not self._auth(): return
        n = int(self.headers.get("Content-Length") or 0)
        if n > 1 << 20: return self._send(413, {"ok": False})
        req = json.loads(self.rfile.read(n) or b"{}"); u = urllib.parse.urlparse(self.path).path
        try:
            if u == "/library/set":
                ROOTS[:] = [os.path.realpath(r) for r in req.get("roots", []) if os.path.isdir(r)]
                return self._send(200, {"ok": True, "roots": ROOTS})
            if u == "/library/list":
                r = os.path.realpath(req.get("root", ""))
                if r not in ROOTS: return self._send(403, {"ok": False, "code": "ERR_OUTSIDE_LIBRARY"})
                return self._send(200, {"ok": True, "files": list_audio(r)})
            paths = [req.get("path")] + [i.get("path") for i in req.get("items", [])]
            if any(p is not None and not within_roots(p) for p in paths):
                return self._send(403, {"ok": False, "code": "ERR_OUTSIDE_LIBRARY"})
            import resolve_adapter as ra
            c = ra.Ctx()
            def done(name, res):
                log.write("INFO" if res.get("ok") else "WARN", name, f"ok={res.get('ok')} code={res.get('code','')} track={res.get('track','')} start={res.get('start','')} file={os.path.basename(str(req.get('path') or ''))}")
                return self._send(200, res)
            if u == "/place": return done("place", c.place(req))
            if u == "/plan": return self._send(200, c.place(req, dry_run=True))
            if u == "/place_batch": return done("batch", c.batch(req))
            if u == "/replace": return done("replace", c.replace(req, dry_run=bool(req.get("dry_run"))))
            if u == "/markers/op": return done("marker", c.marker_op(req))
            if u == "/playhead": return self._send(200, c.set_playhead(req))
            if u == "/track/add": return self._send(200, c.add_track(req))
            self._send(404, {"ok": False})
        except RuntimeError as e: log.write("WARN", "bridge", f"{u} {e}"); self._send(200, {"ok": False, "code": str(e)})
        except Exception as e: log.write("ERROR", "bridge", f"{u} {type(e).__name__}"); self._send(500, {"ok": False, "code": "ERR_INTERNAL", "detail": type(e).__name__})


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 0), H)
    log.write("INFO", "bridge", f"started port={srv.server_address[1]} python={sys.version.split()[0]}")
    print(json.dumps({"port": srv.server_address[1]}), flush=True)
    srv.serve_forever()

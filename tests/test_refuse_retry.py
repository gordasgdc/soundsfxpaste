"""Local test (not shipped): a declined placement must be reported with ERR_RESOLVE_REFUSED and a manual retry must succeed.
Uses a fake resolve_adapter (no Resolve needed) behind the REAL bridge server, so it exercises routing, auth, logging."""
import os, sys, json, threading, types, tempfile, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "bridge"))
os.environ["SSFX_TOKEN"] = "t"; LOG = tempfile.mktemp(suffix=".log"); os.environ["SSFX_LOG"] = LOG
calls = []
class Ctx:
    def place(self, req, dry_run=False):
        calls.append(req)
        return {"ok": False, "code": "ERR_RESOLVE_REFUSED", "track": req["track"], "start": ""} if len(calls) == 1 else {"ok": True, "code": "OK", "track": req["track"], "start": 100, "frames": 3}
fake = types.ModuleType("resolve_adapter"); fake.Ctx = Ctx; sys.modules["resolve_adapter"] = fake
import server
from http.server import ThreadingHTTPServer
srv = ThreadingHTTPServer(("127.0.0.1", 0), server.H); threading.Thread(target=srv.serve_forever, daemon=True).start()
lib = tempfile.mkdtemp(); wav = os.path.join(lib, "a.wav"); open(wav, "wb").write(b"RIFF")
def post(path, body):
    r = urllib.request.Request(f"http://127.0.0.1:{srv.server_address[1]}{path}", data=json.dumps(body).encode(), headers={"X-SSFX-Token": "t", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r))
post("/library/set", {"roots": [lib]})
req = {"path": wav, "track": 3, "record_frame": 100, "project": "p", "timeline_id": "x"}
a = post("/place", req); b = post("/place", req)
assert a["ok"] is False and a["code"] == "ERR_RESOLVE_REFUSED", a
assert b["ok"] is True and b["track"] == 3, b            # same request (same sound, track, position) succeeds on manual retry
assert calls[0] == calls[1] == req
log = open(LOG).read(); assert "code=ERR_RESOLVE_REFUSED" in log and "track=3" in log, log
# the shipped bridge must not contain any simulation switch
src = open(os.path.join(HERE, "..", "bridge", "server.py")).read(); assert "SIM_REFUSE" not in src and "ALLOW_TEST" not in src
# messages present in all three languages
i18n = open(os.path.join(HERE, "..", "app", "i18n.js"), encoding="utf8").read()
for needle in ("Resolve did not place the sound.", "Resolve nu a plasat sunetul. Verifică pista și poziția din panou, apoi încearcă din nou.", "Resolve no colocó el sonido."):
    assert needle in i18n, needle
print("OK refuse + retry + log code + no sim switch in bridge + RO/EN/ES messages")

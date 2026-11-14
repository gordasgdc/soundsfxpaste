import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bridge"))
from core import *

class T(unittest.TestCase):
    def test_tc(self):
        self.assertEqual(tc_to_frames("01:00:00:00", 24), 86400)
        self.assertEqual(duration_frames("00:00:01:00", 24), 24)
    def kw(self, **o):
        d = dict(track=3, record_frame=100, length=24, track_count=6, locked=set(), occupied=[])
        d.update(o); return d
    def test_ok(self):
        p = plan_placement(**self.kw()); self.assertTrue(p.ok); self.assertEqual((p.start, p.end), (100, 124))
    def test_invalid_track(self):  # probe1: API silently clamped track 9 -> 1
        for t in (0, 9, -1): self.assertEqual(plan_placement(**self.kw(track=t)).code, "ERR_TRACK_INVALID")
    def test_locked(self): self.assertEqual(plan_placement(**self.kw(locked={3})).code, "ERR_TRACK_LOCKED")
    def test_collision(self):  # probe1: API silently trimmed/dropped
        self.assertEqual(plan_placement(**self.kw(occupied=[(110, 130)])).code, "ERR_TRACK_BUSY")
    def test_adjacent_ok(self):  # [start,end) exclusive
        self.assertTrue(plan_placement(**self.kw(occupied=[(124, 150), (76, 100)])).ok)
    def test_batch_atomic_self_collision(self):
        reqs = [dict(track=1, record_frame=0, length=50), dict(track=1, record_frame=40, length=50)]
        plans, ok = plan_batch(reqs, track_count=2, locked=set(), occupied_by_track={})
        self.assertFalse(ok); self.assertTrue(plans[0].ok); self.assertEqual(plans[1].code, "ERR_TRACK_BUSY")
    def test_verify(self):
        p = Plan(True, "OK", 3, 100, 124)
        self.assertIsNone(verify_result(p, [(3, 100, 124)]))
        self.assertEqual(verify_result(p, [(1, 100, 124)]), "ERR_VERIFY_MISMATCH")
        self.assertEqual(verify_result(p, [(3, 100, 114)]), "ERR_VERIFY_MISMATCH")

class T2(unittest.TestCase):
    def test_tags_roundtrip(self):
        self.assertEqual(decode_tags(encode_tags(["whoosh", " deep ", ""])), ["whoosh", "deep"])
        self.assertEqual(encode_tags([]), ""); self.assertEqual(decode_tags("other"), [])
    def test_pick_target(self):
        c = [dict(track=1, start=0, end=100, has_marker=False, locked=False),
             dict(track=2, start=40, end=100, has_marker=True, locked=False),
             dict(track=3, start=50, end=100, has_marker=True, locked=True)]
        self.assertEqual(pick_target_clip(c, 60)["track"], 2)       # marker beats distance, locked ignored
        self.assertIsNone(pick_target_clip(c, 150))
        self.assertEqual(pick_target_clip(c[:1], 99)["track"], 1)
        self.assertIsNone(pick_target_clip(c[:1], 100))             # end exclusive
    def test_replace_trims_and_guards(self):
        old = dict(track=1, start=100, end=200)
        p = plan_replace(old=old, new_length=500, keep_new_length=False, locked=set(), neighbours=[(200, 300)])
        self.assertTrue(p.ok); self.assertEqual((p.start, p.end), (100, 200))
        p = plan_replace(old=old, new_length=500, keep_new_length=True, locked=set(), neighbours=[(200, 300)])
        self.assertEqual(p.code, "ERR_TRACK_BUSY")
        self.assertEqual(plan_replace(old=old, new_length=50, keep_new_length=False, locked={1}, neighbours=[]).code, "ERR_TRACK_LOCKED")
        p = plan_replace(old=old, new_length=50, keep_new_length=False, locked=set(), neighbours=[])
        self.assertEqual(p.end, 150)                                 # shorter sound stays shorter
    def test_random_fill(self):
        files = [dict(path="a", duration=1.0), dict(path="b", duration=9.0), dict(path="c", duration=0)]
        r = plan_random_fill([dict(frame=10), dict(frame=20)], files, track=2, seed=1)
        self.assertEqual([x["path"] for x in r], ["a", "a"]); self.assertEqual(r[1]["record_frame"], 20)
        self.assertEqual(plan_random_fill([dict(frame=1)], [dict(path="b", duration=9.0)], track=1), [])
if __name__ == "__main__": unittest.main()

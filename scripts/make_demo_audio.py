#!/usr/bin/env python3
"""Synthesises the CC0 demo sounds in demo-audio/ (deterministic, stdlib only)."""
import math, os, random, struct, wave, sys

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demo-audio")


def write(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32000)) for s in samples))


def env(i, n, a=0.005, r=0.5):
    t = i / SR; d = n / SR
    return min(1, t / a) * math.exp(-(t / (d * r)) * 3)


def whoosh(rng):
    n = int(SR * 1.4); out = []; lp = 0.0
    for i in range(n):
        x = i / n; c = 0.02 + 0.5 * math.sin(math.pi * x) ** 2
        lp += c * (rng.uniform(-1, 1) - lp); out.append(lp * math.sin(math.pi * x) ** 1.5 * 1.8)
    return out


def hit(rng):
    n = int(SR * 0.9)
    return [(math.sin(2 * math.pi * (55 + 90 * math.exp(-i / 2500)) * i / SR) + 0.3 * rng.uniform(-1, 1) * math.exp(-i / 1500)) * env(i, n, .001, .35) for i in range(n)]


def click(rng):
    n = int(SR * 0.12)
    return [rng.uniform(-1, 1) * math.exp(-i / 180) * 0.9 for i in range(n)]


def riser(rng):
    n = int(SR * 2.5); ph = 0.0; out = []
    for i in range(n):
        x = i / n; ph += 2 * math.pi * (200 + 1800 * x * x) / SR
        out.append((0.5 * math.sin(ph) + 0.2 * rng.uniform(-1, 1)) * x)
    return out


def ding(rng):
    n = int(SR * 1.6)
    return [sum(math.sin(2 * math.pi * f * i / SR) * a for f, a in ((880, .5), (1760, .25), (2640, .12))) * env(i, n, .002, .3) for i in range(n)]


def pop(rng):
    n = int(SR * 0.25)
    return [math.sin(2 * math.pi * (900 * math.exp(-i / 1200)) * i / SR) * math.exp(-i / 1500) for i in range(n)]


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [("Whoosh Soft", whoosh), ("Impact Low", hit), ("Click Dry", click), ("Riser Short", riser), ("Ding Bright", ding), ("Pop Round", pop)]:
        write(os.path.join(OUT, name + ".wav"), fn(random.Random(name)))
        print("wrote", name)

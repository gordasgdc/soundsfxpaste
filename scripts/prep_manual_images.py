#!/usr/bin/env python3
"""Tightens the panel screenshots in docs/manual/img: removes the empty band between the content and the bottom bar
(so text stays legible in the PDF). Idempotent: skips images already tightened (marker in the file comment)."""
import os, sys
from PIL import Image
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "manual", "img")
BAR = 890  # y where the bottom bar starts at 1600 px width
for f in sorted(os.listdir(D)):
    if not f.endswith(".jpg") or f[3:6] == "tl_": continue
    im = Image.open(D + "/" + f).convert("RGB")
    if im.height < BAR + 100 or im.info.get("comment") == b"tight": continue
    px = im.load(); last = 90
    for y in range(90, BAR):
        base = px[20, y]
        if any(max(abs(px[x, y][c] - base[c]) for c in range(3)) > 40 for x in range(120, im.width - 20, 3)): last = y
    cut = min(BAR - 40, last + 50)
    out = Image.new("RGB", (im.width, cut + (im.height - BAR)))
    out.paste(im.crop((0, 0, im.width, cut)), (0, 0)); out.paste(im.crop((0, BAR, im.width, im.height)), (0, cut))
    out.save(D + "/" + f, quality=84, comment=b"tight"); print(f, im.height, "->", out.height)

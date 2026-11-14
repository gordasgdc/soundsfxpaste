#!/usr/bin/env python3
"""Writes the practical tutorials into README.md / README.ro.md / README.es.md from scripts/tutorials.py (single source). Idempotent."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tutorials as TU
import pymupdf
R = TU.ROOT
FILES = {"en": "README.md", "ro": "README.ro.md", "es": "README.es.md"}
HEAD = {"en": ("Tutorials", "One written tutorial per video clip (the clips are filmed with the Romanian interface, no voice). Full explanations are in the PDF manual; the same text is on the product page.", "Watch", "Result", "If it differs", "Licence"),
        "ro": ("Tutoriale", "Câte un tutorial scris pentru fiecare clip (clipurile sunt filmate cu interfața în română, fără voce). Explicațiile complete sunt în manualul PDF; același text e pe pagina produsului.", "Vezi clipul", "Rezultat", "Dacă diferă", "Licență"),
        "es": ("Tutoriales", "Un tutorial escrito por cada clip (los clips están grabados con la interfaz en rumano, sin voz). Las explicaciones completas están en el manual PDF; el mismo texto está en la página del producto.", "Ver el clip", "Resultado", "Si difiere", "Licencia")}
PAGES = len(pymupdf.open(f"{R}/docs/manual/pdf/SoundSFXPaste-Manual-RO-0.2.0.pdf"))
for lang, fn in FILES.items():
    h, intro, watch, res, fix, lic = HEAD[lang]
    out = [f"<!-- tutorials:start -->", f"## {h}", "", intro, ""]
    for tu in TU.TUT:
        n = tu["n"]; R_ = lambda x: TU.render(lang, x, "md")
        out += [f"### {n}. {tu['title']}", "", f"{watch}: [{TU.clip_url(lang, n)}]({TU.clip_url(lang, n)}) · [MP4]({TU.mp4_url(n)})", "", R_(TU.loc(tu["goal"], lang)), ""]
        out += [f"{k}. {R_(x)}" for k, x in enumerate(TU.loc(tu["steps"], lang), 1)] + [""]
        out += [f"**{res}:** " + " ".join(R_(x) for x in TU.loc(tu["see"], lang)), "", f"**{fix}:** {R_(TU.loc(tu['fix'], lang))}", ""]
    out.append("<!-- tutorials:end -->")
    block = "\n".join(out) + "\n"
    s = open(f"{R}/{fn}", encoding="utf-8").read()
    s = re.sub(r"\n?<!-- tutorials:start -->.*?<!-- tutorials:end -->\n", "", s, flags=re.S)
    s = re.sub(r"\((PDF, )\d+( pages| pagini| páginas| páginas cada uno)", lambda m: m.group(0), s)
    s = re.sub(r"\(PDF, \d+ ", f"(PDF, {PAGES} ", s)
    page = TU.PAGE[lang] + "#tutoriale-video" if False else TU.PAGE[lang]
    s = re.sub(r"https://gordas\.dev/soundsfxpaste/#tutoriale-video", page + "#clip-1", s)
    s = re.sub(r"https://gordas\.dev/soundsfxpaste/(en/|es/)#tutoriale-video", page + "#clip-1", s)
    i = s.index(f"\n## {lic}")
    s = s[:i] + "\n" + block + s[i:]
    open(f"{R}/{fn}", "w", encoding="utf-8").write(s)
    print(fn, "ok")

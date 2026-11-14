#!/usr/bin/env python3
"""Builds the public pages (RO root, /en/, /es/) into site/ and the social preview. Usage: scripts/build_site.py"""
import json, os, shutil, html, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tutorials as TU
from PIL import Image, ImageDraw, ImageFont
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VER = json.load(open(f"{R}/app/package.json"))["version"]
BASE = "https://gordas.dev/soundsfxpaste/"
PKG = f"https://github.com/gordasgdc/soundsfxpaste/releases/download/v{VER}/SoundSFXPaste-{VER}.pkg"
REPO = "https://github.com/gordasgdc/soundsfxpaste"
T = {
 "ro": dict(path="", title="SoundSFXPaste — panou de efecte sonore pentru DaVinci Resolve", desc="Găsești, asculți și plasezi efecte sonore pe timeline-ul DaVinci Resolve în câțiva pași. Gratuit, MIT, macOS.",
  eyebrow="Panou pentru DaVinci Resolve · macOS · gratuit", h1="Găsești sunetul. Îl asculți. Îl pui pe timeline.",
  lead="Un panou de efecte sonore care stă lângă Resolve: formă de undă reală pe fiecare sunet, audiție rapidă, plasare la cursor pe pista aleasă, fără să lași editarea.",
  dl="Descarcă pentru macOS", dlnote=f"Versiunea {VER} · pachet semnat și notarizat · dublu-clic pentru instalare", src="Cod sursă (MIT)",
  shot_alt="Panoul SoundSFXPaste cu biblioteca de sunete, forme de undă și bara de plasare",
  fl_h="Fluxul", fl=[("Alege folderul","Adaugi folderul cu sunete; panoul le listează cu forma de undă și durata."),("Ascultă","Treci cu mouse-ul sau apasă ▶ pentru audiție rapidă; favorite și recente la un clic."),("Plasează","Alegi pista, vezi poziția cursorului, apeși Plasează. Suprapunerile sunt oprite înainte de scriere.")],
  ft_h="Ce face", ft=[("Forme de undă reale","Calculate din fișier, nu decorative."),("Destinație vizibilă","Pista și timecode-ul cursorului stau lângă butonul Plasează."),("Protecție la suprapunere","Planul se verifică înainte și rezultatul după scriere, cu revenire."),("Ține deasupra","Panoul poate rămâne peste Resolve cât lucrezi."),("Auto SFX","Umple markerele, înlocuiește clipuri, gestionează markere."),("RO / EN / ES","Interfață și documentație în trei limbi.")],
  rq_h="Instalare și cerințe", rq=["DaVinci Resolve Studio 21 sau mai nou, macOS.","Python 3 (panoul îl verifică și arată pașii de instalare).","În Resolve: Preferences → General → External scripting using: Local.","Dublu-clic pe pachet, apoi Workspace → Workflow Integrations → SoundSFXPaste."],
  lm_h="Limite cunoscute", lm=["Timeline-urile drop-frame sunt refuzate explicit.","Resolve nu oferă API pentru selecția clipurilor; Replace folosește selecția manuală.","Tragerea sunetului direct pe timeline nu este disponibilă; plasarea se face cu butonul."],
  sup_h="Susținere", sup="Proiect administrat de dezvoltatori independenți, oferit „as is”. Contribuțiile și donațiile sunt opționale.", lic="MIT · Dumitru Cristinel Gordas (GDC)", docs="Documentație", nav="Limbă", terms="Termeni", priv="Confidențialitate", cookie="Cookie"),
 "en": dict(path="en/", title="SoundSFXPaste — sound-effects panel for DaVinci Resolve", desc="Find, hear and place sound effects on your DaVinci Resolve timeline in a few steps. Free, MIT, macOS.",
  eyebrow="DaVinci Resolve panel · macOS · free", h1="Find the sound. Hear it. Drop it on the timeline.",
  lead="A sound-effects panel that sits next to Resolve: a real waveform on every sound, quick audition, placement at the cursor on the track you choose, without leaving the edit.",
  dl="Download for macOS", dlnote=f"Version {VER} · signed and notarized package · double-click to install", src="Source code (MIT)",
  shot_alt="The SoundSFXPaste panel showing the sound library, waveforms and the placement bar",
  fl_h="The flow", fl=[("Pick a folder","Add your sound folder; the panel lists every sound with its waveform and length."),("Audition","Hover or press ▶ for a quick listen; favorites and recents are one click away."),("Place","Choose the track, see the cursor position, press Place. Overlaps are stopped before anything is written.")],
  ft_h="What it does", ft=[("Real waveforms","Computed from the file, not decorative."),("Visible destination","Track and cursor timecode sit next to the Place button."),("Overlap protection","The plan is checked first and the result verified after writing, with rollback."),("Keep on top","The panel can stay above Resolve while you work."),("Auto SFX","Fill markers, replace clips, manage markers."),("RO / EN / ES","Interface and documentation in three languages.")],
  rq_h="Install and requirements", rq=["DaVinci Resolve Studio 21 or later, macOS.","Python 3 (the panel checks it and shows the install steps).","In Resolve: Preferences → General → External scripting using: Local.","Double-click the package, then Workspace → Workflow Integrations → SoundSFXPaste."],
  lm_h="Known limits", lm=["Drop-frame timelines are refused explicitly.","Resolve has no API to set a clip selection; Replace uses your manual selection.","Dragging a sound straight onto the timeline is not available; placement uses the button."],
  sup_h="Support", sup="Project run by independent developers, offered “as is”. Contributions and donations are optional.", lic="MIT · Dumitru Cristinel Gordas (GDC)", docs="Documentation", nav="Language", terms="Terms", priv="Privacy", cookie="Cookie"),
 "es": dict(path="es/", title="SoundSFXPaste — panel de efectos de sonido para DaVinci Resolve", desc="Encuentra, escucha y coloca efectos de sonido en la línea de tiempo de DaVinci Resolve en pocos pasos. Gratis, MIT, macOS.",
  eyebrow="Panel para DaVinci Resolve · macOS · gratis", h1="Encuentra el sonido. Escúchalo. Colócalo en la línea de tiempo.",
  lead="Un panel de efectos de sonido junto a Resolve: forma de onda real en cada sonido, audición rápida y colocación en el cursor sobre la pista elegida, sin salir de la edición.",
  dl="Descargar para macOS", dlnote=f"Versión {VER} · paquete firmado y notarizado · doble clic para instalar", src="Código fuente (MIT)",
  shot_alt="El panel SoundSFXPaste con la biblioteca de sonidos, formas de onda y la barra de colocación",
  fl_h="El flujo", fl=[("Elige la carpeta","Añade tu carpeta de sonidos; el panel los lista con forma de onda y duración."),("Escucha","Pasa el ratón o pulsa ▶ para una audición rápida; favoritos y recientes a un clic."),("Coloca","Elige la pista, mira la posición del cursor y pulsa Colocar. Los solapamientos se detienen antes de escribir.")],
  ft_h="Qué hace", ft=[("Formas de onda reales","Calculadas desde el archivo, no decorativas."),("Destino visible","La pista y el timecode del cursor están junto a Colocar."),("Protección de solapamientos","El plan se comprueba antes y el resultado después, con reversión."),("Mantener encima","El panel puede quedarse sobre Resolve mientras trabajas."),("Auto SFX","Rellena marcadores, sustituye clips, gestiona marcadores."),("RO / EN / ES","Interfaz y documentación en tres idiomas.")],
  rq_h="Instalación y requisitos", rq=["DaVinci Resolve Studio 21 o posterior, macOS.","Python 3 (el panel lo comprueba y muestra los pasos).","En Resolve: Preferences → General → External scripting using: Local.","Doble clic en el paquete y luego Workspace → Workflow Integrations → SoundSFXPaste."],
  lm_h="Límites conocidos", lm=["Las líneas de tiempo drop-frame se rechazan explícitamente.","Resolve no tiene API para fijar la selección de clips; Replace usa tu selección manual.","Arrastrar un sonido directo a la línea de tiempo no está disponible; se coloca con el botón."],
  sup_h="Apoyo", sup="Proyecto de desarrolladores independientes, ofrecido «tal cual». Las contribuciones y donaciones son opcionales.", lic="MIT · Dumitru Cristinel Gordas (GDC)", docs="Documentación", nav="Idioma", terms="Términos", priv="Privacidad", cookie="Cookie"),
}
CSS = """:root{--bg:#060b19;--s1:#0d1530;--s2:#142048;--line:#223062;--fg:#eaf0ff;--mut:#98a6cc;--gold:#f3c24f;--gold2:#e09a2d;--blue:#3a5bd9;color-scheme:dark}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(1200px 500px at 70% -10%,#16245a 0,transparent 60%),var(--bg);color:var(--fg);font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
a{color:inherit}a:focus-visible,button:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
header{max-width:1180px;margin:0 auto;padding:18px 24px;display:flex;justify-content:space-between;align-items:center;gap:16px}
.brand{display:flex;gap:10px;align-items:center;font-weight:700;text-decoration:none;letter-spacing:-.01em}.brand i{width:22px;height:22px;border-radius:6px;background:linear-gradient(160deg,#ffe08a,var(--gold2));box-shadow:0 0 18px #f3c24f55}
.lang{display:flex;gap:4px;padding:4px;border:1px solid var(--line);border-radius:10px;background:var(--s1)}.lang a{padding:5px 12px;border-radius:7px;text-decoration:none;color:var(--mut);font-size:14px;font-weight:600}.lang a[aria-current]{background:var(--blue);color:#fff;box-shadow:inset 0 -2px 0 var(--gold)}
main{max-width:1180px;margin:0 auto;padding:0 24px}
.hero{padding:40px 0 24px;display:grid;gap:28px}.eyebrow{color:var(--gold);font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
h1{font-size:clamp(2.1rem,5.6vw,4rem);line-height:1.04;margin:.25em 0 .35em;letter-spacing:-.03em;max-width:18ch}.lead{color:var(--mut);font-size:1.15rem;max-width:58ch;margin:0}
.cta{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-top:22px}.btn{display:inline-block;padding:13px 22px;border-radius:12px;font-weight:700;text-decoration:none;background:linear-gradient(180deg,#ffd877,var(--gold2));color:#2a1a02;box-shadow:0 8px 28px #e09a2d44,inset 0 1px 0 #fff8}.btn.ghost{background:var(--s1);color:var(--fg);border:1px solid var(--line);box-shadow:none}
.note{color:var(--mut);font-size:14px;margin:10px 0 0}
.shot{width:100%;height:auto;border-radius:14px;border:1px solid var(--line);box-shadow:0 30px 80px #000a,0 0 0 1px #ffffff08}
section{padding:46px 0}h2{font-size:1.5rem;letter-spacing:-.02em;margin:0 0 18px}h2::after{content:"";display:block;width:44px;height:3px;background:var(--gold);border-radius:2px;margin-top:10px}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;counter-reset:s;padding:0;list-style:none}.steps li{background:linear-gradient(180deg,var(--s2),var(--s1));border:1px solid var(--line);border-radius:14px;padding:20px;counter-increment:s}.steps li::before{content:counter(s);display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--gold);color:#2a1a02;font-weight:800;margin-bottom:10px}.steps b{display:block;font-size:1.05rem}.steps span{color:var(--mut);font-size:15px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.grid div{border:1px solid var(--line);border-radius:12px;padding:16px;background:var(--s1)}.grid b{display:block;color:var(--gold)}.grid span{color:var(--mut);font-size:15px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:32px}ul{padding-left:1.1em;margin:0}li{margin:.4em 0}.two li{color:var(--mut)}
footer{max-width:1180px;margin:20px auto 0;padding:34px 24px 50px;border-top:1px solid var(--line);color:var(--mut);font-size:13px;display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap}footer div{display:flex;gap:18px;flex-wrap:wrap}
@media(max-width:820px){.steps,.grid,.two{grid-template-columns:1fr}header{padding:14px 16px}main{padding:0 16px}footer{padding:28px 16px}}"""

VIDEOS = [("01-deschide-panoul-si-adauga-un-folder-de-sunete", "Deschide panoul și adaugă un folder de sunete", 4),
          ("02-cauta-asculta-si-plaseaza-un-sunet-la-cursor", "Caută, ascultă și plasează un sunet la cursor", 6),
          ("03-scurteaza-un-sunet", "Scurtează un sunet", 7), ("04-inlocuieste-un-sunet-in-timeline", "Înlocuiește un sunet în timeline", 8),
          ("05-foloseste-markere-si-etichete", "Folosește markere și etichete", 9), ("06-completeaza-markerele-cu-sunete-aleatorii", "Completează markerele cu sunete aleatorii", 10),
          ("07-asociaza-rapid-sunete-cu-markerele", "Asociază rapid sunete cu markerele", 11)]  # (file, title in Romanian on every page, manual chapter)
X = {"ro": dict(pdf="Manual PDF (română)", pdf_h="Manual PDF în toate limbile", vid_h="Tutoriale video", vid_p="Clipuri scurte, fără voce și fără text pe ecran. Interfața filmată este în română; titlurile rămân în română și în paginile în alte limbi.", vid_ch="Capitolul din manual"),
     "en": dict(pdf="PDF manual (English)", pdf_h="PDF manual in every language", vid_h="Video tutorials", vid_p="Short clips with no voice and no on-screen text. The filmed interface is in Romanian; the titles stay in Romanian on the pages in other languages.", vid_ch="Manual chapter"),
     "es": dict(pdf="Manual PDF (español)", pdf_h="Manual PDF en todos los idiomas", vid_h="Tutoriales en vídeo", vid_p="Clips cortos sin voz y sin texto en pantalla. La interfaz filmada está en rumano; los títulos se mantienen en rumano en las páginas de otros idiomas.", vid_ch="Capítulo del manual")}
PDFN = {l: f"SoundSFXPaste-Manual-{l.upper()}-{VER}.pdf" for l in X}
CSS += """.pdfs{margin:12px 0 0;font-size:14px;color:var(--mut)}.pdfs a{color:var(--fg);margin-right:10px}
.vids{display:flex;flex-direction:column;gap:22px;margin-top:10px}.tut{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:24px;background:var(--s1);border:1px solid var(--line);border-radius:14px;padding:18px;scroll-margin-top:16px}
.tut video{display:block;width:100%;aspect-ratio:16/9;background:#000;border-radius:10px}.tut .tv p{margin:10px 0 0;font-size:14px}.tut a{color:var(--gold)}
.tut h3{margin:0 0 6px;font-size:19px}.tut h4{margin:14px 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--gold)}.tut .goal{margin:0;font-size:15px}
.tut ol,.tut ul{padding-left:1.2em;margin:0}.tut li{margin:.35em 0;color:var(--fg);font-size:15px;overflow-wrap:anywhere}.tut p{overflow-wrap:anywhere}.tut .names{font-size:13px;color:var(--mut)}
@media(max-width:820px){.tut{grid-template-columns:1fr;padding:14px;gap:16px}}"""
def chap_pages(L):
    try:
        import pymupdf
        toc = [t[2] for t in pymupdf.open(f"{R}/docs/manual/pdf/{PDFN[L]}").get_toc()]
        return {n: toc[n - 1] for n in range(1, len(toc) + 1)}
    except Exception:
        return {}

def page(L):
    t = T[L]; up = "" if L == "ro" else "../"
    alts = "".join(f'<link rel="alternate" hreflang="{l}" href="{BASE}{T[l]["path"]}">' for l in T) + f'<link rel="alternate" hreflang="x-default" href="{BASE}">'
    lang = "".join(f'<a href="{up}{T[l]["path"]}" hreflang="{l}" lang="{l}"{" aria-current=\"page\"" if l == L else ""}>{l.upper()}</a>' for l in T)
    e = html.escape
    steps = "".join(f"<li><b>{e(a)}</b><span>{e(b)}</span></li>" for a, b in t["fl"])
    feats = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in t["ft"])
    cp = chap_pages(L)
    pdf_links = " · ".join(f'<a href="{up}manual/{PDFN[l]}" hreflang="{l}">{l.upper()}</a>' for l in X)
    def tut(i, tu):
        f, ti, ch = tu["file"], tu["title"], tu["chap"][0]
        L_ = lambda k: TU.loc(tu[k], L); R_ = lambda x: TU.render(L, x, "html"); hh = TU.H[L]
        names = TU.ro_names(L, tu)
        nm = f'<p class="names">{e(hh["names"])}: ' + "; ".join(f"{e(a)} = {e(b)}" for a, b in names) + "</p>" if names else ""
        li = lambda xs, tag: f"<{tag}>" + "".join(f"<li>{R_(x)}</li>" for x in xs) + f"</{tag}>"
        return (f'<article class="tut" id="clip-{i}"><div class="tv"><video controls preload="none" playsinline poster="{up}assets/video-{i}.jpg" src="{up}video/{f}.mp4"></video>'
                f'<p>{e(X[L]["vid_ch"])}: <a href="{up}manual/{PDFN[L]}#page={cp.get(ch, 1)}">{ch}</a></p></div>'
                f'<div class="tt"><h3>{i}. {e(ti)}</h3><p class="goal">{R_(L_("goal"))}</p><h4>{e(hh["need"])}</h4>{li(L_("need"), "ul")}<h4>{e(hh["steps"])}</h4>{li(L_("steps"), "ol")}'
                f'<h4>{e(hh["see"])}</h4>{li(L_("see"), "ul")}<h4>{e(hh["ex"])}</h4><p>{R_(L_("example"))}</p><h4>{e(hh["fix"])}</h4><p>{R_(L_("fix"))}</p>{nm}</div></article>')
    vids = "".join(tut(i, tu) for i, tu in enumerate(TU.TUT, 1))
    shot = {"ro": "ro-folders", "en": "en-folders", "es": "es-folders"}[L]
    return f"""<!doctype html><html lang="{L}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(t['title'])}</title>
<meta name="description" content="{e(t['desc'])}"><link rel="canonical" href="{BASE}{t['path']}">{alts}
<meta property="og:title" content="{e(t['title'])}"><meta property="og:description" content="{e(t['desc'])}"><meta property="og:image" content="{BASE}assets/social-preview.png"><meta property="og:url" content="{BASE}{t['path']}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{up}assets/simbol.svg" type="image/svg+xml"><style>{CSS}</style></head><body>
<header><a class="brand" href="{up or './'}"><i></i>SoundSFXPaste</a><nav class="lang" aria-label="{e(t['nav'])}">{lang}</nav></header>
<main><div class="hero"><div><div class="eyebrow">{e(t['eyebrow'])}</div><h1>{e(t['h1'])}</h1><p class="lead">{e(t['lead'])}</p>
<div class="cta"><a class="btn" id="download" href="{PKG}">{e(t['dl'])}</a><a class="btn ghost" href="{up}manual/{PDFN[L]}">{e(X[L]['pdf'])}</a><a class="btn ghost" href="{REPO}">{e(t['src'])}</a></div><p class="note">{e(t['dlnote'])}</p><p class="pdfs">{e(X[L]['pdf_h'])}: {pdf_links}</p></div>
<img class="shot" src="{up}assets/{shot}.png" alt="{e(t['shot_alt'])}" width="1180" height="760"></div>
<section id="flow"><h2>{e(t['fl_h'])}</h2><ol class="steps">{steps}</ol></section>
<section id="features"><h2>{e(t['ft_h'])}</h2><div class="grid">{feats}</div></section>
<section id="tutoriale-video"><h2>{e(X[L]['vid_h'])}</h2><p class="note">{e(X[L]['vid_p'])}</p><div class="vids">{vids}</div></section>
<section class="two"><div id="install"><h2>{e(t['rq_h'])}</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in t['rq'])}</ul></div><div><h2>{e(t['lm_h'])}</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in t['lm'])}</ul></div></section></main>
<footer><span>SoundSFXPaste {VER} · {e(t['lic'])}<br><span style="display:block;margin-top:8px;max-width:52ch">{e(t['sup'])}</span></span><div><a href="{REPO}#readme">{e(t['docs'])}</a><a href="{REPO}">GitHub</a><a href="https://gordas.dev/termeni">{e(t['terms'])}</a><a href="https://gordas.dev/confidentialitate">{e(t['priv'])}</a><a href="https://gordas.dev/cookie">{e(t['cookie'])}</a></div></footer></body></html>"""
out = f"{R}/site"; shutil.rmtree(out, ignore_errors=True); os.makedirs(f"{out}/assets")
for l in T:
    d = out if l == "ro" else f"{out}/{l}"; os.makedirs(d, exist_ok=True); open(f"{d}/index.html", "w").write(page(l))
for n in ("ro-folders", "en-folders", "es-folders", "en-favorites", "en-autosfx"):
    im = Image.open(f"{R}/docs/img/{n}.png").convert("RGB"); im.thumbnail((1600, 1600)); im.save(f"{out}/assets/{n}.png", optimize=True)
open(f"{out}/assets/simbol.svg", "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffe08a"/><stop offset="1" stop-color="#e09a2d"/></linearGradient></defs><rect width="32" height="32" rx="8" fill="#060b19"/><rect x="6" y="6" width="20" height="20" rx="6" fill="url(#g)"/></svg>')
# social preview 1200x630
W, H = 1200, 630; bg = Image.new("RGB", (W, H), "#060b19"); d = ImageDraw.Draw(bg)
for y in range(H): d.line([(0, y), (W, y)], fill=(6 + y // 40, 11 + y // 28, 25 + y // 12))
shot = Image.open(f"{R}/docs/img/en-folders.png").convert("RGB"); shot.thumbnail((700, 460)); bg.paste(shot, (W - shot.width - 50, 150))
def font(sz, bold=True):
    for p in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/SFNS.ttf"):
        try: return ImageFont.truetype(p, sz, index=1 if bold and p.endswith("ttc") else 0)
        except Exception: pass
    return ImageFont.load_default()
d.rounded_rectangle([60, 70, 100, 110], 10, fill="#f3c24f"); d.text((116, 72), "SoundSFXPaste", font=font(38), fill="#eaf0ff")
for i, ln in enumerate(["Find the sound.", "Hear it.", "Drop it on", "the timeline."]): d.text((60, 170 + i * 66), ln, font=font(58), fill="#f3c24f" if i == 3 else "#eaf0ff")
d.text((60, 520), "Free DaVinci Resolve panel · macOS · MIT", font=font(26, False), fill="#98a6cc")
bg.save(f"{out}/assets/social-preview.png", optimize=True); bg.save(f"{R}/docs/img/social-preview.png", optimize=True)
print("site built", VER)
os.makedirs(f"{out}/manual", exist_ok=True); os.makedirs(f"{out}/video", exist_ok=True)
for l in X:
    if os.path.exists(f"{R}/docs/manual/pdf/{PDFN[l]}"): shutil.copy(f"{R}/docs/manual/pdf/{PDFN[l]}", f"{out}/manual/")
import subprocess
for i, (f, ti, ch) in enumerate(VIDEOS, 1):
    src = f"{R}/docs/video/{f}.mp4"
    if os.path.exists(src):
        shutil.copy(src, f"{out}/video/")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "9", "-i", src, "-frames:v", "1", "-vf", "scale=640:-1", "-q:v", "5", f"{out}/assets/video-{i}.jpg"], check=False)

#!/usr/bin/env python3
"""Builds the three SoundSFXPaste user manuals (RO / EN / ES) as PDF.

Usage:  python3 scripts/build_manual.py [out-dir]          (default: dist/manual)
Needs:  reportlab, Pillow, PyMuPDF (summary only). Fonts: macOS Arial / Courier New.
Inputs: docs/manual/img/*.jpg  (panel and timeline screenshots, demo library only)
        docs/manual/i18n.txt   (the panel's own UI strings; labels in the text are
                                 pulled from it so they match the panel exactly)
Content is written once as (ro, en, es) triples so the three manuals stay in parity.
"""
import os, re, sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "docs", "manual", "img")
VERSION = "0.2.0"
SITE = "https://gordas.dev/soundsfxpaste/"
REPO = "https://github.com/gordasgdc/soundsfxpaste"
PLUG = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins/SoundSFXPaste"
CREDIT = "Dumitru Cristinel Gordas (GDC)"

SUP = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("Body", SUP + "Arial.ttf"))
pdfmetrics.registerFont(TTFont("BodyB", SUP + "Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("BodyI", SUP + "Arial Italic.ttf"))
pdfmetrics.registerFont(TTFont("Mono", SUP + "Courier New.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyB")

INK = colors.HexColor("#14161A")
MUTED = colors.HexColor("#5c6270")
BLUE = colors.HexColor("#2f5fd0")
GOLD = colors.HexColor("#e0a020")
LINE = colors.HexColor("#d8dce4")
SOFT = colors.HexColor("#eef1f7")
WARM = colors.HexColor("#fbf3e1")

ST = {
    "h1": ParagraphStyle("h1", fontName="BodyB", fontSize=19, leading=23, textColor=INK, spaceBefore=2, spaceAfter=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="BodyB", fontSize=12.5, leading=16, textColor=BLUE, spaceBefore=10, spaceAfter=4, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Body", fontSize=10, leading=14.5, textColor=INK, spaceAfter=6),
    "li": ParagraphStyle("li", fontName="Body", fontSize=10, leading=14, textColor=INK, leftIndent=13, bulletIndent=0, spaceAfter=3),
    "cap": ParagraphStyle("cap", fontName="BodyI", fontSize=8.5, leading=11, textColor=MUTED, spaceAfter=8),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=8.4, leading=11.5, textColor=INK, backColor=SOFT, borderPadding=5, spaceAfter=8),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=9, leading=12, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="BodyB", fontSize=9, leading=12, textColor=INK),
    "toc1": ParagraphStyle("toc1", fontName="Body", fontSize=10.5, leading=17, textColor=INK),
    "note": ParagraphStyle("note", fontName="Body", fontSize=9.2, leading=13, textColor=INK, backColor=WARM, borderPadding=7, spaceAfter=9, spaceBefore=3),
}

# ---------------------------------------------------------------- UI strings
def load_i18n():
    d, cur = {}, None
    for ln in open(os.path.join(ROOT, "docs", "manual", "i18n.txt"), encoding="utf-8"):
        ln = ln.rstrip("\n")
        if ln.startswith("=== "):
            cur = ln[4:].strip(); d[cur] = {}
        elif "=" in ln and cur:
            k, v = ln.split("=", 1); d[cur][k] = v
    return d

I18N = load_i18n()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ui(lang, text):
    """[[key]] -> bold UI label;  [[key|n=3]] fills {n};  [[=key]] -> plain message text without {detail}."""
    def rep(m):
        body = m.group(1)
        plain = body.startswith("=")
        body = body.lstrip("=")
        key, _, args = body.partition("|")
        v = I18N[lang][key]
        for a in args.split(",") if args else []:
            k2, _, v2 = a.partition("="); v = v.replace("{" + k2 + "}", v2)
        v = re.sub(r"\s*\(\{detail\}\)", "", v)
        v = esc(v)
        return v if plain else "<b>" + v + "</b>"
    return re.sub(r"\[\[([^\]]+)\]\]", rep, text)

# ---------------------------------------------------------------- content
# block kinds: ("h1",(ro,en,es)) ("h2",..) ("p",..) ("ul",[..triples]) ("code",str) ("img",key,(captions)) ("ex",goal,where,appears,undo) ("note",..) ("tbl",[(a,b)],..)
def T(ro, en, es): return (ro, en, es)

CH = []  # list of (title_triple, [blocks])

CH.append((T("Ce rezolvă și primul exercițiu (5 minute)", "What it solves, and your first 5-minute exercise", "Qué resuelve y tu primer ejercicio (5 minutos)"), [
    ("p", T("SoundSFXPaste este un panou pentru DaVinci Resolve Studio în care ai biblioteca ta de efecte sonore la îndemână: cauți, asculți forma de undă și plasezi sunetul direct pe pista audio, la cursor, fără să tragi fișiere din Finder și fără să cauți în Media Pool. Panoul stă lângă timeline (se poate ține deasupra) și vorbește cu Resolve printr-un mic proces local.",
            "SoundSFXPaste is a DaVinci Resolve Studio panel that keeps your sound-effects library at hand: search, see the waveform, audition, and place the sound straight onto an audio track at the cursor, without dragging files from Finder or hunting in the Media Pool. The panel sits next to the timeline (it can stay on top) and talks to Resolve through a small local helper.",
            "SoundSFXPaste es un panel de DaVinci Resolve Studio que te deja la biblioteca de efectos de sonido a mano: buscas, ves la forma de onda, escuchas y colocas el sonido directamente en una pista de audio, en el cursor, sin arrastrar archivos desde Finder ni buscar en el Media Pool. El panel se queda junto al timeline (puede mantenerse encima) y habla con Resolve mediante un pequeño proceso local.")),
    ("p", T("Pe lângă plasarea simplă, panoul face patru lucruri pe care le faci des la sonorizare: scurtează un sunet înainte de plasare, înlocuiește sunete deja puse, gestionează markerele (nume, etichete) și completează markerele cu sunete, aleatoriu sau unul câte unul.",
            "Besides simple placing, the panel does four things you do often when adding sound: trim a sound before placing it, replace sounds already on the timeline, manage markers (names, tags), and fill markers with sounds, randomly or one by one.",
            "Además de colocar sonidos, el panel hace cuatro cosas habituales al sonorizar: recortar un sonido antes de colocarlo, reemplazar sonidos que ya están en el timeline, gestionar marcadores (nombres, etiquetas) y rellenar marcadores con sonidos, al azar o uno a uno.")),
    ("h2", T("Exercițiul de 5 minute", "The 5-minute exercise", "El ejercicio de 5 minutos")),
    ("p", T("Folosește folderul demo <b>demo-audio</b> din proiect (șase sunete sintetice, libere de drepturi) și un timeline gol cu cel puțin o pistă audio. Scopul: un „whoosh” de 1,4 s exact pe tăietura dintre două clipuri video.",
            "Use the project's <b>demo-audio</b> folder (six synthesized, rights-free sounds) and an empty timeline with at least one audio track. Goal: a 1.4 s whoosh exactly on the cut between two video clips.",
            "Usa la carpeta <b>demo-audio</b> del proyecto (seis sonidos sintetizados y libres de derechos) y un timeline con al menos una pista de audio. Objetivo: un “whoosh” de 1,4 s justo en el corte entre dos clips de vídeo.")),
    ("ul", [T("În Resolve: <b>Workspace › Workflow Integrations › SoundSFXPaste</b>. Apare fereastra panoului.", "In Resolve: <b>Workspace › Workflow Integrations › SoundSFXPaste</b>. The panel window opens.", "En Resolve: <b>Workspace › Workflow Integrations › SoundSFXPaste</b>. Se abre la ventana del panel."),
            T("Apasă [[addFolder]] (+ din [[library]]) și alege folderul <b>demo-audio</b>. Apar șase carduri cu forme de undă.", "Press [[addFolder]] (+ in [[library]]) and choose the <b>demo-audio</b> folder. Six cards with waveforms appear.", "Pulsa [[addFolder]] (+ en [[library]]) y elige la carpeta <b>demo-audio</b>. Aparecen seis tarjetas con formas de onda."),
            T("Scrie „whoosh” în câmpul [[search]] și apasă pe cardul <b>Whoosh Soft</b>.", "Type “whoosh” in the [[search]] field and click the <b>Whoosh Soft</b> card.", "Escribe “whoosh” en el campo [[search]] y pulsa la tarjeta <b>Whoosh Soft</b>."),
            T("În Resolve, mută cursorul (playhead) pe tăietură: <b>01:00:05:00</b>.", "In Resolve, park the cursor (playhead) on the cut: <b>01:00:05:00</b>.", "En Resolve, coloca el cursor (playhead) en el corte: <b>01:00:05:00</b>."),
            T("În panou, la [[track]] lasă <b>A1</b> și apasă [[place]].", "In the panel, leave [[track]] on <b>A1</b> and press [[place]].", "En el panel, deja [[track]] en <b>A1</b> y pulsa [[place]]."),
            T("Verifică: mesajul verde de jos și un clip nou pe A1, începând la 01:00:05:00.", "Check: the green message at the bottom and a new clip on A1 starting at 01:00:05:00.", "Comprueba: el mensaje verde de abajo y un clip nuevo en A1 que empieza en 01:00:05:00.")]),
    ("img", "placed", T("După [[place]]: mesajul de confirmare și cursorul sărit la finalul clipului.", "After [[place]]: the confirmation message and the cursor moved to the end of the clip.", "Tras [[place]]: el mensaje de confirmación y el cursor movido al final del clip.")),
    ("img", "tl_placed", T("Timeline-ul: clipul „Whoosh Soft” pe A1, începând exact la tăietura video.", "The timeline: the “Whoosh Soft” clip on A1, starting exactly at the video cut.", "El timeline: el clip “Whoosh Soft” en A1, empezando justo en el corte de vídeo.")),
    ("note", T("<b>Dacă ai greșit:</b> în Resolve apasă <b>Cmd+Z</b> (o plasare = un pas de anulare) sau selectează clipul și șterge-l. Panoul nu atinge fișierul sursă.", "<b>If you made a mistake:</b> in Resolve press <b>Cmd+Z</b> (one placement = one undo step) or select the clip and delete it. The panel never touches the source file.", "<b>Si te equivocas:</b> en Resolve pulsa <b>Cmd+Z</b> (una colocación = un paso de deshacer) o selecciona el clip y bórralo. El panel nunca toca el archivo de origen.")),
]))

CH.append((T("Instalare și cerințe", "Installation and requirements", "Instalación y requisitos"), [
    ("p", T("Pachetul oficial este un <b>SoundSFXPaste-0.2.0.pkg</b> semnat, de pe pagina proiectului sau din ultimul release de pe GitHub. Descarcă-l, deschide-l cu dublu-clic și urmează instalatorul (acceptă licența; macOS cere parola ta, pentru că panoul se instalează în folderul comun al pluginurilor Resolve).",
            "The official package is a signed <b>SoundSFXPaste-0.2.0.pkg</b>, from the project page or the latest GitHub release. Download it, double-click it and follow the installer (accept the license; macOS asks for your password because the panel installs into Resolve's shared plugin folder).",
            "El paquete oficial es un <b>SoundSFXPaste-0.2.0.pkg</b> firmado, desde la página del proyecto o la última release de GitHub. Descárgalo, ábrelo con doble clic y sigue el instalador (acepta la licencia; macOS pide tu contraseña porque el panel se instala en la carpeta común de plugins de Resolve).")),
    ("code", PLUG),
    ("tbl", [(T("DaVinci Resolve Studio", "DaVinci Resolve Studio", "DaVinci Resolve Studio"), T("Obligatoriu. Panourile Workflow Integration nu rulează în versiunea gratuită. Verificat cu Resolve Studio 21.2.", "Required. Workflow Integration panels do not run in the free version. Verified with Resolve Studio 21.2.", "Obligatorio. Los paneles Workflow Integration no funcionan en la versión gratuita. Verificado con Resolve Studio 21.2.")),
             (T("Python 3 (3.8 sau mai nou)", "Python 3 (3.8 or newer)", "Python 3 (3.8 o posterior)"), T("Obligatoriu pentru procesul local care vorbește cu Resolve. Instalează-l de pe python.org dacă lipsește; vezi capitolul Probleme.", "Required for the local helper that talks to Resolve. Install it from python.org if missing; see the Troubleshooting chapter.", "Obligatorio para el proceso local que habla con Resolve. Instálalo desde python.org si falta; consulta el capítulo de problemas.")),
             (T("Scripting extern: Local", "External scripting: Local", "Scripting externo: Local"), T("În Resolve: Preferences › General › External scripting using: <b>Local</b>.", "In Resolve: Preferences › General › External scripting using: <b>Local</b>.", "En Resolve: Preferences › General › External scripting using: <b>Local</b>.")),
             (T("Timeline fără drop-frame", "Non-drop-frame timeline", "Timeline sin drop-frame"), T("Plasarea e refuzată pe timeline-uri drop-frame (vezi Probleme).", "Placing is refused on drop-frame timelines (see Troubleshooting).", "La colocación se rechaza en timelines drop-frame (consulta Problemas)."))]),
    ("h2", T("Verificarea dependențelor", "Checking dependencies", "Comprobar las dependencias")),
    ("p", T("Deschide [[settings]] (roata din colțul de sus) și apasă [[depsOpen]]. Panoul listează Python 3, modulul de scripting Resolve, Resolve, proiectul deschis, timeline-ul activ și rata de cadre, fiecare cu bulină verde sau roșie și, la roșu, cu pasul de reparare. După ce repari ceva, apasă [[depsRecheck]].",
            "Open [[settings]] (the gear at the top) and press [[depsOpen]]. The panel lists Python 3, the Resolve scripting module, Resolve, the open project, the active timeline and the frame rate, each with a green or red dot and, if red, the fix. After fixing something, press [[depsRecheck]].",
            "Abre [[settings]] (la rueda de arriba) y pulsa [[depsOpen]]. El panel lista Python 3, el módulo de scripting de Resolve, Resolve, el proyecto abierto, el timeline activo y la frecuencia de fotogramas, cada uno con un punto verde o rojo y, en rojo, el modo de arreglarlo. Tras arreglar algo, pulsa [[depsRecheck]].")),
    ("img", "deps", T("Verificare & dependențe: totul verde înseamnă că placarea va funcționa.", "Check & dependencies: all green means placing will work.", "Comprobación y dependencias: todo en verde significa que colocar funcionará.")),
]))

CH.append((T("Interfața, pe scurt", "The interface at a glance", "La interfaz de un vistazo"), [
    ("p", T("Deschide panoul din <b>Workspace › Workflow Integrations › SoundSFXPaste</b>. Pe lângă cele patru file, are bara de jos cu tot ce ține de destinație.",
            "Open the panel from <b>Workspace › Workflow Integrations › SoundSFXPaste</b>. Besides the four tabs, it has a bottom bar with everything about the destination.",
            "Abre el panel desde <b>Workspace › Workflow Integrations › SoundSFXPaste</b>. Además de las cuatro pestañas, tiene una barra inferior con todo lo del destino.")),
    ("img", "folders", T("Panoul cu biblioteca demo încărcată. Sus: filele; stânga: biblioteca; jos: volum, densitate, pistă, cursor, [[trim]] și [[place]].", "The panel with the demo library loaded. Top: tabs; left: library; bottom: volume, density, track, cursor, [[trim]] and [[place]].", "El panel con la biblioteca demo cargada. Arriba: pestañas; izquierda: biblioteca; abajo: volumen, densidad, pista, cursor, [[trim]] y [[place]].")),
    ("tbl", [(T("[[tabFolders]]", "[[tabFolders]]", "[[tabFolders]]"), T("Toate sunetele din folderele tale, cu căutare și forme de undă.", "All the sounds in your folders, with search and waveforms.", "Todos los sonidos de tus carpetas, con búsqueda y formas de onda.")),
             (T("[[tabFav]] / [[tabRecent]]", "[[tabFav]] / [[tabRecent]]", "[[tabFav]] / [[tabRecent]]"), T("Sunetele marcate cu stea și ultimele plasate.", "Starred sounds and the last ones you placed.", "Sonidos con estrella y los últimos que colocaste.")),
             (T("[[tabAuto]]", "[[tabAuto]]", "[[tabAuto]]"), T("Patru rute: [[rRandom]], [[rReplace]], [[rMarkers]], [[rMap]].", "Four routes: [[rRandom]], [[rReplace]], [[rMarkers]], [[rMap]].", "Cuatro rutas: [[rRandom]], [[rReplace]], [[rMarkers]], [[rMap]].")),
             (T("[[pinOff]]", "[[pinOff]]", "[[pinOff]]"), T("Butonul cu pin din colțul de sus ține panoul deasupra ferestrei Resolve.", "The pin button at the top keeps the panel above the Resolve window.", "El botón de chincheta de arriba mantiene el panel sobre la ventana de Resolve.")),
             (T("[[track]] și cursor", "[[track]] and cursor", "[[track]] y cursor"), T("Pista țintă (A1, A2…), butonul + ([[addTrack]]) și, cu galben, timecode-ul cursorului Resolve: acolo cade sunetul.", "The target track (A1, A2…), the + button ([[addTrack]]) and, in yellow, the Resolve cursor's timecode: that is where the sound lands.", "La pista de destino (A1, A2…), el botón + ([[addTrack]]) y, en amarillo, el timecode del cursor de Resolve: ahí cae el sonido.")),
             (T("[[trim]] / [[place]]", "[[trim]] / [[place]]", "[[trim]] / [[place]]"), T("Scurtează înainte de plasare; plasează sunetul ales la cursor.", "Trim before placing; place the chosen sound at the cursor.", "Recortar antes de colocar; colocar el sonido elegido en el cursor."))]),
]))

CH.append((T("Foldere, căutare, forme de undă și ascultare", "Folders, search, waveforms and audition", "Carpetas, búsqueda, formas de onda y audición"), [
    ("h2", T("Adăugarea și scoaterea folderelor", "Adding and removing folders", "Añadir y quitar carpetas")),
    ("p", T("[[addFolder]] alege un folder; panoul îl citește recursiv (ignoră folderele ascunse) și arată sunetele în [[allSounds]]. Fiecare folder apare în coloana [[library]], cu numărul de sunete; cu butonul de scoatere ([[removeFolder]]) îl ștergi din bibliotecă, fără să atingi fișierele. [[refresh]] recitește folderele după ce adaugi fișiere noi.",
            "[[addFolder]] picks a folder; the panel reads it recursively (hidden folders are skipped) and lists the sounds under [[allSounds]]. Each folder shows in the [[library]] column with its sound count; the remove button ([[removeFolder]]) drops it from the library without touching any file. [[refresh]] rereads the folders after you add new files.",
            "[[addFolder]] elige una carpeta; el panel la lee de forma recursiva (omite las carpetas ocultas) y lista los sonidos en [[allSounds]]. Cada carpeta aparece en la columna [[library]] con su número de sonidos; el botón de quitar ([[removeFolder]]) la saca de la biblioteca sin tocar ningún archivo. [[refresh]] vuelve a leer las carpetas cuando añades archivos nuevos.")),
    ("h2", T("Căutare", "Search", "Búsqueda")),
    ("p", T("Câmpul [[search]] filtrează pe măsură ce scrii, după numele fișierului. Dacă nu găsești nimic apare „[[=noMatch]]”. Șterge textul ca să vezi din nou toate sunetele.",
            "The [[search]] field filters as you type, by file name. If nothing matches you see “[[=noMatch]]”. Clear the text to see everything again.",
            "El campo [[search]] filtra mientras escribes, por nombre de archivo. Si nada coincide ves “[[=noMatch]]”. Borra el texto para ver todo de nuevo.")),
    ("img", "search", T("Căutarea „whoosh” lasă un singur card; cardul ales are contur auriu.", "Searching “whoosh” leaves one card; the chosen card has a gold outline.", "Buscar “whoosh” deja una sola tarjeta; la tarjeta elegida tiene contorno dorado.")),
    ("h2", T("Forma de undă, ascultare și volum", "Waveform, audition and volume", "Forma de onda, audición y volumen")),
    ("p", T("Fiecare card arată forma de undă, durata, frecvența de eșantionare și canalele. Butonul ► din colțul cardului ([[audition]]) redă sunetul în panou, cu volumul reglat din bara de jos ([[volume]]); apasă din nou ca să oprești. Fiind o audiție locală, sunetul iese pe ieșirea audio a Mac-ului, nu din Resolve. Cu [[hover]] din [[settings]], sunetul începe să se audă când ții cursorul mouse-ului pe card. Al doilea cursor din bara de jos ([[density]]) mărește sau micșorează cardurile.",
            "Each card shows the waveform, length, sample rate and channels. The ► button on the card ([[audition]]) plays the sound inside the panel, at the volume set in the bottom bar ([[volume]]); press again to stop. It is a local audition, so the sound comes out of the Mac's audio output, not from Resolve. With [[hover]] in [[settings]], the sound starts when you rest the mouse on a card. The second slider in the bottom bar ([[density]]) makes the cards larger or smaller.",
            "Cada tarjeta muestra la forma de onda, la duración, la frecuencia de muestreo y los canales. El botón ► de la esquina ([[audition]]) reproduce el sonido dentro del panel, con el volumen de la barra inferior ([[volume]]); púlsalo otra vez para detenerlo. Es una audición local, así que el sonido sale por la salida de audio del Mac, no desde Resolve. Con [[hover]] en [[settings]], el sonido empieza al dejar el ratón sobre la tarjeta. El segundo control de la barra inferior ([[density]]) agranda o reduce las tarjetas.")),
    ("ex", T("Ascultă înainte să alegi", "Audition before you choose", "Escucha antes de elegir"),
     T("Ascultă Whoosh Soft și Ding Bright și decide care se potrivește.", "Listen to Whoosh Soft and Ding Bright and decide which fits.", "Escucha Whoosh Soft y Ding Bright y decide cuál encaja."),
     T("Apasă ► pe fiecare card (în colțul din stânga sus al cardului).", "Press ► on each card (top-left corner of the card).", "Pulsa ► en cada tarjeta (esquina superior izquierda)."),
     T("Cardul în redare arată un indicator; sunetul se aude pe ieșirea Mac-ului, iar în timeline nu se schimbă nimic.", "The playing card shows an indicator; the sound is heard on the Mac's output and nothing changes in the timeline.", "La tarjeta en reproducción muestra un indicador; el sonido se oye por la salida del Mac y no cambia nada en el timeline."),
     T("Apasă din nou ► sau alege alt sunet; audiția nu modifică nimic.", "Press ► again or pick another sound; auditioning changes nothing.", "Pulsa ► de nuevo o elige otro sonido; escuchar no cambia nada.")),
    ("note", T("Greutatea o ține cache-ul formelor de undă: [[clearCache]] din [[settings]] îl golește. Un fișier care nu se poate decoda arată „[[=ERR_DECODE]]”.", "The waveform cache keeps this fast: [[clearCache]] in [[settings]] empties it. A file that cannot be decoded shows “[[=ERR_DECODE]]”.", "La caché de formas de onda lo mantiene rápido: [[clearCache]] en [[settings]] lo vacía. Un archivo que no se puede decodificar muestra “[[=ERR_DECODE]]”.")),
]))

CH.append((T("Favorite, Recente, limbă și „ține deasupra”", "Favorites, Recent, language and Keep on top", "Favoritos, Recientes, idioma y «Mantener encima»"), [
    ("p", T("Steaua de pe card ([[favorite]]) mută sunetul în fila [[tabFav]]; apasă din nou ca să-l scoți. Fila [[tabRecent]] păstrează sunetele pe care le-ai plasat, cele mai noi primele. Ambele liste se păstrează între sesiuni.",
            "The star on a card ([[favorite]]) moves the sound into the [[tabFav]] tab; press it again to remove it. The [[tabRecent]] tab keeps the sounds you placed, newest first. Both lists persist between sessions.",
            "La estrella de la tarjeta ([[favorite]]) lleva el sonido a la pestaña [[tabFav]]; púlsala de nuevo para quitarlo. La pestaña [[tabRecent]] guarda los sonidos que colocaste, los más nuevos primero. Ambas listas se conservan entre sesiones.")),
    ("img", "fav", T("Fila [[tabFav]] cu două sunete marcate.", "The [[tabFav]] tab with two starred sounds.", "La pestaña [[tabFav]] con dos sonidos marcados.")),
    ("img", "recent", T("Fila [[tabRecent]]: ultimele sunete plasate.", "The [[tabRecent]] tab: the last sounds placed.", "La pestaña [[tabRecent]]: los últimos sonidos colocados.")),
    ("h2", T("Limba panoului", "Panel language", "Idioma del panel")),
    ("p", T("În [[settings]], la [[language]], alegi română, engleză sau spaniolă. Schimbarea se aplică imediat; mesajele deja afișate rămân în limba în care au apărut.",
            "In [[settings]], under [[language]], choose Romanian, English or Spanish. The change applies immediately; messages already on screen stay in the language they appeared in.",
            "En [[settings]], en [[language]], elige rumano, inglés o español. El cambio se aplica al instante; los mensajes que ya están en pantalla se quedan en el idioma en que aparecieron.")),
    ("img", "settings", T("Setări: limbă, previzualizare la hover, avertizare la sunete lungi, golire cache, verificare dependențe, versiune și dezinstalare.", "Settings: language, preview on hover, long-sound warning, cache clearing, dependency check, version and uninstall.", "Ajustes: idioma, vista previa al pasar el ratón, aviso de sonidos largos, vaciado de caché, comprobación de dependencias, versión y desinstalación.")),
    ("h2", T("Ține deasupra", "Keep on top", "Mantener encima")),
    ("p", T("Butonul cu pin ([[pinOff]]) ține panoul deasupra ferestrei Resolve, ca să nu dispară când dai clic în timeline. Apasă-l din nou ca să-l eliberezi. Setarea se păstrează.",
            "The pin button ([[pinOff]]) keeps the panel above the Resolve window so it does not vanish when you click in the timeline. Press it again to release it. The setting is remembered.",
            "El botón de chincheta ([[pinOff]]) mantiene el panel sobre la ventana de Resolve para que no desaparezca al hacer clic en el timeline. Púlsalo de nuevo para soltarlo. El ajuste se recuerda.")),
]))

CH.append((T("Plasarea: pista, cursorul, un cadru exact", "Placing: the track, the cursor, an exact frame", "Colocar: la pista, el cursor, un fotograma exacto"), [
    ("p", T("Sunetul cade pe pista aleasă la [[track]], la poziția cursorului Resolve (timecode-ul galben din bara de jos). Ordinea e mereu aceeași: alegi sunetul, alegi pista, pui cursorul unde vrei și apeși [[place]] (sau butonul [[placeHere]] de pe card).",
            "The sound lands on the track chosen in [[track]], at the Resolve cursor position (the yellow timecode in the bottom bar). The order never changes: choose the sound, choose the track, park the cursor where you want it, press [[place]] (or the [[placeHere]] button on the card).",
            "El sonido cae en la pista elegida en [[track]], en la posición del cursor de Resolve (el timecode amarillo de la barra inferior). El orden no cambia: eliges el sonido, eliges la pista, colocas el cursor donde quieres y pulsas [[place]] (o el botón [[placeHere]] de la tarjeta).")),
    ("h2", T("Alegerea pistei", "Choosing the track", "Elegir la pista")),
    ("p", T("Meniul [[track]] listează pistele audio ale timeline-ului; pistele blocate sunt marcate ([[locked]]). [[addTrack]] (butonul +) adaugă o pistă nouă. Dacă pista aleasă are deja un clip în acel loc, plasarea e refuzată, nu suprapusă (vezi Probleme).",
            "The [[track]] menu lists the timeline's audio tracks; locked tracks are marked ([[locked]]). [[addTrack]] (the + button) adds a new track. If the chosen track already has a clip at that spot, the placement is refused, not overlapped (see Troubleshooting).",
            "El menú [[track]] lista las pistas de audio del timeline; las pistas bloqueadas se marcan ([[locked]]). [[addTrack]] (el botón +) añade una pista nueva. Si la pista elegida ya tiene un clip en ese punto, la colocación se rechaza, no se superpone (consulta Problemas).")),
    ("h2", T("Poziția: cursor sau cadru exact", "Position: cursor or exact frame", "Posición: cursor o fotograma exacto")),
    ("p", T("Poziția este cursorul Resolve. Pentru un cadru exact, scrie timecode-ul în Resolve (câmpul de timecode al timeline-ului) sau mută cursorul cu săgețile, apoi verifică în panou valoarea galbenă înainte de [[place]]. După plasare, cursorul sare la finalul clipului nou, ca să poți lipi sunetele unul după altul.",
            "The position is the Resolve cursor. For an exact frame, type the timecode in Resolve (the timeline's timecode field) or step the cursor with the arrow keys, then check the yellow value in the panel before [[place]]. After placing, the cursor jumps to the end of the new clip, so you can lay sounds one after another.",
            "La posición es el cursor de Resolve. Para un fotograma exacto, escribe el timecode en Resolve (el campo de timecode del timeline) o mueve el cursor con las flechas y comprueba el valor amarillo del panel antes de [[place]]. Tras colocar, el cursor salta al final del clip nuevo, para que puedas encadenar sonidos.")),
    ("ex", T("Un „whoosh” exact pe o tăietură", "A whoosh exactly on a cut", "Un whoosh exacto en un corte"),
     T("Whoosh Soft (1,4 s) pe A1, începând la tăietura video 01:00:05:00.", "Whoosh Soft (1.4 s) on A1, starting at the video cut 01:00:05:00.", "Whoosh Soft (1,4 s) en A1, empezando en el corte de vídeo 01:00:05:00."),
     T("Selectează cardul Whoosh Soft; în Resolve pune cursorul pe 01:00:05:00; în panou verifică [[track]] = A1; apasă [[place]].", "Select the Whoosh Soft card; in Resolve park the cursor on 01:00:05:00; in the panel check [[track]] = A1; press [[place]].", "Selecciona la tarjeta Whoosh Soft; en Resolve coloca el cursor en 01:00:05:00; en el panel comprueba [[track]] = A1; pulsa [[place]]."),
     T("Mesaj verde „Whoosh Soft” plasat pe A1 la 01:00:05:00 (1,4 s); clip nou pe A1; cursorul sare la 01:00:06:09 (33 de cadre la 24 fps).", "Green message: “Whoosh Soft” placed on A1 at 01:00:05:00 (1.4 s); a new clip on A1; the cursor jumps to 01:00:06:09 (33 frames at 24 fps).", "Mensaje verde: “Whoosh Soft” colocado en A1 en 01:00:05:00 (1,4 s); clip nuevo en A1; el cursor salta a 01:00:06:09 (33 fotogramas a 24 fps)."),
     T("Cmd+Z în Resolve, sau șterge clipul. Dacă l-ai pus pe pista greșită, anulează și repetă cu altă pistă.", "Cmd+Z in Resolve, or delete the clip. If it went on the wrong track, undo and repeat with another track.", "Cmd+Z en Resolve, o borra el clip. Si fue a la pista equivocada, deshaz y repite con otra pista.")),
    ("h2", T("Plasare verificată, nu presupusă", "Verified placement, not assumed", "Colocación verificada, no supuesta")),
    ("p", T("Panoul planifică plasarea, o scrie în Resolve și o <b>verifică</b> după scriere; dacă rezultatul diferă de plan, anulează și arată o eroare ([[=ERR_VERIFY_MISMATCH]]). Un sunet mai lung decât limita din [[reviewWarn]] cere o a doua apăsare pe [[place]] ca să confirmi. Trasul unui card direct în timeline este în cod, dar <b>nu este verificat</b> în această versiune: folosește butoanele.",
            "The panel plans the placement, writes it to Resolve and <b>verifies</b> it afterwards; if the result differs from the plan it rolls back and shows an error ([[=ERR_VERIFY_MISMATCH]]). A sound longer than the limit in [[reviewWarn]] needs a second press of [[place]] to confirm. Dragging a card straight into the timeline exists in the code but is <b>not verified</b> in this version: use the buttons.",
            "El panel planifica la colocación, la escribe en Resolve y la <b>verifica</b> después; si el resultado difiere del plan, la deshace y muestra un error ([[=ERR_VERIFY_MISMATCH]]). Un sonido más largo que el límite de [[reviewWarn]] pide una segunda pulsación de [[place]] para confirmar. Arrastrar una tarjeta directamente al timeline existe en el código pero <b>no está verificado</b> en esta versión: usa los botones.")),
]))

CH.append((T("Scurtarea unui sunet ([[trim]])", "Trimming a sound ([[trim]])", "Recortar un sonido ([[trim]])"), [
    ("p", T("[[trim]] deschide „[[=trimTitle]]”: forma de undă a sunetului ales, pe care tragi un interval. Doar acea porțiune ajunge pe timeline; fișierul rămâne neatins. Sub undă vezi intervalul în secunde.",
            "[[trim]] opens “[[=trimTitle]]”: the chosen sound's waveform, on which you drag a range. Only that portion reaches the timeline; the file stays untouched. Under the waveform you see the range in seconds.",
            "[[trim]] abre “[[=trimTitle]]”: la forma de onda del sonido elegido, sobre la que arrastras un rango. Solo esa porción llega al timeline; el archivo no se toca. Bajo la onda ves el rango en segundos.")),
    ("img", "trim", T("Dialogul de scurtare: forma de undă și, sub ea, intervalul ales.", "The trim dialog: the waveform and, under it, the chosen range.", "El diálogo de recorte: la forma de onda y, debajo, el rango elegido.")),
    ("ex", T("Doar mijlocul unui „riser”", "Only the middle of a riser", "Solo el centro de un riser"),
     T("Din Riser Short (2,5 s) pui pe timeline doar secunda dintre 0,8 s și 1,8 s, la 01:00:03:00 pe A1.", "From Riser Short (2.5 s) place only the second between 0.8 s and 1.8 s, at 01:00:03:00 on A1.", "De Riser Short (2,5 s) coloca solo el segundo entre 0,8 s y 1,8 s, en 01:00:03:00 en A1."),
     T("Selectează Riser Short; cursorul Resolve pe 01:00:03:00; apasă [[trim]]; trage pe undă de la 0,8 s la 1,8 s; verifică numerele de sub undă; apasă [[trimPlace]].", "Select Riser Short; Resolve cursor on 01:00:03:00; press [[trim]]; drag on the waveform from 0.8 s to 1.8 s; check the numbers under the wave; press [[trimPlace]].", "Selecciona Riser Short; cursor de Resolve en 01:00:03:00; pulsa [[trim]]; arrastra sobre la onda de 0,8 s a 1,8 s; comprueba los números bajo la onda; pulsa [[trimPlace]]."),
     T("Un clip scurt pe A1 la 01:00:03:00, cu lungimea intervalului ales (cursorul sare la capătul lui).", "A short clip on A1 at 01:00:03:00, as long as the chosen range (the cursor jumps to its end).", "Un clip corto en A1 en 01:00:03:00, con la duración del rango elegido (el cursor salta a su final)."),
     T("[[clearSel]] șterge intervalul ca să tragi altul; [[cancel]] (sau Esc) închide fără să plaseze; după plasare, Cmd+Z în Resolve.", "[[clearSel]] clears the range so you can drag another; [[cancel]] (or Esc) closes without placing; after placing, Cmd+Z in Resolve.", "[[clearSel]] borra el rango para arrastrar otro; [[cancel]] (o Esc) cierra sin colocar; tras colocar, Cmd+Z en Resolve.")),
    ("note", T("Verifică întotdeauna numerele de sub undă înainte de [[trimPlace]]: ele sunt intervalul care se va plasa. Un clic fără tragere nu creează interval.", "Always check the numbers under the waveform before [[trimPlace]]: they are the range that will be placed. A click without dragging does not create a range.", "Comprueba siempre los números bajo la onda antes de [[trimPlace]]: son el rango que se colocará. Un clic sin arrastrar no crea rango.")),
]))

CH.append((T("Înlocuirea unui sunet ([[rReplace]])", "Replacing a sound ([[rReplace]])", "Reemplazar un sonido ([[rReplace]])"), [
    ("p", T("Ruta [[rReplace]] din [[tabAuto]] schimbă clipuri deja puse cu sunetul ales în bibliotecă, păstrând poziția. Alegi mai întâi sunetul nou (fila [[tabFolders]]), apoi intri în [[tabAuto]] › [[rReplace]]. La [[repTarget]] alegi ce se înlocuiește: [[repSelected]] (clipurile selectate în Resolve) sau [[repCursor]]. Bifa [[repKeep]] păstrează durata întreagă a sunetului nou, în loc de durata clipului vechi.",
            "The [[rReplace]] route in [[tabAuto]] swaps clips already on the timeline for the sound chosen in the library, keeping the position. Choose the new sound first (the [[tabFolders]] tab), then go to [[tabAuto]] › [[rReplace]]. Under [[repTarget]] pick what gets replaced: [[repSelected]] (the clips selected in Resolve) or [[repCursor]]. The [[repKeep]] checkbox keeps the new sound's whole length instead of the old clip's length.",
            "La ruta [[rReplace]] de [[tabAuto]] cambia clips que ya están en el timeline por el sonido elegido en la biblioteca, manteniendo la posición. Elige primero el sonido nuevo (pestaña [[tabFolders]]) y luego ve a [[tabAuto]] › [[rReplace]]. En [[repTarget]] eliges qué se reemplaza: [[repSelected]] (los clips seleccionados en Resolve) o [[repCursor]]. La casilla [[repKeep]] conserva la duración completa del sonido nuevo en lugar de la del clip antiguo.")),
    ("p", T("Apasă mereu mai întâi [[repPlan]]: tabelul arată ce clip se înlocuiește, pe ce pistă, la ce timecode și cu ce durată, cu „OK” sau motivul refuzului. Abia apoi apeși [[repApply]].",
            "Always press [[repPlan]] first: the table shows which clip gets replaced, on which track, at what timecode and how long, with “OK” or the reason it is refused. Only then press [[repApply]].",
            "Pulsa siempre primero [[repPlan]]: la tabla muestra qué clip se reemplaza, en qué pista, en qué timecode y con qué duración, con “OK” o el motivo del rechazo. Solo entonces pulsa [[repApply]].")),
    ("img", "rep_prev", T("Previzualizarea: Whoosh Soft de pe A1 la 01:00:05:00 va fi înlocuit.", "The preview: Whoosh Soft on A1 at 01:00:05:00 will be replaced.", "La vista previa: Whoosh Soft en A1 en 01:00:05:00 será reemplazado.")),
    ("ex", T("Schimbă un sunet păstrând poziția", "Swap a sound keeping its position", "Cambiar un sonido manteniendo la posición"),
     T("Înlocuiești Whoosh Soft de la tăietură cu Ding Bright, pe aceeași pistă și la același timecode.", "Replace the Whoosh Soft at the cut with Ding Bright, on the same track and at the same timecode.", "Reemplazar el Whoosh Soft del corte por Ding Bright, en la misma pista y en el mismo timecode."),
     T("Pune cursorul Resolve pe clip (de ex. 01:00:05:12); în [[tabFolders]] alege Ding Bright; în [[tabAuto]] › [[rReplace]] setează [[repTarget]] = [[repCursor]]; apasă [[repPlan]], citește tabelul, apoi [[repApply]].", "Park the Resolve cursor on the clip (e.g. 01:00:05:12); in [[tabFolders]] pick Ding Bright; in [[tabAuto]] › [[rReplace]] set [[repTarget]] = [[repCursor]]; press [[repPlan]], read the table, then [[repApply]].", "Coloca el cursor de Resolve sobre el clip (p. ej. 01:00:05:12); en [[tabFolders]] elige Ding Bright; en [[tabAuto]] › [[rReplace]] pon [[repTarget]] = [[repCursor]]; pulsa [[repPlan]], lee la tabla y luego [[repApply]]."),
     T("Mesajul „[[=repDone|n=1]]”; pe A1, la 01:00:05:00, clipul se numește acum Ding Bright.", "The message “[[=repDone|n=1]]”; on A1 at 01:00:05:00 the clip is now named Ding Bright.", "El mensaje “[[=repDone|n=1]]”; en A1, en 01:00:05:00, el clip se llama ahora Ding Bright."),
     T("Cmd+Z în Resolve readuce clipul vechi. Dacă tabelul de previzualizare nu e cel dorit, nu apăsa [[repApply]]: schimbă [[repTarget]] sau mută cursorul.", "Cmd+Z in Resolve brings back the old clip. If the preview table is not what you want, do not press [[repApply]]: change [[repTarget]] or move the cursor.", "Cmd+Z en Resolve devuelve el clip antiguo. Si la tabla de vista previa no es la que quieres, no pulses [[repApply]]: cambia [[repTarget]] o mueve el cursor.")),
    ("img", "rep_done", T("După [[repApply]], tabelul rămâne și mesajul confirmă.", "After [[repApply]] the table stays and the message confirms.", "Tras [[repApply]], la tabla permanece y el mensaje confirma.")),
    ("img", "tl_rep", T("Timeline-ul: clipul înlocuit, în același loc.", "The timeline: the replaced clip, in the same place.", "El timeline: el clip reemplazado, en el mismo sitio.")),
]))

CH.append((T("Markere și etichete ([[rMarkers]])", "Markers and tags ([[rMarkers]])", "Marcadores y etiquetas ([[rMarkers]])"), [
    ("p", T("[[rMarkers]] listează markerele timeline-ului cu timecode, nume și etichete. Câmpul [[mkRename]] redenumește markerul (se salvează când părăsești câmpul), iar în [[mkTags]] scrii o etichetă și apeși Enter ([[mkAddTag]]); fiecare etichetă apare ca o bulă cu × pentru ștergere. Coșul de pe rând șterge markerul ([[mkDelete]]); [[mkTrash]] le șterge pe toate, după o confirmare ([[=mkYes]]). Cu butonul de reîncărcare din colț recitești markerele.",
            "[[rMarkers]] lists the timeline's markers with timecode, name and tags. The [[mkRename]] field renames the marker (saved when you leave the field), and in [[mkTags]] you type a tag and press Enter ([[mkAddTag]]); each tag shows as a bubble with × to remove it. The bin on a row deletes the marker ([[mkDelete]]); [[mkTrash]] deletes them all, after a confirmation ([[=mkYes]]). The reload button in the corner rereads the markers.",
            "[[rMarkers]] lista los marcadores del timeline con timecode, nombre y etiquetas. El campo [[mkRename]] renombra el marcador (se guarda al salir del campo) y en [[mkTags]] escribes una etiqueta y pulsas Enter ([[mkAddTag]]); cada etiqueta aparece como una burbuja con × para quitarla. La papelera de la fila borra el marcador ([[mkDelete]]); [[mkTrash]] los borra todos, tras una confirmación ([[=mkYes]]). El botón de recarga de la esquina vuelve a leer los marcadores.")),
    ("img", "markers", T("Markerele timeline-ului: primul redenumit „Door slam” și etichetat „door”.", "The timeline's markers: the first renamed “Door slam” and tagged “door”.", "Los marcadores del timeline: el primero renombrado “Door slam” y etiquetado “door”.")),
    ("ex", T("Pregătește markerele înainte de umplere", "Prepare markers before filling", "Preparar los marcadores antes de rellenar"),
     T("Pe un timeline cu trei markere (Hit 1/2/3 la 01:00:01:00, 01:00:03:00, 01:00:07:00) dai primului un nume clar și o etichetă.", "On a timeline with three markers (Hit 1/2/3 at 01:00:01:00, 01:00:03:00, 01:00:07:00) give the first one a clear name and a tag.", "En un timeline con tres marcadores (Hit 1/2/3 en 01:00:01:00, 01:00:03:00, 01:00:07:00) dale al primero un nombre claro y una etiqueta."),
     T("[[tabAuto]] › [[rMarkers]]; la primul rând scrie „Door slam” în [[mkRename]] și apasă Tab; în [[mkTags]] scrie „door” și apasă Enter.", "[[tabAuto]] › [[rMarkers]]; on the first row type “Door slam” in [[mkRename]] and press Tab; in [[mkTags]] type “door” and press Enter.", "[[tabAuto]] › [[rMarkers]]; en la primera fila escribe “Door slam” en [[mkRename]] y pulsa Tab; en [[mkTags]] escribe “door” y pulsa Enter."),
     T("Mesajul „[[=mkDone]]”; rândul arată noul nume și bula „door”; markerul din timeline are numele nou.", "The message “[[=mkDone]]”; the row shows the new name and the “door” bubble; the timeline marker has the new name.", "El mensaje “[[=mkDone]]”; la fila muestra el nuevo nombre y la burbuja “door”; el marcador del timeline tiene el nombre nuevo."),
     T("Rescrie numele, sau apasă × pe etichetă. Ștergerea unui marker nu se anulează din panou: folosește Cmd+Z în Resolve imediat după.", "Retype the name, or press × on the tag. Deleting a marker cannot be undone from the panel: use Cmd+Z in Resolve right after.", "Reescribe el nombre o pulsa × en la etiqueta. Borrar un marcador no se deshace desde el panel: usa Cmd+Z en Resolve justo después.")),
]))

CH.append((T("Umplere aleatorie ([[rRandom]])", "Random fill ([[rRandom]])", "Relleno aleatorio ([[rRandom]])"), [
    ("p", T("[[rRandom]] pune pe fiecare marker al timeline-ului câte un sunet scurt ales la întâmplare. [[fillSource]] stabilește sursa ([[fillLib]] sau [[fillFav]]); [[fillMax]] elimină sunetele mai lungi decât limita. [[fillPlan]] arată planul fără să scrie nimic; [[fillReshuffle]] trage alte sunete; [[fillApply|n=3]] scrie planul pe pista aleasă în bara de jos.",
            "[[rRandom]] puts a randomly chosen short sound on every marker of the timeline. [[fillSource]] sets the source ([[fillLib]] or [[fillFav]]); [[fillMax]] drops sounds longer than the limit. [[fillPlan]] shows the plan without writing anything; [[fillReshuffle]] draws different sounds; [[fillApply|n=3]] writes the plan to the track chosen in the bottom bar.",
            "[[rRandom]] pone en cada marcador del timeline un sonido corto elegido al azar. [[fillSource]] fija el origen ([[fillLib]] o [[fillFav]]); [[fillMax]] descarta sonidos más largos que el límite. [[fillPlan]] muestra el plan sin escribir nada; [[fillReshuffle]] saca otros sonidos; [[fillApply|n=3]] escribe el plan en la pista elegida en la barra inferior.")),
    ("img", "fill_plan", T("Planul: trei markere, trei sunete, toate „OK”.", "The plan: three markers, three sounds, all “OK”.", "El plan: tres marcadores, tres sonidos, todos “OK”.")),
    ("ex", T("Completează trei markere dintr-un foc", "Fill three markers in one go", "Rellenar tres marcadores de una vez"),
     T("Un sunet scurt (maxim 5 s) pe fiecare dintre cele trei markere, pe A1.", "A short sound (max 5 s) on each of the three markers, on A1.", "Un sonido corto (máx. 5 s) en cada uno de los tres marcadores, en A1."),
     T("Pista A1 în bara de jos; [[tabAuto]] › [[rRandom]]; [[fillSource]] = [[fillLib]]; [[fillMax]] = 5; apasă [[fillPlan]]; dacă nu-ți place, [[fillReshuffle]]; apoi [[fillApply|n=3]].", "Track A1 in the bottom bar; [[tabAuto]] › [[rRandom]]; [[fillSource]] = [[fillLib]]; [[fillMax]] = 5; press [[fillPlan]]; if you do not like it, [[fillReshuffle]]; then [[fillApply|n=3]].", "Pista A1 en la barra inferior; [[tabAuto]] › [[rRandom]]; [[fillSource]] = [[fillLib]]; [[fillMax]] = 5; pulsa [[fillPlan]]; si no te gusta, [[fillReshuffle]]; luego [[fillApply|n=3]]."),
     T("Mesajul „Filled 3 markers on A1” (în limba panoului) și trei clipuri pe A1, câte unul la fiecare marker.", "The message “Filled 3 markers on A1” and three clips on A1, one at each marker.", "El mensaje “Filled 3 markers on A1” (en el idioma del panel) y tres clips en A1, uno en cada marcador."),
     T("Cmd+Z de trei ori în Resolve (un pas per clip) sau selectează cele trei clipuri și șterge-le. Alt rezultat se obține cu [[fillReshuffle]] înainte de aplicare.", "Cmd+Z three times in Resolve (one step per clip) or select the three clips and delete them. A different result comes from [[fillReshuffle]] before applying.", "Cmd+Z tres veces en Resolve (un paso por clip) o selecciona los tres clips y bórralos. Otro resultado se obtiene con [[fillReshuffle]] antes de aplicar.")),
    ("img", "fill_done", T("După aplicare, planul rămâne vizibil.", "After applying, the plan stays visible.", "Tras aplicar, el plan sigue visible.")),
    ("img", "tl_fill", T("Timeline-ul: câte un clip la fiecare marker.", "The timeline: one clip at each marker.", "El timeline: un clip en cada marcador.")),
    ("note", T("Cu [[fillMax]] mic și markere dese, verifică întâi [[fillPlan]]: „[[=fillNoSounds]]” înseamnă că nu există sunete suficient de scurte în sursa aleasă.", "With a small [[fillMax]] and dense markers, check [[fillPlan]] first: “[[=fillNoSounds]]” means no sound in the chosen source is short enough.", "Con un [[fillMax]] pequeño y marcadores densos, revisa antes [[fillPlan]]: “[[=fillNoSounds]]” significa que ningún sonido del origen elegido es lo bastante corto.")),
]))

CH.append((T("Asociere rapidă ([[rMap]])", "Rapid mapping ([[rMap]])", "Mapeo rápido ([[rMap]])"), [
    ("p", T("[[rMap]] trece prin markere unul câte unul: alegi un sunet, el se plasează pe markerul curent, iar cursorul sare la următorul. Apeși [[mapStart]]; bara de sus arată markerul curent („Targeting … (1/3)”) cu butoanele [[mapPrev]], [[mapSkip]] și [[mapExit]]. Treci în fila [[tabFolders]], alegi un card și apeși [[place]]. La final mesajul „[[=mapDone|n=3]]”.",
            "[[rMap]] steps through the markers one at a time: you pick a sound, it is placed on the current marker, and the cursor jumps to the next. Press [[mapStart]]; the bar at the top shows the current marker (“Targeting … (1/3)”) with the [[mapPrev]], [[mapSkip]] and [[mapExit]] buttons. Go to the [[tabFolders]] tab, choose a card and press [[place]]. At the end you get “[[=mapDone|n=3]]”.",
            "[[rMap]] recorre los marcadores de uno en uno: eliges un sonido, se coloca en el marcador actual y el cursor salta al siguiente. Pulsa [[mapStart]]; la barra superior muestra el marcador actual (“Targeting … (1/3)”) con los botones [[mapPrev]], [[mapSkip]] y [[mapExit]]. Ve a la pestaña [[tabFolders]], elige una tarjeta y pulsa [[place]]. Al final aparece “[[=mapDone|n=3]]”.")),
    ("img", "map_start", T("Maparea pornită: țintă „Door slam (1/3)”, la 01:00:01:00.", "Mapping started: target “Door slam (1/3)” at 01:00:01:00.", "Mapeo iniciado: destino “Door slam (1/3)” en 01:00:01:00.")),
    ("ex", T("Un sunet pe fiecare marker, la alegere", "A sound on each marker, your choice", "Un sonido en cada marcador, a tu elección"),
     T("Ding Bright pe primul marker, Impact Low pe al doilea, Whoosh Soft pe al treilea, pe pista A2.", "Ding Bright on the first marker, Impact Low on the second, Whoosh Soft on the third, on track A2.", "Ding Bright en el primer marcador, Impact Low en el segundo, Whoosh Soft en el tercero, en la pista A2."),
     T("Alege pista A2; [[tabAuto]] › [[rMap]] › [[mapStart]]; în [[tabFolders]] apasă un card, apoi [[place]]; repetă pentru fiecare marker; [[mapSkip]] sare peste unul.", "Choose track A2; [[tabAuto]] › [[rMap]] › [[mapStart]]; in [[tabFolders]] click a card, then [[place]]; repeat for each marker; [[mapSkip]] jumps over one.", "Elige la pista A2; [[tabAuto]] › [[rMap]] › [[mapStart]]; en [[tabFolders]] pulsa una tarjeta y luego [[place]]; repite en cada marcador; [[mapSkip]] se salta uno."),
     T("După fiecare [[place]], mesajul „Placed … on A2 at 01:00:01:00”, iar ținta trece la markerul următor; la final „All 3 markers visited”.", "After each [[place]], the message “Placed … on A2 at 01:00:01:00” and the target moves to the next marker; at the end “All 3 markers visited”.", "Tras cada [[place]], el mensaje “Placed … on A2 at 01:00:01:00” y el destino pasa al siguiente marcador; al final “All 3 markers visited”."),
     T("[[mapPrev]] revine la markerul anterior pentru a plasa din nou; [[mapExit]] oprește maparea. Un clip greșit se anulează cu Cmd+Z în Resolve.", "[[mapPrev]] goes back to the previous marker to place again; [[mapExit]] stops mapping. A wrong clip is undone with Cmd+Z in Resolve.", "[[mapPrev]] vuelve al marcador anterior para colocar otra vez; [[mapExit]] detiene el mapeo. Un clip equivocado se deshace con Cmd+Z en Resolve.")),
    ("img", "map_next", T("După prima plasare, ținta e „Hit 2 (2/3)”.", "After the first placement the target is “Hit 2 (2/3)”.", "Tras la primera colocación, el destino es “Hit 2 (2/3)”.")),
    ("img", "tl_map", T("Timeline-ul: sunete pe A2, la markere.", "The timeline: sounds on A2, at the markers.", "El timeline: sonidos en A2, en los marcadores.")),
    ("note", T("Dacă o plasare e refuzată (pistă ocupată), ținta rămâne pe același marker: schimbă pista sau sari peste.", "If a placement is refused (busy track), the target stays on the same marker: change the track or skip.", "Si se rechaza una colocación (pista ocupada), el destino se queda en el mismo marcador: cambia de pista o sáltalo.")),
]))

CH.append((T("Probleme întâlnite și soluții", "Troubleshooting from real situations", "Problemas habituales y soluciones"), [
    ("tbl", [
        (T("Pista ocupată sau blocată", "Busy or locked track", "Pista ocupada o bloqueada"), T("Mesaje: „[[=ERR_TRACK_BUSY]]” / „[[=ERR_TRACK_LOCKED]]”. Alege altă pistă sau altă poziție, ori deblochează pista în Resolve (lacătul din antetul pistei). Panoul nu suprapune clipuri.", "Messages: “[[=ERR_TRACK_BUSY]]” / “[[=ERR_TRACK_LOCKED]]”. Pick another track or position, or unlock the track in Resolve (the padlock in the track header). The panel never overlaps clips.", "Mensajes: “[[=ERR_TRACK_BUSY]]” / “[[=ERR_TRACK_LOCKED]]”. Elige otra pista u otra posición, o desbloquea la pista en Resolve (el candado de la cabecera de pista). El panel nunca superpone clips.")),
        (T("Resolve refuză plasarea", "Resolve refuses the placement", "Resolve rechaza la colocación"), T("Mesaje: „[[=placeRefused]]” sau „[[=ERR_RESOLVE_REFUSED]]”. Verifică pista și poziția din panou, apoi încearcă din nou; dacă se repetă, deschide [[openLog]] și verifică dacă timeline-ul activ s-a schimbat („[[=ERR_IDENTITY_MISMATCH]]”: nu s-a scris nimic). La „[[=ERR_VERIFY_MISMATCH]]” plasarea a fost anulată: verifică timeline-ul.", "Messages: “[[=placeRefused]]” or “[[=ERR_RESOLVE_REFUSED]]”. Check the track and position in the panel, then try again; if it repeats, open [[openLog]] and check whether the active timeline changed (“[[=ERR_IDENTITY_MISMATCH]]”: nothing was written). On “[[=ERR_VERIFY_MISMATCH]]” the placement was rolled back: check the timeline.", "Mensajes: “[[=placeRefused]]” o “[[=ERR_RESOLVE_REFUSED]]”. Comprueba la pista y la posición en el panel e inténtalo de nuevo; si se repite, abre [[openLog]] y comprueba si cambió el timeline activo (“[[=ERR_IDENTITY_MISMATCH]]”: no se escribió nada). Con “[[=ERR_VERIFY_MISMATCH]]” la colocación se deshizo: revisa el timeline.")),
        (T("Panoul nu se conectează", "The panel does not connect", "El panel no se conecta"), T("Indicatorul arată „[[=disconnected]]” sau apare „[[=ERR_NO_RESOLVE]]”. În Resolve: Preferences › General › External scripting using: <b>Local</b>; apoi [[settings]] › [[depsOpen]] › [[depsRecheck]]. Verifică și că ai un proiect și un timeline deschise.", "The indicator shows “[[=disconnected]]” or “[[=ERR_NO_RESOLVE]]” appears. In Resolve: Preferences › General › External scripting using: <b>Local</b>; then [[settings]] › [[depsOpen]] › [[depsRecheck]]. Also check that a project and a timeline are open.", "El indicador muestra “[[=disconnected]]” o aparece “[[=ERR_NO_RESOLVE]]”. En Resolve: Preferences › General › External scripting using: <b>Local</b>; luego [[settings]] › [[depsOpen]] › [[depsRecheck]]. Comprueba también que hay un proyecto y un timeline abiertos.")),
        (T("Python nu este găsit", "Python is not found", "No se encuentra Python"), T("Mesaje: „[[=ERR_BRIDGE_EXIT]]” / „[[=ERR_BRIDGE_TIMEOUT]]”, iar în [[depsOpen]], Python 3 e roșu. Instalează Python 3 (3.8+) de pe python.org și redeschide panoul. Dacă e instalat într-un loc neobișnuit, scrie „pythonPath” în fișierul de setări (calea e în [[settings]]).", "Messages: “[[=ERR_BRIDGE_EXIT]]” / “[[=ERR_BRIDGE_TIMEOUT]]”, and in [[depsOpen]] Python 3 is red. Install Python 3 (3.8+) from python.org and reopen the panel. If it is installed somewhere unusual, set “pythonPath” in the settings file (its location is in [[settings]]).", "Mensajes: “[[=ERR_BRIDGE_EXIT]]” / “[[=ERR_BRIDGE_TIMEOUT]]”, y en [[depsOpen]] Python 3 está en rojo. Instala Python 3 (3.8+) desde python.org y reabre el panel. Si está instalado en un sitio poco común, escribe “pythonPath” en el archivo de ajustes (su ubicación está en [[settings]]).")),
        (T("Timeline-ul drop-frame e refuzat", "A drop-frame timeline is refused", "Se rechaza un timeline drop-frame"), T("Mesaj: „[[=ERR_DROP_FRAME_UNSUPPORTED]]”. Cu drop-frame, timecode-ul sare numere, iar poziția în cadre nu mai corespunde unui timecode simplu; panoul blochează plasarea ca să nu cadă niciun clip în locul greșit. Folosește un timeline non-drop-frame (de ex. 24 sau 25 fps).", "Message: “[[=ERR_DROP_FRAME_UNSUPPORTED]]”. With drop-frame, the timecode skips numbers, so a frame position no longer maps to a plain timecode; the panel blocks placing so no clip lands in the wrong spot. Use a non-drop-frame timeline (for example 24 or 25 fps).", "Mensaje: “[[=ERR_DROP_FRAME_UNSUPPORTED]]”. Con drop-frame el timecode salta números, así que una posición en fotogramas ya no equivale a un timecode simple; el panel bloquea la colocación para que ningún clip caiga en un sitio equivocado. Usa un timeline non-drop-frame (por ejemplo 24 o 25 fps).")),
        (T("Fișier în afara bibliotecii", "A file outside the library", "Archivo fuera de la biblioteca"), T("„[[=ERR_OUTSIDE_LIBRARY]]”: panoul citește doar din folderele adăugate. Adaugă folderul cu [[addFolder]].", "“[[=ERR_OUTSIDE_LIBRARY]]”: the panel reads only from the folders you added. Add the folder with [[addFolder]].", "“[[=ERR_OUTSIDE_LIBRARY]]”: el panel solo lee de las carpetas añadidas. Añade la carpeta con [[addFolder]].")),
        (T("Bibliotecă goală sau fără rezultate", "Empty library or no results", "Biblioteca vacía o sin resultados"), T("„[[=emptyLib]]” înseamnă că nu ai adăugat niciun folder; „[[=noMatch]]” înseamnă că filtrul din [[search]] nu găsește nimic. Formate citite: WAV, AIFF, MP3, FLAC, M4A și altele uzuale.", "“[[=emptyLib]]” means no folder was added; “[[=noMatch]]” means the [[search]] filter finds nothing. Common formats such as WAV, AIFF, MP3, FLAC and M4A are read.", "“[[=emptyLib]]” significa que no se añadió ninguna carpeta; “[[=noMatch]]” significa que el filtro de [[search]] no encuentra nada. Se leen formatos comunes como WAV, AIFF, MP3, FLAC y M4A."))]),
    ("note", T("Pentru orice altă eroare, [[openLog]] (în [[settings]]) deschide jurnalul; nu conține conținutul fișierelor audio.", "For any other error, [[openLog]] (in [[settings]]) opens the log; it does not contain the audio files' content.", "Para cualquier otro error, [[openLog]] (en [[settings]]) abre el registro; no contiene el contenido de los archivos de audio.")),
]))

CH.append((T("Actualizare și dezinstalare", "Updating and uninstalling", "Actualizar y desinstalar"), [
    ("h2", T("Actualizare", "Updating", "Actualización")),
    ("p", T("În [[settings]], lângă numărul versiunii, apasă [[updCheck]]. Rezultatele posibile: „[[=updCurrent]]”, „[[=updNewer|v=x.y.z]]” cu butoanele [[updNow]] / [[updLater]], sau o eroare de verificare cu motivul. [[updNow]] descarcă pachetul, îi verifică semnătura și îl instalează; macOS afișează cererea nativă de parolă de administrator. La final: „[[=updDone]]”. Închide panoul și deschide-l din nou din Workflow Integrations.",
            "In [[settings]], next to the version number, press [[updCheck]]. The possible results: “[[=updCurrent]]”, “[[=updNewer|v=x.y.z]]” with the [[updNow]] / [[updLater]] buttons, or a check error with the reason. [[updNow]] downloads the package, verifies its signature and installs it; macOS shows its native administrator-password prompt. At the end: “[[=updDone]]”. Close the panel and reopen it from Workflow Integrations.",
            "En [[settings]], junto al número de versión, pulsa [[updCheck]]. Resultados posibles: “[[=updCurrent]]”, “[[=updNewer|v=x.y.z]]” con los botones [[updNow]] / [[updLater]], o un error de comprobación con el motivo. [[updNow]] descarga el paquete, verifica su firma y lo instala; macOS muestra su solicitud nativa de contraseña de administrador. Al final: “[[=updDone]]”. Cierra el panel y ábrelo de nuevo desde Workflow Integrations.")),
    ("h2", T("Dezinstalare", "Uninstalling", "Desinstalación")),
    ("p", T("În [[settings]] apasă [[uninstallBtn]]. După confirmare, panoul își șterge folderul, setările, cache-ul și jurnalul; fișierele tale audio nu se ating. Dacă folderul panoului cere permisiuni de administrator, panoul spune că setările au fost șterse, iar folderul se scoate cu parola ta. Poți și manual: închide Resolve și mută folderul de mai jos la Coș.",
            "In [[settings]] press [[uninstallBtn]]. After confirmation the panel removes its folder, settings, cache and log; your audio files are not touched. If the panel folder needs administrator permission, the panel says the settings were removed and the folder goes away with your password. You can also do it by hand: quit Resolve and move the folder below to the Trash.",
            "En [[settings]] pulsa [[uninstallBtn]]. Tras confirmar, el panel elimina su carpeta, los ajustes, la caché y el registro; tus archivos de audio no se tocan. Si la carpeta del panel necesita permisos de administrador, el panel avisa de que los ajustes se eliminaron y la carpeta se quita con tu contraseña. También puedes hacerlo a mano: cierra Resolve y mueve la carpeta de abajo a la Papelera.")),
    ("code", PLUG),
]))

CH.append((T("Compatibilitate și limite cunoscute", "Compatibility and known limits", "Compatibilidad y límites conocidos"), [
    ("tbl", [(T("Verificat", "Verified", "Verificado"), T("DaVinci Resolve Studio 21.2 pe macOS 27 (Apple Silicon); timeline la 24 fps fără drop-frame; plasare, scurtare, înlocuire, markere, umplere aleatorie și asociere rapidă; instalare și actualizare pe canalul oficial.", "DaVinci Resolve Studio 21.2 on macOS 27 (Apple Silicon); a 24 fps non-drop-frame timeline; placing, trimming, replacing, markers, random fill and rapid mapping; installation and update through the official channel.", "DaVinci Resolve Studio 21.2 en macOS 27 (Apple Silicon); un timeline de 24 fps sin drop-frame; colocar, recortar, reemplazar, marcadores, relleno aleatorio y mapeo rápido; instalación y actualización por el canal oficial.")),
             (T("Neverificat", "Not verified", "No verificado"), T("Tragerea unui card direct în timeline; alte rate de cadre decât 24 fps; instalarea pe un Mac curat, cu fișier în carantină; Windows (etapă separată, încă inexistentă).", "Dragging a card straight into the timeline; frame rates other than 24 fps; installing on a clean Mac with a quarantined file; Windows (a separate stage, not available yet).", "Arrastrar una tarjeta directamente al timeline; frecuencias distintas de 24 fps; instalar en un Mac limpio con archivo en cuarentena; Windows (etapa aparte, aún no disponible).")),
             (T("Nesuportat", "Not supported", "No compatible"), T("Timeline-uri drop-frame (plasarea e refuzată, vezi Probleme). Versiunea gratuită a Resolve nu încarcă panouri Workflow Integration.", "Drop-frame timelines (placing is refused, see Troubleshooting). The free version of Resolve does not load Workflow Integration panels.", "Timelines drop-frame (se rechaza colocar, consulta Problemas). La versión gratuita de Resolve no carga paneles Workflow Integration."))]),
    ("p", T("Lungimea unui clip audio se calculează cu rata de cadre a timeline-ului. Panoul este un proiect independent și gratuit; nu este dezvoltat, aprobat sau susținut de Blackmagic Design.", "A clip's length is computed with the timeline frame rate. The panel is an independent, free project; it is not developed, endorsed or supported by Blackmagic Design.", "La duración de un clip se calcula con la frecuencia de fotogramas del timeline. El panel es un proyecto independiente y gratuito; no está desarrollado, aprobado ni respaldado por Blackmagic Design.")),
]))

CH.append((T("Tutoriale video", "Video tutorials", "Tutoriales en vídeo"), [
    ("p", T("Seria de clipuri scurte, fără voce și fără text suprapus, filmate cu panoul în română, pe biblioteca demo. Titlurile rămân în română și în celelalte limbi. Clipurile sunt pe pagina proiectului: <a href=\"https://gordas.dev/soundsfxpaste/#tutoriale-video\" color=\"#2f5fd0\">gordas.dev/soundsfxpaste</a>.",
            "A series of short clips, without voice or overlaid text, filmed with the panel in Romanian, on the demo library. The titles stay in Romanian in every language. The clips are on the project page: <a href=\"https://gordas.dev/soundsfxpaste/#tutoriale-video\" color=\"#2f5fd0\">gordas.dev/soundsfxpaste</a>.",
            "Una serie de clips cortos, sin voz ni texto superpuesto, grabados con el panel en rumano, sobre la biblioteca demo. Los títulos se mantienen en rumano en todos los idiomas. Los clips están en la página del proyecto: <a href=\"https://gordas.dev/soundsfxpaste/#tutoriale-video\" color=\"#2f5fd0\">gordas.dev/soundsfxpaste</a>.")),
    ("vtbl", [("1", "Deschide panoul și adaugă un folder de sunete", T("Capitolele 3–4", "Chapters 3–4", "Capítulos 3–4")),
              ("2", "Caută, ascultă și plasează un sunet la cursor", T("Capitolele 4 și 6", "Chapters 4 and 6", "Capítulos 4 y 6")),
              ("3", "Scurtează un sunet", T("Capitolul 7", "Chapter 7", "Capítulo 7")),
              ("4", "Înlocuiește un sunet în timeline", T("Capitolul 8", "Chapter 8", "Capítulo 8")),
              ("5", "Folosește markere și etichete", T("Capitolul 9", "Chapter 9", "Capítulo 9")),
              ("6", "Completează markerele cu sunete aleatorii", T("Capitolul 10", "Chapter 10", "Capítulo 10")),
              ("7", "Asociază rapid sunete cu markerele", T("Capitolul 11", "Chapter 11", "Capítulo 11"))]),
]))

CH.append((T("Licență, credite și note ale terților", "License, credits and third-party notices", "Licencia, créditos y avisos de terceros"), [
    ("p", T("SoundSFXPaste este software gratuit sub licență MIT. Autor: " + CREDIT + ". Codul sursă: <a href=\"" + REPO + "\" color=\"#2f5fd0\">" + REPO + "</a>. Sprijinul, dacă îl dorești, se exprimă ca donație voluntară; nu există plată pentru a folosi panoul.",
            "SoundSFXPaste is free software under the MIT license. Author: " + CREDIT + ". Source code: <a href=\"" + REPO + "\" color=\"#2f5fd0\">" + REPO + "</a>. Support, if you wish to give it, is a voluntary donation; nothing is required to use the panel.",
            "SoundSFXPaste es software gratuito bajo licencia MIT. Autor: " + CREDIT + ". Código fuente: <a href=\"" + REPO + "\" color=\"#2f5fd0\">" + REPO + "</a>. El apoyo, si quieres darlo, es una donación voluntaria; no se exige nada para usar el panel.")),
    ("p", T("Panoul rulează în fereastra Electron proprie a Resolve (Electron nu se redistribuie în acest pachet). Sunetele din folderul demo-audio sunt sintetizate de proiect și puse în domeniul public (CC0). Mențiunile terților sunt în fișierul NOTICE.md din proiect și în pagina de licență a pachetului: <a href=\"" + REPO + "/blob/main/NOTICE.md\" color=\"#2f5fd0\">NOTICE.md</a>.",
            "The panel runs in Resolve's own Electron window (Electron is not redistributed in this package). The sounds in the demo-audio folder are synthesized by the project and released into the public domain (CC0). Third-party notices are in the project's NOTICE.md file and on the package license page: <a href=\"" + REPO + "/blob/main/NOTICE.md\" color=\"#2f5fd0\">NOTICE.md</a>.",
            "El panel se ejecuta en la ventana Electron propia de Resolve (Electron no se redistribuye en este paquete). Los sonidos de la carpeta demo-audio están sintetizados por el proyecto y publicados en el dominio público (CC0). Los avisos de terceros están en el archivo NOTICE.md del proyecto y en la página de licencia del paquete: <a href=\"" + REPO + "/blob/main/NOTICE.md\" color=\"#2f5fd0\">NOTICE.md</a>.")),
    ("p", T("DaVinci Resolve este marca a deținătorului ei; SoundSFXPaste este un proiect independent, fără legătură cu Blackmagic Design.", "DaVinci Resolve is a trademark of its owner; SoundSFXPaste is an independent project, unaffiliated with Blackmagic Design.", "DaVinci Resolve es marca de su titular; SoundSFXPaste es un proyecto independiente, sin relación con Blackmagic Design.")),
]))

LANGS = {
    "ro": dict(i=0, file="SoundSFXPaste-Manual-RO-" + VERSION + ".pdf", title="Manual de utilizare", sub="Panou gratuit de efecte sonore pentru DaVinci Resolve Studio pe Mac",
               ver="Versiunea " + VERSION, toc="Cuprins", page="Pagina", note_en="captură cu interfața în engleză", ex_h=("Obiectiv", "Unde apeși", "Ce trebuie să apară", "Cum anulezi"),
               vh=("Clip", "Titlu", "Capitol din manual"), th=("Element", "Detalii"), chap="Capitolul"),
    "en": dict(i=1, file="SoundSFXPaste-Manual-EN-" + VERSION + ".pdf", title="User manual", sub="Free sound-effects panel for DaVinci Resolve Studio on Mac",
               ver="Version " + VERSION, toc="Contents", page="Page", note_en=None, ex_h=("Goal", "Where to click", "What should appear", "How to undo"),
               vh=("Clip", "Title", "Manual chapter"), th=("Item", "Details"), chap="Chapter"),
    "es": dict(i=2, file="SoundSFXPaste-Manual-ES-" + VERSION + ".pdf", title="Manual de usuario", sub="Panel gratuito de efectos de sonido para DaVinci Resolve Studio en Mac",
               ver="Versión " + VERSION, toc="Índice", page="Página", note_en="captura con la interfaz en inglés", ex_h=("Objetivo", "Dónde pulsar", "Qué debe aparecer", "Cómo deshacer"),
               vh=("Clip", "Título", "Capítulo del manual"), th=("Elemento", "Detalles"), chap="Capítulo"),
}


class Doc(BaseDocTemplate):
    def __init__(self, fn, lang, cfg):
        super().__init__(fn, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                         title="SoundSFXPaste — " + cfg["title"], author=CREDIT, subject=cfg["sub"], creator="scripts/build_manual.py")
        self.cfg, self.lang = cfg, lang
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="cover", frames=[fr], onPage=self.cover), PageTemplate(id="body", frames=[fr], onPage=self.footer)])

    def cover(self, c, d):
        c.saveState()
        c.setFillColor(colors.HexColor("#0e1322")); c.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        c.setFillColor(BLUE); c.rect(0, 0, 6 * mm, A4[1], fill=1, stroke=0)
        c.setFillColor(GOLD); c.rect(6 * mm, 0, 1.6 * mm, A4[1], fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont("BodyB", 34); c.drawString(25 * mm, A4[1] - 95 * mm, "SoundSFXPaste")
        c.setFillColor(GOLD); c.setFont("Body", 18); c.drawString(25 * mm, A4[1] - 108 * mm, self.cfg["title"])
        c.setFillColor(colors.HexColor("#c4ccdc")); c.setFont("Body", 11)
        words, line, y = self.cfg["sub"].split(), "", A4[1] - 122 * mm
        for w in words:
            if pdfmetrics.stringWidth(line + " " + w, "Body", 11) > 150 * mm:
                c.drawString(25 * mm, y, line.strip()); line, y = "", y - 6 * mm
            line += " " + w
        c.drawString(25 * mm, y, line.strip())
        c.setFont("Body", 10)
        c.drawString(25 * mm, 30 * mm, self.cfg["ver"] + "  ·  " + SITE)
        c.drawString(25 * mm, 24 * mm, CREDIT + "  ·  MIT")
        c.restoreState()

    def footer(self, c, d):
        c.saveState(); c.setFont("Body", 8); c.setFillColor(MUTED)
        c.drawString(20 * mm, 12 * mm, "SoundSFXPaste · " + CREDIT + "  ·  " + self.cfg["ver"])
        c.drawRightString(A4[0] - 20 * mm, 12 * mm, "%s %d" % (self.cfg["page"], d.page)); c.restoreState()

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name == "h1":
            k = "c%d" % (abs(hash(f.getPlainText())) % 10**8)
            self.canv.bookmarkPage(k); self.canv.addOutlineEntry(f.getPlainText(), k, 0, 0)
            self.notify("TOCEntry", (0, f.getPlainText(), self.page, k))


def build(lang, cfg, out):
    i = cfg["i"]
    X = lambda t: ui(lang, t[i])
    doc = Doc(out, lang, cfg)
    S = [NextPageTemplate("body"), PageBreak(), Paragraph(cfg["toc"], ST["h1"].clone("tocH"))]
    toc = TableOfContents(); toc.levelStyles = [ST["toc1"]]
    S += [toc, PageBreak()]
    nimg = 0
    def tbl(rows, widths, header=None):
        data = ([[Paragraph(h, ST["cellb"]) for h in header]] if header else []) + rows
        t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
        sty = [("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
        if header: sty.append(("BACKGROUND", (0, 0), (-1, 0), SOFT))
        t.setStyle(TableStyle(sty)); return t
    for n, (title, blocks) in enumerate(CH, 1):
        S.append(Paragraph("%d. %s" % (n, re.sub(r"</?b>", "", X(title))), ST["h1"]))
        for b in blocks:
            k = b[0]
            if k == "p": S.append(Paragraph(X(b[1]), ST["p"]))
            elif k == "h2": S.append(Paragraph(X(b[1]), ST["h2"]))
            elif k == "note": S.append(Paragraph(X(b[1]), ST["note"]))
            elif k == "ul": S += [Paragraph(X(t), ST["li"], bulletText="%d." % (j + 1)) for j, t in enumerate(b[1])] + [Spacer(1, 4)]
            elif k == "code": S.append(Paragraph(esc(b[1]), ST["code"]))
            elif k == "img":
                key = b[1]; p = os.path.join(IMG, "%s_%s.jpg" % (lang, key)); fb = False
                if not os.path.exists(p):
                    p = os.path.join(IMG, "en_%s.jpg" % key); fb = not key.startswith("tl_") and lang != "en"
                from PIL import Image as PI
                iw, ih = PI.open(p).size; w = 150 * mm
                cap = X(b[2]) + ((" (" + cfg["note_en"] + ")") if fb else "")
                S.append(KeepTogether([Image(p, width=w, height=w * ih / iw, hAlign="LEFT"), Paragraph(cap, ST["cap"])])); nimg += 1
            elif k == "tbl":
                rows = [[Paragraph(X(a), ST["cellb"]), Paragraph(X(t), ST["cell"])] for a, t in b[1]]
                S += [tbl(rows, [42 * mm, 128 * mm]), Spacer(1, 8)]
            elif k == "vtbl":
                rows = [[Paragraph(a, ST["cell"]), Paragraph("„" + t + "”", ST["cellb"]), Paragraph(X(c), ST["cell"])] for a, t, c in b[1]]
                S += [tbl(rows, [14 * mm, 105 * mm, 51 * mm], cfg["vh"]), Spacer(1, 8)]
            elif k == "ex":
                h = cfg["ex_h"]
                rows = [[Paragraph(h[j], ST["cellb"]), Paragraph(X(b[2 + j]), ST["cell"])] for j in range(4)]
                t = Table(rows, colWidths=[34 * mm, 136 * mm])
                t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), SOFT), ("BOX", (0, 0), (-1, -1), 0.6, BLUE), ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
                S.append(KeepTogether([Paragraph("► " + X(b[1]), ST["h2"]), t, Spacer(1, 8)]))
        S.append(Spacer(1, 6))
    doc.multiBuild(S)
    return nimg


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "manual")
    os.makedirs(out, exist_ok=True)
    import pymupdf
    for lang, cfg in LANGS.items():
        path = os.path.join(out, cfg["file"]); n = build(lang, cfg, path)
        d = pymupdf.open(path)
        print("%s: %d pages, %d images, outline=%d, %.0f KB" % (cfg["file"], len(d), n, len(d.get_toc()), os.path.getsize(path) / 1024))


if __name__ == "__main__":
    main()

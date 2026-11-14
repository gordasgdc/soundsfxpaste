"""Single source for the seven written tutorials (RO/EN/ES). Used by build_site.py, build_manual.py and build_readme.py.
Text uses [[key]] placeholders resolved from docs/manual/i18n.txt (real button names per language)."""
import os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://gordas.dev/soundsfxpaste/"
LANGS = ("ro", "en", "es")
PAGE = {"ro": SITE, "en": SITE + "en/", "es": SITE + "es/"}


def _i18n():
    d, cur = {}, None
    for ln in open(os.path.join(ROOT, "docs", "manual", "i18n.txt"), encoding="utf-8"):
        ln = ln.rstrip("\n")
        if ln.startswith("=== "): cur = ln[4:].strip(); d[cur] = {}
        elif "=" in ln and cur: k, v = ln.split("=", 1); d[cur][k] = v
    return d


I18N = _i18n()
KEYRE = re.compile(r"\[\[(=?)([A-Za-z]+)(?:\|([^\]]*))?\]\]")


def _label(lang, key, args):
    v = I18N[lang][key]
    for a in (args.split(",") if args else []):
        k, _, x = a.partition("="); v = v.replace("{" + k + "}", x)
    return re.sub(r"\s*\(\{detail\}\)", "", v)


def render(lang, text, mode="html"):
    """mode: html (<b>), md (**), plain."""
    def rep(m):
        plain, key, args = m.groups(); v = _label(lang, key, args)
        if mode == "html": v = html.escape(v, quote=False)
        if plain or mode == "plain": return v
        return "<b>%s</b>" % v if mode == "html" else "**%s**" % v
    out = KEYRE.sub(rep, text)
    return out if mode != "html" else out


def keys_in(*texts):
    seen = []
    for t in texts:
        for m in KEYRE.finditer(t):
            if not m.group(1) and m.group(2) not in seen: seen.append(m.group(2))
    return seen


def clip_url(lang, n): return "%s#clip-%d" % (PAGE[lang], n)


def mp4_url(n): return "%svideo/%s.mp4" % (SITE, TUT[n - 1]["file"])


def T(ro, en, es): return (ro, en, es)


# Labels of the section headings, per language.
H = {"ro": dict(goal="Ce obții", need="Pregătește", steps="Pași", see="Ce trebuie să vezi în Resolve", ex="Exemplu din clip", fix="Dacă rezultatul diferă",
                clip="Vezi clipul", names="Numele butoanelor în clip (interfață în română)", tut="Tutorial"),
     "en": dict(goal="What you get", need="Have ready", steps="Steps", see="What you should see in Resolve", ex="Example from the clip", fix="If the result differs",
                clip="Watch the clip", names="Button names in the clip (Romanian interface)", tut="Tutorial"),
     "es": dict(goal="Qué obtienes", need="Ten preparado", steps="Pasos", see="Qué debes ver en Resolve", ex="Ejemplo del clip", fix="Si el resultado difiere",
                clip="Ver el clip", names="Nombres de los botones en el clip (interfaz en rumano)", tut="Tutorial")}

TUT = [
    dict(n=1, file="01-deschide-panoul-si-adauga-un-folder-de-sunete", title="Deschide panoul și adaugă un folder de sunete", chap=(3, 4),
         goal=T("Panoul SoundSFXPaste deschis în Resolve și o bibliotecă de sunete încărcată în el.",
                "The SoundSFXPaste panel open in Resolve with a sound library loaded in it.",
                "El panel SoundSFXPaste abierto en Resolve con una biblioteca de sonidos cargada."),
         need=[T("DaVinci Resolve Studio pornit, cu un proiect și un timeline deschise.", "DaVinci Resolve Studio running, with a project and a timeline open.", "DaVinci Resolve Studio en marcha, con un proyecto y un timeline abiertos."),
               T("Folderul demo-audio din repo (6 sunete): https://github.com/gordasgdc/soundsfxpaste/tree/main/demo-audio", "The demo-audio folder from the repo (6 sounds): https://github.com/gordasgdc/soundsfxpaste/tree/main/demo-audio", "La carpeta demo-audio del repositorio (6 sonidos): https://github.com/gordasgdc/soundsfxpaste/tree/main/demo-audio")],
         steps=[T("În Resolve alege Workspace › Workflow Integrations › SoundSFXPaste.", "In Resolve choose Workspace › Workflow Integrations › SoundSFXPaste.", "En Resolve elige Workspace › Workflow Integrations › SoundSFXPaste."),
                T("Așteaptă fereastra panoului; în bara de jos trebuie să apară „[[=connected]]”.", "Wait for the panel window; the bottom bar should say “[[=connected]]”.", "Espera a la ventana del panel; la barra inferior debe decir «[[=connected]]»."),
                T("În coloana [[library]] apasă + ([[addFolder]]).", "In the [[library]] column press + ([[addFolder]]).", "En la columna [[library]] pulsa + ([[addFolder]])."),
                T("În fereastra Finder alege folderul demo-audio și confirmă.", "In the Finder window choose the demo-audio folder and confirm.", "En la ventana de Finder elige la carpeta demo-audio y confirma."),
                T("Deschide [[allSounds]] și privește cardurile.", "Open [[allSounds]] and look at the cards.", "Abre [[allSounds]] y mira las tarjetas.")],
         see=[T("Folderul apare în [[library]] cu cifra 6, iar [[allSounds]] arată șase carduri cu forme de undă.", "The folder shows in [[library]] with the number 6 and [[allSounds]] shows six cards with waveforms.", "La carpeta aparece en [[library]] con el número 6 y [[allSounds]] muestra seis tarjetas con formas de onda.")],
         example=T("Cele șase carduri din clip: Click Dry, Ding Bright, Impact Low, Pop Round, Riser Short, Whoosh Soft.", "The six cards in the clip: Click Dry, Ding Bright, Impact Low, Pop Round, Riser Short, Whoosh Soft.", "Las seis tarjetas del clip: Click Dry, Ding Bright, Impact Low, Pop Round, Riser Short, Whoosh Soft."),
         fix=T("Panoul nu apare: verifică Resolve Studio (versiunea gratuită nu rulează panouri) și repetă meniul. Indicatorul arată „[[=disconnected]]”: deschide un proiect și un timeline în Resolve. Folderul nu apare: apasă [[refresh]] sau adaugă-l din nou; fișierele de pe disc nu se șterg niciodată când scoți un folder.",
               "Panel does not appear: check you run Resolve Studio (the free version does not run panels) and repeat the menu. The indicator says “[[=disconnected]]”: open a project and a timeline in Resolve. Folder missing: press [[refresh]] or add it again; files on disk are never deleted when you remove a folder.",
               "El panel no aparece: comprueba que usas Resolve Studio (la versión gratuita no ejecuta paneles) y repite el menú. El indicador dice «[[=disconnected]]»: abre un proyecto y un timeline en Resolve. Falta la carpeta: pulsa [[refresh]] o añádela de nuevo; los archivos del disco nunca se borran al quitar una carpeta.")),
    dict(n=2, file="02-cauta-asculta-si-plaseaza-un-sunet-la-cursor", title="Caută, ascultă și plasează un sunet la cursor", chap=(4, 6),
         goal=T("Un sunet găsit prin căutare, ascultat și pus pe timeline exact unde e cursorul.", "A sound found by search, auditioned and placed on the timeline exactly at the cursor.", "Un sonido encontrado por búsqueda, escuchado y colocado en el timeline justo en el cursor."),
         need=[T("Biblioteca demo încărcată (tutorialul 1).", "The demo library loaded (tutorial 1).", "La biblioteca demo cargada (tutorial 1)."),
               T("Un timeline cu pistă audio A1 liberă și cursorul Resolve pe 01:00:05:00 (tăietura video).", "A timeline with a free audio track A1 and the Resolve cursor on 01:00:05:00 (the video cut).", "Un timeline con una pista de audio A1 libre y el cursor de Resolve en 01:00:05:00 (el corte de vídeo).")],
         steps=[T("În Resolve pune cursorul pe 01:00:05:00.", "In Resolve park the cursor on 01:00:05:00.", "En Resolve coloca el cursor en 01:00:05:00."),
                T("În panou, în [[search]], scrie „whoosh”; rămâne un singur card.", "In the panel, in [[search]], type “whoosh”; one card is left.", "En el panel, en [[search]], escribe «whoosh»; queda una sola tarjeta."),
                T("Apasă ► pe card ([[audition]]); butonul devine [[stop]] cât timp sună. Nu se schimbă nimic în timeline.", "Press ► on the card ([[audition]]); the button becomes [[stop]] while it plays. Nothing changes in the timeline.", "Pulsa ► en la tarjeta ([[audition]]); el botón pasa a [[stop]] mientras suena. No cambia nada en el timeline."),
                T("Apasă pe card ca să-l alegi (contur auriu).", "Click the card to choose it (gold outline).", "Pulsa la tarjeta para elegirla (contorno dorado)."),
                T("În bara de jos verifică [[track]] = A1 și timecode-ul galben 01:00:05:00.", "In the bottom bar check [[track]] = A1 and the yellow timecode 01:00:05:00.", "En la barra inferior comprueba [[track]] = A1 y el timecode amarillo 01:00:05:00."),
                T("Apasă [[place]].", "Press [[place]].", "Pulsa [[place]].")],
         see=[T("Mesaj verde „Whoosh Soft” plasat pe A1 la 01:00:05:00 (1,4 s); un clip nou pe A1; cursorul sare la 01:00:06:09, la capătul clipului.", "Green message: “Whoosh Soft” placed on A1 at 01:00:05:00 (1.4 s); a new clip on A1; the cursor jumps to 01:00:06:09, the end of the clip.", "Mensaje verde: «Whoosh Soft» colocado en A1 en 01:00:05:00 (1,4 s); un clip nuevo en A1; el cursor salta a 01:00:06:09, el final del clip.")],
         example=T("Whoosh Soft (1,4 s) pe A1, începând chiar la tăietura video de la 01:00:05:00.", "Whoosh Soft (1.4 s) on A1, starting right on the video cut at 01:00:05:00.", "Whoosh Soft (1,4 s) en A1, empezando justo en el corte de vídeo de 01:00:05:00."),
         fix=T("Cmd+Z în Resolve sau șterge clipul. Plasarea e refuzată (pista are deja un clip acolo): alege altă pistă sau apasă [[addTrack]] și repetă. Sunetul e prea lung: panoul cere o a doua apăsare pe [[place]] ca să confirmi.",
               "Cmd+Z in Resolve or delete the clip. Placement refused (the track already has a clip there): choose another track or press [[addTrack]] and repeat. The sound is too long: the panel asks for a second press on [[place]] to confirm.",
               "Cmd+Z en Resolve o borra el clip. Colocación rechazada (la pista ya tiene un clip ahí): elige otra pista o pulsa [[addTrack]] y repite. El sonido es demasiado largo: el panel pide una segunda pulsación en [[place]] para confirmar.")),
    dict(n=3, file="03-scurteaza-un-sunet", title="Scurtează un sunet", chap=(7,),
         goal=T("Din Riser Short (2,5 s) pui pe timeline doar secunda dintre 0,80 s și 1,80 s.", "From Riser Short (2.5 s) you place only the second between 0.80 s and 1.80 s.", "De Riser Short (2,5 s) colocas solo el segundo entre 0,80 s y 1,80 s."),
         need=[T("Biblioteca demo încărcată și o pistă A1 liberă.", "The demo library loaded and a free track A1.", "La biblioteca demo cargada y una pista A1 libre."),
               T("Cursorul Resolve pe 01:00:03:00.", "The Resolve cursor on 01:00:03:00.", "El cursor de Resolve en 01:00:03:00.")],
         steps=[T("Alege cardul Riser Short.", "Choose the Riser Short card.", "Elige la tarjeta Riser Short."),
                T("Apasă [[trim]]; se deschide „[[=trimTitle]]” cu unda sunetului.", "Press [[trim]]; “[[=trimTitle]]” opens with the sound’s waveform.", "Pulsa [[trim]]; se abre «[[=trimTitle]]» con la onda del sonido."),
                T("Primul click: pe undă, la 0,80 s (aproximativ o treime din lățime). Se mută începutul intervalului.", "First click: on the wave at 0.80 s (about a third of the width). This moves the start of the range.", "Primer clic: en la onda, a 0,80 s (aproximadamente un tercio del ancho). Mueve el inicio del rango."),
                T("Al doilea click: pe undă, la 1,80 s (aproximativ trei sferturi). Se mută sfârșitul.", "Second click: on the wave at 1.80 s (about three quarters). This moves the end.", "Segundo clic: en la onda, a 1,80 s (aproximadamente tres cuartos). Mueve el final."),
                T("Citește sub undă „0.80 s → 1.80 s”; porțiunea aleasă e luminată.", "Read “0.80 s → 1.80 s” under the wave; the chosen part is lit.", "Lee bajo la onda «0.80 s → 1.80 s»; la parte elegida aparece iluminada."),
                T("Apasă [[trimPlace]].", "Press [[trimPlace]].", "Pulsa [[trimPlace]].")],
         see=[T("Un clip de 1 s (24 de cadre la 24 fps) pe A1, la 01:00:03:00; mesaj verde „Riser Short” plasat pe A1 la 01:00:03:00 (1,0 s); cursorul sare la capătul clipului.", "A 1 s clip (24 frames at 24 fps) on A1 at 01:00:03:00; green message “Riser Short” placed on A1 at 01:00:03:00 (1.0 s); the cursor jumps to the end of the clip.", "Un clip de 1 s (24 fotogramas a 24 fps) en A1 en 01:00:03:00; mensaje verde «Riser Short» colocado en A1 en 01:00:03:00 (1,0 s); el cursor salta al final del clip.")],
         example=T("În clip: două clicuri (0,80 s și 1,80 s), numerele „0.80 s → 1.80 s” sub undă, apoi o secundă din riser pe A1.", "In the clip: two clicks (0.80 s and 1.80 s), the numbers “0.80 s → 1.80 s” under the wave, then one second of the riser on A1.", "En el clip: dos clics (0,80 s y 1,80 s), los números «0.80 s → 1.80 s» bajo la onda y luego un segundo del riser en A1."),
         fix=T("Un click mută capătul cel mai apropiat, nu creează un interval nou. Numerele sunt altele: apasă [[clearSel]] și repetă cele două clicuri. [[cancel]] (sau Esc) închide fără să plaseze. După plasare, Cmd+Z în Resolve.",
               "A click moves the nearest end; it does not create a new range. Different numbers: press [[clearSel]] and repeat the two clicks. [[cancel]] (or Esc) closes without placing. After placing, Cmd+Z in Resolve.",
               "Un clic mueve el extremo más cercano; no crea un rango nuevo. Números distintos: pulsa [[clearSel]] y repite los dos clics. [[cancel]] (o Esc) cierra sin colocar. Tras colocar, Cmd+Z en Resolve.")),
    dict(n=4, file="04-inlocuieste-un-sunet-in-timeline", title="Înlocuiește un sunet în timeline", chap=(8,),
         goal=T("Un clip din timeline înlocuit cu alt sunet, pe aceeași pistă și la același timecode.", "A clip on the timeline swapped for another sound, on the same track and at the same timecode.", "Un clip del timeline cambiado por otro sonido, en la misma pista y en el mismo timecode."),
         need=[T("Pe A1 un clip Whoosh Soft la 01:00:05:00 (tutorialul 2).", "A Whoosh Soft clip on A1 at 01:00:05:00 (tutorial 2).", "Un clip Whoosh Soft en A1 en 01:00:05:00 (tutorial 2)."),
               T("Cursorul Resolve pus pe clip, de exemplu 01:00:05:12.", "The Resolve cursor parked on the clip, for example 01:00:05:12.", "El cursor de Resolve sobre el clip, por ejemplo 01:00:05:12.")],
         steps=[T("În [[tabFolders]] alege cardul Ding Bright (sunetul nou).", "In [[tabFolders]] pick the Ding Bright card (the new sound).", "En [[tabFolders]] elige la tarjeta Ding Bright (el sonido nuevo)."),
                T("Deschide [[tabAuto]] › [[rReplace]].", "Open [[tabAuto]] › [[rReplace]].", "Abre [[tabAuto]] › [[rReplace]]."),
                T("La [[repTarget]] alege [[repCursor]].", "At [[repTarget]] choose [[repCursor]].", "En [[repTarget]] elige [[repCursor]]."),
                T("Apasă [[repPlan]] și citește tabelul: ce clip e înlocuit și cu ce.", "Press [[repPlan]] and read the table: which clip is replaced and by what.", "Pulsa [[repPlan]] y lee la tabla: qué clip se reemplaza y por cuál."),
                T("Dacă e cel dorit, apasă [[repApply]].", "If it is the one you want, press [[repApply]].", "Si es el que quieres, pulsa [[repApply]].")],
         see=[T("Mesajul „[[=repDone|n=1]]”; pe A1, la 01:00:05:00, clipul se numește acum Ding Bright.", "The message “[[=repDone|n=1]]”; on A1 at 01:00:05:00 the clip is now named Ding Bright.", "El mensaje «[[=repDone|n=1]]»; en A1, en 01:00:05:00, el clip se llama ahora Ding Bright.")],
         example=T("În clip, Whoosh Soft de la tăietură devine Ding Bright, fără să se miște de pe poziție.", "In the clip, the Whoosh Soft at the cut becomes Ding Bright without moving from its position.", "En el clip, el Whoosh Soft del corte pasa a ser Ding Bright sin moverse de su posición."),
         fix=T("Cmd+Z în Resolve readuce clipul vechi. Tabelul de previzualizare nu e cel dorit: nu apăsa [[repApply]]; schimbă [[repTarget]] sau mută cursorul. Mesaj „[[=repNoTarget]]”: pune cursorul peste un clip sau selectează clipuri în Resolve.",
               "Cmd+Z in Resolve brings back the old clip. The preview table is not what you want: do not press [[repApply]]; change [[repTarget]] or move the cursor. Message “[[=repNoTarget]]”: park the cursor over a clip or select clips in Resolve.",
               "Cmd+Z en Resolve devuelve el clip antiguo. La tabla de vista previa no es la que quieres: no pulses [[repApply]]; cambia [[repTarget]] o mueve el cursor. Mensaje «[[=repNoTarget]]»: coloca el cursor sobre un clip o selecciona clips en Resolve.")),
    dict(n=5, file="05-foloseste-markere-si-etichete", title="Folosește markere și etichete", chap=(9,),
         goal=T("Markerele timeline-ului primesc nume clare și etichete, direct din panou.", "The timeline’s markers get clear names and tags, straight from the panel.", "Los marcadores del timeline reciben nombres claros y etiquetas, directamente desde el panel."),
         need=[T("Un timeline cu trei markere (Hit 1, Hit 2, Hit 3 la 01:00:01:00, 01:00:03:00, 01:00:07:00).", "A timeline with three markers (Hit 1, Hit 2, Hit 3 at 01:00:01:00, 01:00:03:00, 01:00:07:00).", "Un timeline con tres marcadores (Hit 1, Hit 2, Hit 3 en 01:00:01:00, 01:00:03:00, 01:00:07:00).")],
         steps=[T("Deschide [[tabAuto]] › [[rMarkers]].", "Open [[tabAuto]] › [[rMarkers]].", "Abre [[tabAuto]] › [[rMarkers]]."),
                T("La primul rând, în [[mkRename]], scrie „Door slam” și apasă Tab.", "On the first row, in [[mkRename]], type “Door slam” and press Tab.", "En la primera fila, en [[mkRename]], escribe «Door slam» y pulsa Tab."),
                T("În [[mkTags]] scrie „door” și apasă Enter.", "In [[mkTags]] type “door” and press Enter.", "En [[mkTags]] escribe «door» y pulsa Enter."),
                T("Privește rândul și markerul din timeline.", "Look at the row and at the marker on the timeline.", "Mira la fila y el marcador del timeline.")],
         see=[T("Mesajul „[[=mkDone]]”; rândul arată noul nume și bula „door”; markerul din timeline are numele nou.", "The message “[[=mkDone]]”; the row shows the new name and the “door” bubble; the timeline marker has the new name.", "El mensaje «[[=mkDone]]»; la fila muestra el nuevo nombre y la burbuja «door»; el marcador del timeline tiene el nombre nuevo.")],
         example=T("În clip, Hit 1 devine „Door slam” cu eticheta „door”, gata de umplut cu un sunet potrivit.", "In the clip, Hit 1 becomes “Door slam” with the tag “door”, ready to be filled with a fitting sound.", "En el clip, Hit 1 pasa a ser «Door slam» con la etiqueta «door», listo para rellenarse con un sonido adecuado."),
         fix=T("Rescrie numele sau apasă × pe etichetă. Ștergerea unui marker nu se anulează din panou: folosește Cmd+Z în Resolve imediat după. „[[=mkEmpty]]”: adaugă markere în timeline.",
               "Retype the name or press × on the tag. Deleting a marker cannot be undone from the panel: use Cmd+Z in Resolve right after. “[[=mkEmpty]]”: add markers to the timeline.",
               "Reescribe el nombre o pulsa × en la etiqueta. Borrar un marcador no se deshace desde el panel: usa Cmd+Z en Resolve justo después. «[[=mkEmpty]]»: añade marcadores al timeline.")),
    dict(n=6, file="06-completeaza-markerele-cu-sunete-aleatorii", title="Completează markerele cu sunete aleatorii", chap=(10,),
         goal=T("Un sunet scurt, ales la întâmplare, pe fiecare marker, într-o singură aplicare.", "A short, randomly chosen sound on every marker, in a single apply.", "Un sonido corto, elegido al azar, en cada marcador, en una sola aplicación."),
         need=[T("Timeline-ul cu cele trei markere și biblioteca demo.", "The timeline with the three markers and the demo library.", "El timeline con los tres marcadores y la biblioteca demo."),
               T("Pista A1 liberă la poziția markerelor.", "Track A1 free at the markers’ positions.", "La pista A1 libre en la posición de los marcadores.")],
         steps=[T("În bara de jos alege [[track]] = A1.", "In the bottom bar choose [[track]] = A1.", "En la barra inferior elige [[track]] = A1."),
                T("Deschide [[tabAuto]] › [[rRandom]].", "Open [[tabAuto]] › [[rRandom]].", "Abre [[tabAuto]] › [[rRandom]]."),
                T("Setează [[fillSource]] = [[fillLib]] și [[fillMax]] = 5.", "Set [[fillSource]] = [[fillLib]] and [[fillMax]] = 5.", "Configura [[fillSource]] = [[fillLib]] y [[fillMax]] = 5."),
                T("Apasă [[fillPlan]] și citește planul (ce sunet merge pe ce marker).", "Press [[fillPlan]] and read the plan (which sound goes on which marker).", "Pulsa [[fillPlan]] y lee el plan (qué sonido va en qué marcador)."),
                T("Nu-ți place? Apasă [[fillReshuffle]] până când te mulțumește.", "Do not like it? Press [[fillReshuffle]] until you are happy.", "¿No te gusta? Pulsa [[fillReshuffle]] hasta que te convenza."),
                T("Apasă [[fillApply|n=3]].", "Press [[fillApply|n=3]].", "Pulsa [[fillApply|n=3]].")],
         see=[T("Mesajul „[[=fillDone|n=3,track=A1]]” și trei clipuri pe A1, câte unul la fiecare marker. Planul rămâne vizibil.", "The message “[[=fillDone|n=3,track=A1]]” and three clips on A1, one at each marker. The plan stays visible.", "El mensaje «[[=fillDone|n=3,track=A1]]» y tres clips en A1, uno en cada marcador. El plan sigue visible.")],
         example=T("În clip: cele trei markere Hit primesc fiecare un sunet scurt din folderul demo.", "In the clip: the three Hit markers each get a short sound from the demo folder.", "En el clip: los tres marcadores Hit reciben cada uno un sonido corto de la carpeta demo."),
         fix=T("Cmd+Z de trei ori în Resolve (un pas per clip) sau selectează cele trei clipuri și șterge-le. Planul e gol: „[[=fillNoMarkers]]” sau „[[=fillNoSounds]]”; adaugă markere sau mărește [[fillMax]] și apasă din nou [[fillPlan]].",
               "Cmd+Z three times in Resolve (one step per clip) or select the three clips and delete them. Empty plan: “[[=fillNoMarkers]]” or “[[=fillNoSounds]]”; add markers or raise [[fillMax]] and press [[fillPlan]] again.",
               "Cmd+Z tres veces en Resolve (un paso por clip) o selecciona los tres clips y bórralos. Plan vacío: «[[=fillNoMarkers]]» o «[[=fillNoSounds]]»; añade marcadores o sube [[fillMax]] y pulsa [[fillPlan]] de nuevo.")),
    dict(n=7, file="07-asociaza-rapid-sunete-cu-markerele", title="Asociază rapid sunete cu markerele", chap=(11,),
         goal=T("Alegi tu sunetul pentru fiecare marker, pe rând, fără să muți cursorul de mână.", "You choose the sound for each marker, one by one, without moving the cursor by hand.", "Eliges tú el sonido para cada marcador, uno a uno, sin mover el cursor a mano."),
         need=[T("Timeline-ul cu cele trei markere, biblioteca demo și pista A2 liberă.", "The timeline with the three markers, the demo library and a free track A2.", "El timeline con los tres marcadores, la biblioteca demo y la pista A2 libre.")],
         steps=[T("Alege pista A2 în bara de jos ([[track]]).", "Choose track A2 in the bottom bar ([[track]]).", "Elige la pista A2 en la barra inferior ([[track]])."),
                T("Deschide [[tabAuto]] › [[rMap]] și apasă [[mapStart]].", "Open [[tabAuto]] › [[rMap]] and press [[mapStart]].", "Abre [[tabAuto]] › [[rMap]] y pulsa [[mapStart]]."),
                T("Cursorul sare pe primul marker; bannerul arată ținta („Hit 1 (1/3)”).", "The cursor jumps to the first marker; the banner shows the target (“Hit 1 (1/3)”).", "El cursor salta al primer marcador; el banner muestra el destino («Hit 1 (1/3)»)."),
                T("În [[tabFolders]] apasă cardul Ding Bright (doar îl alege), apoi apasă [[place]].", "In [[tabFolders]] click the Ding Bright card (it only selects it), then press [[place]].", "En [[tabFolders]] pulsa la tarjeta Ding Bright (solo la elige) y luego pulsa [[place]]."),
                T("Ținta trece la Hit 2: alege Impact Low și apasă [[place]]; la Hit 3: Whoosh Soft și [[place]].", "The target moves to Hit 2: choose Impact Low and press [[place]]; at Hit 3: Whoosh Soft and [[place]].", "El destino pasa a Hit 2: elige Impact Low y pulsa [[place]]; en Hit 3: Whoosh Soft y [[place]]."),
                T("Dacă un marker nu are nevoie de sunet, apasă [[mapSkip]].", "If a marker needs no sound, press [[mapSkip]].", "Si un marcador no necesita sonido, pulsa [[mapSkip]].")],
         see=[T("După fiecare [[place]], mesajul „Ding Bright” plasat pe A2 la 01:00:01:00 (timecode-ul markerului) și ținta trece la următorul marker; la final „[[=mapDone|n=3]]”.", "After each [[place]], the message Placed “Ding Bright” on A2 at 01:00:01:00 (the marker’s timecode) and the target moves to the next marker; at the end “[[=mapDone|n=3]]”.", "Tras cada [[place]], el mensaje «Ding Bright» colocado en A2 en 01:00:01:00 (el timecode del marcador) y el destino pasa al siguiente marcador; al final «[[=mapDone|n=3]]».")],
         example=T("Ding Bright pe primul marker, Impact Low pe al doilea, Whoosh Soft pe al treilea, toate pe A2.", "Ding Bright on the first marker, Impact Low on the second, Whoosh Soft on the third, all on A2.", "Ding Bright en el primer marcador, Impact Low en el segundo, Whoosh Soft en el tercero, todos en A2."),
         fix=T("[[mapPrev]] revine la markerul anterior ca să plasezi din nou; [[mapExit]] oprește maparea; un clip greșit se anulează cu Cmd+Z în Resolve. „[[=mapNone]]”: adaugă markere. Dacă o plasare e refuzată, ținta rămâne pe același marker: schimbă pista sau apasă [[mapSkip]].",
               "[[mapPrev]] goes back to the previous marker so you can place again; [[mapExit]] stops mapping; a wrong clip is undone with Cmd+Z in Resolve. “[[=mapNone]]”: add markers. If a placement is refused the target stays on the same marker: change the track or press [[mapSkip]].",
               "[[mapPrev]] vuelve al marcador anterior para colocar otra vez; [[mapExit]] detiene el mapeo; un clip equivocado se deshace con Cmd+Z en Resolve. «[[=mapNone]]»: añade marcadores. Si se rechaza una colocación, el destino se queda en el mismo marcador: cambia la pista o pulsa [[mapSkip]].")),
]


def loc(field, lang):
    i = LANGS.index(lang)
    if isinstance(field, list): return [x[i] for x in field]
    return field[i]


def ro_names(lang, tut):
    """For EN/ES: 'English label = Romanian label' for every UI name used (the clips are filmed in Romanian)."""
    if lang == "ro": return []
    texts = [loc(tut[k], lang) for k in ("goal", "example", "fix")]
    for k in ("need", "steps", "see"): texts += loc(tut[k], lang)
    out = []
    for k in keys_in(*texts):
        a, b = I18N[lang][k], I18N["ro"][k]
        if a != b and "{" not in a: out.append((a, b))
    return out

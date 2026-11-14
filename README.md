# SoundSFXPaste

[English](README.md) · [Română](README.ro.md) · [Español](README.es.md)

A sound-effects library panel for DaVinci Resolve: browse with real waveforms, audition, and place on the timeline safely.

![SoundSFXPaste](docs/img/en-folders.png)

## Features

- Folder grid with real waveforms, audition on hover or click, Favorites and Recents.
- Place at the playhead on a chosen track; track and position are shown next to the Place button.
- Safe placement: every write is planned first, verified afterwards and rolled back if it differs.
- Auto SFX: Random Fill on markers, Replace, marker management, Rapid Mapping.
- Plain-language "Verify & Dependencies" panel (Python, Resolve scripting, project, timeline, frame rate).
- English, Romanian, Spanish. Free and open source (MIT); no activation.

## Requirements

- macOS with DaVinci Resolve Studio 21 (Workflow Integrations).
- Python 3.8 or newer on the system (the panel tells you what to do if it is missing).
- Resolve > Preferences > General > External scripting using: Local.

## Install

Download the signed and notarized installer from the Releases page, run it, then open Workspace > Workflow Integrations > SoundSFXPaste.

## Known limits

- Drop-frame timelines are refused (reported in the dependencies panel).
- Resolve has no API to set a clip selection or rename markers; Replace works on the current selection or the clip under the playhead.
- macOS only for now.
- Dragging a sound straight onto the timeline is not available; placement uses the Place button.

## Contributing

Issues and pull requests are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Documentation: [gordas.dev/soundsfxpaste](https://gordas.dev/soundsfxpaste/).

## Documentation

Illustrated step-by-step manuals (PDF, 20 pages each), regenerated with `python3 scripts/build_manual.py`:

- [Manual PDF — Română](https://gordas.dev/soundsfxpaste/manual/SoundSFXPaste-Manual-RO-0.2.0.pdf)
- [PDF manual — English](https://gordas.dev/soundsfxpaste/manual/SoundSFXPaste-Manual-EN-0.2.0.pdf)
- [Manual PDF — Español](https://gordas.dev/soundsfxpaste/manual/SoundSFXPaste-Manual-ES-0.2.0.pdf)
- Video tutorials (no voice, Romanian interface): https://gordas.dev/soundsfxpaste/en/#clip-1

<!-- tutorials:start -->
## Tutorials

One written tutorial per video clip (the clips are filmed with the Romanian interface, no voice). Full explanations are in the PDF manual; the same text is on the product page.

### 1. Deschide panoul și adaugă un folder de sunete

Watch: [https://gordas.dev/soundsfxpaste/en/#clip-1](https://gordas.dev/soundsfxpaste/en/#clip-1) · [MP4](https://gordas.dev/soundsfxpaste/video/01-deschide-panoul-si-adauga-un-folder-de-sunete.mp4)

The SoundSFXPaste panel open in Resolve with a sound library loaded in it.

1. In Resolve choose Workspace › Workflow Integrations › SoundSFXPaste.
2. Wait for the panel window; the bottom bar should say “Connected”.
3. In the **Library** column press + (**Add folder**).
4. In the Finder window choose the demo-audio folder and confirm.
5. Open **All sounds** and look at the cards.

**Result:** The folder shows in **Library** with the number 6 and **All sounds** shows six cards with waveforms.

**If it differs:** Panel does not appear: check you run Resolve Studio (the free version does not run panels) and repeat the menu. The indicator says “Not connected”: open a project and a timeline in Resolve. Folder missing: press **Refresh** or add it again; files on disk are never deleted when you remove a folder.

### 2. Caută, ascultă și plasează un sunet la cursor

Watch: [https://gordas.dev/soundsfxpaste/en/#clip-2](https://gordas.dev/soundsfxpaste/en/#clip-2) · [MP4](https://gordas.dev/soundsfxpaste/video/02-cauta-asculta-si-plaseaza-un-sunet-la-cursor.mp4)

A sound found by search, auditioned and placed on the timeline exactly at the cursor.

1. In Resolve park the cursor on 01:00:05:00.
2. In the panel, in **Search sounds**, type “whoosh”; one card is left.
3. Press ► on the card (**Audition**); the button becomes **Stop** while it plays. Nothing changes in the timeline.
4. Click the card to choose it (gold outline).
5. In the bottom bar check **Track** = A1 and the yellow timecode 01:00:05:00.
6. Press **Place**.

**Result:** Green message: “Whoosh Soft” placed on A1 at 01:00:05:00 (1.4 s); a new clip on A1; the cursor jumps to 01:00:06:09, the end of the clip.

**If it differs:** Cmd+Z in Resolve or delete the clip. Placement refused (the track already has a clip there): choose another track or press **Add track** and repeat. The sound is too long: the panel asks for a second press on **Place** to confirm.

### 3. Scurtează un sunet

Watch: [https://gordas.dev/soundsfxpaste/en/#clip-3](https://gordas.dev/soundsfxpaste/en/#clip-3) · [MP4](https://gordas.dev/soundsfxpaste/video/03-scurteaza-un-sunet.mp4)

From Riser Short (2.5 s) you place only the second between 0.80 s and 1.80 s.

1. Choose the Riser Short card.
2. Press **Trim…**; “Trim before placing” opens with the sound’s waveform.
3. First click: on the wave at 0.80 s (about a third of the width). This moves the start of the range.
4. Second click: on the wave at 1.80 s (about three quarters). This moves the end.
5. Read “0.80 s → 1.80 s” under the wave; the chosen part is lit.
6. Press **Place trimmed**.

**Result:** A 1 s clip (24 frames at 24 fps) on A1 at 01:00:03:00; green message “Riser Short” placed on A1 at 01:00:03:00 (1.0 s); the cursor jumps to the end of the clip.

**If it differs:** A click moves the nearest end; it does not create a new range. Different numbers: press **Clear selection** and repeat the two clicks. **Cancel** (or Esc) closes without placing. After placing, Cmd+Z in Resolve.

### 4. Înlocuiește un sunet în timeline

Watch: [https://gordas.dev/soundsfxpaste/en/#clip-4](https://gordas.dev/soundsfxpaste/en/#clip-4) · [MP4](https://gordas.dev/soundsfxpaste/video/04-inlocuieste-un-sunet-in-timeline.mp4)

A clip on the timeline swapped for another sound, on the same track and at the same timecode.

1. In **Folders** pick the Ding Bright card (the new sound).
2. Open **Auto SFX** › **Replace**.
3. At **Target** choose **Clip under the cursor**.
4. Press **Preview** and read the table: which clip is replaced and by what.
5. If it is the one you want, press **Replace**.

**Result:** The message “Replaced 1 clip(s).”; on A1 at 01:00:05:00 the clip is now named Ding Bright.

**If it differs:** Cmd+Z in Resolve brings back the old clip. The preview table is not what you want: do not press **Replace**; change **Target** or move the cursor. Message “No clip to replace: select clips in Resolve, or park the cursor over one.”: park the cursor over a clip or select clips in Resolve.

### 5. Folosește markere și etichete

Watch: [https://gordas.dev/soundsfxpaste/en/#clip-5](https://gordas.dev/soundsfxpaste/en/#clip-5) · [MP4](https://gordas.dev/soundsfxpaste/video/05-foloseste-markere-si-etichete.mp4)

The timeline’s markers get clear names and tags, straight from the panel.

1. Open **Auto SFX** › **Manage markers**.
2. On the first row, in **Marker name**, type “Door slam” and press Tab.
3. In **Tags** type “door” and press Enter.
4. Look at the row and at the marker on the timeline.

**Result:** The message “Markers updated.”; the row shows the new name and the “door” bubble; the timeline marker has the new name.

**If it differs:** Retype the name or press × on the tag. Deleting a marker cannot be undone from the panel: use Cmd+Z in Resolve right after. “No markers on this timeline.”: add markers to the timeline.

### 6. Completează markerele cu sunete aleatorii

Watch: [https://gordas.dev/soundsfxpaste/en/#clip-6](https://gordas.dev/soundsfxpaste/en/#clip-6) · [MP4](https://gordas.dev/soundsfxpaste/video/06-completeaza-markerele-cu-sunete-aleatorii.mp4)

A short, randomly chosen sound on every marker, in a single apply.

1. In the bottom bar choose **Track** = A1.
2. Open **Auto SFX** › **Random Fill**.
3. Set **Pick from** = **Current folder** and **Max length (s)** = 5.
4. Press **Plan** and read the plan (which sound goes on which marker).
5. Do not like it? Press **Reshuffle** until you are happy.
6. Press **Apply 3 sounds**.

**Result:** The message “Filled 3 markers on A1.” and three clips on A1, one at each marker. The plan stays visible.

**If it differs:** Cmd+Z three times in Resolve (one step per clip) or select the three clips and delete them. Empty plan: “There are no markers on this timeline.” or “No sounds in this source are short enough (or their length is not known yet).”; add markers or raise **Max length (s)** and press **Plan** again.

### 7. Asociază rapid sunete cu markerele

Watch: [https://gordas.dev/soundsfxpaste/en/#clip-7](https://gordas.dev/soundsfxpaste/en/#clip-7) · [MP4](https://gordas.dev/soundsfxpaste/video/07-asociaza-rapid-sunete-cu-markerele.mp4)

You choose the sound for each marker, one by one, without moving the cursor by hand.

1. Choose track A2 in the bottom bar (**Track**).
2. Open **Auto SFX** › **Rapid Mapping** and press **Start mapping**.
3. The cursor jumps to the first marker; the banner shows the target (“Hit 1 (1/3)”).
4. In **Folders** click the Ding Bright card (it only selects it), then press **Place**.
5. The target moves to Hit 2: choose Impact Low and press **Place**; at Hit 3: Whoosh Soft and **Place**.
6. If a marker needs no sound, press **Skip**.

**Result:** After each **Place**, the message Placed “Ding Bright” on A2 at 01:00:01:00 (the marker’s timecode) and the target moves to the next marker; at the end “All 3 markers visited.”.

**If it differs:** **Previous** goes back to the previous marker so you can place again; **Exit** stops mapping; a wrong clip is undone with Cmd+Z in Resolve. “Mapping needs at least one marker.”: add markers. If a placement is refused the target stays on the same marker: change the track or press **Skip**.

<!-- tutorials:end -->

## Licence

MIT. Author: Dumitru Cristinel Gordas (GDC). Support is optional and takes the form of a donation. See NOTICE.md and docs/PROVENANCE.md.

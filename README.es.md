# SoundSFXPaste

[English](README.md) · [Română](README.ro.md) · [Español](README.es.md)

Panel de biblioteca de efectos de sonido para DaVinci Resolve: explora con formas de onda reales, escucha y coloca en la línea de tiempo con seguridad.

![SoundSFXPaste](docs/img/en-folders.png)

## Funciones

- Cuadrícula de carpetas con formas de onda reales, escucha, Favoritos y Recientes.
- Colocación en el cursor sobre la pista elegida; pista y posición visibles junto al botón Colocar.
- Colocación segura: cada escritura se planifica, se verifica y se revierte si difiere.
- Auto SFX: Relleno aleatorio en marcadores, Reemplazo, gestión de marcadores, Rapid Mapping.
- Panel «Verificación y dependencias» en lenguaje sencillo (Python, scripting de Resolve, proyecto, timeline, frame rate).
- Inglés, rumano, español. Gratis y de código abierto (MIT); sin activación.

## Requisitos

- macOS con DaVinci Resolve Studio 21 (Workflow Integrations).
- Python 3.8 o superior en el sistema (el panel indica qué hacer si falta).
- Resolve > Preferences > General > External scripting using: Local.

## Instalación

Descarga el instalador firmado y notarizado desde Releases, ejecútalo y abre Workspace > Workflow Integrations > SoundSFXPaste.

## Límites conocidos

- Las líneas de tiempo drop-frame se rechazan (se indica en el panel de dependencias).
- Resolve no tiene API para fijar la selección ni renombrar marcadores; Reemplazar usa la selección actual o el clip bajo el cursor.
- Solo macOS por ahora.
- Arrastrar un sonido directo a la línea de tiempo no está disponible; se coloca con el botón Colocar.

## Contribuir

Se aceptan incidencias y pull requests; consulta [CONTRIBUTING.md](CONTRIBUTING.md). Documentación: [gordas.dev/soundsfxpaste](https://gordas.dev/soundsfxpaste/es/).

## Documentación

Manuales ilustrados paso a paso (PDF, 15 páginas cada uno), regenerados con `python3 scripts/build_manual.py`:

- [Manual PDF — Română](https://gordas.dev/soundsfxpaste/manual/SoundSFXPaste-Manual-RO-0.2.0.pdf)
- [PDF manual — English](https://gordas.dev/soundsfxpaste/manual/SoundSFXPaste-Manual-EN-0.2.0.pdf)
- [Manual PDF — Español](https://gordas.dev/soundsfxpaste/manual/SoundSFXPaste-Manual-ES-0.2.0.pdf)
- Tutoriales en vídeo (sin voz, interfaz en rumano): https://gordas.dev/soundsfxpaste/#tutoriale-video

## Licencia

MIT. Autor: Dumitru Cristinel Gordas (GDC). El apoyo es opcional y se hace como donación. Ver NOTICE.md y docs/PROVENANCE.md.

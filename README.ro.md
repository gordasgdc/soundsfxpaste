# SoundSFXPaste

[English](README.md) · [Română](README.ro.md) · [Español](README.es.md)

Panou cu bibliotecă de efecte sonore pentru DaVinci Resolve: răsfoiești cu forme de undă reale, asculți și plasezi sigur pe timeline.

![SoundSFXPaste](docs/img/en-folders.png)

## Funcționalități

- Grilă de foldere cu forme de undă reale, ascultare, Favorite și Recente.
- Plasare la cursor pe pista aleasă; pista și poziția se văd lângă butonul Plasează.
- Plasare sigură: fiecare scriere e planificată, verificată după și anulată dacă diferă.
- Auto SFX: Umplere aleatorie pe markere, Înlocuire, gestionare markere, Rapid Mapping.
- Panou „Verificare & Dependențe” în limbaj simplu (Python, scripting Resolve, proiect, timeline, frame rate).
- Engleză, română, spaniolă. Gratuit și open source (MIT); fără activare.

## Cerințe

- macOS cu DaVinci Resolve Studio 21 (Workflow Integrations).
- Python 3.8 sau mai nou în sistem (panoul spune ce ai de făcut dacă lipsește).
- Resolve > Preferences > General > External scripting using: Local.

## Instalare

Descarcă installerul semnat și notarizat din pagina Releases, rulează-l, apoi deschide Workspace > Workflow Integrations > SoundSFXPaste.

## Limite cunoscute

- Timeline-urile drop-frame sunt refuzate (apare în panoul de dependențe).
- Resolve nu are API pentru setarea selecției sau redenumirea markerelor; Înlocuirea lucrează pe selecția curentă sau pe clipul de sub cursor.
- Deocamdată doar macOS.
- Tragerea unui sunet direct pe timeline nu este disponibilă; plasarea se face cu butonul Plasează.

## Contribuții

Sesizările și pull request-urile sunt binevenite; vezi [CONTRIBUTING.md](CONTRIBUTING.md). Documentație: [gordas.dev/soundsfxpaste](https://gordas.dev/soundsfxpaste/).

## Licență

MIT. Autor: Dumitru Cristinel Gordas (GDC). Susținerea este opțională și ia forma unei donații. Vezi NOTICE.md și docs/PROVENANCE.md.

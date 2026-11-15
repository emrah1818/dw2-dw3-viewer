# DW2 Mod Studio 0.95 (Release-Kandidat: volle DW3-Qualität, keine künstlichen Größengrenzen)

## Keine automatische Verkleinerung mehr
- **PS1-Image:** Ist eine Modell- oder Bewegungsdatei größer als das Original, wird sie ans Ende des Images
  verlagert. Dateitabelle des Spiels, ISO-Einträge und Volumengröße werden angepasst. Dreiecke und Bewegungsbilder
  bleiben vollständig. Verkleinert wird nur mit ausdrücklicher Zustimmung und nur, wenn Verlagern unmöglich ist.
  Der Bericht nennt jede verlagerte Datei mit alter und neuer Größe.
- **PC-Port:** volle Geometrie. HD-Texturen bis 2048×4096 werden auf der Grafikkarte in voller Größe gezeichnet
  (bis 512 MiB Texturspeicher, bei Bedarf angelegt, protokolliert).

## Texturqualität
- Atlas aus den genutzten UV-Bereichen, ein gemeinsamer Maßstab (rc4: feste 64×112-Kacheln).
- HD-Textur über die gerundeten Spiel-UVs auf die Originaltexel abgebildet: keine hellen Kantenlinien, UV-Rundung
  ausgeglichen. Die 1x-Palette kommt aus den Originalfarben.
- Augen werden erkannt (Greymon). Blinzeln behält die HD-Textur, im Port und in der Studio-HD-Vorschau.

## Studio
- Karte „DW3-Import: Qualität (gemessen)“: Quelle gegen Ergebnis (Dreiecke, Vertices, Seiten, exakte Texel,
  PSNR, UV-Rundung, Augen) und das DW3-Original im Viewer.
- Modus A zeigt automatisch die HD-Textur. Pixel-Look ist nur noch ein Filter.

Messwerte: `TESTERGEBNISSE_0.95.md`. Grenzen: `GRENZEN_ANALYSE_0.95.md`, `EINSCHRAENKUNGEN_0.95.md`.

# DW2 Mod Studio 1.0.0-rc2 (Release-Kandidat) mit passendem PC-Port

**Kein 1.0.0 FINAL.** Die neuen Funktionen sind im Spiel geprüft (PC-Port unter Linux, PS1-Image im Emulator).
Für FINAL fehlen noch geprüfte Punkte: echter Windows-PC mit Grafikkarten-Renderer, dein echtes PS1-Abbild,
DNA-Digitation, Spieltests auf weiteren Domains. DW3-Effekte, -Töne und -Kamerafahrten werden weiterhin
**nicht** übertragen (es gibt einen DW2-Ersatz). Details: `EINSCHRAENKUNGEN_1.0.0-rc2.md`, `TESTERGEBNISSE_1.0.0-rc2.md`.

## Neu gegenüber 1.0.0-rc1
- **PC-Port (Mod-Studio-Zweig):** Der Port liest `Mods\digivolve_levels.json` (eigene Mindestlevel im Digi-Labor) und
  `Mods\battle_camera.json` (Angriffs-, Ziel- und Nahaufnahmekamera je Digimon). HD-Ersatztexturen bleiben jetzt auch
  beim Blinzeln und bei Farbblitzen erhalten. Ohne diese Dateien verhält sich der Port wie bisher.
- **Kampfkamera je Digimon:** Abstand, Höhe, Zielpunkt und Winkel, Vorschau aller Einstellungen wie im Spiel.
  Beim DW3-Import wird die Kamera automatisch so gesetzt, dass das Digimon ganz im Bild ist.
- **Bessere Qualität importierter DW3-Digimon:** weiche Normalen, HD-Stufe automatisch passend zur DW3-Textur.
- **Größe:** automatischer Maßstab (DW2-Verhältnisse oder DW3-Verhältnisse), Schieberegler je Digimon mit Live-Vorschau.
- **Namen ändern:** eigener Knopf und Reiter „Bearbeiten“.
- **Zwei getrennte Modi:** A PC-Port (Mods-Ordner) und B PS1-Image (neues BIN/CUE oder ISO für Emulatoren).
  Im PS1-Modus werden zu große DW3-Modelle kontrolliert verkleinert (Dreiecke, Bildschritt der Animation) und der
  Bericht zeigt, was verändert wurde. Jeder BIN-Export bekommt eine passende CUE-Datei.
- Die grüne Gitter-Darstellung bei der Befehlswahl ist ein normales DW2-Merkmal und bleibt unverändert.

## Dateien
- `DW2_Mod_Studio_1.0.0-rc2_Windows_x64.zip`: das Programm (entpacken, `DW2_3D_Viewer_Studio.exe` starten).
- `DW2_PC_Port_API2_1.0.0-rc2_Windows_x64.zip`: passender PC-Port (Zweig `development/mod-studio-1.0`), ohne Spieldaten.
- `test-results.xml`, `test-summary.txt`, `windows-smoke.json`, `SHA256SUMS.txt`.
- Anleitung, Änderungsprotokoll, Testergebnisse und Einschränkungen liegen im Programm-ZIP.

Es sind keine Spieldaten enthalten. Du brauchst deine eigene `dw2.pak` bzw. dein eigenes DW2-Abbild und für den
DW3-Import dein eigenes DW3-Abbild.

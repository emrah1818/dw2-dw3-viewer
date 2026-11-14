# DW2 Mod Studio 1.0.0-rc3 (Release-Kandidat) mit passendem PC-Port

**Kein 1.0.0 FINAL.** Neu im Spiel geprüft: DNA-Digitation mit importierten Digimon, geänderte Gegner auf drei
weiteren Domains, im PS1-Emulator Digitation in ein importiertes Digimon, DNA und ein vom PS1-Spiel geschriebener
Spielstand. Für FINAL fehlen weiterhin Tests auf einem echten Windows-PC (Grafikkarten-Renderer, HD bis 2048×4096)
und mit deiner Original-BIN. DW3-Effekte, -Töne und -Kamerafahrten werden nicht übertragen.
Details: `EINSCHRAENKUNGEN_1.0.0-rc3.md`, `TESTERGEBNISSE_1.0.0-rc3.md`.

## Neu gegenüber 1.0.0-rc2
- **Behoben:** Der DW3-Import brach bei großen Modellen mit „Mehr als 256 Normalen in einem Knochen“ ab.

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
- `DW2_Mod_Studio_1.0.0-rc3_Windows_x64.zip`: das Programm (entpacken, `DW2_3D_Viewer_Studio.exe` starten).
- `DW2_PC_Port_API2_1.0.0-rc3_Windows_x64.zip`: passender PC-Port (Zweig `development/mod-studio-1.0`), ohne Spieldaten.
- `test-results.xml`, `test-summary.txt`, `windows-smoke.json`, `SHA256SUMS.txt`.
- Anleitung, Änderungsprotokoll, Testergebnisse und Einschränkungen liegen im Programm-ZIP.

Es sind keine Spieldaten enthalten. Du brauchst deine eigene `dw2.pak` bzw. dein eigenes DW2-Abbild und für den
DW3-Import dein eigenes DW3-Abbild.

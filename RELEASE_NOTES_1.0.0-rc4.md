# DW2 Mod Studio 1.0.0-rc4 (Release-Kandidat) mit passendem PC-Port

**Kein 1.0.0 FINAL.** Neu getestet auf einem echten Windows-PC (GTX 1070, Vulkan): Port mit Grafikkarte und HD-Texturen
bis 2048×4096 im Kampf, Mod Studio mit deiner Original-BIN. Im PS1-Emulator mit deiner Original-BIN: Export,
Digitation, DNA, Speichern. Es fehlen weiterhin echte PS1-Hardware, Spieltests auf allen Domains und mit allen
DW3-Modellen. DW3-Effekte, -Töne und -Kamerafahrten werden nicht übertragen.
Details: `EINSCHRAENKUNGEN_1.0.0-rc4.md`, `TESTERGEBNISSE_1.0.0-rc4.md`.

## Neu gegenüber 1.0.0-rc3
- **Port, GPU-Renderer:** HD-Ersatztexturen bleiben im Grafikspeicher. Mit mehreren 2048×4096-Importen lief der
  128-MiB-Speicher über, wurde in jedem Kampf neu gefüllt und zeigte zwischendurch die niedrige Textur. Jetzt nimmt
  der Renderer bei Bedarf eine kleinere Stufe (höchstens 1024×2048 je Seite).
- **Port:** kein Absturz mehr, wenn die Nahaufnahme-Kamera ein leeres Kämpferfeld abfragt. `--press-file` für lange
  Testeingaben.
- **Studio:** Umbenennen wirkt sofort. Vorher wartete es unter Windows minutenlang hinter der Größentabelle. Die
  Größenkarte lädt beim Aufklappen und wird pro Image gespeichert. Der Name unter dem 3D-Bild wird aktualisiert, und
  Kopf und Startseite zeigen die richtige Version.
- **Studio:** Der DW3-Import bricht bei großen Modellen nicht mehr mit „Mehr als 256 Normalen“ ab (aus rc3).

## Aus 1.0.0-rc2 (gegenüber rc1)
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
- `DW2_Mod_Studio_1.0.0-rc4_Windows_x64.zip`: das Programm (entpacken, `DW2_3D_Viewer_Studio.exe` starten).
- `DW2_PC_Port_API2_1.0.0-rc4_Windows_x64.zip`: passender PC-Port (Zweig `development/mod-studio-1.0`), ohne Spieldaten.
- `test-results.xml`, `test-summary.txt`, `windows-smoke.json`, `SHA256SUMS.txt`.
- Anleitung, Änderungsprotokoll, Testergebnisse und Einschränkungen liegen im Programm-ZIP.

Es sind keine Spieldaten enthalten. Du brauchst deine eigene `dw2.pak` bzw. dein eigenes DW2-Abbild und für den
DW3-Import dein eigenes DW3-Abbild.

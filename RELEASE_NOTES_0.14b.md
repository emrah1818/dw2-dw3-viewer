# DW2 / DW3 Viewer 0.14b — Beta

- Vorhandenen DW2-Viewer 4.0 und Mod Studio übernommen.
- `dw2.pak` direkt öffnen: Katalog, native Modell-/Animationsvorschau und
  bestehende Namen-/Typ-/Attacken-/Werteeditoren ohne rekonstruierte Disc.
- PAK- und Mod-Export an die Desktop-Oberfläche angebunden; Projekt-Rundlauf geprüft.
- **Kompatibilitätsfehler behoben:** Mod-Dateien heißen jetzt hexadezimal
  `NNNN.bin`, entsprechend `host/pak.c` des PC-Ports. Der alte Export verwendete
  dezimale Namen und konnte dadurch falsche Dateien ansprechen.
- Bestehende Mod-IDs einschließlich alternativer Groß-/Kleinschreibung schützen;
  echte Original-Payload-Prüfsumme vor dem Export prüfen; Audio/Video sperren.
- DW3-USA-/DW2003-Europa-Images mit versteckten Modelleinträgen lesen.
- Headless-DW3-Konverter: Skelett, Texturen und Bewegungen nach GLB/PNG;
  Vorschau, ZIP-Export und Übergabe an die manuelle DW2-Knochenzuordnung.
- Starre glTF-Skin-Gruppen beim Import getrennt zuordenbar erhalten.
- Windows-Build und Startprüfung als GitHub Actions; Veröffentlichung als Prerelease.

## Geprüft mit den bereitgestellten Daten

Alle 3.675 PAK-Einträge SHA-256-verifiziert. 249 DW3-Modelldateien gefunden;
248 nach GLB konvertiert, insgesamt 4.186 Animationsclips. `M500WAVE` besitzt
keine vom Konverter erkannte Knochenliste und wird mit Fehlermeldung abgewiesen.
Konvertierte PNG-Dateien wurden mit Pillow geprüft. Diese Prüfung bestätigt
Dateistruktur und Lesbarkeit, nicht die visuelle Korrektheit jedes Clips.

## Noch offen

Dies ist **nicht die vollständige Umsetzung des Gesamtauftrags**.
DW3-Animationen bleiben in GLB/Vorschau; nativer DW2-Ersatz verwendet die
Zielanimationen. Größere Modelle/HD-Texturen im PC-Port, ein neuer Digitation-/DP-Editor,
vollständige Übertragung mehrerer Texturseiten und ein Spiel-Ende-zu-Ende-Test
auf Windows stehen aus. Es gibt keine neue PC-Port-Engine-Unterstützung.
Native Größen-, Skelett- und Palettengrenzen werden weiterhin geprüft.

Historische Berichte zu 3.x/4.x beschreiben die jeweilige Vorversion.
Aktueller Stand und Testgrenzen: `README.md` und `VALIDATION_0.14b.md`.

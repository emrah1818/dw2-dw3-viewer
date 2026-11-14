# DW2 Mod Studio 0.17b – Testversion

Nachfolger des DW2/DW3 Viewers 0.16b. Alle bisherigen Funktionen bleiben erhalten. Keine Spieldaten im Paket: Du öffnest deine eigene `dw2.pak` (und für den Import dein eigenes Digimon World 3).

**Downloads:** `DW2_Mod_Studio_0.17b_Windows_x64.zip` (Programm) und `DW2_PC_Port_API2_0.17b_Windows_x64.zip` (passender PC-Port mit Mod-Schnittstelle 2, unverändert gegenüber 0.16b). Beide vollständig in getrennte Ordner entpacken.

## Neu

- **Neun Bereiche** in einem Fenster: Dateien, 3D-Viewer, Digimon, Attacken, Digitation, Domains, DW3-Import, Texturen, Mod-Export.
- **Eigene Techniken je Digimon:** Kopie einer vorhandenen Technik (Effekte, Animationsteile, Ton) unter einer freien ID 1–255 mit eigenem Namen, Beschreibung, MP, Stärke, Element und Startanimation. Andere Digimon bleiben unverändert.
- **Domain-Editor:** Gegnergruppen je Etage aller 35 Domains, vollständige Gruppen (Kartenfigur, KI, Tempo, Geschenk, Musik, Boss, drei Gegner mit Level, Werten und Techniken), Gruppen kopieren.
- **Digitationslinien:** mehrere Digimon mit Zielen, DP-Grenzen und Stufe in einem Schritt.
- **Mehrere DW3-Digimon auf einmal** ersetzen, mit Namen. Bewegungen, Größe und Kamera werden automatisch gesetzt.
- **Kampfkamera und Treffereffekt-Höhe** je Digimon, automatisch beim Import, im Digimon-Editor einstellbar.
- **Mod-Export mit Prüfung:** Dateiliste, Fehler und Konflikte vor dem Schreiben; vorhandenen Mod ersetzen (er wird verschoben, nicht gelöscht); **Mod wieder einlesen**.
- **HD-Vorschau** bis 2048×4096 direkt am Modell.
- **Datei-Explorer:** alle Spieldateien, Suche, geänderte markiert, Original oder Änderung exportieren.

## Was nachgewiesen ist und was nicht

Kurz: Alles Neue ist mit selbst erzeugten Testdaten automatisch geprüft (siehe `test-summary.txt` dieses Release). Lokal lief zusätzlich die ganze Kette mit echten Spieldaten im echten Spielcode (Linux, ohne Fenster): Renamon aus DW3 mit eigener Technik und geänderter Gegnergruppe im ersten Kampf. **Nicht geprüft:** Windows-Hardware, Klicks in der Oberfläche unter Windows, längere Spielverläufe. Details: `TESTERGEBNISSE_0.17b.md`, Grenzen: `EINSCHRAENKUNGEN_0.17b.md`, Bedienung: `ANLEITUNG.md`.

Ein grüner Build heißt nicht, dass jedes importierte Digimon im Spiel fehlerfrei funktioniert.

# Änderungsprotokoll

## 1.0.0-rc1 – 14.11.2026 (Release-Kandidat)

Neu
- **DW3-Gesichter:** Augenrahmen (offen/halb/zu) und Gesichtszyklen aus der DW3-Kämpfertabelle werden in die
  DW2-Augenanimation übertragen (Rahmen im Atlas, 4-Pixel-ausgerichtet, gleiche Palette). Im Spiel nachgewiesen.
  Der DW3-Konverter liefert dafür Seiten und Texturursprung (`native_source.json`: `pages`, `tex_origin`). Ältere
  Zwischenspeicher werden automatisch neu konvertiert.
- **Formatgrenzen (Abschnitt 15):** große Knochen werden in Teile mit höchstens 256 Vertices/Dreiecken geteilt.
  Ebenen unter Ebene 8 hängen mit dem Produkt der übersprungenen Matrizen exakt an Ebene 8. Vor jedem Mod-Export
  prüft eine Endkontrolle alle vorgemerkten Modelle (Teile, Ebenen, Sprünge). Der Import zeigt, was angepasst wird.
- **Techniken:** Effekt / Ton / Zustand / Startanimation aus einer anderen Technik übernehmen. Eine Technik mehreren
  Digimon als erlernbare Technik geben (ein Schritt). Anzeige der freien IDs mit Begründung der 255er-Grenze.
- **Mod einlesen:** erkennt Überschneidungen mit eigenen Änderungen und doppelt belegte Technik-IDs. Ersetzen nur nach Rückfrage.
- **Digitation:** „Alle Digitationen prüfen“ (Kreise, fehlende Ziele, nicht höherstufige Ziele, nicht erreichbare Arten;
  Fehler des Originals als Hinweis).
- **Digitationslevel je Digimon (Vorbereitung):** Format 1, Speicherung im Projekt, Rückgängig, Export als
  `Mods\digivolve_levels.json` mit Warnung. Im aktuellen Port ohne Wirkung (im Spiel geprüft).
- **Kamera-Vorschau:** Nahaufnahme wie im Kampf (Tabellen aus `camera.c`, 4:3, Stufen live) mit Steuerleiste in der 3D-Ansicht.
- **Spieltests** `integration/ingame/run_ingame.py`: Digitation in und aus importierten Digimon, Speichern/Laden,
  Blinzeln, Domain-Gegner, importierter Partner mit eigener Technik im Kampf.
- Analyse der DW3-Effekte: `DW3_EFFEKTE_ANALYSE.md`.
- Eine Versionsquelle (`dw2studio/version.py`).

Behoben
- Gruppe kopieren vergrößerte ENEMYSET unnötig. Die Dateilänge bleibt jetzt, wenn Platz in der Füllung ist.
- 0.17b-Angabe zur Kamera korrigiert: `field_1E` wirkt nachweislich auf die Nahaufnahmen, nicht auf Attackenkameras.

## 0.17b – 14.11.2026 (DW2 Mod Studio)

Neu
- Oberfläche mit neun Bereichen: Dateien, 3D-Viewer, Digimon, Attacken, Digitation, Domains, DW3-Import, Texturen, Mod-Export.
- Eigene Techniken (`dw2studio/core/techniques.py`, `SkillTable.cloned`): Kopie eines WAZADATA-Datensatzes unter freier ID 1–255; Name und Beschreibung hinter dem Endeintrag, Dateilänge bleibt wenn möglich gleich. Zuweisung als erlernbare Technik (DIGIMNDT) und/oder an Gegnerplätze (ENEMYSET). Bearbeiten nur, wenn ausschließlich dieses Digimon die Technik nutzt.
- Domain-Editor (`dw2studio/core/domains.py`): Domain-Tabelle (Datei 0xE20, Eintrag 0xA), Etagen mit `enemySets[5]`, vollständige ENEMYSET-Gruppen, Gruppen kopieren, Verwendung je Gruppe.
- Digitationslinien (`evolution.change_line`): mehrere Arten in einem Schritt, alles oder nichts.
- DW3-Stapelimport (`dw3_batch_apply`) mit Namen; ein Rückgängig-Schritt.
- Kampfkamera und Treffereffekt-Höhe (`dw2studio/core/battle_camera.py`, MODELDT +0x1E/+0x20); automatisch beim DW3-Import aus dem Höhenunterschied, manuell im Digimon-Editor; Grenze 0xBFF wegen der 9-stufigen Kameratabelle.
- Mod-Export mit Prüfung, Konflikterkennung, Ersetzen und Wiedereinlesen (`dw2studio/mod_io.py`).
- HD-Vorschau bis 2048×4096 im 3D-Viewer; HD-Stufe 2048×4096 beim DW3-Import.
- Datei-Explorer mit Export von Original oder Änderung.
- Anzeige der festen Digitationslevel-Regel; Schnittstellenbeschreibung für den Port (`DIGITATIONSLEVEL_SCHNITTSTELLE.md`).

Behoben
- Auswahllisten zeigen unbekannte aktuelle Werte (z. B. Kartenfiguren wie #322) als eigene Option; vorher hätte „Übernehmen“ sie still durch den ersten Listeneintrag ersetzt.

Geändert
- Programmname in Titel und Windows-Versionsinfo: „DW2 Mod Studio“. Der interne Datenordner-Name bleibt, damit Projekte und Zwischenspeicher erhalten bleiben.
- Release enthält Testergebnisse (`test-results.xml`, `test-summary.txt`).

## 0.16b – 14.11.2026
Bewegungen aus DW3-Kampfskripten vorbelegt, Größe nach Standhöhe, HD 2048×4096 beim Import, Mods deaktivieren/aktivieren, Begleit-Port auf Basis 1.6.2-preview. Details: RELEASE_NOTES_0.16b.md.

## 0.15b und früher
RELEASE_NOTES_0.15b.md, RELEASE_NOTES_0.14b.md, PRUEFUNG_v4_0.md.

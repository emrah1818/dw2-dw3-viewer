# Änderungsprotokoll

## 0.98 – 15.11.2026 (Vorabversion)

- Animationseditor aus `development/animation`: mehrteilige DW3-Aktionen, Abschnitte,
  Bildbereiche, Wiederholungen, Übergänge, Loop-Beginn und Kampfsimulation.
- DW3-Namen aus DIGNAM, alternative Suchnamen, Varianten, Vorschaubilder und Name im Editor.
- Namens-/ID-Suche in Oberfläche und Python abgeglichen. Reine Zahlen suchen exakt nach
  Katalog-ID, interner Dateinummer oder Kämpfer-ID, ohne Teiltreffer in Dateinamen.
- Übergänge nach abgeschnittenen Anfangsüberblendungen verwenden die tatsächlich gezeigte
  Pose statt der unverblendeten Quellpose. Export inklusive Loop-Rücksprung binär getestet.
- SciPy für die Matrixüberblendung als direkte Abhängigkeit ergänzt.
- Version in Anwendung, Windows-Dateiressource und lokalem Build-Skript auf 0.98 abgeglichen.
- Windows-Pakete werden erst nach Tests, Build und Startprüfung veröffentlicht;
  vorhandene Releases werden nicht überschrieben. Prüfgrenzen: TESTERGEBNISSE_0.98.md.

## 0.95 – 15.11.2026

DW3-Import
- Texturatlas aus den genutzten UV-Bereichen (Skyline-Packung, gemeinsamer Maßstab) statt fester Kacheln je Seite.
- HD-Textur über die gerundeten Spiel-UVs auf die DW3-Originaltexel abgebildet; Lücken aufgefüllt (keine hellen Kanten).
- 1x-Palette aus den Originalfarben der Seite. Augen über Polygon-Überlappung erkannt.
- Keine automatische Verkleinerung: PS1-Image verlagert größere Dateien; Verkleinern nur mit Zustimmung.
- Größenfaktor bezieht sich immer auf die Original-DW2-Höhen (multiplizierte sich vorher auf).

PC-Port
- HD-Texturen in 24 Bit im GPU-Renderer (`DW2_HD_15BIT=1` schaltet auf 15 Bit).
- Texturspeicher bis 7 × 128 MiB nach Bedarf (`DW2_TEXTURE_MEMORY_MB`), 2048×4096 in voller Größe.
- Blinzeln und andere VRAM-Kopien behalten die HD-Textur. Log: „HD summary“, Speicherbereiche, Grenzen.

Studio
- Qualitätskarte, DW3-Original im Viewer, HD-Vorschau automatisch und mit Blinzeln, Pixel-Look nur als Filter.
- Testwerkzeuge: `integration/uitest/` (Oberfläche in Headless-Chrome), `integration/windows/` (Kampftest).

## 1.0.0-rc4 – 14.11.2026 (Release-Kandidat)

Behoben (gefunden beim Test auf einem Windows-PC mit GTX 1070 und der Original-BIN)
- Port, GPU-Renderer: Bei mehreren 2048×4096-Importen lief der 128-MiB-Speicher für Ersatztexturen über. Er wurde
  in jedem Kampf neu gefüllt, die Modelle zeigten zwischendurch die niedrige Textur. Jetzt wird eine kleinere Stufe
  genommen (höchstens 16 MiB je Stufe). Auf dem PC wird der Speicher im ganzen Lauf nicht mehr neu gefüllt.
- Port: Absturz (Speicherzugriff) beim Abfragen der Nahaufnahme-Kamera für ein leeres Kämpferfeld.
- Studio: Umbenennen erschien erst nach Minuten. Die Bearbeiten-Seite fragte sofort die Größentabelle aller Digimon
  ab, jede Aktion wartete dahinter. Die Größenkarte lädt jetzt beim Aufklappen, die Tabelle wird pro Image gespeichert.
- Studio: Name unter dem 3D-Bild wird nach dem Umbenennen aktualisiert. Kopf und Startseite zeigen die richtige
  Version statt „0.17b“.

Neu
- Port: `--press-file DATEI` für lange Testeingaben (Windows-Kommandozeilen sind begrenzt).
- Windows-Spieltest `integration/windows/` (Battle Mode mit drei HD-Importen über die Grafikkarte).

## 1.0.0-rc3 – 14.11.2026 (Release-Kandidat)

Behoben
- DW3-Import brach bei manchen Modellen mit „Mehr als 256 Normalen in einem Knochen“ ab (z. B. MegaloGrowmon
  in Platz 12). Die weichen Normalen brauchen je Teil mehr Einträge als vorher. Ist die Tabelle voll, nimmt der
  Kodierer jetzt die nächstliegende gespeicherte Normale (nur die Schattierung ist minimal gröber), statt abzubrechen.
  Test: `test_more_than_256_normals_in_one_part`.

Neu geprüft
- DNA-Digitation mit importierten Digimon (PC-Port und PS1-Emulator).
- Geänderte Gegner auf drei weiteren Domains und tieferen Etagen (PC-Port).
- PS1: Digitation in ein importiertes DW3-Digimon im Digi-Labor, Spielstand vom PS1-Spiel geschrieben und vom
  PC-Port gelesen.
- Spieltest-Szenen `dna` und `domains`, PS1-Testwerkzeuge unter `integration/ps1emu/`.

## 1.0.0-rc2 – 14.11.2026 (Release-Kandidat, mit passendem PC-Port)

Neu
- **PC-Port, Zweig `development/mod-studio-1.0`:** liest `Mods\digivolve_levels.json` (Mindestlevel je Digimon im
  Digi-Labor, Mega bleibt gesperrt) und `Mods\battle_camera.json` (Abstand, Höhe, Zielpunkt, Winkel für Angriffs-, Ziel-
  und Nahaufnahmekamera je Digimon). `--mod-api` meldet beides. Fehlende, kaputte oder neuere Dateien ändern nichts.
- **Kampfkamera je Digimon** im Studio mit Vorschau jeder Einstellung (gleiche Projektion wie das Spiel, mit dem
  Modellrechteck des Spiels abgeglichen). Beim DW3-Import automatisch so gesetzt, dass das Modell ganz im Bild ist.
- **Größe:** Maßstab aus den Modellmaßen (DW2-Verhältnisse: gleiche Art wie in DW2, sonst Größenkurve; oder
  DW3-Verhältnisse), Schieberegler je Digimon mit Live-Vorschau, im Projekt gespeichert.
- **Qualität:** weiche Normalen (Knickwinkel bleibt hart), HD-Stufe automatisch passend zur DW3-Textur.
- **Namen:** Knopf „Name ändern“ und Reiter „Bearbeiten“.
- **Zwei Modi:** A PC-Port, B PS1-Image. Im PS1-Modus: DW3-Import mit kontrollierter Verkleinerung (Dreiecke
  zusammenfassen, Animation mit Bildschritt), Bericht der Änderungen; jeder BIN-Export schreibt eine CUE-Datei.
- Projekte speichern Digitationslevel, Kameras und DW3-Importe mit.

Behoben
- Port: HD-Ersatztexturen wurden beim ersten Teilschreiben in die Texturseite (Blinzeln, Farbblitz) verworfen.
  Importierte Digimon erschienen deshalb im Kampf mit der niedrigen Textur.
- PS1-Verkleinerung: kleine Teile, die ganz zusammenfallen würden, bleiben jetzt erhalten.
- Nach einem DW3-Import in ein PS1-Image brach die Oberfläche bei der HD-Anzeige ab.

Unverändert
- Die grüne Gitter-Darstellung bei der Befehlswahl (DW2-Original).

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

DW2 3D Viewer · PC · Version 4.0
Stand: 11.11.2026

START AUF WINDOWS
1. ZIP vollständig in einen normalen Ordner entpacken.
2. Python 3.12 (64 Bit) installieren, falls noch nicht vorhanden.
3. start_windows.bat doppelklicken. Beim ersten Start werden die benötigten
   Python-Pakete installiert. Dafür ist eine Internetverbindung erforderlich.
4. Eigenes Digimon World 2 USA-Spielabbild über „BIN / ISO öffnen“ auswählen.

Dieses Paket enthält den Python-Quellcode, alle Viewer-Dateien und das
Windows-Buildskript. Es enthält KEINE fertig gebaute Windows-EXE.
EXE_ERSTELLEN.bat erstellt die EXE auf einem Windows-PC. Zum Weitergeben immer
DEN KOMPLETTEN erzeugten Ordner dist/DW2_3D_Viewer_Studio verwenden.

NEUE OBERFLÄCHE
Der Viewer, Animationsplayer und die Werkzeuge stammen aus Android v5.2.1.
Auf großen Fenstern bleiben links die Digimon-Liste und mittig der Viewer
sichtbar; Bearbeiten, Änderungen und Mehr erscheinen rechts. Auf kleineren
Fenstern werden die Seiten über die untere Navigation gewechselt.

Übernommen:
- Bewegter DW2-Hintergrund, DigiCode, Raster, grünes Statusfenster und Rahmen.
- Original-Schatten aus dem geladenen Spielabbild, sofern lesbar.
- 30-Hz-Animationen, Schleifenpunkte, Einmal-Clips, Augen- und Texturanimation.
- PS1-Mischmodi, Rückseitenverwerfung, Original/Bearbeitet-Vergleich.
- Diagnose der Animationskanäle, Animationsprüfung, Rohdaten-ZIP.
- PNG-Vergleich vor dem Vormerken, Augenersatz, Export in 1× bis 4×.
- Namen, Typ, Spezialgebiet, Attacken, Gegnerwerte und EXP.
- Spielstand-/Memory-Card-Editor mit den vom Android-Kern unterstützten Feldern.
- Undo/Redo, .dw2mod-Projekte, neues Image und Spielstand exportieren.
- GLB/glTF/OBJ-Import, Knochenzuordnung und nativer Modellaustausch.

PC-WERKZEUGE BLEIBEN ERHALTEN
„Mod Studio“ oben oder PC-Werkzeuge → Mod Studio öffnet die bisherigen
PC-Werkzeuge: 3D-Import, grafisches Rigging, Knochenzuordnung, Vollfarben-
Projekte, Texturwerkzeuge, Digimon-Austausch und 3D-Export aus Version 3.9.
Das Mod Studio führt EIN EIGENES Projekt und eine eigene Änderungsliste.
Zum Übertragen nativer Änderungen: .dw2mod speichern, im anderen Fenster
Dasselbe Ausgangsimage öffnen und das Projekt laden. Änderungen werden
nicht automatisch zwischen beiden Fenstern synchronisiert. Vollfarben-
Projekte bleiben im Mod Studio und sind keine nativen PS1-Texturen.

Für OBJ und glTF die Texturen, MTL- und BIN-Begleitdateien im Modellordner
belassen. Der Desktop-Import übernimmt lokale Begleitdateien mit.
Für Spielimporte gelten weiterhin die Grenzen des nativen Modellformats.

BEDIENUNG
Maus: ziehen zum Drehen, Mausrad zum Zoomen, rechte Taste zum Verschieben.
Pfeil links/rechts: benachbartes Digimon. Leertaste: Wiedergabe/Pause.
Strg+O: Image öffnen. Strg+Z: Rückgängig. Strg+Umschalt+Z: Wiederholen.
F11: Vollbild. In Eingabefeldern bleiben normale Tastatureingaben erhalten.

DATEIEN UND SPEICHERN
Die Desktop-Version liest das ausgewählte Image direkt. Sie kopiert es beim
Öffnen nicht in einen Android-Appordner. Änderungen werden zunächst vorgemerkt.
„Neues Image exportieren“ öffnet einen Windows-Speicherdialog.
„Original überschreiben“ sichert die bisherige Datei mit eindeutigem Namen
und schreibt das Image über den geprüften PC-Writer neu.
Die Oberfläche, Three.js und der Python-Kern sind im Paket enthalten.
Beim normalen Betrieb werden keine Web-Abhängigkeiten heruntergeladen.

PRÜFSTATUS
Siehe PRUEFUNG_v4_0.md. Die Kern- und Integrationstests verwenden synthetische
Daten. Ein echtes Disc-Image und Windows standen beim Erstellen nicht zur
Verfügung. Ein vollständiger visueller Windows- und Emulator-Test ist offen.

QUELLEN
PC-Basis: die vom Nutzer bereitgestellte Version 3.9.
Android: emrah1818/dw2-viewer-android, Tag v5.2.1, Commit 8125ccd894d552fb85ee59df51ff8a2b86745f37
Commit-Datum: 09.11.2026, Autor/Commitdetails im Repository.
https://github.com/emrah1818/dw2-viewer-android/tree/v5.2.1
Herkunft und Prüfsumme stehen zusätzlich in SOURCES_v4_0.json.

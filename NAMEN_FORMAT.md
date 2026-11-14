# Native Digimon-Namen im separaten Viewer 3.1

Stand der Prüfung: 31.10.2026. Implementierung: `dw2studio/core/digimon_names.py`,
Dialog: `dw2studio/gui/name_dialog.py`, Regressionstests: `tests/test_digimon_names_v31.py`.

## Nachvollziehbare Formatgrundlage

Die folgende Grundlage wurde am Quellstand im bereitgestellten v8-Archiv geprüft.
Die GitHub-Links benennen die Originalprojekte; die geprüften lokalen Kopien sind
für diese Änderung maßgeblich. Es wird kein PC-Port-Code eingebunden.

- **Wyrelade, Digimon-World-2-Decomp**, `src/main/digidata.c`:
  `Digi_GetDataFileId`, `Digi_FindDataById`, `Digi_GetDefaultName`.
  https://github.com/Wyrelade/Digimon-World-2-Decomp
- Dasselbe Projekt, `include/main/156C.h`: Struktur `DigiData`, 40 Bytes.
  Offset +0 ist der relative Namenszeiger; die ID steht in den Bits 1–15
  des Halbworts bei +4. Modell-/Animationsverweise bleiben erhalten.
- Dasselbe Projekt, `src/main/cd.c`, `Cd_GetFileEntry`: Das erste Wort einer
  MODELDT-Datei zeigt relativ zum Dateianfang auf die Datensatzliste.
- Dasselbe Projekt, `src/main/gamedata.c`, `Digi_InitFromTable` und
  `Enemy_InitRosterEntry`: Der Standardname wird über `Digi_GetDefaultName`
  gelesen und mit 14 Bytes in das Namensfeld kopiert. Die neue Eingabe bleibt
  deshalb auf 13 einbytekodierte Zeichen plus FF-Abschluss begrenzt.
- **RemyRM, DigimonWorld2Tool**, `DigimonWorld2Tool/FileFormats/MODELDT0.cs`:
  unabhängiger Leser für Datensätze, Namenszeiger und FF-Textabschluss.
  `DigimonWorld2Tool/Utility/TextConversion.cs`: US-Buchstaben, Ziffern,
  Leerzeichen und die unterstützten Satzzeichen.
  https://github.com/RemyRM/DigimonWorld2Tool
- **acemon33, DW2-TT**, `dw2_exp_multiplier/Resources/FileList.txt` und
  `Base/DW2Slus.cs`: private US-Dateitabelle, LBA-/Sektoranzahl-Offsets und
  Index 3257 für MODELDT0. Die Folgeindizes 3258/3259 werden hier zusammen
  mit Wyrelades Dateiauswahl 0xCB9/0xCBA/0xCBB abgeglichen.
  https://github.com/acemon33/DW2-TT

Es handelt sich um eine eigene Python-Implementierung des Dateiformats. Für die
Namensfunktion werden keine fremden Tools ausgeführt und keine Spieldaten verteilt.

## Genaue Änderungen

In den geprüften Dateien enthält der Kopf zwei Zeiger: Datensatzbeginn bei +0,
Beginn der Effektzeilen bei +4. Die Namen liegen zwischen +8 und dem Beginn
der Effektzeilen. Die Liste umfasst 40-Byte-Datensätze und einen Null-Endeintrag.
Der Parser prüft diese Grenzen, alle Namenzeiger, FF-Abschlüsse, Zeichen,
überlappende Bereiche sowie ausschließlich nullgefüllte Zwischenräume.

Passt der neue Name in seinen eigenen Platz, bleiben die anderen Namen und
alle Zeiger unverändert. Andernfalls packt der Writer ausschließlich den schon
vorhandenen Namensblock neu. Identische Texte dürfen einen Zeiger teilen;
alle geänderten Zeiger werden explizit aktualisiert und auf 4 Bytes ausgerichtet.
Eine spätere Änderung eines gemeinsamen Textes löst nur den ausgewählten Eintrag
von diesem Text. Der Effektblock, IDs, Modellverweise, Animationen und die
Dateilänge bleiben erhalten. Bei zu wenig Platz wird nichts vorgemerkt.

Die ID-Auswahl folgt `Digi_GetDataFileId`: unter 300 MODELDT0; 400–500 MODELDT2;
sonst MODELDT1. Fehlt ein Verzeichniseintrag, wird nur bei eindeutig gefundenem
`SLUS_011.93` mit PS-X-EXE-Kopf die dokumentierte US-Dateitabelle verwendet.
Alle Allokationen werden gegen die Image-Grenzen geprüft; der Zielinhalt muss
anschließend den MODELDT-Parser bestehen. Es gibt keine globale Textersetzung
und keinen zusätzlichen Datenanhang am Image.

Die Daten gehen in die bestehende `EditSession`. Dadurch lassen sich Namen,
Texturen und Modelle in einem Export zusammensetzen. RAW-Sektoren erhalten
wie bisher neue EDC/ECC. Die Image-Speicherung übernimmt weiterhin
Überschreibbestätigung, Sicherung der aktiven Quelle und atomare Übernahme.

## Was dadurch im Spiel geändert wird

Geändert wird der Standardname, auf den die Spiel-Funktion
`Digi_GetDefaultName` zugreift. Neu daraus initialisierte Gegner und Anzeigen,
die diesen Namen nachschlagen, können den neuen Text verwenden. Bereits
separat gespeicherte Spitznamen, feste Starter-Spitznamen sowie eigenständige
Dialogtexte bleiben getrennte Daten. Eine Umbenennung aller Textvorkommen
oder ein Spielstandeditor ist damit nicht verbunden.

Die binären Prüfungen ersetzen keinen vollständigen Emulator-/Konsolentest.
Ob eine bestimmte modifizierte Spielversion alle erwarteten Anzeigen genauso
übernimmt, ist ohne Test dieser Spielversion nicht nachgewiesen.

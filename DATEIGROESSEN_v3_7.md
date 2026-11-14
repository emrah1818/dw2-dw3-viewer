# Native Dateiverlagerung: größere Digimon ersetzen

Stand: 01.11.2026. Separater 3D Viewer v3.7; Mod Studio und PC Port unberührt.

## Behobene Beschränkung

Bisher musste jede M-/A–K-Quelldatei in die alte Ziel-Dateigröße passen.
Das Nutzerfoto zeigt unter anderem Greymon M mit 29.652 Bytes gegenüber
Frigimon M mit 27.316 Bytes und Animation A mit 20.096 gegenüber 9.640 Bytes.
Die Quell-/Ziel-Skelette haben dort 20 bzw. 12 Knochen. In v3.6.1 führten
solche Größenüberschreitungen zur Sperre der gesamten Vormerkung.

In v3.7 werden größere Ersatzdateien in neue, eigene Datenbereiche am Ende
des Images geschrieben. Das Image darf dabei wachsen. Die alte Zielgröße
ist keine Sperre mehr für diese native Verlagerung. Es wird nicht über das
Ende des alten Bereichs hinweg in benachbarte Dateien geschrieben.

## Was zusammen geändert wird

1. Die vollständigen nativen Quelldateien werden zunächst als reversible
   Änderungen gesammelt. Das Original-Image wird dabei nicht geschrieben.
2. Beim späteren Speichern werden neue Sektorbereiche für größere Dateien
   angelegt. Jede Datei bekommt ihre eigene Kopie; kein gemeinsamer Zeiger
   auf ein anderes Digimon, das später versehentlich mitbearbeitet würde.
3. Die private US-DW2-Ladetabelle im SLUS erhält den neuen Startsektor und
   die neue Sektoranzahl für die jeweilige Ziel-Datei-ID.
4. Die passenden ISO9660-Dateieinträge werden in beiden Byteordnungen mit
   neuem Startsektor und neuer Dateilänge aktualisiert.
5. Die ISO-Volumegröße wird an die tatsächliche neue Sektorzahl angepasst.
6. RAW-BIN bekommt gültige Mode-2-Form-1-Sektoren mit neuer BCD-MSF-Adresse,
   neu berechneten EDC/ECC und anschließend geprüften Nutzdaten.
7. Die neuen Verweise und Dateien werden nochmals mit einem neu geöffneten
   Reader eingelesen. Erst danach wird das fertige Image atomar veröffentlicht.
8. Die Oberfläche übernimmt die neuen Dateigrößen und LBAs nach dem Speichern
   ebenfalls. Auch alternative Dateipfade desselben Eintrags werden aktualisiert.

Kleinere/passende Änderungen bleiben normalerweise an ihrer bisherigen
Stelle. Bereits gemeinsam referenzierte native Dateien werden vor einer
Änderung in eigene Bereiche kopiert, wenn ihre IDs sicher bestimmt sind.
Ein Fehler beim Schreiben veröffentlicht kein halbes Image. Beim Überschreiben
des Quell-Images wird wie bisher vorher eine eigene Sicherung erstellt.

## Fortlaufende Bearbeitung

PNG-Änderungen nach einem größeren Modellimport behalten dessen neue Länge.
`.dw2mod` speichert den Verlagerungsmodus und die tatsächliche Ersatzgröße;
Laden validiert weiterhin das ursprüngliche Image und die Originalbytes.
Erneutes Öffnen eines vergrößerten Images liest die geänderten ISO-Einträge.
Das Quell-Digimon und die ursprünglichen Zielbereiche werden bei einer
Verlagerung nicht verändert. Weitere Änderungen am Ziel sind unabhängig.

## Unterstütztes Layout und verbleibende Prüfungen

Implementiert ist das dokumentierte US-Layout SLUS_011.93 bei LBA 24:
3675 Startsektoren ab Exe-Offset 0x33F94, Sektoranzahlen ab 0x37900.
0x18 ist hier der LBA der Exe, NICHT eine angenommene private Datei-ID.
Das Programm prüft PS-X-EXE-Signatur, ISO-Eintrag der Exe, Bereichsgrenzen,
private Tabelleneinträge, native Dateinamen und die ISO-Datensätze.
Bekannte US-Datei-IDs aus FileList.txt lösen gemeinsam genutzte Bereiche
auf; eine widersprüchliche bekannte ID wird nicht durch eine Vermutung ersetzt.
Bei unbekannten Namen ist ein eindeutig passender Tabelleneintrag erforderlich.

Die Ausgabe unterstützt 2048-ISO und 2352-Mode-2-Form-1-BIN, bei CUE einen
MODE2/2352-Datentrack. JAP-/PAL-/unbekannte Tabellen, Audio-Track-Umbauten und
mehrdeutige Dateiverweise werden nicht auf Verdacht geändert. Die nativen
16-Bit-Sektoranzahlen und das CD-MSF-Adressformat bleiben Formatgrenzen.
Modell-/Skelett-/TIM-/Animationsprüfungen und die benötigten Animationsrollen
und Clipnummern bleiben bestehen. Fehlende Animationen werden nicht erfunden.
Das ist keine Zusage unbeschränkten PS1-Heaps/VRAMs oder jeder denkbaren Mod.

Die Frigimon-/Greymon-Originaldateien aus dem Nutzer-Image liegen hier nicht
vor. Ein Emulator-/Windows-Test mit diesem konkreten Image wurde daher nicht
ausgeführt. Die technische Größenbeschränkung im bisherigen Writer ist
aufgehoben; praktische Spielekompatibilität ist zusätzlich zu prüfen.

## Tests und Quellen

218 Tests erfolgreich, darunter 14 neue Verlagerungstests. Sie verwenden
neu erzeugte Modelle und ISO-/BIN-Strukturen mit privaten Tabellen und echten
ISO9660-Records. Ein Test übernimmt genau die im Foto genannten M-/A-Größen
und die Skelettanzahlen 20/12, mit vollständig synthetischen Geometrie-/Frame-
Daten. Die Vormerkung ist dabei freigegeben und die komplette Ausgabe geprüft.
Das ist kein Test mit den tatsächlichen Greymon-/Frigimon-Polygonen.

Weitere Prüfungen: RAW-EDC/ECC, alte Nachbar-/Quelldaten unverändert,
beide Dateitabellen, Volumegröße, Mod-Projekt, weitere Texturänderung,
Wiederöffnen, Sicherheitskopie, Abbruch eines fehlgeschlagenen Speicherns,
kleine Änderungen ohne Image-Wachstum, gemeinsame Originalverweise und ein
ISO-Prüffall, dessen Dateigröße zufällig auch durch 2352 teilbar ist.

Primärreferenzen der Implementierung, lokal eingesehen:
- acemon33, DW2-TT: Base/DW2Slus.cs (US-Tabellenoffsets), Base/DW2Image.cs
  WriteFile (neue Datei anhängen und LBA/Sektoranzahl anpassen), sowie
  Resources/FileList.txt (Dateiname → US-Datei-ID).
  https://github.com/acemon33/dw2-tt/
- Vorhandener DW2-Decomp-Quellstand: src/main/cd.c, Cd_GetFileLba,
  Cd_GetFileSectors, Cd_QueueFile; src/main/cdread.c, Cd_ReadFileAsync.
  Der Loader reserviert und liest anhand der Tabellen-Sektoranzahl.
- Die Tabellenwerte M-Greymon=15, M-Frigimon=14, A-Greymon=10 und
  A-Frigimon=5 Sektoren wurden zusätzlich mit der bereits vorhandenen
  SLUS-Referenzressource aus dem Community-Quellpaket verglichen. Sie passen
  zu den auf dem Foto genannten Bytegrößen. Diese Ressource wird nicht
  in diesem Viewer-Paket mitgeliefert.

Neue Dateien: core/native_relocation.py und data/native_file_ids_us.json
(2423 Dateinamen-/ID-Zuordnungen, keine Spieldateien). Änderungen in
core/edit_session.py, core/digimon_transfer.py, core/disc.py und main.py.
Regressionstests: tests/test_native_relocation_v37.py.

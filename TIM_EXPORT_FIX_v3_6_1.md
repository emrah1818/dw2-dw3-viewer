> Dieser TIM-Exportfix ist in v3.7 weiterhin enthalten. Die spätere
> Dateiverlagerung wird in DATEIGROESSEN_v3_7.md beschrieben.

# Exportfehler aus v3.6: TIM-Ende und anschließender Import

Stand: 01.11.2026. Betrifft ausschließlich den separaten 3D Viewer.

## Nachgewiesener Programmfehler

`dw2studio/core/digimon_transfer.py`, Funktion `_validate_family`, verlangte:
`model.tim_start + tim.end == model.tim_end`. Bei einer Abweichung löste sie
exakt die fotografierte Meldung aus: „TIM-Ende passt nicht zum nativen
Modellkopf.“ Die Prüfung lief beim Erstellen des nativen Austauschpakets,
also noch bevor eine neue GLTF-/GLB-Datei veröffentlicht werden konnte.

Diese Gleichheitsbedingung war nicht aus dem Referenzleser abgeleitet.
Der unveränderte jype-C++-Leser in `third_party/dw2_model_converter/src/`
liest den Modellkopf, verwendet in `dw2_model::read_tim` aber `tim_start`,
die CLUT-/Pixelblockgrößen und das native Texturlayout. Das zweite Kopfwort
`tim_end` wird dort nicht als zusätzliche End-Prüfung benutzt.

Die vorhandenen synthetischen Tests hatten immer das Kopfwort auf denselben
Wert wie das berechnete TIM-Ende gesetzt. Deshalb deckten die bisherigen
191 Tests diese fehlerhafte zusätzliche Bedingung nicht auf.

Die genaue Bedeutung und der Wert dieses Kopfworts im fotografierten
Agumon-Modell sind ohne dessen Originaldatei nicht bestimmbar. Es wird hier
keine neue Bedeutung dafür behauptet oder in die Spieldaten geschrieben.

## Korrektur

- `_texture_end` parst die tatsächlichen TIM-Blöcke am validierten Modell-
  zeiger. Der bekannte native DW2-Aufbau (128×256, 4 Bit, Pixelbeginn 64,
  Gesamt-TIM 16448 Bytes und vorhandene CLUT) wird weiterhin geprüft.
- `_validate_family` verwendet diese Blockprüfung statt der Kopfwort-Gleichheit.
- `plan_transfer` verwendet ebenfalls das berechnete TIM-Ende anstelle des
  zweiten Kopfworts. Eine falsch kurze angenommene Grenze darf beim Entfernen
  von Null-Padding keine Textur-/Palettendaten abschneiden.
- Der originale Kopfwert und die gesamten belegten TIM-Daten bleiben
  byteidentisch erhalten. Die Änderung ist keine Korrektur der Quelldatei,
  sondern eine Korrektur der zusätzlichen Import-/Exportprüfung.
- Das native Paketformat bleibt kompatibel; die Prüfsummen und die übrigen
  Modell-/Animations-/Dateiplatzprüfungen bleiben aktiv.

Eine alte GLTF-/GLB-Datei ohne das Paket lässt sich dadurch nicht rückwirkend
als Spielmodell importieren. Nach dem korrigierten Export muss die neu erzeugte
Datei ausgewählt werden. Das fehlende Paket ist mit der Meldung auf dem zweiten
Nutzerfoto vereinbar; die dort ausgewählte Datei selbst wurde nicht bereitgestellt.

## Prüfung

204 Tests bestanden, darunter 13 neue Regressionstests:

- Echte UI-Schaltfläche „3D-Datei exportieren“, anschließend Schaltfläche
  „Digimon ersetzen“, Vormerkung und natives Image-Speichern für GLTF und GLB.
- Vier unterschiedliche synthetische Kopfwerte, die nicht dem tatsächlichen
  TIM-Ende entsprechen; Kopfwerte werden unverändert exportiert und übernommen.
- Erfolgreiche VTK-Ladung der neuen Exporte samt Animationen.
- Vollständige Modell-/Textur-/Animationsdaten vor und nach Image-Ausgabe;
  unveränderte Quell-Images und unveränderte Image-Größe.
- Erhalt der letzten Palettenbytes trotz eines künstlich zu kurzen Kopfwerts.
- Weiterhin Abweisung abgeschnittener TIMs, falscher Längen und falscher Größe.
- Der originale C++-Reader liest denselben Testfall mit abweichendem Kopfwort
  ebenfalls erfolgreich; seine Geometrie- und Animationsausgabe wird geprüft.

Alle Testdaten sind synthetisch. Die Original-Agumon-Datei und die im zweiten
Foto ausgewählte Exportdatei liegen nicht vor. Ein Lauf unter Windows bzw.
im Emulator mit dem konkreten Nutzer-Image konnte hier nicht erfolgen.

## Quellen

Eigene Quellstände v3.6 und v3.6.1; neue Tests unter
`tests/test_tim_export_hotfix_v361.py`. Unveränderte Format-Lesereferenz:
jype, dw2_model_converter, MIT, Copyright 2024,
https://github.com/jype/dw2_model_converter ; beigefügte Dateien
`third_party/dw2_model_converter/src/dw2_model.cpp` und `dw2_model.hpp`.

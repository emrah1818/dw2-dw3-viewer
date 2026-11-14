# Hotfix 3.8.1: Attackeneditor öffnet bei logischem Dateiende

Prüfstand: 01.11.2026. Betrifft `dw2studio/core/battle_skills.py`, Klasse
`SkillTable`. Die Meldung aus dem Nutzerfoto lautet **WAZADATA-Endeintrag fehlt**.

## Reproduzierter Fehler

Der Leser in 3.8 iterierte nur, solange noch ein vollständiger 68-Byte-Satz
vorlag, und verlangte innerhalb dieser Schleife zusätzlich die Technik-ID 0.
Dadurch wurden drei konstruierte gültige Varianten abgewiesen: Ende direkt
nach dem letzten vollständigen Datensatz, ein nachfolgender Zwei-Byte-Nullcode
oder ein Vier-Byte-Nullcode. Alle drei erzeugten vor dem Fix die gemeldete
Fehlermeldung. Die bisherigen Tests enthielten immer einen ganzen zusätzlichen
Nullsatz und erfassten diesen Fehler deshalb nicht.

## Nachvollziehbare Formatgrundlage

- **acemon33, DW2-TT**, [File-Manager-Tutorial](https://github.com/acemon33/DW2-TT/blob/main/Documentation/file-manager.md),
  online geprüft am 01.11.2026. Es unterscheidet die logische WAZADATA-Datei
  von ihrer 13 Sektoren großen Allokation und beschreibt die Nullauffüllung.
  Dieselbe Dokumentation liegt im bereitgestellten v8-Quellarchiv unter
  `third_party/community/tiny/Documentation/`.
- Die lokal geprüften Tutorialbilder `File-Manager/e6.PNG` und `e9.PNG`
  zeigen den letzten Technikdatensatz bei `0x6468` beziehungsweise die
  nachfolgenden Nullzeilen nur im sektorweise exportierten `603.BIN`.
  Der dokumentierte Tabellenanfang ist `0x20AC`, der Abstand 68 Bytes.
  Daraus folgt für das gezeigte Layout: 256 Datensätze, logisches Dateiende
  `0x6468 + 0x44 = 0x64AC = 25.772 Bytes`. Die Allokation beträgt
  `13 × 2048 = 26.624 Bytes`, also 852 zusätzliche Padding-Bytes.
- **Wyrelade, Digimon-World-2-Decomp**, bereitgestellter Quellstand,
  `src/main/skill.c`, `Skill_FindById`: Der Endtest liest die `s16`-ID,
  nicht sämtliche unbenutzten Felder eines Enddatensatzes. Das tatsächliche
  Techniklayout hat 68 Bytes (`EntED40`, `include/main/156C.h`).

Das persönliche Nutzer-Image und dessen WAZADATA-Datei sind hier nicht
vorhanden. Die konkrete Dateilänge darin wurde daher nicht gemessen. Die
Korrektur beruht auf dem reproduzierten Parserfehler und dem unabhängig
dokumentierten Dateilayout, nicht auf einer Untersuchung dieses Images.

## Korrektur

Der neue Leser beendet sich entweder an der Null-ID oder exakt am Dateiende
nach einem vollständig validierten Datensatz. Für die Null-ID genügen ihre
zwei Bytes. Ein angebrochener Datensatz mit nichtnull ID und ein einzelnes
Restbyte werden weiter abgewiesen. Fehlermeldungen enthalten dafür Position
und vorhandene/benötigte Bytezahl. Prüfungen auf doppelte IDs, Textzeiger,
FF-Textabschlüsse und erlaubte Werte bleiben erhalten.

Der Writer ergänzt keine erfundenen Nullsätze und vergrößert keine Tabelle.
Nur die tatsächlich geänderten Felder werden geschrieben. Vorhandene
Padding-/Endbytes bleiben bytegleich. Das gilt sowohl für echte ISO-Dateilängen
als auch für über die private US-Tabelle gefundene Sektorallokationen.

## Zusätzliche Prüfung

23 neue Tests in `tests/test_wazadata_end_v381.py`: konstruierte Datei mit den
obigen Original-Layoutgrenzen und 256 selbst erzeugten Datensätzen; EOF und
verschiedene Null-Endlängen; abgeschnittene Datensätze/IDs; doppelte IDs und
ungültige Textzeiger; direkte sowie private Dateieinträge in ISO und RAW-BIN;
Vormerken, Projektdatei, Image-Export und Wiederöffnen; unveränderte Quell-
und Dateigrößen; RAW-EDC/ECC. Ein Qt-Test klickt den tatsächlichen Button bei
Agumon, öffnet den Katalog und merkt eine andere Standardtechnik vor.

Es sind ausschließlich erzeugte Testdaten, keine Original-Spielinhalte.
Der vollständige Teststand steht in `PRUEFUNG_v3_8_1.txt`. Ein Emulatorlauf
oder eine Prüfung des persönlichen Nutzer-Images wird damit nicht behauptet.

## Installation

Die neue ZIP in einen eigenen Ordner vollständig entpacken und daraus
`start_windows.bat` starten. Der Fenstertitel muss **v3.8.1** anzeigen.
Es ist kein Image-Export nötig, um den Parserfix anzuwenden. Danach das
vorhandene Spiel-Image öffnen und **Attacken bearbeiten** erneut verwenden.
Vorgemerkte Arbeiten aus einer noch offenen alten Sitzung zuvor als
`.dw2mod` sichern; die Projektstruktur bleibt unverändert.

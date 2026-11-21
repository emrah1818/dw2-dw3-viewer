# Prüfstand 0.99 – 22.11.2026

## Implementierung

- DNA-Oberfläche mit Partnern, Ergebnis und Stufe; Bearbeiten/Löschen.
- Backend-Validierung gegen vorhandene DIGIMNDT-IDs, ungeordnete Partnerpaare,
  einheitliche Stufe je Ergebnisart, Rückgängig/Wiederherstellen.
- Projekt speichern/laden, Konflikterkennung beim Einlesen installierter Mods,
  DNA-Mods ohne Ersatzdateien, Ersetzen/Deaktivieren/Aktivieren.
- Leere DNA-Regeldatei zum Zurücksetzen der letzten installierten Regel.
- Native Laufzeit: `Stg20_GetDnaResult`, `Digi_GetRank`, Labor-Zulassung und
  Nachwuchserzeugung (`Stg20_BuildDnaOffspring`, auch von der Live-Laborroutine aufgerufen).
- Windows-/Linux-Buildworkflow vorbereitet und auf den begleitenden Port gepinnt.
  Ein Push auf den Feature-Branch baut/testet; Veröffentlichung ist manuell.

## Lokal geprüft

`python -m pytest -q -rs`: **383 bestanden, 51 übersprungen**, zusätzlich
8 bestandene Untertests. Die übersprungenen Tests benötigen überwiegend private
Spieldaten oder eine hier nicht verfügbare EGL-Grafikumgebung. Eine Warnung
stammt vom installierten AnyIO-/Pytest-Plugin (veralteter interner Typname).

- Linux-PC-Port mit `tools/build_native.py --release --no-disc` erfolgreich gebaut.
  `--no-disc` ersetzt die eingebetteten Disc-Daten durch Platzhalter. Dieser Build
  ist kein Nachweis eines gestarteten Spiels mit echten Spieldaten.
- `dna_test`: bestanden. Aufruf der echten Ergebnis-, Rang- und
  Nachwuchsfunktionen mit synthetischer DIGIMNDT-Tabelle und synthetischen Eltern.
  Geprüft: Partnerreihenfolge, Original-Fallback, globale Stufe, Mega-Startlevel 31,
  Mindesthöchstlevel, HP/MP/Angriff/Abwehr/Tempo, DP/Eltern, ungültige Dokumente,
  doppelte Paare, widersprüchliche Stufen, Rücksetzen und Rookie-Fallback.
  EXP-/Technik-Hilfsfunktionen sind im synthetischen Test durch Stubs ersetzt;
  damit sind echte EXP-Kurven und Technikvererbung nicht vollständig nachgewiesen.
- `modconf_test`: bestanden (vorhandene Level-/Kamerakonfiguration).
- `dw2 --mod-api`: meldet API 2, `digivolve_levels: 1`, `battle_camera: 1`,
  `dna_overrides: 1`.
- `dw2 --check-cache`: 200 Ersatzdatei-Prüfungen bestanden.
- `fonts_test`: bestanden; `textscript_test`: 90/90 Prüfungen bestanden.
- JavaScript-Syntax und die bestehenden Animation-, DW3-Such- und
  Bewegungszuordnungstests bestanden (Suche: 22, Zuordnung: 17 Prüfungen).

## Ingame mit echten Spieldaten unter Linux

Die früher hochgeladenen `dw2.pak` und `dw2.pak.slus` konnten anschließend
bereitgestellt werden. Der Editor öffnet diese PAK mit 395 Modell-/Katalogeinträgen
und erkennt 194 gültige DNA-Arten aus DIGIMNDT.

Mit dem gebauten Linux-Entwicklungsport:

1. Testregel über das Studio installiert: WarGreymon (#213) + M-Garurumon (#196)
   → Omnimon (#150), Ergebnisstufe Mega.
2. Wegwerf-Testsitzung im Spiel gestartet. Ort und zwei Eltern wurden mit den
   vorhandenen Entwicklertestfunktionen vorbereitet. Kein vorhandener Benutzer-
   Spielstand wurde geändert. Die Club-Typbeschränkung in Modus 0x305 wurde bei
   einem ersten Versuch beobachtet; der anschließende Test nutzt 0x301.
3. DNA-Menü, Partnerwahl und Bestätigung über die Spielsteuerung ausgeführt.
   Die Vorschau nennt Omnimon; die DNA-Sequenz läuft bis zur Namenseingabe.
4. Ergebnis im Spiel: Omnimon, Mega, Level 31, DP 1, Eltern WarGreymon/M-Garurumon.
   Die beiden Eltern werden durch ein Ergebnis-Digimon ersetzt.
5. Namen über die Spielsteuerung bestätigt, Labor verlassen und über das
   Spielmenü auf eine neue 128-KiB-Memorycard gespeichert.
6. Neuer Programmstart, Continue/Laden über die Spielsteuerung: Omnimon (#150),
   Level 31 ist weiterhin im Kader vorhanden.

Die DNA-Sequenz und das Ergebnis wurden anhand der Spielbilder und des
Spielzustands geprüft. Das ist ein Linux-Ingame-Test mit echten Spieldaten,
aber kein Windows-Test. `integration/ingame/dna_runtime.py` macht diesen Ablauf
wiederholbar. Der erneute automatisierte Gesamtdurchlauf hat ebenfalls bestanden:

| Lauf | Ergebnis-ID | Startlevel |
| --- | ---: | ---: |
| Dieselben Eltern mit `--no-mods` | 113 | 21 |
| Installierter DNA-Mod | 150 (Omnimon) | 31 |
| Nach Speichern und neuem Programmstart | 150 (Omnimon) | 31 |

Maschinenlesbares Ergebnis: `docs/validation_0.99/dna_ingame.json`.

## Noch nicht nachgewiesen

- Die Browseroberfläche wurde nicht erfolgreich mit Playwright durchgeklickt:
  Chromium wird in dieser Umgebung beim Anlegen eines Unix-Sockets blockiert
  (`Operation not permitted`). Der neue Test `integration/uitest/dna_editor.py`
  ist vorbereitet, aber nicht als bestanden gezählt.
- Windows-Build/Windows-Smoke-Test lokal nicht verfügbar. Diese Nachweise
  müssen die vorbereiteten GitHub-Actions vor der Veröffentlichung liefern.
- Nicht alle Partnerpaare und Ergebnisstufen wurden im echten Spiel durchlaufen.
  Das dokumentierte Paar und die synthetischen Laufzeittests decken die neue
  Anbindung ab; sie ersetzen keine vollständige Spielregression.
- Die Veröffentlichung erfolgt erst nach den noch ausstehenden CI-Prüfungen.

## GitHub-Builds und Veröffentlichung

Dieser Bericht dokumentiert die lokalen Prüfungen vor den GitHub-Builds.
Nach ausdrücklicher Benutzerfreigabe vom 22.11.2026 wurden die Änderungen
für den Upload freigegeben. Der Studio-Workflow baut und prüft Studio und
begleitenden PC-Port unter Windows und Linux. Die zugehörigen CI-Ergebnisse,
Windows-/Linux-Smoke-Berichte und UI-Testausgaben werden als Release-Belege
mitgeliefert. Die Veröffentlichung darf erst nach erfolgreichen Pflichtprüfungen
und dem bereits dokumentierten Ingame-Test erfolgen.

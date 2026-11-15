# Prüfstand 0.98.1

Autor: Codex, 15. November 2026.

## Lokal ausgeführt

- Vollständige Python-Suite: **412 bestanden, 4 wegen fehlender Spieldaten übersprungen**.
- Neue Auswahl-/Exportregression: 9 Tests bestanden, einschließlich erneut geänderter F/G/H.
- JavaScript: 17 Auswahlprüfungen, 22 Suchprüfungen und 24 native Animationsprüfungen bestanden.
- Syntaxprüfung `www/app.js` und `git diff --check`: erfolgreich.

## Gezielte Regression

`tests/test_manual_motion_selection.py` prüft mit selbst erstellten Daten:
- ausdrückliche Auswahl derselben Motion wie am Anfang der automatischen Kette;
- abweichende Motion trotz alter mitgesendeter Aktion (auch ältere Dialog-Aufträge);
- eigener DW3-Loop-Beginn, Halten, ganze Motion wiederholen und Standby-Übergang;
- Schleife aus/ein ohne Verlust des bisherigen Loop-Bereichs;
- unveränderte automatische Vorgaben und unveränderter Legacy-Auftrag;
- tatsächlichen Import mit drei verschiedenen F/G/H-Animationsdateien;
- gespeicherte Zuordnung beim erneuten Anwenden und danach nochmals geänderte F/G/H.

`tests/test_dw3_assignment.mjs`: 17 Prüfungen der Auswahl-/Schleifenvorgaben im Frontend.

`integration/uitest/manual_selection.py` öffnet die echte Studio-Oberfläche in Chrome mit
synthetischer Python-Brücke. Geprüft werden die drei Dropdowns, automatische Loop-Vorgaben,
der übermittelte Importauftrag, ausdrückliche Auswahl der ersten Motion, manueller
Schleifenschalter, Zurücksetzen und unberührte Aktionsketten sowie JavaScript-Fehler.
Der lokale Browserstart wurde durch die Ausführungsumgebung blockiert; die Browserprüfung
ist deshalb eine verbindliche Prüfung des GitHub-Release-Workflows.

## Release-Belege

Der Release-Workflow baut beide Windows-Pakete und prüft das gepackte Studio einschließlich
WebGL/Python-Brücke, SciPy-Überblendung und Windows-Versionsressource 0.98.1.
Er veröffentlicht erst nach erfolgreichen Prüfungen. Die Ergebnisse liegen im Release als
`test-results.xml`, `test-summary.txt`, `ui-manual-selection.txt` und `windows-smoke.json`.

Quellen (Quellstand der Korrektur):
- [Regressionstests](https://github.com/emrah1818/dw2-dw3-viewer/blob/development/release-0.98.1/tests/test_manual_motion_selection.py)
- [Dialogprüfung](https://github.com/emrah1818/dw2-dw3-viewer/blob/development/release-0.98.1/integration/uitest/manual_selection.py)
- [Workflow](https://github.com/emrah1818/dw2-dw3-viewer/blob/development/release-0.98.1/.github/workflows/release.yml)

## Grenze

Keine Originalspieldaten und kein Zugriff auf den früher von Claude verwendeten Windows-PC
in dieser Fortsetzung. Die neue manuelle Auswahl wird mit selbst erstellten Daten geprüft.
Ein neuer echter Kampf-/GPU-/PS1-Test wird nicht als durchgeführt behauptet.

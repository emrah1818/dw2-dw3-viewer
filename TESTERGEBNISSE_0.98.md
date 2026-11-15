# Prüfstand 0.98

Autor: Codex, 15. November 2026. Grundlage: Branch `development/animation` bis `54d363f`,
anschließend die Änderungen für `development/release-0.98`.

## In dieser Fortsetzung ausgeführt

| Prüfung | Ergebnis |
|---|---|
| `python tools/build_dw3_converter.py` | C++-Konverter unter Linux erfolgreich gebaut |
| `python -m pytest -q -rs` (Python 3.12, VTK 9.7.2, Qt 6.8) | 403 bestanden, 4 übersprungen |
| `node tests/test_native_anim.mjs` | 24 Prüfungen bestanden |
| `node tests/test_dw3_search.mjs` | 22 Prüfungen bestanden |
| `node --check www/app.js`, `node --check www/animeditor.js` | erfolgreich |
| `git diff --check` | erfolgreich |

Die vier übersprungenen Tests benötigen private DW2-/DW3-Spieldaten
(`test_015_native.py`, `test_016_motion_map.py`, zweimal `test_release_014b.py`).
Eine Warnung stammt vom vorinstallierten AnyIO-Pytest-Plugin (veralteter CallSpec2-Import).
Sie ist kein fehlgeschlagener Anwendungstest.

Neue Exportprüfungen lesen die tatsächlich geschriebenen DW2-Animationsbytes wieder ein:
- Anfangsüberblendung abgeschnitten, anschließend weiterer Übergang: Positionen
  `[20, 40, 120, 200, 210, 200, 210]` statt Sprung aus der unverblendeten Quellpose.
- Letztes Bild halten bzw. Loop-Rücksprung auf Zeile 4 mit Wiederholungen.
- Unveränderter 0.95-Zweig für die Einzelmotion bleibt bei diesen Testdaten bytegleich.

Suchprüfungen decken Namen, Aliase, Kürzel, exakte Katalog-/Datei-/Kämpfer-IDs,
fehlende Namensdaten und das Verhindern numerischer Teiltreffer ab.

## Release-Prüfung in GitHub Actions

Der Workflow baut Studio und Begleit-Port unter Windows. Er prüft den Start des
gepackten Studios mit WebGL/Python-Brücke sowie die SciPy-Matrixüberblendung und
Versionsressource 0.98. Der Port wird mit Overlay-API 2 und den vorhandenen
Cache-/Schrift-/Texttests geprüft. Erst erfolgreiche Jobs dürfen veröffentlichen.
Die konkreten Ergebnisse des Release-Laufs stehen in den Actions-Logs sowie den
beigefügten `test-results.xml`, `test-summary.txt` und `windows-smoke.json`.

Quellen: [Workflow](https://github.com/emrah1818/dw2-dw3-viewer/blob/development/release-0.98/.github/workflows/release.yml),
[Exporttests](https://github.com/emrah1818/dw2-dw3-viewer/blob/development/release-0.98/tests/test_098_action_export.py).

## Noch offen

- Echte neue Kampfaktionen (Attacken, Fallen/Aufstehen, K.o., Sieg) im DW2-PC-Port mit Originalspieldaten.
- Windows-GPU-Prüfung dieser Aktionen auf der GTX 1070 des Nutzers.
- Neuer PS1-Emulator-/Konsolentest der mehrteiligen Aktionen.

Es besteht hier kein Zugriff auf den früher von Claude benutzten Windows-Arbeitsordner.
Keine dieser Prüfungen wird als bestanden ausgegeben. Die alten Screenshots und
Prüfberichte von 0.95 belegen ausschließlich den damaligen Stand. 0.98 wird deshalb
als Vorabversion veröffentlicht; ein vollständig abgenommener Spieltest ist damit nicht behauptet.

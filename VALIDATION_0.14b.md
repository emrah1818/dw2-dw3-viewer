# Prüfung 0.14b — 14.11.2026

Durchgeführt in Linux x86_64, Python 3.12, Qt 6.8, VTK 9.7.2; mit den vom Nutzer bereitgestellten Dateien.

| Prüfung | Eingabe / Erwartung | Ergebnis |
|---|---|---|
| Python-Regression | vollständige Testsuite, ohne private Spieldaten in CI | 287 bestanden, 2 übersprungen (optionale Tests mit privaten Spieldaten); VTK-EGL-Oberflächentests ausgeführt |
| Echte PAK-Integration | `dw2.pak`: Vorschau, Agumon umbenennen, Typ ändern, Mod exportieren, Projekt neu laden | bestanden; ursprüngliche PAK-Prüfsumme unverändert |
| Echter DW3-Integrationstest | USA-Abbild: versteckte Modelle, Agumon-Skelett, Animationen, Texturen, starre Skin-Gruppen | bestanden |
| Neue Regressionen | hexadezimale Mod-ID, bestehende alternative Dateinamenschreibweise, beschädigte PAK, Audio-Datei | bestanden |
| PAK-Payloads | SHA-256 aller 3.675 Einträge | 3.675 bestanden |
| DW3-Batch | 249 gefundene M-Dateien nach GLB; PNGs mit Pillow lesen | 248 konvertiert, 4.186 Clips; `M500WAVE` abgewiesen: keine erkannte Knochenliste |
| JavaScript-Animation | `node tests/test_native_anim.mjs` | alle Prüfungen bestanden |
| Desktop-Bridge und WebGL | synthetisches DW2-Image sowie echte PAK und echtes DW3-Modell, Qt-WebEngine mit SwiftShader | bestanden: synthetisch 2 Modelle / 4 Clips; echt 395 PAK-Katalogeinträge und DW3-Agumon mit 35 Clips, ohne Textur-Ladefehler |
| Windows-Paket | Build und Start des eingefrorenen Programms | GitHub Actions führt diese Prüfung separat aus; hier nicht lokal als Windows-Test behauptet |
| PC-Port-Spielbetrieb | Mod laden und Kampf/Animation im laufenden Spiel | nicht durchgeführt |

Die separaten vier neuen Tests mit echten Daten bzw. Export-Schutz mit aktivierten `DW2_TEST_PAK`/`DW3_TEST_DISC`
haben bestanden. Die Tabelle der vollständigen Suite zählt die beiden privaten
Datentests als übersprungen, da sie dort nicht erneut aktiviert waren.

Strukturelle Konvertierung bestätigt keine visuelle Fehlerfreiheit sämtlicher
Modelle oder Bewegungen. Die Desktop-Prüfung umfasst auch den Ablauf PAK öffnen → Agumon wählen → DW3 öffnen → Modell konvertieren → Vorschau mit 35 Clips.
Eine Hardwareprüfung auf dem Windows-PC des Nutzers steht aus.

Die ursprüngliche `dw2.pak` hatte SHA-256
`ff8735ff9fae59ddb23770b1e4c9a8f8cd1c053369aef66975b061520c40d100`.
Das bereitgestellte DW3-7z hatte SHA-256
`206e4a38505465a46670ac466546cdd50555e8c5d41d8587670fe5324eddfe0c`.
Originalspieldaten und erzeugte Spielmodelle werden nicht veröffentlicht.

Quellen zur Kompatibilität: `emrah1818/dw2-pc-port`, `host/pak.c`
(am 14.11.2026 gelesen; Mod-Dateinamen werden mit Basis 16 ausgewertet),
und `third_party/dw3_converter/UPSTREAM.json` für den festgehaltenen DW3-Konverterstand.

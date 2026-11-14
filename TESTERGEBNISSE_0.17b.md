# Testergebnisse 0.17b – 14.11.2026

Drei Arten von Nachweisen, getrennt:

## 1. Automatisierte Tests (ohne Spieldaten, auch in GitHub Actions)
Selbst erzeugte Testdaten im Tabellenformat des Spiels (`tests/fixtures017.py`): kleines `dw2.pak` mit WAZADATA, DIGIMNDT, ENEMYSET, MODELDT0, Domain-Tabelle und einer Domain-Datei. Keine Spieldaten.

| Bereich | Tests |
|---|---|
| Parser und Datenstrukturen (Domains, Etagen, Gegnergruppen, Techniken) | `test_017_editors.py` |
| Fehlerhafte/unvollständige Dateien (abgeschnitten, ohne Endeintrag, Zeiger außerhalb) | `test_017_editors.py` |
| Individuelle Techniken (Originale bytegleich, Kopie, Namen, Sperre geteilter Techniken) | `test_017_editors.py` |
| Digitationslinien (ein Schritt, alles-oder-nichts) | `test_017_editors.py` |
| Kamera (Stufen, Grenze, nur zwei Felder geändert, Höhenmessung) | `test_017_editors.py` |
| Mod-Export, Konflikt, Ersetzen, Wiedereinlesen, Vergleich (Rundlauf) | `test_017_mod_roundtrip.py` |
| Beschädigte Mods (unbekannte ID, leer, > 2 MiB, andere dw2.pak) | `test_017_mod_roundtrip.py` |
| Texturgrößen 128×256 bis 2048×4096, abgelehnte Größen | `test_017_hd_and_ui.py` |
| Fenster: neun Bereiche, alle Aufrufe registriert, Pfade nur über Dialoge | `test_017_hd_and_ui.py` |
| Alle bisherigen Tests (Viewer 4.0 bis 0.16b) | übrige Dateien in `tests/` |

Ergebnis lokal (Linux, Python 3.13): **351 bestanden, 4 übersprungen** (die 4 brauchen private Spieldaten). Das Ergebnis des Release-Builds steht in `test-summary.txt` und `test-results.xml` im Release.

## 2. Tatsächlich durchgeführte Laufzeittests
Lokal unter Linux mit der eigenen `dw2.pak` des Nutzers und seinem DW3-Abbild (USA). Diese Dateien liegen nicht im Repository.

| Prüfung | Ergebnis |
|---|---|
| Testsuite mit beiden echten Abbildern | 355 bestanden, 0 übersprungen |
| Alle 192 Gegnergruppen lesen und unverändert zurückschreiben | bytegleich |
| 35 Domains, 151 Gruppenverweise der Etagen | alle aufgelöst |
| Technik klonen in der echten WAZADATA | alle 256 Originaldatensätze bytegleich |
| Programm ohne sichtbares Fenster, echte dw2.pak: jeder der neun Bereiche geöffnet und Inhalt gelesen | alle Bereiche zeigen Daten, keine Fehlermeldung |
| Kette: zwei DW3-Digimon im Stapel, Linie, eigene Technik, Gruppe, Export, Wiedereinlesen in frische Sitzung | 21 Dateien und 2 HD-Texturen identisch |
| **Im Spielcode (PC-Port mit Mod-Schnittstelle 2):** Renamon (DW3) im Gazimon-Slot, eigene Technik „Fox Fire“ (ID 116, Kopie von 105) für Gruppe 154, Gruppe 154 Level 7 / 80 HP; neues Spiel bis zum ersten Kampf der Boot Domain | Spielspeicher im Kampf: Gegner 4 = „Renamon“, Lv 7, max. HP 80, Techniken [116, 0, 0]. Ohne Mod: „Gazimon“, Lv 5, 54 HP, [105, 0, 0]. Kampf vollständig durchgelaufen, 13 Mod-Dateien geladen |
| Kamera automatisch vs. drei Stufen höher, gleiche Kampfszene | kein sichtbarer Unterschied in dieser Szene; Original zeigt dort dasselbe Bild |

## 3. Nicht überprüfte Spielintegration
- Windows-PC mit echter Grafikkarte (Programm und Port).
- Mausbedienung der neuen Dialoge unter Windows.
- Ersetztes Digimon als Partner, Digitation hinein, Speichern/Laden damit.
- Geänderte Domain-Etagen im laufenden Spiel (nur Datenrundlauf geprüft).
- HD-Texturen im GPU-Renderer des Ports.

Ein erfolgreicher CI-Build zeigt nicht, dass importierte Digimon im echten Spiel fehlerfrei funktionieren.

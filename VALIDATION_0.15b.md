# Prüfung 0.15b — 14.11.2026

Umgebung: Linux x86_64, Python 3.12, Qt 6.8, VTK 9.7.2. DW3-Konverter mit GCC C++17 gebaut. Begleit-PC-Port mit GCC 14 und SDL 3.4.8 aus der festgehaltenen Quellbasis gebaut; nur leere Platzhalter im Programm, echte Daten erst lokal zur Laufzeit gelesen.

Die vollständige Suite mit aktivierten privaten Datentests bestand: **294 Tests bestanden** (kein übersprungener Test). Zusätzlich bestanden die JavaScript-Animationsprüfungen. In CI ohne private Daten werden drei Tests übersprungen.

## Lokale Integrationsprüfungen

- Echte dw2.pak geöffnet; Original-Prüfsummen unverändert.
- DW3-Agumon konvertiert: 18 Körperknochen, 738 Dreiecke, 3 Texturseiten.
- 11 native Dateien für den bestehenden Agumon-Slot erzeugt; 512×1024-HD-Atlas exportiert.
- Vorschau nach Import: 14 native A–K-Clips lesbar. DW3-Motions lassen sich ausdrücklich den Spielplätzen zuweisen.
- Mod-Projekt gespeichert und neu geöffnet; native Ersatz-Prüfsummen und HD-Datei erhalten.
- Größere Dateien bei fehlender API-2-Kennung abgewiesen, mit kompatiblem Zielordner exportiert.
- Echter PC-Port-Titelstart mit 11 aktiven Mods und erkanntem HD-Pack bis 120 VBlank-Wartepunkten erfolgreich.
- Nativer Modelltest im echten Spielprozess: Datei 0x05C über den virtuellen CD-Bereich geladen; 18 Knochen gebunden. Animation 0x001 durch den Spiellader gelesen. 120 Schritte der originalen Animations- und Knochenmatrixfunktionen, 60 Zeilenfortschaltungen, sauberer Programmabschluss.
- Gesamtdurchlauf über die 249 gefundenen DW3-Dateien: 248 Modelle einschließlich ihrer ersten Motion konvertiert und mit den nativen Parsern gelesen. M500WAVE wird vom Quellkonverter ohne lesbare Knochenliste abgewiesen; das ist keine Aussage über alle Motions oder Kampfaktionen.
- Zusätzlicher Animationsdurchlauf: alle 15.376 Motions der 248 lesbaren Modelle einzeln nativ kodiert und wieder eingelesen. Das prüft weder eine automatische Aktionszuordnung noch beliebige Kombinationen mehrerer Motions in einer Zieldatei.
- Golemon nach Teilmesh-Aufteilung zusätzlich im echten Spielprozess geprüft: 19 native Teile, 1.083 Dreiecke, 120 Animationsschritte / 60 Zeilenfortschaltungen; 512×1024-HD-Textur erkannt und abgetastet.
- Erweiterter Spielablauf mit aktiver Mod-Schicht: neues Spiel, Boot Domain, zwei abgeschlossene Kämpfe, Rückkehr zur Stadtkarte (30.079 Waits, 76 Bot-Schritte). Ein dabei gefundener voller CD-Cache wurde durch Slotdruck-Verdrängung behoben. Der Soundkopiervorgang wird durch die tatsächliche CD-Allokation begrenzt.
- Separater Cache-Regressionstest ohne Spieldaten: 200 Ersetzungen bei 80 belegten Einträgen, gesperrte und noch ladende Einträge unverändert. Läuft auch im Windows-Build.
- Heap-Erweiterung auf 6 MiB mit Start-/Endadressprüfung im gemeinsamen 16-MiB-Fenster geprüft. Die PS1-RAM-Spiegelung bleibt unverändert.

Die neuen Unit-Tests prüfen Koordinaten, Matrix-/Translationskodierung, Clip-Schleifen, Pose-Überlauf, unabhängige Texturhash-Berechnung und DP-Grenzen inklusive unveränderter Nachbarbytes. Ein zusätzlicher echter Datentest deckt History, Projekt-Rundlauf und Export ab. Die vollständigen Testzahlen und Windows-Build-/Startprotokolle stehen bei dem jeweiligen GitHub-Actions-Lauf; private Originaldaten werden dort nicht bereitgestellt.

## Nachweise

- PC-Port-Quellbasis: https://github.com/emrah1818/dw2-pc-port/commit/d5b69b997c0c97e01a639a5e0aab62250ec4174c
- DIGIMNDT: include/main/156C.h (DigiBaseData), src/main/gamedata.c (Digi_GetEvolutionTarget), host/devdata.c.
- Native Animation/Modell: src/main/anim.c, src/main/model.c, src/main/cd.c und src/main/cdread.c.
- HD-Pack-Namen/Hash: backend/texrep.c und backend/texrep.h.
- Änderungen des Begleit-Ports: integration/pc_port_api2.patch.
- DW3-Konverterherkunft und MIT-Lizenzen: third_party/dw3_converter/UPSTREAM.json, LICENSE, CREDITS.md. cli.cpp ergänzt die numerischen nativen Motion-Samples.

Keine Behauptung über einen vollständig durchgespielten Windows-Kampf oder sämtliche DW3-Modelle. Der echte Spielmodelltest läuft unter Linux ohne sichtbares Fenster. Windows-Build und Viewer-Start werden zusätzlich automatisiert ausgeführt. Motion-Semantik, DW3-Aktionsskripte, Gesichtsausdrücke und sämtliche möglichen Slotkombinationen sind nicht vollständig validiert.

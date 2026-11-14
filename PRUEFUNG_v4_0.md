# DW2 3D Viewer PC 4.0 – Prüfbericht

Erstellt am 11.11.2026. Basis: vom Nutzer bereitgestellte PC-Version 3.9 und
[Android v5.2.1](https://github.com/emrah1818/dw2-viewer-android/tree/8125ccd894d552fb85ee59df51ff8a2b86745f37)
vom 09.11.2026. Die genaue Quellenzuordnung steht in `SOURCES_v4_0.json`.

## Ergebnis

- Python-Gesamtprüfung: **234 bestanden, 47 übersprungen**; keine fehlgeschlagenen Tests.
- JavaScript-Animationsprüfung: **24 Prüfungen bestanden**. Python und JavaScript
  dekodieren die synthetischen Texturmaterialien ohne Pixelabweichung.
- Native Desktop-Integration: Qt WebEngine → WebChannel → Python-Worker →
  Imageanalyse → Katalog → glTF-Konvertierung → Viewer erfolgreich.
  Synthetisches Image mit zwei Modellen: Agumon geladen, vier Animationseinträge,
  keine Fehlermeldung in der Oberfläche.
- Zusätzliche PC-Tests: begrenzte HTTP-Dateipfade, ES-Modul-MIME-Typen,
  Exportveröffentlichung, Schutz des geöffneten Original-Images vor dem normalen
  Exportdialog, Fehlerrückgabe der Brücke und OBJ-Import mit MTL/PNG.
- Python-Dateien erfolgreich kompiliert.

Die 47 ausgelassenen Tests betreffen überwiegend den alten VTK-Viewer und
Operationen mit nicht verfügbarem EGL oder weiteren Laufzeitvoraussetzungen.
Sie gelten ausdrücklich **nicht als bestanden**. Die unveränderten alten
Werkzeuge sind im Mod Studio enthalten, ihre Darstellung wurde hier nicht
vollständig neu visuell geprüft.

## Übernahme und Erhalt

| Bereich | Umsetzung in PC 4.0 | Prüfung |
| --- | --- | --- |
| DW2-Hintergrund, DigiCode, grünes Fenster, Rahmen | Android-Dateien übernommen | Dateien enthalten, Web-Oberfläche lädt |
| Animationsplayer, Augen, Texturzyklen, Mischmodi, Rückseiten | Derselbe Three.js-Player und Python-Konverter wie Android 5.2.1 | Python- und JS-Fixtures, synthetisches Modell geladen |
| Original-Schatten | Android-Lader und Renderer übernommen | Synthetisches Schattenmodell und Export-Payload getestet |
| Namen, Typ, Spezialgebiet, Attacken, Gegnerwerte, EXP | Android-API und vorhandene PC-Kernmodule | Synthetische Tabellen und Änderungsabläufe |
| Spielstand-/Memory-Card-Editor | Android-ROSTER-Kern und Oberfläche | Synthetischer Spielstand, Werte und Export |
| Undo/Redo, Projekt, Image-Export | Android-Oberfläche, native Dateidialoge, PC-Writer | Backend-Tests und zusätzliche Exporttests |
| PNG-Vorschau, Augenersatz und Paletten | Android-Oberfläche, bestehende PC-Konvertierung | Synthetische PNG-/Palettenprüfungen |
| 3D-Import, Mapping, nativer Austausch | Android-Frontend plus bestehendes Mod Studio | Bestehende Rig-/Importtests; zusätzlicher Sidecar-Test |
| Vollfarben, grafische Knochenzuordnung, alter PC-Export | Mod Studio erhalten | Bestehende Kerntests; visuelle VTK-Prüfung offen |
| Desktop-Layout | Liste links, Modell mittig, Werkzeuge rechts; schmale Fenster mit Seitennavigation | DOM/Bridge-Start geprüft, Windows-Sichtprüfung offen |

Die beiden Fenster verwenden getrennte Bearbeitungssitzungen. Native Änderungen
können über `.dw2mod` ausgetauscht werden. Diese Trennung steht auch in der
Oberfläche und Startanleitung; es gibt keine automatische Sitzungssynchronisation.

## Offene Prüfungen

**Keine echte Disc-Datei wurde mitgeliefert.** Deshalb sind weder die tatsächliche
Darstellung aller Digimon noch exportierte Änderungen in einem Emulator mit
Originalspieldaten in dieser Sitzung geprüft worden. Die Anzahl der Modelle
hängt vom geladenen Image ab.

**Windows steht in dieser Umgebung nicht zur Verfügung.** Es wurde keine
Windows-EXE gebaut. Das ZIP ist ein startbares Python-Quellpaket mit
`start_windows.bat`, PyInstaller-Spezifikation und korrigiertem Windows-Workflow.
Ein erfolgreicher Windows-Build und ein vollständiger sichtbarer GPU-Test
sind noch offen. Die native Integration lief ohne sichtbares Fenster mit
Software-WebGL; Qt meldete fehlende Host-GPU-/Vulkan-Unterstützung.
Ein zusätzlicher Chromium-Screenshotversuch war durch die Prozess-/Socket-
Beschränkungen der Umgebung blockiert. Daher wird kein Screenshot als visueller
Nachweis ausgegeben.

Die Behauptungen zur Rekonstruktion des Spielformats stammen aus dem Android-
Projekt. Seine Hintergrund- und Animationsanalyse sind zur Nachvollziehbarkeit
beigelegt; sie ersetzen keinen eigenen Vergleich mit dem laufenden Spiel.

## Prüfungen wiederholen

```text
python -m pip install -r requirements.txt pytest
python -m pytest -q tests
node tests/test_native_anim.mjs
python tools/verify_desktop.py
```

Der JS-Test verwendet die vom Python-Test erzeugte `_fixture_payload.json`.
Unter Linux ohne Bildschirm für die native Integrationsprüfung:
`QT_QPA_PLATFORM=offscreen` und
`QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader"`.
Diese Testoptionen sind nicht im normalen Windows-Startskript aktiviert.

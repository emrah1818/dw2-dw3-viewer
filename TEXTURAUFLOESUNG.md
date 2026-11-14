> v3.5: **PNG importieren** ist bei Spiel-Digimon wieder der native Import.
> Die hier beschriebenen Größenregeln gelten dafür weiterhin. **Vollfarben
> nur im Viewer ersetzen** behält die PNG-Datei ohne Neucodierung und ohne
> Größen-/Seitenverhältnisabgleich im Viewer-Modell; exportierbar als .dw2rgb.
> Der frühere Button „HD-PNG in Vorschau“ wurde entsprechend umbenannt.

# Größere PNGs und die tatsächliche Spielauflösung

Implementierung im separaten Viewer 3.2, geprüft am 31.10.2026.

## Was diese Version übernimmt

| Weg | 512×1024-PNG | Gespeichertes Ergebnis |
| --- | --- | --- |
| PNG importieren → natives Spiel | Mit ausdrücklicher Bestätigung | 128×256, native PS1-Paletten |
| Augen vollständig ersetzen | Mit derselben Bestätigung | Erkannte Augenflächen im nativen Atlas |
| PNG im OBJ-Rigging | Mit derselben Bestätigung | 128×256 für das neue native Modell |
| HD-PNG in Vorschau | Volle Auflösung | 512×1024 im Projektmodell |
| 3D-Export der HD-Projektvorschau | Volle Auflösung | GLTF/GLB bzw. OBJ mit größerer Textur |

Die Bilddatei wird vor dem nativen Kodieren verkleinert. Die Original-PNG
bleibt erhalten. Das ist eine Importhilfe für größere Arbeitsdateien, kein
Patch für hochauflösende Texturen im originalen Spielrenderer.

## Weshalb die Größenprüfung nicht einfach entfallen kann

Der vorhandene DW2-Writer ersetzt einen festen TIM-Block. Für den erkannten
DW2-Atlas besteht dieser aus 128×256 Pixeln mit 4 Bit pro Index einschließlich
der physisch darin gespeicherten Farbpaletten. Geometrie, UVs, Augenrechtecke
und Dateiablage setzen diese Struktur voraus. Der Größenabgleich in den
unteren nativen Codecs bleibt deshalb absichtlich erhalten; die GUI führt
vorher eine bestätigte Normalisierung durch.

128×256 = 32.768 Bildpositionen. 512×1024 = 524.288 Bildpositionen, also
16-mal so viele. Eine PNG-Kompression ändert nicht die Zahl der Texturpositionen,
die der Renderer im Spiel ansprechen müsste.

Auch ein größerer Datenanhang an die BIN würde für sich genommen weder die
Texturkoordinaten noch die GPU-Ansteuerung anpassen. Sony beschreibt Texturseiten
von 256×256 und die Nutzung derselben Texturmuster für Sprites und Polygone.
Für einen nativen Umbau wären zusätzliche Änderungen an Spieldaten und
Lade-/Renderlogik nötig. Ein solcher Umbau ist hier nicht implementiert.

Primärquelle: **Sony Computer Entertainment, PlayStation Hardware, August 1998**,
Abschnitt 3-6 „Sprite and Texture Page“, Abschnitt 3-7 „Texture Mapping“.
https://psx.arthus.net/sdk/Psy-Q/DOCS/Devrefs/Hardware.pdf

Formatquelle im Paket: `third_party/dw2_model_converter/src/gltf_exporter.cpp`,
`dw2studio/core/dw2_native_atlas.py` und `native_tim_patch.py`.
Der vorhandene Konverter baut den Atlas mit 128×256 auf und normiert UVs
über 128 bzw. 256. Diese Datenstruktur wird beim Spiel-Export beibehalten.

## Ein separater Weg für echte HD-Texturen im Emulator

DuckStation dokumentiert eine Texturersetzung außerhalb des Spiel-Images:
Texturen im laufenden Spiel dumpen, die passende Dump-Datei bearbeiten bzw.
vergrößern und unter dem identischen Dump-Dateinamen in `replacements` ablegen.
Die Erkennung verwendet unter anderem Textur- und Paletten-Hashes sowie den
Texturausschnitt. Eine beliebig benannte Viewer-PNG erzeugt diese Zuordnung nicht.

Das erfordert echte Dumps aus dem verwendeten Spiel. Ob DW2 mit den jeweiligen
Emulatoreinstellungen korrekt dumpen und ersetzen lässt, wurde hier nicht
praktisch geprüft. Das offizielle Wiki weist auf begrenzte Spielekompatibilität
hin. Deshalb erzeugt der Viewer kein ungeprüftes „fertiges DW2-HD-Paket“.

Primärquelle: **Connor McLaughlin / stenzek, DuckStation Wiki: Texture Replacement**,
Seitenrevision vom 27.11.2024, abgerufen am 31.10.2026.
https://github.com/stenzek/duckstation/wiki/Texture-Replacement

Dieser Weg verändert kein BIN/CUE und gehört nicht zum nativen Image-Export.
Ein PC-Port wird in diesem Projekt weiterhin nicht bearbeitet.

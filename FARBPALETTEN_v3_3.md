> v3.5: **PNG importieren** verwendet bei Spiel-Digimon wieder den nativen
> Palettenimport. Standard ist **Wie v3.1 · automatische Paletten**. Die unten
> dokumentierten Modi Farbschutz/Exakt bleiben optionale Alternativen.
> Die reine Vollfarben-Ersetzung aus v3.4 ist unter „Vollfarben nur im Viewer
> ersetzen“ weiterhin getrennt verfügbar. Aktuelle Bedienung: README.txt.

# Farbverlust bei kleinen Änderungen: Korrektur in Viewer 3.3

Prüfstand: 01.11.2026. Dieses Dokument bezieht sich auf den separaten Viewer.

## Nachgestellter Fehler

Die bisherige `_palette_from_target`-Funktion verglich zwei Kandidaten über
den aufsummierten Farbfehler aller Pixel einer Teilpalette. Viele graue
Metallpixel konnten dadurch den Verlust weniger blauer Augenpixel aufwiegen.
Auch die anschließende Qualitätsprüfung über die Gesamtfläche war für diesen
Fall zu großzügig.

Der Unterschied wurde mit künstlichen Daten tatsächlich gemessen:
16 Grautöne mit jeweils 1000 Pixeln, dazu vier bearbeitete blaue Pixel in
derselben Teilpalette. Gewünschte Vorschaufarbe: RGBA `(8, 96, 248, 255)`.
Die v3.2-Funktion lieferte dafür `(64, 64, 64, 255)`. Die neue Farbschutzfunktion
liefert `(8, 96, 248, 255)` und kodiert diesen Farbwert in die native Teilpalette.

Das belegt einen Fehler mit demselben Symptom wie auf deinem Foto. Der exakte
MetalGreymon-Fall ist ohne bearbeitete Original-PNG und zugehörige Modellbytes
nicht überprüfbar. Das Foto wurde nicht als Ersatz für diese Daten benutzt.

## Neue Modi

**Exakt RGB555 (Voreinstellung):** Aus den gewünschten Farben entstehen die
benötigten nativen RGB555-Wörter. Benötigt eine Teilpalette höchstens 16 Wörter,
werden diese ohne weitere Quantisierung geschrieben. Die Pixelindizes werden
passend dazu umgesetzt. Reichen die 16 Einträge nicht aus, endet der Vorgang
mit einer Meldung einschließlich der betroffenen Teilpalette. Es wird keine
abgeschwächte Fassung vorgemerkt.

**Farbschutz (Näherung erlaubt):** Die neuen Farben bearbeiteter Pixel werden
reserviert, wenn sie mit den benötigten Alpha-Klassen in die Teilpalette passen.
Erst die verbleibenden Einträge stehen für eine Näherung der anderen Flächen
zur Verfügung. Sind schon die bearbeiteten Farben zu zahlreich, erhalten sie
bei der begrenzten Auswahl mindestens vergleichbares Gewicht zu den großen
unveränderten Flächen. Ein sichtbarer Farbton wird nicht allein wegen seiner
kleinen Fläche aussortiert und anschließend anhand des Gesamtfehlers freigegeben.
Dieser Modus garantiert keine verlustfreie Übernahme beliebig vieler Farben.

Die Vorschau prüft zusätzlich die tatsächlich bearbeiteten Pixel. Deutliche
Entfärbung wird blockiert; außerdem darf deren mittlerer RGB-Fehler nicht über
18/255 und deren Anteil starker Kanalabweichungen nicht über 10 % liegen.
Die bisherigen globalen Prüfungen und Alpha-Prüfungen bleiben erhalten.
Diese Schwellen sind Prüfregeln des Tools, keine zusätzliche PS1-Funktion.

## Was ins Spiel geschrieben wird

Die neuen RGB555-Einträge landen in den realen 64 Face-CLUTs am Ende des
nativen TIM-Pixelblocks. Die zugehörigen 4-Bit-Indizes werden ersetzt. Es wird
nicht bloß eine farbige PNG neben das Image gelegt. Die Vorschau wird aus den
kodierten Bytes zurückgelesen; beim Vormerken wird derselbe Modus verwendet.
Der Test für gespeicherte ISO-/RAW-Images vergleicht den TIM-Block nach dem
Wiederöffnen bytegenau mit der Vorschau-Kodierung.

Dateigröße, TIM-Kopf, UVs, Geometrie, Augenkoordinaten und Animationen werden
von dieser Palettenkorrektur nicht erweitert. Reservierte Atlaszeilen werden
weiterhin geschützt. Bereits vorgemerkte Texturänderungen sind die Grundlage
für einen weiteren Import; für die Fehlerprüfung dient jeweils dieser Stand.

## Physische Grenzen und Quelle

Das erkannte DW2-Format verwendet 4-Bit-Indizes und damit 16 Paletteinträge
pro bestehender Teilpalette. RGB555 bedeutet 5 Bit je Farbkanal. Eine beliebige
24-Bit-PNG mit mehr Farben pro verwendeter Teilpalette kann dieses Format
nicht exakt speichern. Die neue Voreinstellung behauptet das auch nicht.

Die unvermeidliche RGB555-Umrechnung bleibt bestehen. Die Tool-Vorschau dekodiert
5-Bit-Kanäle mit Linksverschiebung um drei Bits; deshalb zeigt sie z.B. Kanalcode
31 als 248. „Exakt“ bezeichnet die Übernahme in diesem nativen Farbformat,
nicht die Identität mit sämtlichen 24-Bit-PNG-Werten oder eine Messung der
späteren Darstellung eines bestimmten Emulators/Displays.

Primärquelle: **Sony Computer Entertainment, PlayStation Hardware, August 1998**,
Abschnitt 3-6 „Sprite Pattern Color Modes“: 16 Einträge bei 4-Bit-CLUT,
15-Bit-Farbstruktur der Einträge. Abgerufen am 01.11.2026.
https://psx.arthus.net/sdk/Psy-Q/DOCS/Devrefs/Hardware.pdf

Implementierung und Prüfungen im Paket:
- `dw2studio/core/dw2_palette_recolor.py`
- `dw2studio/core/dw2_native_atlas.py`
- `dw2studio/core/native_tim_patch.py`
- `tests/test_color_protection_v33.py`

Ein In-Game-Test deines konkreten Images wurde hier nicht durchgeführt.

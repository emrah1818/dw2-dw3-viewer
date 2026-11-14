# Viewer v3.5: PNG-Import und Spielpaletten wie in v3.1

Stand: 01.11.2026. Nur das separate Viewer-Projekt wurde geändert.

## Ursache des Unterschieds

Verglichen wurden die hier vorhandenen Quellstände 3.1 und 3.4:

- `main.py` in v3.1 leitete den normalen PNG-Button bei einer nativen Szene
  nach `import_native_png`. Der TIM-Encoder schrieb Paletten und Pixelindizes.
- `dw2_palette_recolor.py` in v3.1 bildete zwei Kandidaten: neue RGB555-Farben
  pro altem Index sowie Median-Cut mit neuen Pixelindizes. Auswahl nach der
  kleineren Summe quadratischer RGB-Abweichungen über die zugehörigen Pixel.
- v3.3/v3.4 boten die Modi protect/exact. In der Oberfläche war exact zuerst
  ausgewählt. Mehr als 16 benötigte RGB555-Einträge brachen dort ab, statt wie
  zuvor eine Annäherung mit einer neu berechneten Palette anzubieten.
- In v3.4 wurde `replace_png` zudem stets zu `replace_preview_png` geleitet.
  Diese Funktion änderte ausschließlich das Viewer-Modell. Sie schrieb keine
  nativen Änderungen in die Vormerkliste für den Image-Export.

## Änderung

Der normale PNG-Import verwendet für ein geladenes Spiel-Digimon wieder den
nativen TIM-Import. Der Standard ist **Wie v3.1 · automatische Paletten**.
Das Originalverfahren wurde in `dw2studio/core/palette_v31.py` übernommen.
Farbschutz und Exakt sind optionale Alternativen; die Vollfarben-Ersetzung
nur im Viewer steht weiterhin als ausdrücklich eigener Button zur Verfügung.
Der normale PNG-Export liefert bei nativer Szene wieder den nativen Atlas
mit den erkannten Augenstellungen. Die Original-PNG wird nicht überschrieben.

Der v3.1-Modus übernimmt auch die bisherigen globalen Prüfungen. Die später
hinzugefügte harte lokale Farbfehler-Sperre gilt in diesem Modus nicht; die
Werte und bei auffälligen Abweichungen ein Hinweis bleiben im Vorschaufenster.
Schreiben erfolgt nach Bestätigung der tatsächlich kodierten Vorschau und
nach späterem Image-Speicherauftrag. Paletten werden dabei wirklich ersetzt.

## Vorschau-Cache

Zuvor identifizierte `request_for` native Änderungsvorschauen über die laufende
Änderungsnummer (z.B. edits/1). Diese Nummer beginnt nach einem Neustart erneut.
Ein vorhandenes Konvertierungsergebnis konnte dadurch für eine andere PNG
wiederverwendet werden. Jetzt enthält der Cache-Pfad den SHA-256 über Namen,
Längen und Inhalt aller vorgemerkten Modell-/Animationsdateien. Zurücksetzen
auf Originaldaten verwendet wieder den ursprünglichen Konvertierungspfad.

## Belege und Grenzen

`tests/palette_v31_golden.json` enthält TIM- und Vorschau-SHA-256-Werte, die
mit der unveränderten v3.1-Implementierung erzeugt wurden. Die neuen Tests
prüfen vier Fälle dagegen: einfarbiges Umlackieren, mehr als 658 PNG-Farben,
breite Änderung über eine Graupalette und fünf Augenstellungen.
Der Vergleich bezieht sich auf die gesamte native TIM und alle Vorschaupixel.

SHA-256 der v3.1-Referenzdatei:
`7ae71bc8aaf5b10afd2494840897b61545c7e712dad7f35d733017efb0ef2e24`

Der Test für farbreiche PNGs hatte 1.74/255 mittleren absoluten RGB-Fehler
auf allen geprüften sichtbaren Pixeln, und 10.02/255 ausschließlich auf den
1.225 bearbeiteten Pixeln. Das ist ein synthetischer Test, keine Messung der
MetalGreymon-Textur auf dem Nutzerfoto und keine Zusage für jedes Bild.
Der mittlere Fehler wird als Summe der absoluten Kanalabweichungen geteilt
durch (Anzahl geprüfter sichtbarer Pixel × 3) berechnet. Eine starke Abweichung
zählt, wenn mindestens ein RGB-Kanal um mehr als 48 von 255 abweicht.
Diese Anzeige ist keine Prozentangabe für subjektiv empfundenen Farbverlust.

Das Bildschirmfoto zeigt eine Vorschau, liefert aber keine Original-PNG und
keine nativen Modellbytes. Der konkrete MetalGreymon-Fall ist damit nicht
pixelgenau reproduzierbar. Windows-Start, Konverterlauf mit einem vollständigen
Original-Spiel-Image und Emulatorlauf wurden hier nicht ausgeführt.
RGB555 und die bestehende Zuordnung von Teilpaletten bleiben unverändert.

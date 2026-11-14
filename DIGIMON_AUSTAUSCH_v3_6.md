> Historische Beschreibung des Standes v3.6/v3.6.1. Ab v3.7 entfällt die
> Beschränkung auf die alte Ziel-Dateigröße durch geprüfte Dateiverlagerung.
> Aktuelle Anleitung/Prüfung: README.txt, DATEIGROESSEN_v3_7.md, PRUEFUNG_v3_7.txt.

> Korrektur in v3.6.1: Der Vergleich des zweiten Modellkopfwerts mit dem
> berechneten TIM-Ende wurde entfernt. Die Texturgrenze kommt jetzt aus den
> tatsächlichen TIM-Blöcken. Das Paketformat und der Austauschablauf bleiben
> erhalten. Aktueller Prüfstand: 204 Tests, siehe PRUEFUNG_v3_6_1.txt.

# Digimon-Austausch in Viewer v3.6

Stand: 01.11.2026. Projekt: separater 3D Viewer, keine Änderung am PC Port
oder Mod Studio. Der normale native PNG-Import bleibt wie in v3.5 erhalten.

## Implementierter Ablauf

Quell-Digimon öffnen → als GLTF/GLB exportieren → Ziel auswählen →
„Digimon ersetzen · Modell + Animationen“ → Austausch prüfen/vormerken →
später das gesamte Image speichern.

Beim nativen Export erzeugt `main.Main.transfer_export_payload` ein Paket
aus den aktuellen Quelldateien der EditSession: M enthält Geometrie, Skelett,
Textur, Paletten und Blinkmetadaten; die A–K-Dateien enthalten die zugehörigen
nativen Animationsclips. Bereits vorgemerkte Änderungen werden berücksichtigt.
Im Export steht dieses Paket unter `extras.DW2_native_transfer`. Es ist kein
Standard für beliebige Spiele, sondern ein vom Viewer definierter Zusatz.

`core/digimon_transfer.export_exchange` bettet zusätzlich alle sichtbaren
GLTF-Puffer und PNG/JPEG-Texturen unverändert ein. Die resultierende GLTF
oder GLB ist jeweils eine allein transportierbare Datei. Die normale GLTF-
Darstellung und ihre Animationen bleiben von gewöhnlichen Viewern lesbar.
Der Export wird im temporären Ordner geprüft und erst dann atomar veröffentlicht.

## Natives Ersetzen

GLTF ist nicht das native DW2-Dateiformat. Der Import schreibt deshalb nicht
die GLTF-JSON/GLB-Bytes ins Spiel, sondern die eingebetteten nativen Quelldaten.
A ersetzt A, B ersetzt B usw.; M ersetzt das Zielmodell. Das gesamte Quell-
Skelett und alle vorhandenen Quell-Animationsbanken gehen gemeinsam über.
Unterschiedliche Knochenanzahlen sind dadurch zulässig. Der Zielname und
Werte-/Angriffstabellen werden nicht mit dem optischen Modell ausgetauscht.
Das Spiel benutzt weiterhin die Aktions-/Clipnummern des Ziel-Digimon.
Die semantische Gleichheit einzelner Kampfaktionen wird nicht zugesagt.

Vor dem Vormerken werden geprüft:

- Modellkopf, Geometrieblöcke, Hierarchie und TIM-Zeiger.
- Animationsköpfe, Tabellen, Matrixbereiche und Clipströme gegen das
  Quell-Skelett; Ziel-Animationen werden gegen das bisherige Ziel-Skelett gelesen.
- Dateiplätze für alle Quell- und Zielrollen; weder Quell- noch Zielrollen
  dürfen fehlen. Für neue Animationsdateien wird kein Dateieintrag angelegt.
- Die Quelle stellt mindestens alle benötigten Ziel-Clipnummern bereit.
- Die native Quellgröße passt je Datei in die bisherige Zielgröße. Ausschließlich
  unbenutztes Null-Padding nach den letzten referenzierten Daten wird entfernt;
  unbekannte nicht-nullhaltige Trailer bleiben vollständig erhalten.
- Die sichtbare GLTF/GLB und die eingebetteten nativen Daten sind seit dem
  Export unverändert. Modell-/Animations-JSON und alle Puffer-/Bildbytes
  werden gehasht. Das ist eine Konsistenzprüfung, kein Herkunftsnachweis.

Kleinere Daten werden mit Nullbytes auf die Ziel-Dateigröße aufgefüllt. Es
werden keine Dateien verschoben, keine Dateiadressen geändert, keine Polygone
reduziert und keine Animationen automatisch verkürzt. Passt etwas nicht,
bleibt die Übernahme gesperrt und das vorhandene Image wird nicht verändert.

Die Vormerkung ist eine gemeinsame native Änderungsgruppe. Die Oberfläche
setzt beim Verwerfen eines zugehörigen Eintrags die gesamte Modell-/Animations-
Familie auf die Daten des geöffneten Images zurück. `.dw2mod` enthält diese
vorgemerkten Bytes ebenfalls. Erst der spätere Image-Speicherauftrag schreibt.
RAW-BIN-Sektoren erhalten wie bisher geprüfte EDC/ECC; die Image-Größe bleibt.

## Grenzen und ältere Exporte

Ein Export aus v3.5 oder früher enthält das native Paket nicht. Die Quelle
muss im neuen Viewer erneut geöffnet und exportiert werden. Eine allgemeine
Rückkonvertierung fremder bzw. in Blender veränderter GLTF-/GLB-Dateien wird
nicht implementiert. Bei geändertem Inhalt wird der alte eingebettete Stand
nicht als vermeintlich neues Modell übernommen. Reines Neuformatieren des
JSON oder Verschieben der eigenständigen Datei ändert den Inhaltsnachweis nicht.

Die Funktion „Vollfarben nur im Viewer ersetzen“ entfernt veraltete native
Austauschmetadaten, damit ihr Ergebnis nicht mit den ursprünglichen nativen
Pixeln verwechselt werden kann. Native PNG-Änderungen mit der echten TIM-
Kodierung lassen sich dagegen über das frisch konvertierte Quellmodell mit
exportieren. OBJ ist weiterhin statisch und verwendet den OBJ-Rigging-Import.

Nicht jede beliebige Digimon-Kombination passt in die vorhandenen Dateiplätze.
Ein größerer Donor kann daher abgewiesen werden. Ein Dateisystem-/Loader-Patch
für vergrößerte/verlagerte Assets ist nicht Bestandteil dieser Version.

## Validierung und Quellen

191 Tests erfolgreich, davon 23 neue Austauschtests. Die Tests verwenden
synthetische Modelle und Images; keine Spieldateien werden mitgeliefert.
Getestet wurden unter anderem:

- GLTF/GLB-Export und vollständiger nativer Rückimport mit neuem Skelett.
- Transport als einzelne Datei bei ursprünglich externen Puffern/Texturen.
- Weiterexport von GLB nach GLTF mit weiterhin lesbaren Austauschdaten.
- Echte VTK-Wiedergabe der erhaltenen Animationen nach dem normalen UI-Export.
- Vergleich von Modell, Texturen und Animationsdaten vor/nach Image-Ausgabe.
- Native Änderungsprojekte sowie ISO- und RAW-BIN-Ausgabe mit unveränderter Größe.
- Abbruch, zu wenig Platz, fehlende Rollen, fehlende Clips, manipulierte Daten,
  gemeinsame Rücknahme und Rückrollen eines Fehlers während der Vormerkung.
- Zusätzlich liest der unveränderte C++-Reader aus dem ursprünglichen
  jype-Konverter das übertragene Modell und seine Animation erfolgreich ein.

Formatreferenz: jype, dw2_model_converter, MIT, Copyright 2024;
https://github.com/jype/dw2_model_converter
Lokaler Quellen-Ausschnitt: `third_party/dw2_model_converter/src/dw2_model.cpp`,
`dw2_anim.cpp`, zugehörige Header und Lizenz. Neue Implementierung:
`dw2studio/core/digimon_transfer.py`, `gui/digimon_transfer_dialog.py`, `main.py`.
Tests: `tests/test_digimon_transfer_v36.py`.

Hauptoberfläche und Prüfdialog wurden in Qt offscreen visuell geprüft.
Windows-Start, der Windows-Konverterlauf mit dem Original-Image sowie
Emulator-/Konsolenlauf wurden in dieser Umgebung nicht durchgeführt.
Die konkreten Digimon-Beispiele des Nutzers wurden ohne ihre Originaldaten
nicht geprüft. Struktur- und Dateitests ersetzen diesen praktischen Test nicht.

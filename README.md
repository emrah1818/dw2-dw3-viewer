# DW2 / DW3 Viewer — 0.14b

Windows-Desktop-Viewer und Mod-Werkzeuge auf Basis des erhaltenen DW2-Viewers 4.0.
Eigene Spieldaten sind erforderlich; dieses Repository enthält keine Disc-Images oder PAK-Spieldaten.

## Windows starten

Unter **Releases → v0.14b** das Windows-x64-ZIP laden, vollständig entpacken und
`DW2_3D_Viewer_Studio.exe` starten. Den gesamten Ordner zusammenlassen.
Ein Release-Paket wird erst nach erfolgreichen Tests, Build und Startprüfung veröffentlicht.

Aus Quellcode: Python 3.12 x64 installieren, `start_windows.bat` starten.
Der DW3-Konverter benötigt zusätzlich einen C++17-Compiler:
`python tools/build_dw3_converter.py`. Im gebauten Windows-Paket ist er enthalten.
Das bisherige Mod Studio bleibt über die PC-Werkzeuge erreichbar und führt weiterhin ein eigenes Projekt.

## DW2 und PC-Port

1. **BIN / ISO öffnen** akzeptiert jetzt auch `dw2.pak`.
2. Digimon wählen, Modell und Animationen ansehen; Namen, Typ, Specialty,
   Attacken sowie unterstützte Gegnerwerte und EXP bearbeiten.
3. Unter **Änderungen → PC-Port-Mod exportieren** den Ordner mit `dw2.exe` wählen.
   Bei einem geöffneten Disc-Image wird zusätzlich die passende PAK abgefragt.
4. Die Dateien werden als `Mods/files/NNNN.bin` mit **hexadezimalen IDs** erzeugt.
   Den PC-Port neu starten. Bestehende Mods gleicher ID werden nicht überschrieben.
5. `.dw2mod` speichert die vorgemerkten Änderungen zum späteren Weiterarbeiten.

Die PAK wird ausschließlich gelesen. PAK-Sitzungen erlauben keinen Image-Export
und kein Überschreiben. Der Mod-Export prüft LBA, Länge und Original-Prüfsumme.
Audio-/Video-Dateien und größere Ersatzdateien werden abgewiesen.
Beim ursprünglichen Disc-Workflow bleiben die bisherigen Image-Werkzeuge erhalten.

## DW3 / DW2003

**DW3-Modelle öffnen** liest ein eigenes USA-DW3- oder europäisches DW2003-Abbild
(`.bin`, `.cue`, `.iso`, `.img`). Versteckte ISO9660-Dateieinträge werden gesucht.
Anschließend ein Modell wählen:

- **Ansehen / DW2-Slot ersetzen** öffnet die Modellvorschau bzw. die vorhandene
  manuelle DW2-Knochenzuordnung. Zum Ersetzen zuerst ein DW2-Ziel wählen.
- **GLB mit Texturen und Animationen exportieren (ZIP)** erhält das DW3-Skelett,
  die konvertierten Bewegungen und die benötigten PNG-Dateien zusammen.

**Grenzen dieser Beta:** DW3-Animationen sind in Vorschau und GLB vorhanden.
Die native DW2-Knochenzuordnung verwendet die DW2-Zielanimationen; sie überträgt
keine DW3-Bewegungsclips in das DW2-Animationsformat. Native DW2-Modellgröße,
Knochenzahl und Palettenlimits gelten weiter. Mehrere DW3-Texturseiten werden im
GLB erhalten; der bisherige native Import übernimmt nur seine Haupttextur.
Ein beliebiges DW3-Modell passt deshalb nicht automatisch in einen DW2-Slot.

Der Gesamtauftrag ist noch nicht vollständig umgesetzt: automatische Übertragung
der DW3-Animationen in DW2, frei größere Modelle/HD-Texturen im PC-Port sowie ein
neuer Digitation-/DP-Editor stehen aus. Der PC-Port wurde in dieser Version
nicht geändert. Eine vollständige Spielprüfung auf einem Windows-Spieler-PC ist offen.

## Nachweise und Entwicklung

Siehe [RELEASE_NOTES_0.14b.md](RELEASE_NOTES_0.14b.md) und
[VALIDATION_0.14b.md](VALIDATION_0.14b.md). Die GitHub-Actions-Protokolle dokumentieren
den Windows-Build und die Startprüfung für den veröffentlichten Commit.

`python -m pytest -q` prüft den Python-Kern. `node tests/test_native_anim.mjs`
prüft den JavaScript-Animationsplayer. Optionale echte Daten werden ausschließlich
lokal über `DW2_TEST_PAK` und `DW3_TEST_DISC` eingebunden.

Herkunft: ursprünglicher Nutzer-Quellstand `DW2_DW3_Viewer_4_1_Source.zip`;
DW2-/Android-Quellen und Lizenzen siehe `SOURCES_v4_0.json`, `THIRD_PARTY_v4_0.md`
und `licenses/`. Der DW3-Konverter verwendet MIT-lizenzierten Code von
[Feerdus95/dw3-model-viewer](https://github.com/Feerdus95/dw3-model-viewer),
Commit `b8a77d32cbdcad2a1385ccc49b98876090069ccb`, abgerufen am 14.11.2026.
Details, Anpassungen und vollständige Lizenzen: `third_party/dw3_converter/`.

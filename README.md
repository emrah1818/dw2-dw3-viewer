# DW2 / DW3 Viewer — 0.16b (Testversion)

Ersetzt DW2-Digimon durch DW3-Digimon (eigenes Skelett, Texturen, Bewegungen) und exportiert das als Mod für den DW2-PC-Port. 0.16b belegt die Bewegungen aus den DW3-Kampfskripten vor, passt die Größe an die Standhöhe an und kann Port-Mods deaktivieren. Neu in 0.16b: RELEASE_NOTES_0.16b.md, Prüfstand: VALIDATION_0.16b.md. Frühere Stände: RELEASE_NOTES_0.15b.md, VALIDATION_0.15b.md.

## Windows

Das Viewer-ZIP vollständig entpacken und DW2_3D_Viewer_Studio.exe starten. Der bisherige DW2-Viewer und das separate Mod Studio bleiben erhalten. Im Release liegt zusätzlich der angepasste PC-Port mit Overlay-API 2. Größere Dateien benötigen diesen Begleit-Port; die bisherige dw2.exe unterstützt sie nicht. Die eigenen dw2.pak und dw2.pak.slus bleiben unverändert.

## Nativer DW3-Import

1. dw2.pak öffnen und ein DW2-Ziel wählen.
2. DW3-Modelle öffnen, eigenes USA-/Europa-Abbild und ein Modell wählen.
3. „DW2-Slot mit DW3-Skelett und Bewegungen ersetzen“ wählen.
4. Die vorbelegten DW3-Motions prüfen: Standby, Treffer, K.o. und Angriffe stammen aus den Kampfskripten des DW3-Digimon, die Quelle steht neben jedem Platz. Jede Zuordnung lässt sich ändern; Schleifen und Größe prüfen.
5. Import vormerken, Modell/Animationen ansehen, unter Änderungen als PC-Port-Mod exportieren. Das Zielverzeichnis muss dw2_mod_api.json mit mod_api 2 aus dem Begleitpaket enthalten.

Alle Texturseiten werden in einem gemeinsamen Atlas abgelegt. Der native Fallback ist indiziert; das HD-Pack erhält die RGBA-Seiten in höherer Auflösung. In der PC-Port-Anzeige den HD-Modus ab Skalierung 2 verwenden. Eine Zuordnung von Angriffseffekten oder Aktionsskripten wird nicht aus Motion-Nummern abgeleitet.

## Digitation / DP und HD-PNG

Unter Bearbeiten → Digitation & DP lassen sich bis zu vier vorhandene Ziele, ihre steigenden DP-Untergrenzen und die Stufe bearbeiten. Das per Spielcode bestimmte Digitationslevel ist kein freies Feld in DIGIMNDT. DP im Spielstand bleibt über den bestehenden Spielstandeditor zugänglich.

„HD-PNG als PC-Port-Texturpack exportieren“ übernimmt echte PNGs unverändert, z. B. 512×1024. Erlaubt sind ganzzahlige Faktoren 1–16 von 128×256. Der klassische 1×-Renderer verwendet weiter die native Textur. Blink-/Texturkopien vorhandener Modelle können das aktive Pack invalidieren; der neue DW3-Import deaktiviert native Blink-Rechtecke.

## Grenzen

Native DW2-Strukturen begrenzen jeden Knochen auf 256 Vertices/Normalen und die Hierarchie auf acht Ebenen. Pro Animationsdatei werden höchstens 254 verschiedene Posen je Knochen kodiert; zu große oder unpassende Modelle werden mit Begründung abgewiesen. Geteilte Zielanimationen werden nicht automatisch überschrieben. Die Motion-Zuordnung muss zum Ziel passen. DW3-Gesichts-/Sichtbarkeitsanimationen und Aktionsskripte sind eigene Systeme und werden hier nicht als vollständig übernommen behauptet.

## Quellcode

Python 3.12 x64; start_windows.bat installiert requirements.txt. Für DW3 aus Quellcode zuerst python tools/build_dw3_converter.py mit C++17-Compiler ausführen. EXE_ERSTELLEN.bat erzeugt das Viewer-Paket. Der Begleit-Port wird aus emrah1818/dw2-pc-port gebaut (Commit in integration/pc_port_base.txt, Beschreibung doc/MOD_API2.md im Port). Der Build nutzt ausschließlich Quellcode und Platzhalter; keine Originalspieldaten werden veröffentlicht.

Herkunft/Lizenzen: SOURCES_v4_0.json, THIRD_PARTY_v4_0.md, licenses/ und third_party/dw3_converter/UPSTREAM.json. Vorheriger Stand: Tag v0.14b.

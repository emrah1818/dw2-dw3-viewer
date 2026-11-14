# DW2 / DW3 Viewer — 0.15b

Diese Version ergänzt die 0.14b-Basis um einen nativen DW3-Import, einen Digitation-/DP-Editor und HD-Texturpacks. Vollständige Bedienung und Testgrenzen stehen in RELEASE_NOTES_0.15b.md und VALIDATION_0.15b.md.

## Windows

Das Viewer-ZIP vollständig entpacken und DW2_3D_Viewer_Studio.exe starten. Der bisherige DW2-Viewer und das separate Mod Studio bleiben erhalten. Im Release liegt zusätzlich der angepasste PC-Port mit Overlay-API 2. Größere Dateien benötigen diesen Begleit-Port; die bisherige dw2.exe unterstützt sie nicht. Die eigenen dw2.pak und dw2.pak.slus bleiben unverändert.

## Nativer DW3-Import

1. dw2.pak öffnen und ein DW2-Ziel wählen.
2. DW3-Modelle öffnen, eigenes USA-/Europa-Abbild und ein Modell wählen.
3. „DW2-Slot mit DW3-Skelett und Bewegungen ersetzen“ wählen.
4. Die numerischen DW3-Motions den DW2-Plätzen (A0, B0 …) zuweisen. Motion 1 ist nur der Anfangswert, keine automatisch erkannte Kampfaktion. Schleifen und Skalierung prüfen.
5. Import vormerken, Modell/Animationen ansehen, unter Änderungen als PC-Port-Mod exportieren. Das Zielverzeichnis muss dw2_mod_api.json mit mod_api 2 aus dem Begleitpaket enthalten.

Alle Texturseiten werden in einem gemeinsamen Atlas abgelegt. Der native Fallback ist indiziert; das HD-Pack erhält die RGBA-Seiten in höherer Auflösung. In der PC-Port-Anzeige den HD-Modus ab Skalierung 2 verwenden. Eine Zuordnung von Angriffseffekten oder Aktionsskripten wird nicht aus Motion-Nummern abgeleitet.

## Digitation / DP und HD-PNG

Unter Bearbeiten → Digitation & DP lassen sich bis zu vier vorhandene Ziele, ihre steigenden DP-Untergrenzen und die Stufe bearbeiten. Das per Spielcode bestimmte Digitationslevel ist kein freies Feld in DIGIMNDT. DP im Spielstand bleibt über den bestehenden Spielstandeditor zugänglich.

„HD-PNG als PC-Port-Texturpack exportieren“ übernimmt echte PNGs unverändert, z. B. 512×1024. Erlaubt sind ganzzahlige Faktoren 1–16 von 128×256. Der klassische 1×-Renderer verwendet weiter die native Textur. Blink-/Texturkopien vorhandener Modelle können das aktive Pack invalidieren; der neue DW3-Import deaktiviert native Blink-Rechtecke.

## Grenzen

Native DW2-Strukturen begrenzen jeden Knochen auf 256 Vertices/Normalen und die Hierarchie auf acht Ebenen. Pro Animationsdatei werden höchstens 254 verschiedene Posen je Knochen kodiert; zu große oder unpassende Modelle werden mit Begründung abgewiesen. Geteilte Zielanimationen werden nicht automatisch überschrieben. Die Motion-Zuordnung muss zum Ziel passen. DW3-Gesichts-/Sichtbarkeitsanimationen und Aktionsskripte sind eigene Systeme und werden hier nicht als vollständig übernommen behauptet.

## Quellcode

Python 3.12 x64; start_windows.bat installiert requirements.txt. Für DW3 aus Quellcode zuerst python tools/build_dw3_converter.py mit C++17-Compiler ausführen. EXE_ERSTELLEN.bat erzeugt das Viewer-Paket. Die passende PC-Port-Quellbasis und der Patch stehen in integration/. Der Build nutzt ausschließlich Quellcode und Platzhalter; keine Originalspieldaten werden veröffentlicht.

Herkunft/Lizenzen: SOURCES_v4_0.json, THIRD_PARTY_v4_0.md, licenses/ und third_party/dw3_converter/UPSTREAM.json. Vorheriger Stand: Tag v0.14b.

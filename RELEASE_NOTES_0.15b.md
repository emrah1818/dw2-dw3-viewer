# DW2 / DW3 Viewer 0.15b — Beta

## Neu

- Nativer DW3-Import in einen vorhandenen DW2-Slot: eigenes Skelett, Geometrie, alle verwendeten Texturseiten und ausgewählte Motions werden in native DW2-Modell-/Animationsdateien geschrieben. Bewegungen werden mit 30 Hz aus dem DW3-Motionplayer abgetastet; die Slot-Zuordnung ist ausdrücklich vom Nutzer wählbar.
- Große starre Körperteile werden bei Bedarf auf mehrere native Teilmeshes mit identischen Bewegungen verteilt; Geometrie und Flächennormalen bleiben erhalten.
- Größere Dateien über einen beiliegenden, aus Quellcode gebauten PC-Port mit Overlay-API 2. Virtuelle CD-Bereiche, richtige Ladegrößen und ein separater 6-MiB-Spielheap erhalten die Original-PAK und das PS1-Adressmapping. Die Quelländerungen liegen als Patch gegen einen festgehaltenen PC-Port-Commit bei.
- CD-Cache-Verdrängung auch bei vollständig belegten Einträgen und korrekte Sound-Kopiergrenzen für den vergrößerten Heap. Neuer Regressionstest im Windows-Build.
- Alle DW3-Texturseiten in einem gemeinsamen Atlas: native 16-Farb-Paletten je Seite als Fallback und RGBA-HD-Texturpack. Der Import bietet z. B. 512×1024 und 1024×2048 an.
- Separater Export eigener HD-PNGs in das bestehende PC-Port-Texturpackformat, ohne Herunterskalieren oder Ändern der PNG-Datei.
- Digitation-/DP-Editor für bis zu vier Ziele, DP-Grenzen und Stufe. Werte stammen aus DIGIMNDT.BIN und folgen Digi_GetEvolutionTarget; keine erfundenen Offset-Felder.
- Neue Modelle, Bewegungen und HD-Packs über .dw2mod sichern und wieder laden; Undo/Redo bindet aktive HD-Packs an den jeweiligen Modellstand.

## Windows verwenden

Beide Windows-ZIPs aus dem Release vollständig entpacken. Den Viewer starten, dw2.pak öffnen und ein Ziel auswählen. Für den vollständigen nativen Import „DW2-Slot mit DW3-Skelett und Bewegungen ersetzen“ wählen. Die Motions müssen den A0/B0/…-Spielplätzen zugeordnet werden. Motion 1 ist nur der Anfangswert, keine Behauptung über Idle-/Angriffssemantik.

Den Mod in den Ordner des beigefügten PC-Ports mit dw2_mod_api.json exportieren. Die eigenen dw2.pak und dw2.pak.slus daneben legen. Größere Dateien funktionieren mit der bisherigen dw2.exe nicht. Für HD-Texturen im PC-Port mindestens die interne HD-Skalierung 2 verwenden.

## Prüfgrenzen

Der native Import und der Projekt-Rundlauf wurden mit dem bereitgestellten DW3-USA-Abbild und der echten PAK geprüft. Im angepassten Linux-PC-Port lud der echte CD-Code das größere Agumon-Modell mit 18 Knochen; Gfx_AttachModel, Anim_StepModelAnim und Gfx_CalcModelBoneMatrices liefen 120 Schritte mit 60 Zeilenfortschaltungen. Zusätzlich wurde der normale Titelstart mit aktiven Mods geprüft. Das ersetzt keinen vollständigen Kampf-/Kampagnen-Test.

Weiterhin gelten die nativen Knochen-/Vertex-/Pose-Limits. Unpassende Daten werden abgewiesen. Geteilte Zielanimationen werden nicht automatisch überschrieben. Gesichtsausdrücke, sichtbarkeitsgesteuerte Zusatzmeshes, DW3-Effekte und Aktionsskripte werden nicht vollständig in DW2 übertragen. Die gleiche Motion ist nicht automatisch die gleiche Kampfaktion. Klassischer 1×-Modus nutzt reduzierte native Texturen. Der pro Art frei konfigurierbare Digitationslevel ist kein Feld in DIGIMNDT und wird daher nicht als solcher Editor angeboten.

Details und Belege stehen in VALIDATION_0.15b.md. Keine Originalspieldaten sind in den Paketen enthalten.

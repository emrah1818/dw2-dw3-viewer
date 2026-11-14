# DW2 Mod Studio 1.0.0-rc1 (Release-Kandidat)

**Kein 1.0.0 FINAL.** Drei Punkte des 1.0-Auftrags brauchen eine Änderung am PC-Port, der unverändert bleiben sollte:
Attackenkamera je Digimon, Digitationslevel je Art (im Studio vorbereitet) und DW3-Effekte.
Details: `EINSCHRAENKUNGEN_1.0.0-rc1.md`.

## Neu gegenüber 0.17b
- DW3-Gesichter: Augen blinzeln wie in DW3 (im Spiel nachgewiesen).
- Formatgrenzen: automatische Teilung großer Knochen, exakte Abbildung tiefer Hierarchien, Endprüfung vor dem Export.
- Techniken: Effekt/Ton/Zustand/Animation übernehmen, eine Technik für mehrere Digimon, ID-Budget.
- Mod einlesen erkennt Konflikte und doppelte Technik-IDs.
- Digitationsprüfung über alle Arten.
- Digitationslevel je Digimon: vorbereitet (Format 1), im aktuellen Port ohne Wirkung.
- Kamera-Vorschau „Nahaufnahme wie im Kampf“.

## Im Spiel geprüft (PC-Port, eigene dw2.pak, Linux)
Digitation **in** und **aus** importierten DW3-Digimon im Digi-Labor, Speichern/Neustart/Laden, Blinzeln,
geänderte Domain-Gegner, importierter Partner mit eigener Technik im Kampf: 28 von 28 Prüfungen bestanden.
Nicht auf einem echten Windows-PC geprüft.

## Dateien
- `DW2_Mod_Studio_1.0.0-rc1_Windows_x64.zip`: das Programm (entpacken, `DW2_3D_Viewer_Studio.exe` starten).
- `DW2_PC_Port_API2_1.0.0-rc1_Windows_x64.zip`: passender PC-Port mit Mod-Schnittstelle 2, ohne Spieldaten.
- `test-results.xml`, `test-summary.txt`, `windows-smoke.json`, `SHA256SUMS.txt`.
- Anleitung, Änderungsprotokoll, Testergebnisse und Einschränkungen liegen im Programm-ZIP.

Es sind keine Spieldaten enthalten. Du brauchst deine eigene `dw2.pak` (und für den DW3-Import dein eigenes DW3-Abbild).

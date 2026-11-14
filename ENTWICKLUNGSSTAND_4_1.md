# DW2/DW3 Mod Studio – Entwicklungsstand 4.1 (14.11.2026)

## Verifiziert implementiert
- `dw2studio/pak.py`: DW2-PC-Port-PAK-v1-Index, SHA-256-Prüfung, sichere Einzelextraktion.
- Alle 3.675 Einträge der vom Nutzer bereitgestellten echten `dw2.pak` erfolgreich SHA-256-verifiziert.
- `dw2studio/port_mod.py`: strikter Overlay-Export nach `Mods/files/<ID>.bin` anhand eindeutig passender LBA, Dateigröße und SHA-256. Kein Überschreiben bestehender Mods, keine Änderung von PAK oder ISO. Verlagerte und größere Ersatzdateien werden abgewiesen.
- `tests/test_pak_port_mod_v41.py`: drei Tests bestanden.

## Noch nicht umgesetzt
- PAK-/Mod-Export-UI und Android-/Desktop-Bridge-Integration.
- DW3-Archiv-/ISO-Parser und DW3-3D-Modell-, Textur- und Animationskonverter.
- DW3-Slot-Ersatz im laufenden Spiel, Attacken-/Evolutions-/DP-Editor für DW3, HD-Textur-Limits und PC-Port-Loader-Erweiterung.
- Windows-EXE-Build und Ende-zu-Ende-Test im PC-Port.

## Tests
Die vollständige bestehende Testsuite wurde versucht; 13 Fehler bereits bei der Sammlung, offenbar wegen fehlender Test-/GUI-Abhängigkeiten. Siehe `TESTERGEBNISSE_4_1.txt`. Die drei neuen gezielten Tests sind erfolgreich.

## Daten
Die urheberrechtlich geschützten Originalspiel-Dateien und das DW3-Archiv sind NICHT im Quellcodepaket enthalten.

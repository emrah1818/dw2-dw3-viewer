# PS1-Emulatortests (Modus B)

Lokale Testhilfe, keine Spieldaten im Repository. Ablauf wie für 1.0.0-rc3 verwendet:

1. Testabbild: `rebuild.py dw2.pak dw2.pak.slus dw2_rebuilt.bin` setzt aus deiner `dw2.pak` ein bootfähiges
   2352-Byte-Abbild zusammen (alle Dateien an ihren Original-LBAs). Mit deiner echten BIN entfällt der Schritt.
2. Im Studio das Abbild öffnen, ändern, „Neues Image exportieren“ (schreibt BIN + CUE).
3. Emulator: Mednafen (`-force_module psx`) mit OpenBIOS als `scph5501.bin`, unter Xvfb.
   `emu.py CUE OUT SCRIPT` drückt Tasten (Skripte in `scripts/`), macht Bilder (F9), speichert/lädt Zustände (F5/F7)
   und beendet Mednafen mit Escape, damit die Memory Card geschrieben wird.
4. `stpatch.py` ändert in einem Zustand nur den nächsten Spielmodus (Digi-Labor 0x32F, Stadtkarte 0x32D), wie
   `warp=` im Port. Alles andere (Labor, DNA, Speichern) läuft über die Menüs des Spiels.

Tastenbelegung Spieler 1: w/s/a/d, Kreuz KP_2, Kreis KP_6, Viereck KP_4, Dreieck KP_8, Start Return.
Spieler 2: i/k/j/l, Kreuz m, Kreis n, Start p.

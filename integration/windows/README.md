# Windows-Spieltest (Port mit Grafikkarte, Battle Mode, HD-Texturen)

Keine Spieldaten im Repository. Ablauf wie für 1.0.0-rc4 auf einem Windows-10-PC (GTX 1070, Vulkan) verwendet:

1. `make_win.py` (Linux, Studio-Quellen): drei DW3-Importe (Guilmon #84, MegaloGrowmon #131, Growlmon #48) mit
   HD 2048×4096, Export in einen `Mods`-Ordner. `make_card.py`: Spielstand mit diesen drei im Team (Bot des Ports).
2. Testordner neben deiner `dw2.pak`: `Mods`, `saves\card1.mcd` + `card2.mcd` (gleiche Datei), `press_battle_mode.txt`
   als `press_battle.txt`, das Port-ZIP, `DW2-Windows-Test.ps1/.bat`. Doppelklick auf die `.bat`.
3. Der Port spielt den Battle Mode über `--press-file` (Eingaben je VBlank, beide Spieler) und speichert Fensterbilder
   (`--window-shot-vb`). Ergebnisse in `results\`.

Die Eingaben sind auf Linux und Windows gleich getaktet (gleiche `[mode]`-Zeilen im Log), wenn beim ersten Start
kein Sprachauswahl-Fenster offen ist (eigene `test_settings.ini` einmal anlegen lassen) und das Intro-Video
läuft (Fenster-Modus). Die Wiederholung des Kampfs selbst kann abweichen (Zufall im Kampf).

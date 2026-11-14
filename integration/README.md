# Begleit-PC-Port mit Mod-Schnittstelle 2

Seit 0.16b liegen die Änderungen am Port nicht mehr als Patch hier, sondern im Port selbst:
emrah1818/dw2-pc-port, Branch `development/dw3-mod-studio`, Beschreibung in `doc/MOD_API2.md`.
Der Build verwendet genau den Commit aus `pc_port_base.txt` (Basis 1.6.2-preview).

- Bis 2 MiB je Ersatzdatei, 64 MiB gesamt, virtuelle CD unter 450.000 Sektoren. Audio-/Videodateien
  bleiben gesperrt. `--no-mods` startet ohne Mods. `dw2.pak` und `dw2.pak.slus` werden nicht verändert.
- `--mod-api` gibt die Schnittstellenversion aus, `--check-model MODELL ANIMATION` prüft ein Modell
  im Spielcode (kein vollständiger Spieltest).

Das Begleitpaket enthält dw2.exe, SDL3.dll, dw2_mod_api.json, die deutschen Texte und die Schriftlizenzen.
In einen eigenen Ordner entpacken, die eigenen dw2.pak und dw2.pak.slus dazulegen und den Mod dorthin
exportieren. Spielstände des Ports liegen weiter in %APPDATA%\DW2-Online\.

## Spieltests mit dem echten Port (`integration/ingame/run_ingame.py`)

Reproduzierbar, aber nur mit eigenen Spieldaten (sie werden nie eingecheckt). Szenen:

- `evo`: DW3-Linie Guilmon/Growlmon/MegaloGrowmon in die Plätze 84/48/12 importieren, Linie
  Agumon > Growlmon > MegaloGrowmon setzen, Mod prüfen und exportieren. Im Spiel (neues Spiel bis zur
  Stadt, `--cheats` nur für Agumon Lv15 und DP) im Digi-Labor digitieren: Agumon > Growlmon (in ein
  importiertes Digimon), danach Lv25 > MegaloGrowmon (aus einem importierten heraus). Speichern,
  Port neu starten, laden: MegaloGrowmon Lv25 ist im Spielstand.
- `domain`: Gruppe 154 kopieren, Mitglieder ändern (Greymon Lv6/70 HP, Agumon Lv4/50 HP), der
  Boot Domain 1F zuweisen, exportieren. Im Spiel: der erste Kampf liest diese Gegner aus dem
  Kampfspeicher.

Ergebnis in `WORK/ingame_results.json`, Bilder in `WORK/<szene>/run/shots`.

# Begleit-PC-Port mit Mod-Schnittstelle 2

Die Änderungen am Port liegen im Port selbst: emrah1818/dw2-pc-port, Branch `development/mod-studio-1.0`
(Mod-Schnittstelle 2 aus `development/dw3-mod-studio`, Beschreibung in `doc/MOD_API2.md`).
Der Build verwendet genau den Commit aus `pc_port_base.txt`.

Neu für das Mod Studio 1.0 (beide Dateien im Ordner `Mods`, Format 1, fehlende oder kaputte Dateien ändern nichts):
- `digivolve_levels.json`: `{"format":1,"levels":{"<ID>":<Level>}}` – Mindestlevel je Digimon im Digi-Labor
  (sonst 11/21/31, Mega bleibt gesperrt).
- `battle_camera.json`: `{"format":1,"digimon":{"<ID>":{"distance":100,"height":0,"target":0,"angle":0,"closeup":{…}}}}` –
  Abstand in Prozent (25–400), Höhe, Zielpunkt und Winkel der Angriffs- und Zielkameras sowie der Nahaufnahme.
- `--mod-api` meldet `"digivolve_levels":1,"battle_camera":1`.

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
  importiertes Digimon), danach > MegaloGrowmon (aus einem importierten heraus). Mit eigenen Mindestleveln
  (Agumon 20, Growlmon 18): Sperre unter 20, Digitation bei 20 und bei 18. Speichern, Port neu starten, laden.
- `partner`: Guilmon als Partner mit eigener Technik, MegaloGrowmon als Gegner, Kameras automatisch. Im Kampf wird
  das Modellrechteck jedes Kämpfers in jeder Kameraeinstellung gemessen (Bot-Befehl `fbox`).
- `domain`: Gruppe 154 kopieren, Mitglieder ändern (Greymon Lv6/70 HP, Agumon Lv4/50 HP), der
  Boot Domain 1F zuweisen, exportieren. Im Spiel: der erste Kampf liest diese Gegner aus dem
  Kampfspeicher.

Ergebnis in `WORK/ingame_results.json`, Bilder in `WORK/<szene>/run/shots`.

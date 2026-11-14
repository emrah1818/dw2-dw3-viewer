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

# Prüfung 0.16b – 14.11.2026

Umgebung: Linux x86_64, Python 3.13, Qt 6.8, GCC 13, SDL 3.4.8 aus dem Quellcode. Eigene `dw2.pak` des Nutzers (SHA-256 beginnt mit `ff8735ff9fae59dd`, vor und nach allen Schritten gleich) und eigenes Digimon World 3 (USA).

Kennzeichnung: **geprüft** = selbst ausgeführt und Ergebnis gesehen; **nur CI** = im GitHub-Build automatisch; **nicht geprüft** = steht aus.

## Viewer

| Prüfung | Ergebnis |
|---|---|
| Testsuite mit beiden echten Abbildern (`DW2_TEST_PAK`, `DW3_TEST_DISC`) | geprüft: 303 bestanden, 0 übersprungen |
| JavaScript-Animationstests, `node --check www/app.js` | geprüft |
| DW3-Kämpfertabelle (USA, Datei 0x1BE) | geprüft: 248 Kämpfer, Dateitabelle 2.194 Einträge |
| Kampfskripte aller 249 DW3-Modelle gelesen | geprüft: 248 mit eigenen Skripten (M500WAVE ohne). 245 folgen dem Schema Standby/Treffer/K.o. in drei Varianten |
| Vorbelegung Renamon → Gazimon | geprüft: A0=1, C0/C1/C2=5/6/7, F0/G0/H0=17/23/29, J0=12, K0=11 |
| Größe DW3-Agumon → DW2-Agumon | geprüft: Faktor 1,04 (gleiche Einheiten in beiden Spielen) |
| Mods deaktivieren/aktivieren | geprüft: Dateien bytegleich zurück, nichts gelöscht |

## Ende-zu-Ende im Port (Begleit-Port, Commit c998953, Linux, ohne Fenster)

| Prüfung | Ergebnis |
|---|---|
| Renamon (DW3) in den Gazimon-Slot, Name „Renamon“, 11 Mod-Dateien + HD-Textur 512×1024 exportiert | geprüft |
| `--check-model` mit Renamons Modell und den Dateien A, C, K, F | geprüft: 21 Knochen, je 120 Spielschritte, HD-Textur gefunden |
| Neues Spiel → Boot Domain → erster Kampf (Story-Bot) | geprüft: Renamon steht als Gegner an Gazimons Platz, Name im Kampf „Renamon“, Größe wie Gizamon daneben, Angriff spielt, Kampf endet, Spiel läuft weiter |
| Gleicher Lauf ohne Mod | geprüft: Gazimon wie im Original |
| Referenzbilder des Ports (Original-Profil) | geprüft: 6/6 bitgleich |
| Speichern/Laden (save_test.py) | geprüft: 9/9 |
| Cheat- und Domain-Test | mit frischer Karte nicht aussagekräftig: scheitern im gepatchten und im unveränderten Port gleich (Karte ohne Gruppe und ohne Domain-Zugang) |

Gesehen in den Bildern, aber offen: In der Angriffs-Nahaufnahme ist Renamon teilweise außerhalb des Bildes (Kamera des ersetzten Digimon, DW3-Angriff mit Sprung).

## Nicht geprüft

- **Windows auf echter Hardware:** Viewer und Begleit-Port. Die CI baut beide und startet den Viewer einmal mit Software-OpenGL. Das ersetzt keinen Test auf deinem PC mit GTX 1070.
- **Klicks in der Oberfläche:** Der neue Dialog (Vorbelegung, Quelle je Platz, 2048×4096) und die Knöpfe zum Deaktivieren/Aktivieren sind nur über die Programmschnittstelle und `node --check` geprüft.
- **HD-Texturen im GPU-Renderer:** Der Kampftest lief im Software-Renderer (native Textur). Dass der Port die HD-Datei findet, zeigt nur `--check-model`.
- **2048×4096:** nur erzeugt, nicht im Port angesehen.
- **Längeres Spiel** mit ersetztem Partner-Digimon, Digitation in ein ersetztes Digimon, Spielstände mit ersetztem Digimon.

## Quellen

- DW2-Kampfplätze: dw2-pc-port, `src/stag0000/digimodel.c` (`Stg00_DigiModelTask`, `Stg00_HitReactUpdate`), `src/main/anim.c`.
- DW3-Skripte: dw3_decomp (MIT, ReGame Labs) `src/battle/battle_mode/hit_effect.c`, `battle_script.c`, `include/battle/battle_mode/effect.h` (Ergebnis 1 Treffer, 2 K.o., Skript = Ergebnis + 1), `src/battle/normal_battle/techs.c`; `config/us/symbols.txt` (Dateitabelle USA), `include/battle/battle_mode/model.h` (FILE_FIGHTERS, FighterInfo).
- Skriptleser: `third_party/dw3_converter` (Feerdus95/dw3-model-viewer, MIT), neue Option `--scripts`.

# DW3-Effekte und -Aktionen: Analyse für 1.0.0-rc1

Stand 14.11.2026. Quellen: DW3-Decompilation (dw3_decomp, nur gelesen), der mitgelieferte DW3-Konverter
(`third_party/dw3_converter`, `--scripts`), der DW2-PC-Port (nur gelesen).

## Was DW3 speichert
- Jeder Kämpfer hat in `FighterInfo` drei Verweise: Modell, Bewegungen, **Effekte** (Datei << 16 | Archiveintrag).
- Das Effektarchiv enthält die **Kampfskripte** (Eintrag N = Skript N: 0 Stand, 2 Treffer, 3 K.o., 5–8 Techniken)
  und die Effektdaten, die diese Skripte abspielen (Partikel, Sprites, Bahnen, Kamerafahrten, Töne).
- Die Skripte steuern Bewegungen, Ortswechsel (`moveCmd` 3/8), Trefferzeitpunkte und Effektaufrufe. Ausgeführt
  werden sie vom DW3-Kampfcode (`battle_script.c` und Effekt-Routinen im DW3-Programm).

## Was DW2 erwartet
- Eine DW2-Technik (WAZADATA, 68 Byte) verweist auf **DW2**-Effektteile (`partsEntry`, `fxFiles[4][3]`),
  einen Ruf (XA-Kanal/-Datei) und Zustandsbits. Abgespielt wird das vom DW2-Kampfcode
  (`src/stag3000/skilleffect.c` und Verwandte) mit fest eingebauten Abläufen und Kameras (Einstellungen 10–21).

## Ergebnis
| DW3-Bestandteil | Übertragbar? | Grund / Umsetzung |
|---|---|---|
| Bewegungen der Techniken (Motions) | **ja** | Seit 0.16b aus den Skripten vorbelegt (`dw3_motion_map.py`), Zuordnung änderbar |
| Trefferzeitpunkt | teilweise | Der Konverter liest ihn (`strike`). DW2 bestimmt den Treffer im eigenen Ablauf. Es wird nur die Bewegung gewählt, die beim ersten Treffer läuft |
| Gesicht (Augen, Gesichtszyklen) | **ja (1.0)** | `face_plan`/`atlas`: Augenrahmen offen/halb/zu als DW2-Augenanimation. Im Spiel nachgewiesen (VRAM-Kopie beim Blinzeln) |
| Effektgrafik (Partikel, Sprites) | **nein** | Andere Datenformate und ein anderer Abspielcode. DW2 kann nur DW2-Effektteile abspielen. Das bräuchte einen DW3-Effektinterpreter im Port |
| Ortswechsel / Sprünge im Skript | nein | DW2 bewegt Kämpfer in festen Abläufen. Skriptgesteuerte Wege gibt es dort nicht |
| Kamerafahrten der Technik | nein | DW2-Attackenkameras sind im Code fest (Einstellungen 10–21), ohne Daten je Digimon oder Technik |
| Ton | nein | DW3-Töne liegen in DW3-eigenen Soundbänken. DW2 spielt XA-Rufe aus seinen eigenen Dateien |
| Sichtbarkeit einzelner Teile je Aktion | nein | DW2-Modelle haben keine Sichtbarkeitsspur je Animation. Bewegungen werden 1:1 übernommen, ausgeblendete DW3-Teile bleiben sichtbar |

## Ersatz im Studio (umgesetzt)
- **Eigene Technik** aus einer DW2-Vorlage (Effekte, Teile, Ton, Zustand kopiert), mit eigenem Namen und eigenen Werten.
- **„Effekt/Ton/Animation übernehmen“**: einzelne Teile einer anderen DW2-Technik in die eigene Technik kopieren:
  Effekte `+0x0C..0x18` und `+0x2C..0x44`, Ton `+0x05..0x08`, Zustand `+0x18..0x1C`, Startanimation Bits 16–17.
- Die Trefferhöhe ist ein Wert des Digimon (MODELDT `hitFxOffsetY`). Sie wird beim DW3-Import aus der Modellhöhe gesetzt
  und ist im Digimon-Editor einstellbar.

## Was eine Port-Erweiterung bräuchte
Einen Interpreter für DW3-Effektarchive im Kampfcode des Ports: Lader für die DW3-Effektformate, Abspielen
der Effektbefehle aus den Skripten, Zuordnung der DW3-Zeitachse auf den DW2-Technikablauf. Das ist eine große
Änderung am Spielcode und nach Auftrag ausgeschlossen („Der DW2 PC-Port bleibt unverändert“). Darum ist das
hier nur beschrieben, nicht vorbereitet.

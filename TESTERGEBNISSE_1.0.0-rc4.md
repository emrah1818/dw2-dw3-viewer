# Testergebnisse DW2 Mod Studio 1.0.0-rc4

Stand 14.11.2026. Studio: Zweig `development/1.0`. Port: `emrah1818/dw2-pc-port`, Zweig `development/mod-studio-1.0`
(Commit in `integration/pc_port_base.txt`). Jede Angabe nennt, **wie** geprüft wurde:

- **Auf deinem Windows-PC getestet:** Windows 10 Education 19045, NVIDIA GeForce GTX 1070 (Treiber 32.0.15.6603),
  Vulkan. Studio und Port aus den Windows-Builds dieses Stands, deine `dw2.pak` und deine Original-BIN.
- **Im Spiel getestet (PC-Port, Linux):** echter Port, deine `dw2.pak`, Software-Renderer, Bot-Schnittstelle.
- **Im Emulator getestet (PS1):** Mednafen 1.29 mit OpenBIOS (freies BIOS), **deine Original-BIN**
  (SHA-256 `c8c8646d…d586a`, 461 993 952 Bytes) als Ausgangsbild.
- **Automatisiert getestet:** pytest und Port-Tests mit selbst erzeugten Daten.
- **Nicht getestet** ist ausdrücklich aufgeführt.

## Zahlen
| Prüfung | Ergebnis |
|---|---|
| pytest (lokal) | **379 bestanden, 4 übersprungen**, 0 fehlgeschlagen |
| Port-Renderer-Test `hd_test --require-gpu` auf der GTX 1070 | **bestanden** bei Skalierung 2, 4 und 8 (GPU-Bild = Software-Bild, Filter, Texturpakete) |
| `modconf_test` auf dem PC | bestanden |
| Port `--mod-api` auf dem PC | `mod_api 2`, `digivolve_levels 1`, `battle_camera 1` |
| Battle Mode mit drei DW3-Importen, GPU-Renderer, HD 2048×4096, auf dem PC | läuft, siehe unten |
| Port ohne Mods (`--no-mods`) auf dem PC | startet und läuft |
| Spielszenen PC-Port, Linux (evo, domain, partner, dna, domains) | 45 von 45 (Stand rc3, Code dafür unverändert) |
| PS1-Emulator mit deiner Original-BIN: Export, Kampf, Digitation, DNA, Speichern | bestanden |

Hinweis zu `hd_test`: Bei Skalierung 1 und 16 schlägt der Test auch unter Linux fehl. Er ist für 2 bis 8 gebaut
(Skalierung 1 hat kein HD, der Port erlaubt höchstens 12). Das ist eine Grenze des Testprogramms, kein Renderer-Fehler.

## Auf deinem Windows-PC getestet
**Port mit Grafikkarte.** Battle Mode, Spieler 1 und 2 mit Guilmon (#84), MegaloGrowmon (#131) und Growlmon (#48),
alle drei aus DW3 importiert mit HD-Textur 2048×4096. Gesteuert über eine Eingabedatei (`--press-file`), Bilder
aus dem Fenster. Ergebnis: Kampf läuft mit Vulkan, Modelle, Techniken (z. B. E-Stun Blast, Toy Flame) und das grüne
Gitter erscheinen, das Spiel endet ohne Absturz (Exit 0).

**Gefundener Fehler, behoben und erneut geprüft:** Der GPU-Renderer hat 128 MiB für Ersatztexturen. Drei
2048×4096-Texturen (je 32 MiB) und ihre Stufen passten nicht hinein. Der Speicher wurde in jedem Kampf mehrmals neu
gefüllt („replacement memory is full, it starts over“, 8× in einem Lauf). Dazwischen zeigten die Modelle die
niedrige Originaltextur. Das passt zu deinen Fotos vom Fernseher.
- Port-Korrektur 1: Ist der Speicher voll, nimmt der Renderer die nächstkleinere Stufe derselben Textur.
- Port-Korrektur 2: Eine Stufe ist höchstens 16 MiB groß (1024×2048 pro Seite, 8× Auflösung).
- Ergebnis auf der GTX 1070: Der Speicher wird im ganzen Lauf nicht mehr neu gefüllt (0×). Die HD-Textur bleibt im
  Speicher. Im Log steht: „drawing a smaller level of 2048x4096 (1/2) to keep it in GPU memory“.

**Mod Studio (Windows-Build).** Gestartet, deine Original-CUE geöffnet („395 Digimon · Modus B: PS1-Image“),
3D-Ansicht zeigt Agumon (WebGL), Mod-Export-Seite mit getrennten Gruppen Modus A/B, Hinweis beim Schließen mit
vorgemerkten Änderungen.
- **Name ändern:** Agumon → Agumax über „Name ändern“ und Enter. Mit dem korrigierten Build steht der Name nach
  unter 3 Sekunden in der Liste, im Kopf der Bearbeiten-Seite und unter dem 3D-Bild. Rückgängig ist aktiv.
- **Gefundener Fehler, behoben:** Vorher erschien der neue Name erst nach Minuten. Die Bearbeiten-Seite fragte sofort
  die Größentabelle aller 395 Digimon ab (auf einer BIN rund eine Minute, unter Windows länger). Jede weitere Aktion
  wartete dahinter. Die Größe lädt jetzt erst beim Aufklappen der Karte. Danach wird sie pro Image gespeichert.
  Auf dem PC dauerte das erste Aufklappen rund 1,5 Minuten.
- **Gefundener Fehler, behoben:** Kopf und Startseite zeigten „0.17b“ statt der Programmversion.
- **Neues Image exportieren:** aus deiner BIN mit dem neuen Namen, gespeichert als
  `Digimon_World_2_USA_bearbeitet.bin` plus passende `.cue` (`MODE2/2352`, richtiger Dateiname), Größe gleich dem Original.

## Im Emulator getestet: deine Original-BIN (PS1, Modus B)
Neues Image aus deiner BIN mit:
- DW3-Growlmon in Platz 48: kontrolliert verkleinert auf 1065 → 468 Dreiecke, Bewegungen B/J/K mit jedem 2.,
  C mit jedem 4. Bild.
- DW3-Renamon in Platz 131: 848 → 552 Dreiecke.
- Agumon digitiert zu Platz 48, Agumon heißt „Agumax“.

**BIN/CUE-Konsistenz:**
- Gleiche Größe wie das Original (196 426 Sektoren).
- 252 Sektoren geändert, jeder davon mit gültiger EDC und gültigem Subheader.
- Alle anderen Sektoren sind byte-gleich.
- Die CUE wird geschrieben, das Studio öffnet das neue Image wieder.
- Dein Original ist unverändert (gleiche SHA-256).

1. **Spielstand laden:** Ein Port-Spielstand mit Renamon, Agumon, Greymon (Lv20) lädt im PS1-Spiel.
2. **Digitation:** Im Digi-Labor heißt es „Digivolve to Growlmon“. Agumax wird zum DW3-Growlmon. Die Liste zeigt
   Renamon und Agumax.
3. **Speichern im PS1-Spiel:** „The game has been saved.“ Die Memory Card ändert sich. Der PC-Port lädt diesen
   Spielstand mit Growlmon (#48) Lv20 im Team.
4. **DNA:** Greymon und das DW3-Growlmon ergeben „DNA digivolve to ToyAgumon?“ (Platz 84 nach der DNA-Tabelle des
   Spiels). Die Eltern verschmelzen, das neue Digimon steht mit Lv1 im Spielspeicher.
5. **Battle Mode:** Der Kampf läuft. In der Übersicht steht das DW3-Renamon auf dem grünen Gitter.

Abkürzung im Test: Den Weg ins Digi-Labor und zur Stadtkarte habe ich über einen geänderten Emulator-Zustand
genommen (nur der nächste Spielmodus, wie `warp=` im Port, `integration/ps1emu/stpatch.py`). Labor, DNA und
Speichern liefen über die Menüs des Spiels.

## Im Spiel getestet (PC-Port, Linux, aus rc3)
- **Digitationslevel:** Sperre, Digitation in und aus importierten Digimon, Speichern/Laden, Blinzeln (17/17).
- **Partner:** eigene Technik, Kampfkamera, Modelle ganz im Bild (11/11).
- **DNA mit importiertem Elternteil und importiertem Ergebnis:** 7/7.
- **Importiertes MegaloGrowmon als Gegner:** SCSI 2F, Laser 3F und Core Tower 4F sowie Boot Domain (6/6 und 4/4).

## Nicht getestet
- Echte PS1-Hardware und andere Emulatoren als Mednafen. DuckStation auf deinem PC habe ich nicht gestartet: Sein
  Ordner liegt auf dem Desktop, außerhalb des freigegebenen Ordners.
- Laufen durch die Stadt bis zum Labor im PS1-Spiel (abgekürzt, siehe oben).
- Gegner auf Domains im PS1-Emulator. Gegner auf Domains sind nur im PC-Port geprüft, dort auf 4 von 35 Domains.
- Alle DW3-Modelle einzeln im Spiel. Geprüft: Guilmon, Growlmon, MegaloGrowmon, Renamon.
- Bildvergleich HD an/aus bei gleichem Kampfbild auf dem PC: Der Kampf verläuft bei jedem Lauf anders (Zufall),
  daher gibt es keine deckungsgleichen Bilder. Geprüft ist, dass die HD-Textur im GPU-Speicher bleibt.
- Exklusiver Vollbildmodus und andere Grafikkarten als die GTX 1070.
- DW3 Europa (DW2003).

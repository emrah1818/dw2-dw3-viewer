# Testergebnisse 1.0.0-rc5

## DW3 → DW2: gemessen gegen die DW3-Originaltexel an den Stellen, die das Spiel liest
(jedes Polygon-Texel über die gerundeten Spiel-UVs; `dw3_native.quality_report`, Karte im Studio)

| Modell | Dreiecke Quelle / PC / PS1 | Atlas-Maßstab | HD (4×, 512×1024): exakte Texel | PSNR HD | PSNR 1x | UV-Rundung Ø / max | Augen |
|---|---|---|---|---|---|---|---|
| Greymon M005GREY | 952 / 952 / 952 | 0,98 | 99,9 % | 50,5 dB | 31,0 dB | 0,30 / 0,69 | 1 |
| Guilmon M366GIRU | 914 / 914 / 914 | 0,90 | 99,8 % | 47,2 dB | 24,9 dB | 0,40 / 0,76 | 1 |
| Growlmon M367GRAW | 1065 / 1065 / 1065 | 0,90 | 99,8 % | 49,9 dB | 24,3 dB | 0,42 / 0,75 | 1 |
| MegaloGrowmon M368MGRW | 1531 / 1531 / 1531 | 0,73 | 97,9 % | 30,0 dB | 20,7 dB | 0,60 / 0,96 | 1 |

rc4 zum Vergleich (Greymon): 64×112-Kachel je Seite, UV Ø 1,40 / max 2,30, Auge fehlte. PS1-Image rc5-Entwurf: Greymon 479 Dreiecke.
Die HD-Abweichungen liegen dort, wo mehrere Polygone dieselben Texel nutzen (eine Rundung je Texelbereich).

## PS1-Image (Modus B), echte US-BIN, Mednafen 1.29 + OpenBIOS
- 4 DW3-Importe, **keine Verkleinerung**. 18 Dateien ans Ende des Images verlagert (z. B. M131GAZI.BIN 31 552 → 55 880 Bytes).
- Battle Mode, Spieler 1 Greymon/MegaloGrowmon/Growlmon, Spieler 2 Guilmon/MetalGreymon/Myotismon:
  Kampf läuft, Angriffe und Treffer, alle Modelle vollständig. Skript `integration/ps1emu/scripts/bmode_two_cards.txt`.
- Nicht geprüft: echte PS1-Hardware, andere Emulatoren, Domains/Stadt mit DW3-Importen auf der PS1.

## PC-Port (Linux), Battle Mode, gleicher Ablauf
- Software-Renderer 4×: HD ändert nur die Modellbereiche. Die hellen Kantenlinien (rc5-Entwurf) sind weg (Bildvergleich Greymon-Stirn).
- GPU-Renderer (Vulkan, Mesa lavapipe) mit vier 2048×4096-Texturen: 3 Speicherbereiche à 128 MiB angelegt,
  keine kleinere Stufe, kein Neustart des Speichers. „HD summary: 5 copy picture(s), 0 … fell back to 1x“.
- `hd_test --require-gpu --scale 4`: 0 Fehler.

## Studio
- pytest: 384 bestanden, 4 übersprungen.
- HD-Vorschau mit Blinzeln: Code geprüft (Syntax), **in der Oberfläche noch nicht geprüft**.

## Windows / Vulkan (GTX 1070)
**Ausstehend:** Der PC war nicht erreichbar. Testordner `Test_p0` liegt bereit.

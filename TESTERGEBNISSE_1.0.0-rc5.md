# Testergebnisse 1.0.0-rc5

## DW3 → DW2 (gemessen gegen die DW3-Originaltexel, jedes Polygon-Texel)
| Modell | Dreiecke Quelle/konvertiert (PC) | Atlas-Maßstab | PSNR 1x | PSNR HD | UV Ø/max (Quelltexel) | Augen |
|---|---|---|---|---|---|---|
| Greymon M005GREY | 952 / 952 | 0,98 | 33,0–40,4 dB | identisch | 0,30 / 0,82 | 1 (vorher 0) |
| Guilmon M366GIRU | 2242 / 2242 | 0,89 | siehe Bericht | identisch | – | ja |
| Growlmon M367GRAW | voll | 0,89 | 26,8 dB (vorher 20,1) | identisch | – | ja |
| MegaloGrowmon M368MGRW | voll | 0,73 | geringer (Maßstab) | identisch | – | ja |

Vorher (rc4) Greymon: Kachel 64×112 je Seite, PSNR 1x 18–22 dB, UV Ø 1,40 / max 2,30.
PS1-Image (Modus B, echte US-BIN): Greymon 952 → 479 Dreiecke (Größenlimit der Originaldatei), im Bericht angezeigt.

## Im Spiel (Linux, Soft-Renderer, Battle Mode, 4×)
- Gleiche Bilder mit/ohne HD-Paket. HD ändert nur die Modellbereiche.
- Greymon blinzelt mit HD: 6 Kopie-Bilder erzeugt, **0** Rückfälle auf 1x („HD summary“).

## Windows / Vulkan
Ausstehend in diesem Stand (wird nachgetragen).

## Automatische Tests
pytest: alle grün (siehe CI-Artefakt).

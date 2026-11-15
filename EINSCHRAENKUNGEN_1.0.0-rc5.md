# Bekannte Einschränkungen 1.0.0-rc5

Release-Kandidat, kein FINAL. Grund: Der Windows-Test auf der GTX 1070 steht aus (PC nicht erreichbar), und die
Studio-HD-Vorschau mit Blinzeln ist nicht in der Oberfläche geprüft.

Alle Größen- und Qualitätsgrenzen mit Ursache und Messung: `GRENZEN_ANALYSE_1.0.0-rc5.md`. Kurz:

- **PC-Port (Modus A):** keine Polygon- oder Bewegungsreduktion. Die HD-Textur liest an 98–99,9 % der Stellen den
  exakten Originaltexel. Farbtiefe 15 Bit wie die PS1 (DW3-Texturen haben selbst 15 Bit).
- **PS1-Image (Modus B):** keine Verkleinerung mehr (Dateien werden verlagert). Echte Grenzen: 1x-Textur 128×224 bei
  4 Bit (VRAM-Belegung des Spiels), 2 MB RAM (nur der getestete Kampf ist belegt).
- **Nicht geprüft:** echte PS1-Hardware, DuckStation, andere Grafikkarten, exklusiver Vollbildmodus.

## DW3-Effekte, -Töne, -Kamerafahrten
Nicht übertragen (eigene DW3-Formate und DW3-Code). Übertragen werden Modell, Texturen, Bewegungen, Augen/Gesicht.
Details: `DW3_EFFEKTE_ANALYSE.md`.

## Grenzen der Daten (unverändert)
- Technik-IDs ein Byte (höchstens 255). Gegnergruppen-IDs 1–255.
- Modellformat: 256 Vertices/Normalen/Dreiecke je Teil (automatisch geteilt), 8 Ebenen, 64 Teile, 254 Posen je Knochen.
- Ziele mit geteilten Animationsdateien werden beim DW3-Import abgelehnt.
- Digimon-Namen höchstens 13 Zeichen, Technik-Namen höchstens 17 Zeichen.

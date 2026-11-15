# Bekannte Einschränkungen 0.95

## DW3-Import
- **DW3-Effekte, -Töne, -Kamerafahrten** werden nicht übertragen (eigene DW3-Formate). Übertragen werden Modell,
  Texturen, Bewegungen, Augen. Details: `DW3_EFFEKTE_ANALYSE.md`.
- **Beleuchtung:** DW2 beleuchtet Modelle über Normalen, DW3 zeigt sie heller. Importe wirken im Kampf und im
  Studio etwas dunkler als im DW3-Original (weiße Flächen leicht grau).
- **„DW3-Original ansehen“** zeigt auch Effektteile, die DW3 in der Bewegung ausblendet (WarGreymons Lichtkranz,
  Brustkanone von Imperialdramon FM). Der Import blendet sie richtig aus.
- **UV-Raster:** Die UVs bleiben Bytes auf dem 1x-Raster. Die HD-Textur gleicht das aus, außer wo mehrere Polygone
  dieselben Texel teilen (WarGreymon 0,3 %, Imperialdramon 1,5–1,8 % der Texel, 15 von 248 Modellen über 3 %).
- **1x-Textur** (ohne HD-Paket, Pixel-Look mit HD aus, PS1-Image): 128×224 Texel, 15 Farben je Seite. Bei Modellen
  mit vielen Texturseiten deutlich gröber (Imperialdramon FM Maßstab 0,53).
- **Mehr als 64 Modellteile** und ein erweitertes Modellformat sind nicht umgesetzt. Kein DW3-Modell braucht es
  (höchstens 45 Teile). Ein Modell mit mehr Teilen wird mit Meldung abgelehnt.
- **24-Bit-Texturen:** Der GPU-Renderer zeichnet HD-Texturen in 24 Bit. Der Software-Renderer und die 1x-Textur
  bleiben bei 15 Bit. Das Studio erzeugt HD-Texturen aus DW3 (15 Bit Quelle); eigene 24-/32-Bit-PNGs als HD-Textur
  sind über den HD-Import möglich, aber in dieser Version nicht eigens getestet.
- **GPU-Speicher:** bis 7 × 128 MiB (Grenze der Grafikschnittstelle: 8 Speicherbereiche je Shader). Größer als
  2048×4096 je Seite geht nicht (HD-Faktor höchstens 16).
- Ziele mit geteilten Animationsdateien werden beim Import abgelehnt. Welche Plätze geeignet sind, zeigt das Studio.

## Tests
- Auf Windows im Spiel geprüft: sieben Digimon im Battle Mode auf einer GTX 1070. Das Studio lief auf Windows nur im
  automatischen Starttest; seine Funktionen sind unter Linux in der echten Oberfläche geprüft.
- Nicht geprüft: Vollbild, andere Grafikkarten, Domains/Stadt mit den neuen Importen, echte PS1-Hardware.

## Grenzen der Daten (unverändert)
- Technik-IDs ein Byte (höchstens 255). Gegnergruppen-IDs 1–255.
- Modellformat: 256 Vertices/Normalen/Dreiecke je Teil (automatisch geteilt), 8 Ebenen, 64 Teile, 254 Posen je Knochen.
- Digimon-Namen höchstens 13 Zeichen, Technik-Namen höchstens 17 Zeichen.

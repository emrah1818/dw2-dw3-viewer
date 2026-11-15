# Testergebnisse 0.95

Alle Werte sind gemessen (Skripte im Repository: `dw3_native.quality_report`, `integration/uitest/`, `integration/windows/`).
Nicht Gemessenes ist als solches gekennzeichnet.

## 1. Die sieben Digimon: DW3-Original gegen Import
| Digimon | DW3-Modell | DW2-Platz im Test | Dreiecke Quelle = Import | Vertices | Teile | Texturseiten | Atlas-Maßstab | HD | exakte Texel HD | PSNR HD | PSNR 1x | UV-Rundung Ø / max | Augen | Bewegungen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Greymon | M005GREY | #5 | 952 = 952 | 539 | 22 | 4 | 0.981 | 512×1024 | 99.9 % | 50.5 dB | 31.0 dB | 0.3 / 0.69 | 1 | 62 von 62 |
| Guilmon | M366GIRU | #84 | 914 = 914 | 523 | 24 | 2 | 0.902 | 512×1024 | 99.8 % | 47.2 dB | 24.9 dB | 0.4 / 0.76 | 1 | 62 von 62 |
| Growlmon | M367GRAW | #48 | 1065 = 1065 | 593 | 24 | 2 | 0.902 | 512×1024 | 99.8 % | 49.9 dB | 24.3 dB | 0.42 / 0.75 | 1 | 62 von 62 |
| MegaloGrowmon | M368MGRW | #131 | 1531 = 1531 | 860 | 27 | 6 | 0.731 | 512×1024 | 97.9 % | 30.0 dB | 20.7 dB | 0.6 / 0.96 | 1 | 62 von 62 |
| WarGreymon | M213WGRE | #213 | 1420 = 1420 | 698 | 24 | 16 | 0.654 | 512×1024 | 99.7 % | 38.2 dB | 22.0 dB | 0.77 / 1.06 | 1 | 62 von 62 |
| Imperialdramon Fighter Mode | M359IPDF | #150 | 1603 = 1603 | 917 | 26 | 13 | 0.529 | 512×1024 | 98.2 % | 35.2 dB | 23.8 dB | 0.73 / 1.34 | 1 | 62 von 62 |
| Imperialdramon Paladin Mode | M381IPDP | #246 | 1517 = 1517 | 852 | 26 | 10 | 0.556 | 512×1024 | 98.5 % | 35.6 dB | 21.3 dB | 0.73 / 1.26 | 1 | 62 von 62 |

- „exakte Texel HD“: Anteil der Polygon-Texel, an denen das Spiel über seine UVs genau den DW3-Originaltexel liest.
- Geometrie: bei allen sieben kein Dreieck und kein Vertex verloren. Animationen: alle 62 Bewegungen je Modell lassen
  sich umrechnen; im Kampf geprüft sind Stand, Angriff, Treffer, K.o. (soweit im Testkampf vorgekommen).

## 2. Warum WarGreymon und Imperialdramon in rc4/rc4b so schlecht aussahen
- Geometrie war auch in rc4 vollständig (WarGreymon 1420, Fighter Mode 1603, Paladin Mode 1517 Dreiecke).
- Ursache war die Textur: Diese Modelle haben 10 bis 16 Texturseiten. rc4 gab jeder Seite eine feste Kachel im
  128×224-Atlas, bei 16 Seiten 32×56 Texel je 256×256-Seite (8× bzw. 4,6× verkleinert). Die UVs wurden auf dieses
  grobe Raster gerundet, dadurch griffen Polygone in Nachbarbereiche (falsche Farben an Helm, Schultern, Hüfte).
- Behoben: Atlas nur aus den genutzten UV-Bereichen (Maßstab 0,53 bis 0,65 statt 0,125), HD-Textur über die
  Spiel-UVs auf die Originaltexel abgebildet. Vergleichsbild rc4 gegen 0.95 im selben Kampfbild liegt dem Bericht bei.

## 3. Alle DW3-Modelle (allgemeines Importsystem)
249 Einträge im DW3-USA-Abbild, 248 sind Modelle (M500WAVE ist kein Modell). Alle 248 wurden umgerechnet:
- Dreiecke verloren: bei 0 Modellen. Größtes Modell 2245 Dreiecke. Höchstens 45 Teile (Grenze 64 wird nie erreicht).
- Alle Bewegungen aller Modelle umrechenbar.
- Exakte Texel HD: Median 99,2 %. 15 Modelle unter 97 % (kleinster Wert 69,9 % bei M463CDS1, einem Karten-Modell;
  sonst ≥ 91,7 %). Atlas-Maßstab 0,48 bis 1,0 (Median 0,79). HD-Größen 256×512 bis 1024×2048, automatisch gewählt.
- 46 Modelle ohne erkannte Augenanimation (nicht einzeln geprüft, ob DW3 dort eine hat).
- Nur die sieben oben wurden im Spiel angesehen.

## 4. Windows-PC (GTX 1070, Treiber 32.0.15.6603, Windows 10 19045, Vulkan, Fenster, 4×)
Battle Mode, automatischer Ablauf (`integration/windows/DW2-Windows-Test.ps1`), 8 Fensterbilder je Lauf:
| Lauf | Digimon | Ergebnis |
|---|---|---|
| A_hd | WarGreymon, Imperialdramon FM, Imperialdramon PM | Exit 0. HD aktiv, 24 Bit, 1 Speicherbereich (128 MiB). Blinzeln: 6 HD-Kopien, 0 Rückfälle auf 1x |
| B_hd | Greymon, Guilmon, Growlmon | Exit 0, wie oben |
| C_hd | MegaloGrowmon, WarGreymon, Imperialdramon FM | Exit 0, wie oben |
| A_nopack | wie A, ohne HD-Paket | Exit 0 (Vergleich 1x) |
| A_hd_15bit | wie A, 15-Bit-Farben | Exit 0. Log: „replacement colours: 15 bit“, sonst wie A_hd |
Alle sieben Modelle vollständig, Texturen richtig zugeordnet, Angriffe und Treffer liefen. Keine hellen Kantenlinien in den Bildern.
**Nicht auf Windows geprüft:** das Studio selbst (nur der automatische Starttest im Build), Vollbild, 2048×4096-Texturen
(nur unter Linux/Software-Vulkan), andere Grafikkarten.

## 5. Linux
- Software-Renderer und GPU-Renderer (Mesa lavapipe): gleicher Kampf, gleiche Ergebnisse im Log. `hd_test --require-gpu`: 0 Fehler.
- Vier 2048×4096-Texturen im GPU-Renderer: 3 Speicherbereiche, keine kleinere Stufe (Stand vor der Erweiterung auf 7 Bereiche).
- Größe: WarGreymon-Import steht im selben Kampfbild so groß wie das DW2-Original (Bildvergleich).

## 6. Studio-Funktionen (echte Oberfläche in Headless-Chrome, `integration/uitest/functions.py`): 21 von 21 bestanden
DW2-pak öffnen, DW3 öffnen, Import mit allen Dreiecken, Viewer mit automatischer HD-Textur, Qualitätskarte,
11 Animationen bewegen das Skelett, Blinzeln in der HD-Vorschau (Bild wechselt, öffnet wieder, blinzelt im Ablauf),
Pixel-Look nur als Filter, HD abschaltbar, Name ändern, Größe ändern und zurück, Projekt speichern/laden, Mod-Prüfung,
Mod-Export mit HD-Textur, keine JavaScript-Fehler. Vergleich Original/Import mit gleichem Bildausschnitt: `compare.py`.
Dabei gefunden und behoben: Der Größenfaktor multiplizierte sich bei wiederholtem Ändern auf.
**Nicht geprüft:** Textur-Import/-Export per PNG in dieser Runde (unverändert seit rc4, dort geprüft).

## 7. PS1-Image (keine Priorität)
Mednafen + OpenBIOS: 4 unverkleinerte DW3-Importe im Kampf (Stand rc5, siehe GRENZEN_ANALYSE). WarGreymon und
Imperialdramon nicht im PS1-Image geprüft.

## 8. Automatische Tests
pytest: 384 bestanden, 4 übersprungen (brauchen private Spieldaten).

# Größen- und Qualitätsgrenzen beim DW3-Import (Analyse 0.95)

Jede Grenze ist geprüft und einer Ursache zugeordnet: **Hardware** (echte PS1), **Spiel-Engine** (Code von DW2),
**Format** (DW2-Dateiformat) oder **Editor** (nur Studio/Port, aufhebbar).

## Aufgehoben

| Grenze bis rc4/rc5 | Ursache | Jetzt |
|---|---|---|
| PS1-Image: Modell- und Bewegungsdatei höchstens so groß wie das Original. Sonst Dreiecke zusammengefasst (Greymon 952 → 479) bzw. Bewegungsbilder ausgelassen | **Editor.** Das Spiel liest Sektor und Länge jeder Datei aus der Tabelle in `SLUS_011.93` (`Cd_FileLba` / `Cd_FileSectors`) und reserviert den Puffer nach dieser Länge (`Cd_QueueFile` → `Mem_Alloc(Sektoren << 11)`). | Größere Dateien wandern ans Ende des Images: Tabelle, ISO-Einträge und Volumengröße werden angepasst. **Nichts wird verkleinert.** Nur wenn Verlagern unmöglich ist, kann der Nutzer die Verkleinerung ausdrücklich erlauben. Sonst bricht der Import mit Originalgröße, Zielgröße und Grund ab. |
| Textur: jede DW3-Seite (256×256) fest auf 64×112 Texel verkleinert | **Editor** (starres Raster) | Nur die genutzten UV-Bereiche, dicht gepackt, ein gemeinsamer Maßstab (Greymon 0,98; Guilmon/Growlmon 0,90; MegaloGrowmon 0,73) |
| HD-Textur nur hochskaliert, UV-Rundung zeigt Nachbartexel (helle Kantenlinien) | **Editor** | HD-Bild wird über die gerundeten Spiel-UVs auf die Originaltexel abgebildet. Lücken werden aufgefüllt. Die Kantenlinien sind verschwunden. |
| GPU: höchstens 16 MiB je Textur, ein 128-MiB-Speicher (2048×4096 wurde als 1024×2048 gezeichnet) | **Port** | Bis zu 4 × 128 MiB (512 MiB), bei Bedarf angelegt und protokolliert. 2048×4096 wird in voller Größe gezeichnet. `DW2_TEXTURE_MEMORY_MB` begrenzt den Speicher. |
| Blinzeln fiel auf die 1x-Textur zurück | **Port** | VRAM-Kopien werden im HD-Bild nachgebildet, im Port und in der Studio-HD-Vorschau. |
| Greymons Auge fehlte | **Editor** | Gesichtsrechtecke werden über Polygon-Überlappung erkannt. |

## Bleiben (technisch begründet)

| Grenze | Ursache | Wirkung / Umgang |
|---|---|---|
| 1x-Textur: 128×224 Texel, 4 Bit (15 Farben + transparent je Palette) | **Spiel-Engine + Hardware:** DW2 legt jedes Kampf-Digimon in einen festen 128×256-Bereich im 1 MB großen VRAM der PS1 (zusammen mit Bildspeicher und anderen Figuren) | PS1-Image: Texturdetails nach Atlas-Maßstab (Greymon fast 1:1, MegaloGrowmon 0,73). **Im PC-Port (Modus A) unerheblich:** Die HD-Textur enthält die Originaltexel. Ein größerer VRAM-Bereich bräuchte einen Umbau der VRAM-Belegung des Spiels auf der PS1. Nicht umgesetzt. |
| UVs als Byte (0–255) auf dem 1x-Raster | **Format/Hardware** (PS1-GPU-Befehle) | Die Rundung (Ø 0,3–0,6, max. 0,96 Quelltexel) wird in der HD-Textur ausgeglichen. 99,8–99,9 % der Texel stimmen exakt (MegaloGrowmon 97,9 %). Abweichungen gibt es nur, wo Polygone dieselben Texel teilen. |
| Farbtiefe 15 Bit (5 Bit je Kanal) | **Hardware**, im Port nachgebildet (Bildspeicher wie die PS1) | DW3-Texturen sind selbst 15 Bit: **kein Verlust bei DW3-Importen.** Künftige 24-Bit-Texturen würden auf 15 Bit gerundet (mit Dithering). |
| Je Modellteil 256 Vertices / Normalen / Dreiecke, 64 Teile, 8 Ebenen | **Format** (Byte-Indizes) | Große Knochen werden automatisch in Teile geteilt, **ohne Verlust**. Ein Modell über 64 Teile wird abgelehnt (mit Meldung). |
| HD höchstens 16× (2048×4096 je Seite) | **Port** (5-Bit-Faktor im Shader, Speicher) | Für DW3 genügt 4× (jeder Originaltexel ≥ 2 Pixel). |
| PS1-RAM (2 MB) | **Hardware** | Größere Dateien brauchen mehr Speicher im Kampf. Geprüft in Mednafen: 6 verschiedene Digimon, davon 4 volle DW3-Importe (bis 55 880 Bytes Modell), lief stabil. Andere Kombinationen und Orte (Domains) sind nicht geprüft. |
| Disc: Sektoranzahl 16 Bit je Datei, CD-Länge 80 min | **Format/Hardware** | Weit über den heutigen Größen (128 MB je Datei). |

# DW2 Mod Studio 1.0.0-rc5 (Release-Kandidat, Schwerpunkt DW3-Importqualität)

## Ursache des Qualitätsverlusts (gemessen an DW3 Greymon M005GREY)
- Die Geometrie war vollständig (952/952 Dreiecke).
- Die Texturen wurden verkleinert: Jede 256×256-Seite kam ganz in eine feste 64×112-Kachel (4× bzw. 2,3× kleiner),
  obwohl das Modell nur einen Teil davon nutzt. Dazu UV-Rundung (Ø 1,4 Quelltexel). Greymons Auge wurde nicht übernommen.

## Änderungen
- **Neuer Texturatlas:** nur die genutzten UV-Bereiche, dicht gepackt (Skyline), ein gemeinsamer Maßstab, ggf. gedreht.
- **HD-Textur:** jeder Originaltexel exakt (Faktor so, dass ≥ 2 Pixel je Texel). Kleiner als bisher (512×1024 statt 2048×4096).
- **1x-Palette** aus den Originalfarben der Seite. Behebt z. B. Growlmons gelbe Brust.
- **Augen:** Gesichtsrechtecke werden über Polygon-Überlappung erkannt. Greymons Auge blinzelt.
- **Port:** Blinzeln behält die HD-Textur (VRAM-Kopien werden ins HD-Bild übernommen). Log-Zeile „HD summary“ beim
  Beenden. Die 16-MiB-GPU-Grenze wird protokolliert.
- **Studio:** Karte „DW3-Import: Qualität (gemessen)“ zeigt Quelle gegen konvertiert (Dreiecke, Vertices, Seiten,
  PSNR 1x/HD, UV-Abweichung, Augen) und das DW3-Original im Viewer. Modus A zeigt automatisch die HD-Textur.
  Pixel-Look ist nur noch ein Filter.

Details: `TESTERGEBNISSE_1.0.0-rc5.md`, `EINSCHRAENKUNGEN_1.0.0-rc5.md`.

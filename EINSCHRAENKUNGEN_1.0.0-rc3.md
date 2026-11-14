# Bekannte Einschränkungen 1.0.0-rc3

Diese Version ist ein **Release-Kandidat**, kein 1.0.0 FINAL.

## Warum noch nicht FINAL
1. **Nicht auf einem echten Windows-PC im Spiel geprüft.** Studio und Port werden unter Windows gebaut und
   automatisch geprüft (Startprüfung, Port-Tests). Die Spieltests liefen unter Linux mit dem Software-Renderer.
   Grafikkarten-Renderer und HD bis 2048×4096 im laufenden Spiel sind ungeprüft.
2. **PS1-Modus nicht mit deiner Original-BIN geprüft.** Getestet wurde ein aus der `dw2.pak` neu gebautes Abbild im
   Emulator (Mednafen mit freiem BIOS), nicht auf echter Hardware. Andere Abbilder können abweichen. Das Studio lehnt
   nicht unterstützte Aufbauten ab (mehrere Spuren in der CUE, Mode 2 Form 2 im Dateisystem, unbekannte Sektorgröße).
3. Im PS1-Test wurde der Weg ins Digi-Labor und zur Stadtkarte über einen geänderten Emulator-Zustand abgekürzt
   (nur der nächste Spielmodus, wie `warp=` im Port). Labor, DNA und Speichern liefen über die Menüs des Spiels.

## DW3-Effekte, -Töne, -Kamerafahrten (Teil C)
Nicht übertragen. DW3 speichert sie in eigenen Formaten, abgespielt von DW3-eigenem Code. Der DW2-Port bräuchte dafür
einen eigenen DW3-Effektinterpreter. Das ist nicht umgesetzt. Ersatz im Studio: Effekt, Ton, Zustand und
Startanimation einer DW2-Technik übernehmen. Übertragen werden: Modell, Texturen, Bewegungen, Augen/Gesicht.
Ein DW3-Import ist deshalb **kein vollständiger DW3-Import** der Techniken. Details: `DW3_EFFEKTE_ANALYSE.md`.

## Was es nur im PC-Port gibt (Modus A)
- Digitationslevel je Digimon, Kampfkamera je Digimon, HD-Texturen, Dateien größer als das Original.
- Ohne den mitgelieferten Port haben `digivolve_levels.json` und `battle_camera.json` keine Wirkung (Studio warnt beim Export).

## PS1-Image (Modus B)
- Jede geänderte Datei muss in die Größe der Originaldatei passen. Ein DW3-Modell, das zu groß ist, wird kontrolliert
  verkleinert (Dreiecke zusammenfassen, Animation mit weniger Zwischenbildern). Der Import-Bericht nennt die Werte
  vorher/nachher. Passt es auch dann nicht, bricht der Import ab, statt ein kaputtes Image zu schreiben.
- Das Original wird nie stillschweigend geändert. „Image überschreiben“ fragt nach und legt vorher eine Sicherung an.
- Getestet mit Mednafen und freiem BIOS, nicht auf echter Hardware.

## Grenzen der Daten (unverändert aus rc1)
- Technik-IDs ein Byte (höchstens 255, im US-Spiel 45 frei). Gegnergruppen-IDs 1–255.
- Modellformat: 256 Vertices/Normalen/Dreiecke je Teil, 8 Ebenen, 64 Teile, 254 Posen je Knochen. Große Knochen
  werden automatisch geteilt, tiefere Ebenen exakt eingehängt.
- Ziele mit geteilten Animationsdateien werden beim DW3-Import abgelehnt.
- Digimon-Namen höchstens 13 Zeichen, Technik-Namen höchstens 17 Zeichen, US-Zeichensatz des Spiels.

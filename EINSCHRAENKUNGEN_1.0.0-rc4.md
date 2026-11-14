# Bekannte Einschränkungen 1.0.0-rc4

Diese Version ist ein **Release-Kandidat**, kein 1.0.0 FINAL.

## Warum noch nicht FINAL
1. **Nicht auf echter PS1-Hardware geprüft.** Das PS1-Image (aus deiner Original-BIN) lief in Mednafen mit freiem
   BIOS. Andere Emulatoren, darunter DuckStation auf deinem PC, sind ungetestet.
2. **Nicht alle Inhalte im laufenden Spiel geprüft.** Gegner auf 4 von 35 Domains im PC-Port. DW3-Modelle im Spiel:
   Guilmon, Growlmon, MegaloGrowmon, Renamon. Die übrigen Domains und Modelle sind nur strukturell oder automatisch
   geprüft.
3. **Abkürzungen in den Spieltests:** Sprünge in Domains, Etagen, Digi-Labor und Stadtkarte über die
   Entwickler-Bearbeitung bzw. einen geänderten Emulator-Zustand. Die geprüften Abläufe selbst liefen über die Menüs
   des Spiels.
4. **Windows:** geprüft auf einem PC (GTX 1070, Vulkan, Fenstermodus). Andere Grafikkarten und der exklusive
   Vollbildmodus sind ungetestet.

## GPU-Renderer und HD-Texturen
Ersatztexturen werden auf der Grafikkarte mit höchstens 1024×2048 Pixeln je 128×256-Seite gezeichnet (8×). Eine
2048×4096-Textur (16×) bleibt im Paket und erscheint im Software-Renderer bei hoher Skalierung voll. Auf der
Grafikkarte nimmt der Port die halbe Stufe, damit mehrere große Modelle zugleich in den Speicher passen.

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

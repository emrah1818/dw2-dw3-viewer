# Testergebnisse DW2 Mod Studio 1.0.0-rc2

Stand 14.11.2026. Studio: Zweig `development/1.0`. Port: `emrah1818/dw2-pc-port`, Zweig `development/mod-studio-1.0`
(Commit in `integration/pc_port_base.txt`). Jede Angabe nennt, **wie** geprüft wurde:

- **Im Spiel getestet (PC-Port):** echter Port aus diesem Zweig, eigene `dw2.pak`, Linux ohne Fenster
  (Software-Renderer, Bot-Schnittstelle des Ports). Kein echter Windows-PC.
- **Im Emulator getestet (PS1):** Mednafen 1.29 mit OpenBIOS (freies BIOS, kein Sony-BIOS), gesteuert per Tastatur-Skript.
  Abbild: aus meiner `dw2.pak` neu zusammengesetztes DW2-Abbild (Dateien an ihren Original-LBAs, ISO9660), nicht dein
  Original-BIN (461 MB, über die Brücke nicht übertragbar).
- **Automatisiert getestet:** pytest und Port-Tests mit selbst erzeugten Daten (keine Spieldaten).
- **Nur strukturell validiert:** mit echten Daten gelesen/geschrieben und verglichen, nicht im Spiel angesehen.
- **Nicht getestet** und **Fehlgeschlagen** sind ausdrücklich aufgeführt.

## Zahlen
| Prüfung | Ergebnis |
|---|---|
| pytest (lokal, Linux) | **378 bestanden, 4 übersprungen**, 0 fehlgeschlagen |
| pytest in GitHub Actions | `test-summary.txt` / `test-results.xml` im Release |
| Port-Tests unter Windows (Actions): `--mod-api`, Cache-Test, Schriften, Text, `modconf_test`, `hd_test` | bestanden; GPU-Teil von `hd_test` übersprungen (kein Vulkan-Gerät auf dem Server) |
| Spielszene „evo“ (Port) | **17 von 17** |
| Spielszene „partner“ mit Kampfkamera (Port) | **11 von 11** |
| Spielszene „domain“ (Port, Stand rc1) | 4 von 4 |
| PS1: Export, Wiederöffnen, Emulatorstart, Kampf | bestanden (siehe unten) |

## Im Spiel getestet (PC-Port)
**Digitationslevel (`Mods\digivolve_levels.json`):** DW3-Guilmon/-Growlmon/-MegaloGrowmon in 84/48/12, Linie
Agumon > Growlmon > MegaloGrowmon, Mindestlevel Agumon 20, Growlmon 18.
- Agumon Lv15 digitiert nicht (gesperrt, Meldung des Spiels).
- Agumon Lv20 digitiert in das **importierte** Growlmon. Growlmon Lv18 digitiert in das **importierte** MegaloGrowmon,
  also unter der Spielregel 21.
- Speichern, Port beenden, neu starten, laden: MegaloGrowmon Lv18 im Spielstand. Blinzeln der DW3-Augen im Spiel.
- Ohne die Datei gilt die Spielregel 11/21/31 unverändert (Port-Test `modconf_test`; kaputte oder neuere Dateien ändern nichts).

**Kampfkamera (`Mods\battle_camera.json`):** Guilmon (84, Partner, eigene Technik) und MegaloGrowmon (131, Gegner
der Boot Domain), Kamera beim Import automatisch.
- Der Port meldet die gelesenen Kameras. Kampf zu Ende gespielt, zurück in der Stadt.
- In jeder gemessenen Angriffs-, Ziel- und Nahaufnahme-Einstellung liegen beide Modelle ganz im Bild. Gemessen mit
  dem Modellrechteck des Spiels (`Gfx_ModelScreenBounds`, Bot-Befehl `fbox`). Die Vorschau im Studio rechnet mit
  derselben Projektion (Abweichung nur durch die Pose).

**Qualität importierter Digimon:** Mit HD-Stufe ×2 und mehr zeigt der Port die HD-Textur der importierten DW3-Modelle.
Vorher verwarf er sie beim ersten Blinzeln (behoben, Port-Test `hd_test`). Weiche Normalen sind im Kampfbild sichtbar.

**Grünes Gitter bei der Befehlswahl:** unverändert vorhanden (Kampfbilder Port und Emulator).

## Im Emulator getestet (PS1-Image, Modus B)
1. Abbild im Studio geöffnet (395 Digimon). Renamon (DW3) in Platz 131 (Gazimon) importiert. Der PS1-Modus hat das
   Modell kontrolliert verkleinert (848 → 552 Dreiecke, Animationen H/J/K mit jedem 2. Bild), damit jede Datei in ihre
   Originalgröße passt. Agumon in „Agumax“ umbenannt.
2. „Neues Image exportieren“: neues BIN, Original unverändert. Studio öffnet das neue Image wieder: Renamon und Agumax
   in der Liste.
3. Mednafen startet das neue Image (Intro, Titel). Spielstand mit drei Digimon (131, 3, 5) auf der Memory Card;
   der Spielstand stammt aus dem PC-Port und wird vom PS1-Spiel gelesen („Verifying saved file“).
4. Battle Mode, zwei Spieler: Die Auswahl zeigt die Artnamen **Renamon** und **Agumax** aus dem geänderten Image.
   Der Kampf startet und läuft (Befehlswahl, Technik, Treffer). In der Kampfübersicht steht das DW3-Renamon-Modell
   (gelber Fuchs, weiße Schwanzspitze) auf dem grünen Gitter.

## Automatisiert getestet (neu in rc2)
- Port: Lesen beider JSON-Dateien (gültig, kaputt, neueres Format, Grenzen), HD-Ersatz bei Teilschreiben, 16×-Ersatz
  (2048×4096) genau bei Software-Skalierung 16 (unter Linux und Windows).
- Studio: Kamera-Projektion und Auto-Kamera, Kamera-JSON, Größenkurve und Maßstabsmodi, PS1-Verkleinerung
  (weniger Dreiecke, Eingabe unverändert, kleine Teile bleiben erhalten), Bildschritt der Animation, CUE beim BIN-Export.

## Nur strukturell validiert
- Neue Oberflächenteile (Kamera-Editor, Größenkarte, Namen-Knopf, Modus-Gruppen A/B): unter Linux ohne Fenster
  gerendert und als Text ausgelesen. Nicht per Maus unter Windows bedient.
- 35 Domains / 437 Etagen ändern und zurücksetzen: byte-gleich (aus rc1, Code unverändert).

## Nicht getestet
- Echter Windows-PC, Grafikkarten-Renderer des Ports (auf dem Build-Server kein Vulkan-Gerät).
- Dein Original-BIN (zu groß für die Übertragung). Getestet ist ein aus `dw2.pak` neu gebautes Abbild.
- Echte PS1-Hardware; Speichern **durch das PS1-Spiel** in der Story (geladen wurde ein Port-Spielstand).
- DNA-Digitation mit importierten Digimon.
- Gegner auf weiteren Domains/Etagen im laufenden Spiel (nur Boot Domain 1F).
- Attackenkamera im PS1-Modus: dort gibt es keine Kamera-Datei, das Spiel nutzt seine festen Kameras.
- DW3 Europa (DW2003).

## Fehlgeschlagen
- Keine offene Prüfung ist fehlgeschlagen. Während der Arbeit gefundene und behobene Fehler stehen im Änderungsprotokoll.

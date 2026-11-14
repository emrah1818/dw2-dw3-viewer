# Testergebnisse DW2 Mod Studio 1.0.0-rc3

Stand 14.11.2026. Studio: Zweig `development/1.0`. Port: `emrah1818/dw2-pc-port`, Zweig `development/mod-studio-1.0`
(Commit in `integration/pc_port_base.txt`). Jede Angabe nennt, **wie** geprüft wurde:

- **Im Spiel getestet (PC-Port):** echter Port aus diesem Zweig, eigene `dw2.pak`, Linux ohne Fenster
  (Software-Renderer, Bot-Schnittstelle des Ports). Kein echter Windows-PC.
- **Im Emulator getestet (PS1):** Mednafen 1.29 mit OpenBIOS (freies BIOS, kein Sony-BIOS), gesteuert per Tastatur-Skript.
  Abbild: aus meiner `dw2.pak` neu zusammengesetztes DW2-Abbild (Dateien an ihren Original-LBAs, ISO9660), nicht dein
  Original-BIN (dieser Durchgang ohne Zugriff auf deinen PC).
- **Automatisiert getestet:** pytest und Port-Tests mit selbst erzeugten Daten (keine Spieldaten).
- **Nur strukturell validiert:** mit echten Daten gelesen/geschrieben und verglichen, nicht im Spiel angesehen.
- **Nicht getestet** und **Fehlgeschlagen** sind ausdrücklich aufgeführt.

## Zahlen
| Prüfung | Ergebnis |
|---|---|
| pytest (lokal, Linux) | **379 bestanden, 4 übersprungen**, 0 fehlgeschlagen |
| pytest in GitHub Actions | `test-summary.txt` / `test-results.xml` im Release |
| Port-Tests unter Windows (Actions): `--mod-api`, Cache-Test, Schriften, Text, `modconf_test`, `hd_test` | bestanden; GPU-Teil von `hd_test` übersprungen (kein Vulkan-Gerät auf dem Server) |
| Spielszenen PC-Port (`integration/ingame/run_ingame.py`, alle 5 Szenen) | **45 von 45**: evo 17, domain 4, partner 11, dna 7, domains 6 |
| PS1-Emulator: Export, Wiederöffnen, Kampf, Digitation, DNA, Speichern | bestanden (siehe unten) |

Zum Ablauf: Im Gesamtlauf schlugen 2 Prüfungen der Szene „partner“ fehl. Ursache war eine veraltete Erwartung
im Testskript: Es verlangte Kameraeinträge für beide Digimon, aber Guilmon passt mit der aktuellen Größe ohne
Anpassung ins Bild und bekommt deshalb keinen Eintrag. Das Skript prüft jetzt genau die Digimon mit angepasster
Kamera. Danach lief die Szene einzeln mit 11 von 11.

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

## Neu in rc3 im Spiel getestet (PC-Port)
**DNA-Digitation (Szene „dna“, 7/7):** DW3-Guilmon in Platz 84 und DW3-Growlmon in Platz 48 importiert. Greymon Lv25
und das importierte Growlmon Lv25 wurden im Digi-Labor über das Spielmenü per DNA verbunden. Ergebnis nach der
DNA-Tabelle des Spiels: Platz 84, also das **importierte Guilmon**. Die Eltern sind verschmolzen. Bilder zeigen die
Abfrage „DNA digivolve to Guilmon?“, beide Eltern-Modelle in der DNA-Szene und die Namenseingabe.

**Weitere Domains (Szene „domains“, 6/6):** Je Domain eine Gruppe kopiert, das importierte DW3-MegaloGrowmon
(Platz 12) als Gegner mit eigenem Level/HP eingesetzt und der Etage zugewiesen:
SCSI Domain 2F, Laser Domain 3F, Core Tower 4F. Im Spiel steht in jeder dieser Etagen das importierte MegaloGrowmon
mit genau diesen Werten im Kampfspeicher; die Kampfbilder zeigen das DW3-Modell. (Testaufbau: Sprung auf die Etage
und volle Beetle-HP per Entwickler-Bearbeitung.)

## PS1-Emulator: Digitation, DNA, echte Spielstände (neu in rc3)
Neues Image aus dem Studio: DW3-Growlmon in Platz 48 (PS1-Verkleinerung 1065 → 520 Dreiecke, Bewegungen B/C/J/K mit
jedem 2./3. Bild), Agumon digitiert zu Platz 48. Der BIN-Export schrieb die CUE selbst, das Studio öffnete das neue
Image wieder (Linie Agumon → Growlmon gespeichert).
1. **Spielstand vom PS1-Spiel:** Port-Spielstand geladen, auf der Stadtkarte über das Spielmenü gespeichert
   („The game has been saved.“). Die Memory Card ändert sich (Spielzeit). Der PC-Port lädt diesen Spielstand mit
   allen drei Digimon.
2. **Digitation im Digi-Labor:** Agumon Lv20 → „Digivolve to Growlmon“ → das DW3-Modell erscheint im Labor.
   Danach im Spiel gespeichert; der PC-Port lädt den PS1-Spielstand mit Growlmon (#48) Lv20 im Team.
3. **DNA:** Greymon + importiertes Growlmon → „DNA digivolve to ToyAgumon?“ (Platz 84, nach der Tabelle des Spiels),
   DNA-Szene mit dem DW3-Growlmon, Namenseingabe, neuer Eintrag im Spielspeicher.
Abkürzung im Test: Der Weg ins Digi-Labor und zur Stadtkarte wurde über einen geänderten Emulator-Zustand
genommen (nur der nächste Spielmodus, `integration/ps1emu/stpatch.py`), alles andere über die Menüs.

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
- Deine Original-BIN. Sie liegt auf deinem PC, dieser Durchgang lief auf deinen Wunsch ohne Zugriff auf den PC. Getestet ist ein aus `dw2.pak` neu gebautes Abbild.
- Echte PS1-Hardware.
- Gegner im PS1-Emulator außerhalb des Battle Mode (Domains wurden nur im PC-Port geprüft).
- Laufen durch die Stadt bis zum Labor im PS1-Emulator (abgekürzt, siehe oben).
- Attackenkamera im PS1-Modus: dort gibt es keine Kamera-Datei, das Spiel nutzt seine festen Kameras.
- DW3 Europa (DW2003).

## Fehlgeschlagen
- Keine offene Prüfung ist fehlgeschlagen. Während der Arbeit gefundene und behobene Fehler stehen im Änderungsprotokoll.

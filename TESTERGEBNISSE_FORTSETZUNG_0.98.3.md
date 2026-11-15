# Prüfungen nach 0.98.3 (Fortsetzung, 15.11.2026)

Basis: Studio `6e2aff4` (0.98.3) und Port `84d4379` (Pin). Nichts davon ist ein Release.

| Prüfung | Ergebnis |
|---|---|
| Python-Tests mit privaten Spieldaten (`DW2_TEST_PAK`, `DW3_TEST_DISC`) | 420 bestanden |
| JS-Tests | Animationen, Suche (22), Auswahl (17) bestanden |
| Feldmodell im echten Spiel | DW3-Greymon in #322 und #320 (SCSI Domain 1F), 0.98.3-Import, Mod-Export, Linux-Port. Das Modell erscheint auf der Karte mit Standby (E0) und richtiger Bodenlage; Begegnung startet den Kampf; drei Kämpfe gewonnen, Rückkehr in die Domain, 4 Etagen. Bild: `docs/fortsetzung_0983/feld_greymon_322.png` |
| Gehen im Feld (E1) | Bleibt „Noch ungeklärt“; im Spiel läuft das Standby weiter. Erwartet, nicht erfunden |
| Grafikfehler Kampfvideo | Nicht nachgestellt, siehe `UNTERSUCHUNG_KAMPFVIDEO_0.98.3.md` |
| Windows GTX 1070, 0.98.3-Port + 0.98.3-Export (7 Digimon) | Gelaufen am 15.11.2026, 18:29–18:38, NVIDIA-Treiber 32.0.15.6603, Vulkan, Scale 4, Smooth Frames an. 72 Mod-Dateien und 7 HD-Texturen geladen. Karte B (Greymon, Guilmon, Growlmon) und Karte C (MegaloGrowmon, WarGreymon, Imperialdramon FM) über 220 bzw. 207 s im Kampf, Exit 0, keine Fehler im Log. Im Bild: Standby, Angriffe (Growlmons Feuer, MegaloGrowmons E-Stun Blast), „Missed“. Kein Keil, keine verzerrten Teile. Lauf A wurde nach 100 s im Menü über das Fenster beendet, noch vor dem Kampf; nicht ausgewertet. Bilder: `docs/fortsetzung_0983/windows_gtx1070_0983.jpg` |
| PS1-Emulator | **noch nicht geprüft** |
| Mehrteilige Angriffe, Fallen, K.o. und Sieg im Bild | **noch nicht im Bild geprüft** (das Testskript trifft im VS-Modus selten) |

## Test mit dem Spielstand, den Einstellungen und dem Mod des Nutzers (15.11.2026, 19 Uhr)
- Spielstand `card1.mcd` aus `%APPDATA%\DW2-Online\saves`. Er steht auf der Weltkarte (Directory Continent).
- Gruppe: KADIR Lv 37 (#59), AYKAN Lv 39 (#213), RASHO Lv 40 (#148). Das ist dieselbe Gruppe wie im Video, aber
  KADIR ist dort Guilmon und jetzt ein Vogel-Digimon.
- Einstellungen aus `settings.ini`: Deutsch, 16:9, PGXP, Smooth Frames, Sharpen 25, FXAA.
- Mod: der wiederhergestellte `Documents\DW2-PC\Mods` mit #4 und #133. Diese beiden Digimon sind nicht in der
  Gruppe, sie tauchen nur als Gegner auf.
- Ablauf: Spielstand geladen, nach SCSI Domain gewechselt, zwei Kämpfe mit der eigenen Gruppe. Hauptmenü
  „KAMPF“, Ziel, Attacke, Mega Fire, Schaden, Sieg, Rückkehr in die Domain. Beide Kämpfe gewonnen, kein Absturz
  (Software-Renderer, Scale 2). Bilder: `docs/fortsetzung_0983/nutzer_spielstand_kampf.jpg`.
- Mit dem GPU-Renderer stürzte der Linux-Testrechner zweimal beim ersten Angriff ab. Der Absturz liegt im
  Software-Vulkan-Treiber des Testrechners (lavapipe, `memset` in einem lavapipe-Thread), nicht im Port-Code. Unter
  Windows mit der GTX 1070 spielt der Nutzer mit GPU; dort ist kein Absturz bekannt. Ob der Port lavapipe ein
  ungültiges Zeichenkommando schickt, ist nicht geprüft.
- Kein Keil in diesem Lauf. Der Guilmon aus dem Video ist mit diesem Spielstand und Mod nicht mehr in der Gruppe;
  der Fehler im Video stammt also aus einem früheren Mod-Stand.

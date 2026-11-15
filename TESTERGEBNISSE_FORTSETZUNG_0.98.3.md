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

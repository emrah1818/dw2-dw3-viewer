# DW2 Mod Studio 0.17b – Bedienungsanleitung

## Einrichten
1. `DW2_Mod_Studio_0.17b_Windows_x64.zip` vollständig entpacken, `DW2_3D_Viewer_Studio.exe` starten.
2. `DW2_PC_Port_API2_0.17b_Windows_x64.zip` in einen eigenen Ordner entpacken und deine eigenen `dw2.pak` und `dw2.pak.slus` dazulegen. Diesen Ordner wählst du später beim Export.
3. Im Studio oben **„Open BIN / ISO“** bzw. im Bereich **Dateien** „dw2.pak / Image öffnen“ und deine `dw2.pak` wählen. Die Datei wird nur gelesen.

Alle Änderungen werden zuerst nur **vorgemerkt** (Zähler am Reiter Mod-Export). Rückgängig/Wiederherstellen gilt für jeden Bereich.

## Die Bereiche
**Dateien** – alle Spieldateien mit LBA und Größe, Suche, „nur geänderte“. Original oder geänderte Fassung einer Datei exportieren. Mod-Projekt laden/speichern.

**3D-Viewer** – Modell und Animationen des gewählten Digimon, Ansicht, Diagnose, 3D-Export/-Import wie bisher.

**Digimon** – Liste; „Gewähltes Digimon bearbeiten“ öffnet den Editor: Name, Typ, Spezialität, Digitation & DP, **Kampfkamera & Treffereffekt**, Attacken, Gegnerwerte & EXP, Spielstand.
*Kampfkamera:* Die Nahaufnahme im Kampf wählt Abstand und Blickhöhe in 9 Stufen. „Stufe ±1“ verschiebt um eine Stufe, „Original“ setzt zurück.

**Attacken** – Katalog aller Techniken mit Nutzern. „Eigene Technik … anlegen“ oder bei einer Technik „als Vorlage“: Name (max. 17 Zeichen, US-Zeichensatz), optional Beschreibung, MP, Stärke, Element-Code, Startanimation F/G/H; Zuweisung als erlernbare Technik und/oder an die Gegnerplätze dieses Digimon. „bearbeiten“ erscheint nur bei Techniken, die ausschließlich das gewählte Digimon nutzt.

**Digitation** – zeigt die Linie ab dem gewählten Digimon (bis 4 Stufen). Je Digimon Stufe und bis zu vier Ziele mit DP-Untergrenzen (erste 0, streng steigend). „Digimon zur Linie hinzufügen“ nimmt weitere Arten auf. „Linie übernehmen“ prüft alles zusammen.

**Domains** – Domain wählen; je Etage fünf Gruppenplätze (Platz 0 liest das Spiel beim Erzeugen nicht). Darunter die gewählte Gegnergruppe: Kartenfigur, KI, Tempo, Lieblingsgeschenk, Punkte pro Level, Domain-Musik, Boss und drei Gegner mit Digimon, Level, HP, MP, Angriff, Abwehr, Tempo und drei Technik-IDs. „Als neue Gruppe kopieren“ legt eine Kopie unter freier ID an, die du dann einer Etage zuweisen kannst.

**DW3-Import** – „DW3-Abbild öffnen“. *Einzeln:* Ziel im Reiter Digimon wählen, beim DW3-Modell „Einzeln importieren“, Bewegungszuordnung prüfen (Vorbelegung aus den DW3-Kampfskripten, Quelle steht daneben), Größe und HD-Stufe (bis 2048×4096) wählen. *Stapel:* „zum Stapel“, Ziel-Slot und optional neuen Namen wählen, dann „Alle importieren“ – ein Rückgängig-Schritt.

**Texturen** – öffnet die Texturkarte des 3D-Viewers: PNG export/import wie bisher, HD-PNG als Texturpaket exportieren, **HD-PNG in der Vorschau zeigen** (128×256 × 1–16, bis 2048×4096), **Vorgemerkte HD-Textur zeigen**, HD-Vorschau aus.

**Mod-Export** – Liste der vorgemerkten Änderungen.
- **Mod prüfen:** zeigt Dateien, Größe, Fehler, Konflikte und ob die Mod-Schnittstelle 2 nötig ist. Schreibt nichts.
- **PC-Port-Mod exportieren:** schreibt `Mods\files\<ID>.bin`, HD-Texturen und `dw2studio_mod.json`. Bei einem schon vorhandenen Mod bricht er mit einer Meldung ab.
- **Vorhandenen Mod ersetzen:** verschiebt den aktiven Mod nach `Mods\disabled\<Zeit>` und exportiert dann.
- **Mod einlesen:** übernimmt einen exportierten Mod wieder als vorgemerkte Änderungen (prüft, ob er zu deiner `dw2.pak` passt).
- **PC-Port-Mods deaktivieren/aktivieren:** Originalzustand herstellen bzw. zurückholen; nichts wird gelöscht.

Danach den Port starten (`dw2.exe` im Port-Ordner). Für HD-Texturen im Port die Auflösung ab 2× wählen.

## Beispiel: Renamon aus DW3 ersetzt Gazimon und bekommt eine eigene Technik
1. Digimon: Gazimon (#131) wählen. DW3-Import: Abbild öffnen, M373RENA → „zum Stapel“ → Ziel #131, Name „Renamon“ → „Alle importieren“.
2. Attacken: bei Technik 105 „als Vorlage“, Name „Fox Fire“, Häkchen bei Gegnergruppe 154 Platz 1 → Vormerken.
3. Domains: Gruppe 154, Gegner 1 Level 7, HP 80 → Gruppe übernehmen.
4. Mod-Export: Mod prüfen → PC-Port-Mod exportieren → Port starten → Boot Domain.

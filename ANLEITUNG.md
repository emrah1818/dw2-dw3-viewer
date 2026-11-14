# DW2 Mod Studio 1.0.0-rc1 – Installation und Bedienung

## Installation
Voraussetzungen: Windows 10/11 x64, deine eigene `dw2.pak` (+ `dw2.pak.slus`) aus deinem PC-Port, für den DW3-Import dein eigenes DW3-Abbild (USA, `.bin`).
1. `DW2_Mod_Studio_1.0.0-rc1_Windows_x64.zip` vollständig entpacken (nicht aus dem ZIP heraus starten), `DW2_3D_Viewer_Studio.exe` starten. Prüfsummen: `SHA256SUMS.txt` (PowerShell: `Get-FileHash <Datei>`).
2. `DW2_PC_Port_API2_1.0.0-rc1_Windows_x64.zip` in einen eigenen Ordner entpacken und deine eigenen `dw2.pak` und `dw2.pak.slus` dazulegen. Diesen Ordner wählst du später beim Export.
3. Im Studio oben **„Open BIN / ISO“** bzw. im Bereich **Dateien** „dw2.pak / Image öffnen“ und deine `dw2.pak` wählen. Die Datei wird nur gelesen.

Alle Änderungen werden zuerst nur **vorgemerkt** (Zähler am Reiter Mod-Export). Rückgängig/Wiederherstellen gilt für jeden Bereich.

## Die Bereiche
**Dateien** – alle Spieldateien mit LBA und Größe, Suche, „nur geänderte“. Original oder geänderte Fassung einer Datei exportieren. Mod-Projekt laden/speichern.

**3D-Viewer** – Modell und Animationen des gewählten Digimon, Ansicht, Diagnose, 3D-Export/-Import wie bisher.

**Digimon** – Liste; „Gewähltes Digimon bearbeiten“ öffnet den Editor: Name, Typ, Spezialität, Digitation & DP, **Kampfkamera & Treffereffekt**, Attacken, Gegnerwerte & EXP, Spielstand.
*Kampfkamera:* Die Nahaufnahme im Kampf (Befehlseingabe, Zielwahl) wählt Abstand und Blickhöhe in 9 Stufen. „Stufe ±1“ verschiebt um eine Stufe, „Original“ setzt zurück. **„Vorschau: Nahaufnahme wie im Kampf“** zeigt das Bild in der 3D-Ansicht (4:3), die Leiste unten ändert die Stufe live. Attackenszenen nutzen feste Kameras des Spiels.

**Attacken** – Katalog aller Techniken mit Nutzern. Darunter die Zahl der freien Technik-IDs (höchstens 255, im US-Spiel 45 frei). „Eigene Technik … anlegen“ oder bei einer Technik „als Vorlage“: Name (max. 17 Zeichen, US-Zeichensatz), optional Beschreibung, MP, Stärke, Element-Code, Startanimation F/G/H; Zuweisung als erlernbare Technik und/oder an die Gegnerplätze dieses Digimon. „bearbeiten“ erscheint nur bei Techniken, die ausschließlich das gewählte Digimon nutzt.
*Effekt/Ton/Animation übernehmen:* eigene Technik wählen, Quelltechnik wählen, Teile ankreuzen (Effekte, Ton/Ruf, Zustandseffekte, Startanimation).
*Technik mehreren Digimon geben:* Technik wählen, Digimon ankreuzen. Sie wird bei allen zur erlernbaren Technik.

**Digitation** – zeigt die Linie ab dem gewählten Digimon (bis 4 Stufen). Je Digimon Stufe und bis zu vier Ziele mit DP-Untergrenzen (erste 0, streng steigend). „Digimon zur Linie hinzufügen“ nimmt weitere Arten auf. „Linie übernehmen“ prüft alles zusammen. „Alle Digitationen prüfen“ listet Fehler (Kreise, fehlende Ziele), Hinweise und nicht erreichbare Arten.
*Digitationslevel je Digimon (Vorbereitung):* Mindestlevel speichern. Wird im Projekt gespeichert und als `Mods\digivolve_levels.json` exportiert. **Der aktuelle PC-Port liest das nicht**, im Spiel gilt weiter 11/21/31.

**Domains** – Domain wählen; je Etage fünf Gruppenplätze (Platz 0 liest das Spiel beim Erzeugen nicht). Darunter die gewählte Gegnergruppe: Kartenfigur, KI, Tempo, Lieblingsgeschenk, Punkte pro Level, Domain-Musik, Boss und drei Gegner mit Digimon, Level, HP, MP, Angriff, Abwehr, Tempo und drei Technik-IDs. „Als neue Gruppe kopieren“ legt eine Kopie unter freier ID an, die du dann einer Etage zuweisen kannst.

**DW3-Import** – „DW3-Abbild öffnen“. *Einzeln:* Ziel im Reiter Digimon wählen, beim DW3-Modell „Einzeln importieren“, Bewegungszuordnung prüfen (Vorbelegung aus den DW3-Kampfskripten, Quelle steht daneben), Größe und HD-Stufe (bis 2048×4096) wählen. Der Dialog zeigt die DW2-Formatgrenzen (Teile, Ebenen, was automatisch geteilt wird) und ob die Augen aus DW3 übernommen werden. *Stapel:* „zum Stapel“, Ziel-Slot und optional neuen Namen wählen, dann „Alle importieren“ – ein Rückgängig-Schritt.

**Texturen** – öffnet die Texturkarte des 3D-Viewers: PNG export/import wie bisher, HD-PNG als Texturpaket exportieren, **HD-PNG in der Vorschau zeigen** (128×256 × 1–16, bis 2048×4096), **Vorgemerkte HD-Textur zeigen**, HD-Vorschau aus.

**Mod-Export** – Liste der vorgemerkten Änderungen.
- **Mod prüfen:** zeigt Dateien, Größe, Fehler, Konflikte und ob die Mod-Schnittstelle 2 nötig ist. Schreibt nichts.
- **PC-Port-Mod exportieren:** schreibt `Mods\files\<ID>.bin`, HD-Texturen und `dw2studio_mod.json`. Bei einem schon vorhandenen Mod bricht er mit einer Meldung ab.
- **Vorhandenen Mod ersetzen:** verschiebt den aktiven Mod nach `Mods\disabled\<Zeit>` und exportiert dann.
- **Mod einlesen:** übernimmt einen exportierten Mod wieder als vorgemerkte Änderungen (prüft, ob er zu deiner `dw2.pak` passt). Überschneidet er sich mit deinen Änderungen (z. B. dieselbe Technik-ID), fragt das Studio vorher.
- **PC-Port-Mods deaktivieren/aktivieren:** Originalzustand herstellen bzw. zurückholen; nichts wird gelöscht.

Danach den Port starten (`dw2.exe` im Port-Ordner). Für HD-Texturen im Port die Auflösung ab 2× wählen.

## Beispiel: Renamon aus DW3 ersetzt Gazimon und bekommt eine eigene Technik
1. Digimon: Gazimon (#131) wählen. DW3-Import: Abbild öffnen, M373RENA → „zum Stapel“ → Ziel #131, Name „Renamon“ → „Alle importieren“.
2. Attacken: bei Technik 105 „als Vorlage“, Name „Fox Fire“, Häkchen bei Gegnergruppe 154 Platz 1 → Vormerken.
3. Domains: Gruppe 154, Gegner 1 Level 7, HP 80 → Gruppe übernehmen.
4. Mod-Export: Mod prüfen → PC-Port-Mod exportieren → Port starten → Boot Domain.

## Spieltests selbst ausführen (Linux, für Entwickler)
`integration/README.md`: Port aus `integration/pc_port_base.txt` bauen, dann
`python3 integration/ingame/run_ingame.py --port … --pak … --dw3 … --autoplay … --work …`.

# Testergebnisse DW2 Mod Studio 1.0.0-rc1

Stand 14.11.2026, Zweig `development/1.0`. Jede Angabe nennt, **wie** geprüft wurde:

- **Erfolgreich getestet (im Spiel):** echter PC-Port (Commit c9989534, Mod-Schnittstelle 2), eigene `dw2.pak`,
  Linux ohne Fenster (Software-Renderer, Bot-Schnittstelle des Ports). Kein echter Windows-PC.
- **Automatisiert getestet:** pytest mit selbst erzeugten Daten in den Formaten des Spiels (keine Spieldaten).
- **Nur strukturell validiert:** mit echten Daten gelesen/geschrieben und verglichen, aber nicht im Spiel angesehen.
- **Nicht getestet** und **Fehlgeschlagen** sind ausdrücklich aufgeführt.

## Zahlen
| Prüfung | Ergebnis |
|---|---|
| pytest (lokal, Linux, Python 3.13) | **373 bestanden, 4 übersprungen**, 0 fehlgeschlagen |
| pytest in GitHub Actions | siehe `test-summary.txt` / `test-results.xml` im Release |
| Spieltests `integration/ingame/run_ingame.py` (3 Szenen, lokal) | **28 von 28 bestanden** |
| Windows-Build und Startprüfung (Actions, Windows Server) | siehe `windows-smoke.json` im Release |
| Alle 249 DW3-USA-Modelle durch den 1.0-Kodierer | 248 kodiert, 1 ist kein Modell (Konverter: „no bone list“). 227 byte-gleich zu 0.17b, 21 anders geteilt (Teile nach Vertices statt nach Dreiecken) |
| 773 Originalmodelle von DW2 gegen die neue Formatprüfung | 0 Beanstandungen (größtes Modell: 49 Teile) |
| 35 Domains, 437 Etagen: jede Etage ändern und zurücksetzen | danach 0 vorgemerkte Änderungen (byte-gleich) |

## Spieltests im Einzelnen (Erfolgreich getestet)
**Szene „evo“** (16 Prüfungen): DW3-Guilmon, -Growlmon und -MegaloGrowmon in die Plätze 84/48/12 importiert,
Linie Agumon > Growlmon > MegaloGrowmon gesetzt, Mod geprüft und exportiert (33 Dateien). Neues Spiel bis zur
Stadt, Agumon Lv15 angelegt (Entwickler-Bearbeitung `--cheats`, nur für Level/DP).
- Digi-Labor: Agumon digitiert zu **Growlmon (importiert)**. Mit Lv25 digitiert Growlmon zu **MegaloGrowmon (importiert)**.
  Labor-Bilder zeigen beide Modelle und den Bestätigungstext.
- Speichern, Port beenden, neu starten, laden: MegaloGrowmon Lv25 steht im Spielstand.
- Blinzeln: Im Labor ändern sich über 90 Bilder nur 8 Texel der Texturseite (VRAM 897–898 / 10–14), genau das
  Augenrechteck. Das ist die DW2-Augenanimation mit den aus DW3 übernommenen Rahmen.
- Kompatibilität: `digivolve_levels.json` (Agumon 20) liegt im Mod. Der Port startet und digitiert Agumon trotzdem ab Lv11.
  Das bestätigt: Die Datei wirkt mit diesem Port nicht und stört nicht.

**Szene „domain“** (4): Gruppe 154 kopiert (neue ID), Gegner geändert (Greymon Lv6/70 HP/Technik 4,
Agumon Lv4/50 HP/Technik 1), der Boot Domain 1F zugewiesen. Im ersten Kampf stehen genau diese Gegner im Kampfspeicher.

**Szene „partner“** (8): Guilmon in Platz 84, Kamera automatisch (Stufe 1), eigene Technik 116 „Pyro Sphere“
(Vorlage Pepper Breath, MP 7, Stärke 90). Guilmon als Partner im Team. Im Kampf: Guilmon auf Platz 1 mit Technik 116.
Bilder: Kampfbeginn, Nahaufnahme mit vollständig sichtbarem Guilmon, Feuerball-Effekt, Schadenszahl.
Kampf zu Ende gespielt, zurück in der Stadt, Spiel läuft.

**Aus 0.17b/1.0 einzeln geprüft (nicht im Skript):** Kamerawert `field_1E` von Platz 61 auf 0x300 / Original / 0xBFF:
Die Nahaufnahme bei der Befehlseingabe ändert sich sichtbar (Bildvergleich). Die Attackenkameras ändern sich nicht (im Code fest).

## Automatisiert getestet (neu in 1.0)
- Techniken: Teile übernehmen (nur gewählte Bytes, ID und Name bleiben), Ablehnung bei geteilten Techniken, eine
  Technik für mehrere Digimon in einem Schritt, ID-Budget.
- Mod-Einlesen: Überschneidung mit eigenen Änderungen wird erkannt, doppelte Technik-IDs werden genannt, ohne
  Zustimmung wird nichts ersetzt.
- Digitationsprüfung: Kreise, Ziele ohne Eintrag, nicht höherstufige Ziele, Fehler schon im Original als Hinweis.
- Formatgrenzen: Teilung großer Knochen (≤256 Vertices/Dreiecke je Teil), Hierarchie mit 12 Ebenen exakt auf 8 abgebildet
  (Weltmatrizen gleich), Schutzgrenzen (64 Teile, 254 Posen, 16 Bit) bleiben, Endprüfung vor dem Export.
- Gesichter: Zuordnung DW3-Rechteck → Texturseite, Rahmen 4-Pixel-ausgerichtet im Atlas, offen ≠ zu, Seite zeigt „offen“.
- Digitationslevel: Format 1 (Lesen, Schreiben, höhere Formate abgelehnt), Port-Fähigkeit aus `dw2_mod_api.json`,
  Export mit Warnung, Rückgängig/Wiederherstellen, Projekt speichern/laden.
- Kamera-Vorschau: Werte genau aus den Tabellen des Spiels.

## Nur strukturell validiert
- Domain-Editor auf allen 35 Domains (siehe oben). Im Spiel geprüft ist nur Boot Domain 1F.
- Kamera-Vorschau im Studio: unter Linux ohne Fenster gerendert und mit Spielbildern verglichen. Größe und Stufenfolge
  stimmen. Die Bildlage weicht je Pose leicht ab, die Seitenplätze sehen schräg.
- Neue Oberflächenteile (Teile übernehmen, mehrere Digimon, Digitationsprüfung, Level-Karte, Kamera-Leiste):
  JavaScript-Syntaxprüfung und Programmschnittstelle. Nicht per Maus unter Windows bedient.

## Nicht getestet
- Echter Windows-PC, Grafikkarten-Renderer des Ports, HD-Texturen im Port bei 2048×4096.
- Gegner auf anderen Etagen und in anderen Domains im laufenden Spiel; Gruppen tauschen im Spiel.
- DNA-Digitation mit importierten Digimon.
- DW3 Europa (DW2003).
- Team-Menü als Bild: Die Liste blieb in der Aufnahme leer (Ursache nicht geklärt). Die Team-Zugehörigkeit ist über die
  Spielstanddaten und den Kampf belegt.

## Fehlgeschlagen
- Keine offene Prüfung ist fehlgeschlagen. Während der Arbeit gefundene und behobene Fehler stehen im Änderungsprotokoll.

# DW2 / DW3 Viewer 0.16b – Testversion

Baut auf 0.15b auf. Alle bisherigen Funktionen bleiben erhalten.

## Neu

- **Bewegungen sinnvoll vorbelegt.** Beim Ersetzen eines DW2-Digimon durch ein DW3-Digimon bekommt jeder DW2-Bewegungsplatz jetzt eine passende DW3-Motion statt überall Motion 1. Die Zuordnung stammt aus den Kampfskripten des DW3-Digimon und aus dem Kampfcode von DW2. Neben jedem Platz steht die Quelle, jede Wahl lässt sich ändern:

  | DW2-Platz | im DW2-Kampf | DW3-Motion |
  |---|---|---|
  | A0 | Kampf-Standby | Skript 0 (Standby) |
  | C0, C1, C2 | Treffer: zwei Sprünge, Landen | Skript 2 (Treffer), Folge ohne die letzte |
  | J0 | Aufstehen | Skript 2, letzte Motion |
  | K0 | Niederschlag, 90 Bilder liegen | Skript 3 (K.o.), letzte Motion |
  | F0, G0, H0 | Angriff je nach Technik | Skripte 5–7, Motion beim ersten Treffer |
  | B0, I0, übrige | im Code nicht einer Kampfaktion zugeordnet | Standby |

- **Größe nach Standhöhe.** Das neue Digimon bekommt die Standhöhe des ersetzten. Bisher wurde die größte Ausdehnung verglichen, dadurch wurde z. B. Renamon im Gazimon-Slot fast doppelt so groß (Gazimons größte Ausdehnung sind die Ohren nach hinten). Der Größenfaktor im Dialog bleibt zum Nachjustieren.
- **HD-Textur 2048×4096** als vierte Stufe beim DW3-Import (neben 256×512, 512×1024, 1024×2048).
- **PC-Port-Mods deaktivieren und aktivieren** auf der Seite „Änderungen“. Die Dateien werden nach `Mods\disabled\<Zeitpunkt>` verschoben, nicht gelöscht. Das Spiel lädt dann wieder die Originale. Ein zweiter Export ist so ohne Handarbeit möglich.
- **Begleit-PC-Port auf Basis 1.6.2-preview.** Die Mod-Schnittstelle 2 liegt jetzt im Port-Repository selbst (Branch `development/dw3-mod-studio`, `doc/MOD_API2.md`) statt als Patch im Viewer. Damit enthält der Begleit-Port auch die Neuerungen von 1.6.2-preview (Grafikprofile, FXAA, Farbregler, FPS-Anzeige).
- Veröffentlicht wird nur noch auf ausdrücklichen Start des Workflows, nicht mehr bei jedem Push.

## So ersetzt du ein Digimon

1. Beide ZIPs vollständig in getrennte Ordner entpacken. In den Port-Ordner deine eigenen `dw2.pak` und `dw2.pak.slus` legen.
2. Viewer starten, `dw2.pak` öffnen, das zu ersetzende Digimon wählen.
3. „DW3-Modelle öffnen“, dein DW3-Abbild (USA) wählen, das DW3-Digimon auswählen.
4. „DW2-Slot mit DW3-Skelett und Bewegungen ersetzen“: Vorbelegung prüfen, „Prüfen und vormerken“.
5. Optional Name, Werte, Typ, Attacken, Digitation/DP ändern.
6. „Änderungen“ → „PC-Port-Mod exportieren“, den Port-Ordner wählen.
7. Port starten. Für HD-Texturen im Port ab Auflösung 2× spielen.

## Grenzen

- Die Kamera einer Technik bleibt die des ersetzten Digimon. DW3-Angriffe mit Sprüngen können in der Nahaufnahme teilweise aus dem Bild laufen.
- DW3-Effekte, Gesichtsausdrücke und Aktionsskripte werden nicht übernommen. Die Techniken bleiben die DW2-Techniken des Slots.
- Native DW2-Grenzen: 256 Eckpunkte je Knochen, acht Hierarchieebenen, 254 Posen je Knochen und Animationsdatei. Unpassende Modelle werden mit Begründung abgewiesen.
- HD-Texturen beim DW3-Import werden aus den PS1-Texturen hochskaliert. Echte HD-Details gibt es nur mit eigenen PNGs („HD-PNG als PC-Port-Texturpack exportieren“).
- Mit der bisherigen `dw2.exe` laufen größere Ersatzdateien nicht. Den Begleit-Port verwenden.

Prüfstand und Belege: VALIDATION_0.16b.md. Keine Originalspieldaten in den Paketen.

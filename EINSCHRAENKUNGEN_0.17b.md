# Bekannte Einschränkungen 0.17b

## Nicht umgesetzt
- **DW3-Gesichtsausdrücke:** Die DW3-Gesichtsrechtecke (16 Teile, Augen mit offen/halb/zu, `step_face`) beziehen sich auf die ursprüngliche DW3-Texturlage. Der Import packt die Texturseiten verkleinert in einen gemeinsamen Atlas; die Rechtecke müssten danach umgerechnet und in das DW2-Blinzelformat (ein Zielrechteck, Quellbilder) übertragen werden. Das ist nicht gebaut. Importierte Modelle haben keine Augenanimation.
- **DW3-Effekte und Aktionsskripte:** DW3 nutzt ein eigenes Effektsystem. Übernommen werden können die Effekte vorhandener **DW2**-Techniken (über eigene Techniken), nicht die von DW3.
- **Digitationslevel je Art:** Das Level steht nicht in den Daten, sondern als feste Regel im Code des Digi-Labors. Dafür bräuchte der PC-Port eine Erweiterung, siehe `DIGITATIONSLEVEL_SCHNITTSTELLE.md`. Der Port wurde nicht verändert.
- **Neue Digimon-IDs:** bewusst nicht. Ersetzt werden vorhandene Slots.

## Grenzen der Daten
- Technik-IDs sind einbytekodiert: höchstens 255; im US-Spiel sind 45 IDs frei. Technik-Namen höchstens 17 Zeichen im US-Zeichensatz.
- Gegnergruppen-IDs 1–255 (im US-Spiel 63 frei). Eine Etage hat fünf Gruppenplätze; Platz 0 wird beim Erzeugen nicht gelesen.
- Kampfkamera: 9 Stufen; Werte über 0xBFF würden hinter die Kameratabelle des Spiels greifen und werden abgelehnt.
- Native DW2-Modellgrenzen beim DW3-Import: 256 Eckpunkte je Knochen, acht Hierarchieebenen, 254 Posen je Knochen und Animationsdatei.
- Ersatzdateien größer als das Original brauchen den mitgelieferten Port mit Mod-Schnittstelle 2 (bis 2 MiB je Datei).

## Nicht geprüft oder nur teilweise geprüft
- **Windows-Hardware:** Programm und Port liefen nur in GitHub Actions (Windows-Server, Software-OpenGL; Startprüfung des Programms) und lokal unter Linux. Nicht auf einem echten Windows-PC, nicht auf einer GTX 1070.
- **Bedienung per Maus unter Windows:** Alle Bereiche wurden unter Linux ohne sichtbares Fenster mit echter `dw2.pak` geöffnet und ausgelesen; Eingaben in Dialoge sind nur über die Programmschnittstelle getestet.
- **Automatische Kamera im Spiel:** Der Wert wird gesetzt und vom Spielcode für die Nahaufnahmen (`src/stag3000/camera.c`) gelesen. In der geprüften Kampfszene war kein Unterschied zu sehen: Dort zeigt die Kamera auch im Original Gazimon nur mit den Ohren am unteren Bildrand. Ob der Wert andere Szenen sichtbar verbessert, ist offen.
- **Längeres Spiel:** ersetztes Digimon als eigener Partner, Digitation in ein ersetztes Digimon, Spielstände mit ersetzten Digimon, neue Gegnergruppen auf anderen Etagen im laufenden Spiel.
- **HD-Texturen im GPU-Renderer des Ports** und 2048×4096 im Port.
- **DW3 Europa (DW2003):** Tabellenadressen eingetragen, aber nur die USA-Version geprüft.

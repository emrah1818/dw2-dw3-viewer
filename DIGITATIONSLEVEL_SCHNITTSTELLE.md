# Digitationslevel je Digimon: benötigte Port-Schnittstelle

Stand 0.17b. Der PC-Port wird dafür **nicht** verändert; diese Datei beschreibt, was er bräuchte.

## Wie das Spiel heute entscheidet (dw2-pc-port, nur gelesen)

- `src/stag2000/labinfo.c`: `Stg20_DigivolveRuleTbl[4][4] = {{0,0,0,2},{1,0,0,2},{1,1,0,2},{1,1,1,2}}`.
  Zeile = Levelband `(level - 1) / 10`, höchstens 3; Spalte = Stufe aus DIGIMNDT (`Digi_GetRank`).
  1 = darf digitieren, 0 = noch nicht, 2 = nie (Mega).
- Ergebnis: Rookie ab Level 11, Champion ab 21, Ultimate ab 31. Das gilt für **alle** Arten gleich.
- Das Ziel bestimmt danach `Digi_GetEvolutionTarget` (`src/main/gamedata.c`) aus den DP-Grenzen
  und Zielen in DIGIMNDT. Diese Felder bearbeitet der Studio-Editor schon.
- Die Tabelle liegt im Code des Labors (Overlay STAG2000), nicht in einer Datendatei. Sie zu
  ändern wäre ein Eingriff in den Programmcode, den das Studio bewusst nicht vornimmt.

## Vorgeschlagene Schnittstelle

1. Der Port liest beim Start optional `Mods/digivolve_levels.json`:
   `{"format": 1, "levels": {"131": 15, "84": 8}}`: Digimon-ID → Mindestlevel (1–99).
2. In `labinfo.c` (Anzeige) und an der Stelle, die die Digitation im Labor tatsächlich ausführt
   (`Stg20_LabDigivolve`, `src/stag2000/digilab.c`), gilt für eine ID aus der Datei
   `level >= Mindestlevel` statt der Tabellenzeile. Ohne Eintrag bleibt alles wie bisher.
   Mega bleibt gesperrt (Tabellenwert 2).
3. `--mod-api` meldet zusätzlich `"digivolve_levels": 1`. Erst dann bietet das Studio das Feld an
   und schreibt die Datei in den Mod-Export.
4. Spielstände bleiben unverändert, die Datei ist rein optional.

Bis der Port das liest, zeigt der Digitations-Editor die feste Regel nur an.

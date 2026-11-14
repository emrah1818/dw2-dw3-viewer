# Bekannte Einschränkungen 1.0.0-rc1

Diese Version ist ein **Release-Kandidat**, kein 1.0.0 FINAL. Die folgenden Punkte des 1.0-Auftrags sind ohne
Änderung am PC-Port nicht erfüllbar (der Port bleibt laut Auftrag unverändert):

## Offen, braucht eine Port-Erweiterung
1. **Attackenkamera je Digimon.** Die Kameras während einer Attacke (Einstellungen 10–21 in `src/stag3000/skilleffect.c`)
   sind im Spielcode fest und lesen keine Daten des Digimon. Der Studio-Wert `field_1E` wirkt nur auf die Nahaufnahmen
   bei Befehlseingabe und Zielwahl (im Spiel nachgewiesen). Große Digimon können in Attackenszenen angeschnitten sein,
   wie im Original (z. B. Gazimon). Abhilfe bräuchte im Port eine Größenanpassung der Einstellungen 10–21.
2. **Digitationslevel je Art.** Feste Regel im Code (`Stg20_DigivolveRuleTbl`). Das Studio speichert und exportiert die
   Werte bereits (Format 1, `Mods\digivolve_levels.json`, `DIGITATIONSLEVEL_SCHNITTSTELLE.md`). Im aktuellen Port haben sie
   **keine Wirkung** (im Spiel geprüft).
3. **DW3-Effekte, Kamerafahrten, Sprünge, Töne und Sichtbarkeit je Aktion.** Andere Formate und ein anderer Abspielcode,
   siehe `DW3_EFFEKTE_ANALYSE.md`. Ersatz: Effekt/Ton/Zustand/Animation aus DW2-Techniken übernehmen.

## Grenzen der Daten (gelten weiter)
- Technik-IDs sind ein Byte (DIGIMNDT, ENEMYSET, Spielstand): höchstens 255. Im US-Spiel sind **45** frei. Eine sichere
  Erweiterung gibt es ohne Port-Änderung nicht. Ungenutzte IDs werden nur angezeigt, nie automatisch wiederverwendet
  (Spielstände können sie gelernt haben).
- Gegnergruppen-IDs 1–255 (63 frei). Fünf Gruppenplätze je Etage, Platz 0 liest das Spiel beim Erzeugen nicht.
- Kampfkamera: 9 Stufen, höchstens 0xBFF.
- Modellformat: 256 Vertices/Normalen/Dreiecke je Teil, 8 Ebenen, 64 Teile, 254 Posen je Knochen und Animationsdatei.
  Seit 1.0 werden große Knochen automatisch geteilt und tiefere Ebenen exakt eingehängt. Nur mehr als 64 Teile nach dem
  Teilen und mehr als 254 Posen werden abgelehnt.
- Ziele mit **geteilten** Animationsdateien werden beim DW3-Import abgelehnt, damit fremde Digimon nicht mitverändert werden.
- Blinzeln: Bei HD-Texturen zeichnet der Port die Augenstelle beim Blinzeln aus der Originaltextur (niedrige Auflösung).
- Ersatzdateien größer als das Original brauchen den mitgelieferten Port mit Mod-Schnittstelle 2 (bis 2 MiB je Datei).

## Nicht oder nur teilweise geprüft
Siehe `TESTERGEBNISSE_1.0.0-rc1.md`, Abschnitte „Nur strukturell validiert“ und „Nicht getestet“.

# Typ ändern im separaten 3D Viewer 3.9

Stand: 01.11.2026. Implementierung: `digimon_types.py`, `BaseTable` in
`battle_skills.py`, `type_dialog.py` und Hauptfenster. Keine Änderungen am
separaten PC-Port-Projekt und keine eingebundenen Spiel-Binärdateien.

## Bedienung

Links Digimon markieren → **Typ ändern** → **Vaccine**, **Virus** oder
**Data** auswählen → **Typ vormerken**. Der bisherige Typ wird aus dem
geöffneten Image gelesen; vorhandene Vormerkungen werden berücksichtigt.
Ein geladenes Modell ist nicht erforderlich. Die Seitenleiste zeigt den
aktuellen Typ und aktualisiert sich nach dem Vormerken.

**Originaltyp aus geöffnetem Quell-Image einsetzen** setzt einen einzelnen
Typ zurück. **Abbrechen** verwirft den Fensterentwurf. Unverändert kann nicht
erneut vorgemerkt werden. Unbekannte ursprüngliche Codes werden angezeigt,
aber nicht als einer der drei unterstützten Typen geraten.

Erst der gemeinsame Image-Export beziehungsweise das bestätigte Überschreiben
speichert die Änderungen. `.dw2mod` erhält Typänderungen ebenfalls. Weil Typ
und Standardtechnik in derselben Datei stehen, verwirft das Entfernen der
gesamten `DIGIMNDT.BIN` rechts alle darin vorgemerkten Änderungen. Der Hinweis
und die Bestätigung beziehen sich jetzt ausdrücklich auf Typen und Attacken.

## Geprüftes Speicherformat

Datei `DIGIMNDT.BIN`, privater US-Index 3180 / `0xC6C`, Datensätze 18 Bytes.
Die Digimon-ID steht als `s16` bei +0. Der Typ liegt in den unteren vier Bits
des Bytes bei +4. In den oberen vier Bits desselben Bytes liegt der Rank.

| Code | Typ |
|---:|---|
| 0 | Data |
| 1 | Vaccine |
| 2 | Virus |

Der Writer verwendet `(vorher & 0xF0) | neuer_typ`. Dadurch bleibt der Rank
auch dann erhalten, wenn er im selben Byte steckt. Es wird nur dieses eine
Byte angefasst; Standardtechnik (+2), DNA-Gruppe (+3), Element, Wachstum,
Entwicklungseinträge und alle anderen Arten bleiben bytegleich. Bei
unverändertem Typ wird nichts vorgemerkt. Das Wiederherstellen des letzten
geänderten Typs entfernt die Datei nur dann aus der EditSession, wenn sie
auch sonst keine unabhängigen Änderungen mehr enthält.

Für die Typfunktion wird ausschließlich DIGIMNDT gesucht und geprüft.
WAZADATA und ENEMYSET sind dafür nicht erforderlich. Die bestehenden
Verzeichnis-/privaten US-Allokationsprüfungen gelten weiterhin. Ein reines
Typprojekt registriert und validiert beim Laden nur diese Basistabelle.

## Quellen und Abgleiche

- **Wyrelade, Digimon-World-2-Decomp**, bereitgestellter Quellstand:
  `src/main/digibase.c`, `Digi_GetType` liefert `attrsLo & 0xF`;
  `Digi_GetRank` liest das folgende Nibble.
  `include/main/156C.h`, `DigiBaseData`: Byte +4 und 18-Byte-Schrittweite.
  Projekt: https://github.com/Wyrelade/Digimon-World-2-Decomp
- Derselbe Quellstand: `src/stag3000/skilleffect.c` fragt den Typ für den
  Kampf ab, `src/main/digistatus.c` für die Anzeige,
  `src/main/itemeffect.c` für typabhängige Items und `src/stag2000/dna.c`
  für DNA-Abfragen. Eine Typänderung kann deshalb auch diese Abläufe
  beeinflussen, obwohl deren Daten und Engine-Code nicht bearbeitet werden.
- **RemyRM, DigimonWorld2Tool**, bereitgestellte `FileFormats/DIGIMNDT.cs`:
  unabhängiger Abgleich von Datei, 18-Byte-Sätzen und Feldpositionen.
  https://github.com/RemyRM/DigimonWorld2Tool
- Vorhandene lokale DIGIMNDT-Referenz nur lesend geprüft: 194 Datensätze,
  ausschließlich Codes 0/1/2. Beispiele: Agumon (#3) Code 1, Gabumon (#17)
  Code 0, Devimon (#6) Code 2. Die Referenzdatei wird nicht mitgeliefert.
- **MetalKid**, [Digipedia](https://dev.metalkid.info/DigimonWorld2/Digipedia)
  und [Digimon Types](https://dev.metalkid.info/DigimonWorld2/DigimonTypes),
  abgerufen am 01.11.2026: Agumon als Vaccine, Devimon als Virus und Gabumon
  in der Data-Liste. Die Kombination dieser Angaben mit den lokalen Codes
  bestätigt die obige Zuordnung. Die Oberfläche übernimmt keine pauschalen
  Typnamen pro Art aus dieser Webseite; sie liest das geöffnete Image.

## Prüfung und Grenzen

13 neue Tests: alle drei Typen bei allen 16 oberen Nibblewerten, ausschließlich
erlaubte Änderungen am Zielbyte, ungültige Codes/fehlende Arten, abwechselnde
Typ-/Attackenänderungen und getrenntes Wiederherstellen, ISO/RAW-Export,
private und direkte Dateieinträge, Projekt-Rundlauf, tatsächlicher Button vor
dem Modellladen, Originalwiederherstellung, unbekannter Originalcode und
Abbrechen. Ein Typprojekt lässt sich ohne Attackentabellen laden.
Zusätzlich visuelle Prüfung des neuen Fensters mit konstruierten Testdaten.

Gesamtstand siehe `PRUEFUNG_v3_9.txt`. Kein Windows-/Emulatorlauf mit dem
persönlichen Nutzer-Image. Der Game-Image-Export ist geprüft; das Verhalten
einer konkreten modifizierten Partie muss im Spiel getestet werden.

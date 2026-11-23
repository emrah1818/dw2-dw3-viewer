# DW2 Mod Studio 0.99 – DNA-Digitation

Version 0.99 vom 22.11.2026.

Im Digitations-Editor gibt es einen eigenen Bereich für DNA-Digitation:
Partner A, Partner B, Ergebnis-Digimon und Ergebnisstufe (Rookie, Champion,
Ultra/Ultimate, Mega). A+B und B+A sind dieselbe Kombination. Regeln lassen sich
bearbeiten und löschen, mit Rückgängig/Wiederherstellen und Speicherung im
`.dw2mod`-Projekt. Auch ein Mod, der ausschließlich DNA-Regeln enthält, ist möglich.

Der begleitende PC-Port liest `Mods/dna_overrides.json` und meldet
`"dna_overrides": 1` in `--mod-api`. Ohne passende Schnittstelle verweigert der
Editor die Installation von DNA-Regeln. Ersetzen, Deaktivieren und Aktivieren
nehmen die DNA-Datei mit; das Löschen der letzten Regel kann eine leere Datei
installieren und so die Originalkombinationen wiederherstellen.

Die DNA-Regel wird in der tatsächlichen Spielroutine `Stg20_GetDnaResult`
angewendet. Die Ergebnisstufe wird über `Digi_GetRank` abgefragt. **Die Stufe ist
im Spiel eine Eigenschaft der Art:** Alle Exemplare eines Ergebnis-Digimon
verwenden im Port diese Stufe, solange der DNA-Mod aktiv ist. Widersprüchliche
Stufen für dieselbe Ergebnisart werden abgewiesen.

Startlevel = Stufe × 10 + 1: Rookie 1, Champion 11, Ultra 21, Mega 31.
Das geerbte Höchstlevel wird bei Bedarf bis zum Startlevel angehoben. Für Mega
wird die vorhandene Ultra-Vererbung der Kampfwerte verwendet. Die Club- und
Typbeschränkungen im Digi-Labor gelten weiter. Explizit konfigurierte Rookie-DNA
ist möglich; unkonfigurierte Rookie-Kombinationen werden abgewiesen.

Ein neues Modell wie Omnimon wird dadurch nicht hinzugefügt. Es muss zuvor in
einen vorhandenen Digimon-Platz importiert werden; diese ID kann dann als
DNA-Ergebnis ausgewählt werden. Nach Änderungen an installierten Mods das
Spiel neu starten. Diese Erweiterung gilt für den PC-Port; sie patcht keine PS1-ROM.

Prüfstand und noch offene Nachweise: [TESTERGEBNISSE_0.99.md](TESTERGEBNISSE_0.99.md).
Der Linux-Ingame-Test mit installierter DNA-Regel, DNA-Sequenz und erzeugtem
Omnimon (Mega, Level 31) ist gelungen. Speichern über das Spielmenü und Laden
in einem neuen Programmstart erhalten das Ergebnis. Der Windows-Build und
der Klicktest der Studio-Oberfläche sind noch nicht bestätigt.

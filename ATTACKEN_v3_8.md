# Native Attacken im separaten Viewer 3.8.2

Tabellenende: `WAZADATA_FIX_v3_8_1.md`. Aktuelle MP/AP-Anzeige: `ATTACKENWERTE_v3_8_2.md`.

Der Button **Attacken bearbeiten** steht links unter **Namen ändern**. Er
benötigt eine markierte Digimon-Art und ein geöffnetes Image, keine geladene
3D-Szene. Alle Änderungen verwenden die bestehende `EditSession` und lassen
sich mit Namen, Texturen und größeren Modell-/Animationsersetzungen kombinieren.

## Was geändert werden kann

- Eine Standard-/erlernbare Technik pro Art.
- Drei initiale Techniken je Gegner in einer Begegnungsgruppe; dieselbe Art
  kann in mehreren Gruppen unterschiedliche Kombinationen haben.
- Vier KI-Regeln je Gegner: Bedingung, Slot-/Abwehraktion, Zielcode.
- Globale Technikwerte: MP-Kosten, nativer `power`-Wert, Kategorie,
  Startanimation, Zieltyp, Element-/Spezialitätscode und Rangcode.
- Übernahme der Standardtechnik sowie einer ausdrücklich ausgewählten
  Gegnerkombination einschließlich KI von einem anderen Digimon.
- Suche im vollständigen Katalog des Images und CSV-Export seiner Werte.

Der Dialog unterscheidet eigene Entwürfe, bereits vorgemerkte Bytes und die
Originaldaten des geöffneten Images. Abbrechen verwirft nur den Dialogentwurf.
Wiederherstellen betrifft das gewählte Digimon beziehungsweise die gewählte
globale Technik. Andere vorgemerkte Änderungen bleiben erhalten. Dagegen ist
das Verwerfen einer gemeinsamen Datei rechts im Hauptfenster dateiweit.

Die zwölf Lernplätze gehören zur gespeicherten `DigiRosterEntry`-Instanz. Die
native Gegnerinitialisierung befüllt ausdrücklich nur Slots 0–2 und leert
3–11. Diese Version verändert weder den Spielstand noch diese Engine-Routine.
Sie bietet deshalb keine zwölf vermeintlichen Image-Slots an. Neue globale
Effekte, neue Technikeinträge und individuelle Animationen pro Attacke werden
nicht automatisch erzeugt. Einträge aus dem vorhandenen Technikkatalog können
in freie native Gegner-Slots eingesetzt werden.

## Geprüfte Tabellen

Alle Offsets sind relativ zum jeweiligen Dateianfang, little endian. Private
Dateiindizes gelten für das dokumentierte US-Layout `SLUS_011.93`.

| Datei | Privater Index | Datensatz | Schreibfelder |
|---|---:|---:|---|
| `DIGIMNDT.BIN` | 3180 / `0xC6C` | 18 Bytes ab Dateianfang | ID `s16` bei +0; erlernbare Technik `u8` bei +2 |
| `ENEMYSET.BIN` | 3183 / `0xC6F` | 100 Bytes ab Dateianfang | Gruppen-ID `u8` bei +0; drei Gegnerblöcke ab +8 im Abstand 30 Bytes |
| `WAZADATA.BIN` | 603 / `0x25B` | 68 Bytes ab dem Zeiger in Wort +0 | Technik-ID `s16` bei +0; Werte unten |

Im 30-Byte-Gegnerblock liegen Digimon-ID bei +0, Level bei +10, die drei
Technik-IDs bei +15/+16/+17 und vier KI-Tripel bei +18/+21/+24/+27. Ein Tripel
enthält Bedingung, Aktion und Zielcode. Aktionscodes 1–3 verweisen auf die drei
Slots; 4 ist Abwehr; 0 beendet die Auswertung. Ein leerer Slot darf nicht von
einer aktiven Regel referenziert werden. Regeln hinter dem ersten Endecode
bleiben erhalten und werden nicht als aktive Regeln interpretiert. Eine
Regel mit Bedingung 0 gilt immer; frühere erfüllte Regeln haben Vorrang.

In WAZADATA steht der Name als relativer `u32`-Zeiger bei +0x24, die Beschreibung
bei +0x28. FF beendet den Text. Der Decoder zeigt unbekannte Steuerbytes als
`⟨XX⟩`; er schreibt keine aus diesen Platzhaltern rekonstruierte Zeichenkette.
Alle Texte und Effektverweise bleiben bytegleich.

| WAZADATA-Feld | Position / Maske |
|---|---|
| MP-Kosten | `u8` bei +4 |
| Native Stärke `power` | `s16` bei +8 |
| Startanimation | Bits 16–17 des Wortes bei +0 |
| Kategorie | Bits 18–19: Attack / Assist / Counter / Interrupt |
| Zieltyp | Bits 20–23 |
| Spezialität/Element | Bits 24–27 |
| Rang | Bits 28–31 |

`power` ist ein Eingabewert verschiedener Schadens-/Effektformeln, kein
garantierter Endschaden. Für Rang, Element und Zieltyp zeigt die Oberfläche
bewusst die nativen Codes und erfindet keine unbestätigten Bedeutungen.
Textbeschreibungen ändern sich nicht automatisch mit diesen Werten.
Zuordnungen in DIGIMNDT/ENEMYSET sind einbytekodiert: nur vorhandene IDs 1–255
können eingetragen werden; 0 bezeichnet einen leeren Gegner-Slot. Die
Katalogansicht liest auch vorhandene Technik-IDs außerhalb dieses Bereichs.

## Quellen und unabhängige Abgleiche

Eigene Python-Implementierung des Formats; kein fremder Programmcode wird für
die Attackenfunktion eingebunden oder ausgeführt.

- [Wyrelade / Digimon-World-2-Decomp](https://github.com/Wyrelade/Digimon-World-2-Decomp),
  lokal bereitgestellter Quellstand: `src/main/digibase.c` (`Digi_GetLearnedSkill`),
  `src/main/gamedata.c` (`Enemy_FindSetById`, `Enemy_InitRosterEntry`),
  `src/main/skill.c` (`Skill_FindById`, `Skill_GetMpCost`, `Skill_GetPower`,
  Feldzugriffe), `include/main/156C.h` (Datenstrukturen),
  `src/stag3000/turn.c` (Regelabbruch, Slotwahl, Bedingungen, Zielcodes),
  `src/stag3000/skillmenu.c` (zwölf Rosterplätze und MP-Anzeige).
- [RemyRM / DigimonWorld2Tool](https://github.com/RemyRM/DigimonWorld2Tool),
  bereitgestellter Quellstand: `FileFormats/DIGIMNDT.cs`, `FileFormats/ENEMYSET.cs`,
  `Utility/TextConversion.cs`. Unabhängiger Abgleich der 18-/100-/30-Byte-Layouts
  und US-Zeichen. Die vorhandenen Referenzdateien wurden nur lokal gelesen.
  Der Parser erkennt dort 194 Basisdatensätze und 479 belegte Gegnerplätze.
- [acemon33 / DW2-TT, File-Manager-Tutorial](https://github.com/acemon33/DW2-TT/blob/main/Documentation/file-manager.md),
  online geprüft am 01.11.2026: WAZADATA, 68-Byte-Techniken, Zeiger in Wort 0,
  DIGIMNDT mit 18-Byte-Sätzen sowie private Indizes 603/3180. Die numerischen
  AP-/MP-Angaben im Beispiel wurden **nicht ungeprüft übernommen**: maßgeblich
  sind die tatsächlichen Getter und ihr Maschinen-Code.
- Lokal vorhandene SLUS-Referenz: `Skill_GetMpCost` bei `0x8001EE80` lädt Byte +4
  (`lbu`, Wort `0x90420004`); `Skill_GetPower` bei `0x8001EF64` lädt Halbwort +8
  (`lh`, Wort `0x84420008`). Dieser Abgleich vermeidet eine Verwechslung der
  beiden Felder. Das ausführbare Spiel ist nicht im Paket enthalten.
- Bereitgestellte MMC-Cheatliste: 202 benannte Technik-IDs separat als
  `ATTACKEN_REFERENZ_US.csv`. Sie dient als zusätzliche Referenz; der Dialog
  überschreibt damit keine Namen oder Werte des geöffneten Images.

Im unveränderten lokalen Referenzstand: Agumon Standard `0x1F` (Pepper Breath),
Greymon `0x24` (Nova Blast), MetalGreymon `0x30` (Giga Blaster), Frigimon `0x60`
(SubZero Ice Punch). Greymon hat beispielsweise in Gruppen 42/43 nur `0x24`,
in Gruppe 97 zusätzlich `0x6E`. Es wird deshalb keine allgemeingültige zweite
Attacke pro Art behauptet; der Dialog lässt die Quellbegegnung auswählen.

## Schreiben und Prüfen

Reale Verzeichniseinträge haben Vorrang. Fehlen sie, wird der private US-Index
nur bei eindeutigem SLUS, gültigem PS-X-EXE-Kopf, geprüften Allokationen und
erfolgreichem Inhaltsparser benutzt. Mehrdeutige Dateien werden abgewiesen.
Der Writer ändert nur dokumentierte Felder innerhalb der vorhandenen Datei.
IDs, Stats, Dateigröße, unbekannte Bytes, Texte, FX- und Tonverweise bleiben
erhalten. Alle Entwurfsdateien werden vor dem Vormerken geprüft; schlägt ein
anschließendes `stage` fehl, werden alle vorherigen Session-Änderungen erhalten.

Das vorhandene Image-Schreibverfahren übernimmt ISO/RAW, RAW-EDC/ECC,
atomare Veröffentlichung, Überschreibbestätigung und Sicherung der aktiven
Quelle. Auch bei gleichzeitig größeren Modell-/Animationsdateien werden die
Attackentabellen mitgeschrieben. Private Attackentabellen werden vor einem
`.dw2mod`-Import registriert, damit ein Projekt ohne vorheriges Öffnen dieses
Dialogs geladen werden kann.

Tests und visuelle Fensterprüfung sind in `PRUEFUNG_v3_8.txt` dokumentiert.
Es wurde kein vollständiger Emulatorlauf mit dem persönlichen Nutzer-Image
durchgeführt. Vor allem die Kombination aus Animation, FX-Ankern und den
gewählten Techniken muss im konkreten Kampf mit dem exportierten Image
geprüft werden; ein alter Savestate kann bereits geladene Daten weiterverwenden.

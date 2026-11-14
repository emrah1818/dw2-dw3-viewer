# Version 3.8.2: MP und AP neben dem Attackennamen

Stand: 01.11.2026. Im separaten Viewer stehen Kosten und Stärke jetzt direkt
in der Standardtechnik-Auswahl, den drei Gegner-Slot-Listen, der Begegnungs-
tabelle und den auswählbaren Quellbegegnungen eines anderen Digimon. Auch die
Seitenleiste enthält beide Werte. Lange Tabellen-/Spendereinträge haben einen
Tooltip mit dem vollständigen Text.

Die Werte stammen aus der WAZADATA-Datei des geöffneten Images, einschließlich
vorgemerkter Änderungen. Internet-Tabellen dienen zum Vergleich, nicht als
Ersatz für die tatsächlichen Spieldaten. Änderungen im globalen Technikreiter
aktualisieren die Beschriftungen sofort, ohne die zugeordneten Technik-IDs
oder die ausgewählte Quellbegegnung zu ändern. Noch nicht abgeschlossene
Sucheingaben bleiben erhalten.

## MP, AP und der interne Wert

MP bezeichnet den Verbrauch pro Einsatz. Das vorhandene native Byte bei +4
wird direkt angezeigt. Das vorzeichenbehaftete Halbwort bei +8 ist `power`.
Für normale positive Angriffswerte gilt die gebräuchliche AP-Darstellung:

`AP = power / 2`

Ein Rohwert von 35 erscheint beispielsweise als 17,5 AP, 55 als 27,5 AP.
Die geprüfte normale Schadensformel im Spiel enthält
`aAtk * power / (def * 2)`. Typ-, Element-, Status- und technikspezifische
Modifikatoren können den tatsächlichen Schaden ändern. AP ist deshalb kein
garantierter HP-Abzug. Die beiden Quellen unten zeigen diese halben AP-Werte.

Ein Nullwert erscheint als `— AP`, da die Technik weiterhin einen Effekt
besitzen kann. Ein negativer Wert wird ausdrücklich als nativer Heilwert
beschriftet; daraus wird kein gewöhnlicher Angriffsschaden berechnet.
Der globale Rohwert-Editor bleibt erhalten, heißt nun aber eindeutig
**Nativer power-Wert (2 × AP)**. Eine zusätzliche Anzeige zeigt die daraus
berechneten MP/AP. Das bestehende Binärformat und gespeicherte Projekte
werden nicht auf halbe Werte umgeschrieben. Der CSV-Export trennt die Spalten
**MP**, **Power (nativ)** und **AP**.

## Vergleichsquellen

Geprüft am 01.11.2026:

- **MetalKid**, [Skill List auf GameFAQs](https://gamefaqs.gamespot.com/ps/437339-digimon-world-2/faqs/64683).
  Der direkte Vollabruf war gesperrt; der Suchindex lieferte Auszüge des
  ausdrücklich vom Nutzer genannten Dokuments. Darin: Pepper Breath
  8 MP / 17,5 AP und Nova Blast 12 MP / 27,5 AP. Es wird kein vollständiger
  Import dieser Liste behauptet.
- **MetalKid**, [Skills](https://dev.metalkid.info/DigimonWorld2/Skills).
  Die Hauptseite lieferte beim Textabruf keine ausgefüllten Tabellenzeilen.
  Die ebenfalls abgerufene
  [MetalGreymon-Detailseite](https://dev.metalkid.info/DigimonWorld2/Digipedia/Details/MetalGreymon)
  enthält jedoch dieselben Angaben in der Entwicklungslinie sowie Giga
  Blaster mit 18 MP / 37,5 AP. Daraus werden keine festen Programmwerte
  erzeugt; modifizierte Images können andere Werte enthalten.
- **Wyrelade**, bereitgestellter Quellstand von
  [Digimon-World-2-Decomp](https://github.com/Wyrelade/Digimon-World-2-Decomp):
  `src/main/skill.c`, `Skill_GetMpCost` und `Skill_GetPower` für die nativen
  Feldzugriffe; `src/stag3000/skilleffect.c`, Schadensberechnung mit dem
  Faktor 2 im Nenner; `src/stag3000/battlestate.c`,
  `Stg30_GetSkillEffectKind` für die Unterscheidung positiver, negativer und
  Null-Powerwerte. Hier wird nur das Viewer-Projekt geändert.

## Prüfung und Start

Sechs neue Tests prüfen die AP-Umrechnung, sämtliche Auswahlstellen, das
Aktualisieren der Labels bei lokalen Änderungen, unveränderte Zuordnungen,
Sucheingaben und Spenderauswahl, Wiederherstellen, CSV-Spalten und die
Seitenleiste mit vorgemerkten Image-Werten. Die visuelle Prüfung verwendet
ausdrücklich konstruierte Testdaten. Das Nutzer-Image wurde nicht geprüft.
Gesamtergebnis: `PRUEFUNG_v3_8_2.txt`.

ZIP in einen neuen Ordner entpacken, `start_windows.bat` starten und auf
**v3.8.2** im Fenstertitel achten. Der Tabellenende-Fix aus 3.8.1 ist enthalten.

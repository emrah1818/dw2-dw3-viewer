# Animationssystem 0.96 (Entwicklungsstand, Branch `development/animation`)

Stand: 15. November 2026. **Noch kein Release.** 0.95 bleibt die stabile Basis.
Grundlage sind der Spielcode beider Spiele (DW2: `src/main/anim.c`, `src/stag3000/fighter.c`,
`battle.c`, `battlescript.c`, `skilleffect.c`; DW3: `dw3_decomp` `battle/battle_mode/model_mesh.c`,
`battle_script.c`, `face.c`, `menu.c`) und Messungen an allen Modellen beider Spiele.

## 1. Wie DW2 seine Kampfanimationen abspielt (Code und Messung an allen 202 Digimon)

Ein Clip besteht aus Zeilen mit je einem Schlüssel pro Knochen, eine Zeile alle 2 VBlanks (30 Bilder/s).
Das Ende ist entweder `0xFF` (letztes Bild halten) oder `0xFE` + 16-Bit-Versatz (zurückspringen auf
**jede beliebige Zeile**). Nach dem ersten Durchlauf meldet ein Clip in beiden Fällen „fertig“
(`animDone = -1`). Eine Schleife hält den Kampf deshalb nie auf.

| Clip | Wann im Kampf | Wie er läuft | Gemessen (202 Digimon) |
|---|---|---|---|
| A0 | Standby | Schleife | 202× ganzer Clip als Schleife |
| B0 | Treffer, während das Ziel abwehrt | einmal, danach A0 | 202× halten |
| C0 / C1 | Erster / zweiter Sprung beim Fallen | so lange wie der Sprung (≈ 20 / 17 Bilder) | C0: 191 Schleifen (101 ganz, 90 ab einem Zwischenbild) |
| C2 | Landen, Liegen | einmal, halten | halten |
| J0 | Aufstehen | einmal, danach A0 | halten |
| K0 | K.o. (nach C0 → C1 → C2) | einmal, halten | Schleife ab Zwischenbild (meist nur das letzte Bild) |
| F0 / G0 / H0 | Attacke 1–3 | einmal, dann Schleife bis zur nächsten Aktion | 202× Schleife ab Zwischenbild (Median: letzte 14–16 Bilder) |
| I0 | Sieg | Schleife | 172× ab Zwischenbild, 30× ganz |

Fehlschlag: nur Treffereffekt, keine eigene Animation. Die Schleifenbereiche sind je Digimon
verschieden – es gibt keinen festen Wert wie „die letzten 3 oder 5 Bilder“.

## 2. Wie DW3 seine Kampfanimationen abspielt

* Eine **Motion** besteht aus Schritten: Bilder, Überblendungen und ein Abschluss.
  `0x8000` = Schleife ab einem Bild, `0xFFFF` = fertig (halten oder – nach einer Überblendung ins
  Standby – Standby). Fast jede Motion außer Standby **beginnt mit einer Überblendung aus der Pose, die
  gerade zu sehen ist** (meist 10 Keyframes ≈ 5 Bilder).
* Was wann läuft, steht in **Skripten** je Digimon: 0 Standby, 1 Treffer, 2 Fallen + Aufstehen,
  3 K.o., 4 Ausweichen, 5–8 Techniken, 9 Standardangriff, 13/14 Auftritt. Sieg = Motion 13 (`menu.c`).
  Skripte enthalten Motions, Wartezeiten, Sprünge (Sprungdauer aus der Sprunggeschwindigkeit) und
  Trefferzeitpunkte.
* DW3 kennt **keine Abwehr**. Das nächste Gegenstück ist „Treffer ohne Umfallen“ (Skript 1).

Die Liste aus dem Auftrag ist damit bestätigt und verfeinert:

| DW2 | DW3 | Status |
|---|---|---|
| A0 Standby | Skript 0 (Motion 1) | Durch Daten bestätigt |
| B0 Verteidigung | Skript 1 (Treffer ohne Umfallen) | Automatisch erkannt (DW3 hat keine Abwehr) |
| C0 / C1 / C2 | Skript 2: Motion beim 1. Sprung, beim 2. Sprung, Landung | Daten, wenn DW3 zweimal springt, sonst automatisch |
| J0 Aufstehen | Skript 2, letzte Motion | Daten |
| K0 K.o. | Skript 3, letzte Motion | Daten |
| F0 / G0 / H0 | je ein ganzes Technikskript (5–8), mit allen Motions in DW3-Reihenfolge und -Dauer | Daten |
| fehlende Attacke | Standardangriff (Skript 9), **nur für einen Platz** | Automatisch erkannt |
| übrige Attacke | Standby | Noch ungeklärt |
| I0 Sieg | Motion 13 | Daten |

Weitere Motions (Auftritt, schwaches Standby 2, Ausweichen 3, Bewegungen) haben in DW2 keinen eigenen
Kampfplatz. Im Editor stehen sie trotzdem zur Auswahl.

Ergebnis über alle 248 DW3-Modelle: alle 247 Modelle werden fehlerfrei kodiert. Nicht kodiert wird nur
`M500WAVE`, das kein Digimon-Modell ist.

| Platz | Daten | Automatisch | Ungeklärt |
|---|---|---|---|
| A0 | 248 | – | – |
| F0 | 241 | 3 | 4 |
| G0 | 56 | 57 | 135 |
| H0 | 52 | 2 | 194 |
| I0 / J0 / K0 | 248 / 245 / 245 | – | – / 3 / 3 |

## 3. Umsetzung

* **Konverter v9**: liefert je Motion das Ende (Schleife ab Bild / Standby / halten) und die Länge der
  Anfangsüberblendung, dazu die Skripte mit Wartezeiten, Sprüngen und Treffern.
* **Aktionen** (`dw2studio/dw3_actions.py`): Jede Kampfanimation ist eine Kette aus Abschnitten
  (Motion, Start-/Endbild, Wiederholungen, Übergang). Sie endet mit „halten“ oder „ab Abschnitt X,
  Bild Y wiederholen“.
* **Kodierung**: Die Kette wird zu **einem normalen DW2-Clip**, die Schleife wird ein `0xFE`-Sprung.
  Das Format ist unverändert. Deshalb braucht der PC-Port keine Änderung, alte Mods und 0.95-Exporte
  bleiben gültig, und es läuft auch auf der PS1. Der 0.95-Weg (eine Motion je Clip) erzeugt nachweislich
  byte-identische Dateien.
* **Übergänge**:
  * DW3s Anfangsüberblendung beginnt jetzt bei der Pose, die im Spiel davor wirklich zu sehen ist:
    * innerhalb einer Kette beim vorherigen Bild;
    * bei C1, C2, J0 und K0 beim Ende des Clips, der in DW2 davor läuft;
    * bei allen anderen beim Standby.
  * Vorher wurde sie aus einer zufälligen Pose eingeblendet. Bei WarGreymon war das ein Sprung von 34°.
  * Wo DW3 selbst hart schneidet (≥ 45°), werden 4 Bilder Übergang ergänzt. Das steht im Grundtext,
    und im Editor lässt es sich entfernen. Beispiele: Birdramon 86° → 34°, Meramon 83° → 31°.
* **Editor im Studio** (Karte „Animationen (DW3-Import)“, Knopf „Animationen bearbeiten“):
  * Plätze mit Status.
  * Zeitleiste: Abschnitte farbig, Loop-Bereich gelb, Abspielposition rot, mit Klick springen.
  * Steuerung: Bild vor/zurück, Abspielen/Anhalten.
  * Setzen per Knopf: „Start/Ende = dieses Bild“, „Loop ab diesem Bild“.
  * Abschnittstabelle zum Bearbeiten: Motion, Start, Ende, Wiederholungen, Übergang; Abschnitte
    verschieben, löschen, hinzufügen.
  * Sprungwarnung, „DW3-Vorgabe“ (zurücksetzen).
  * Liste aller DW3-Motions mit Original-Vorschau Bild für Bild.
  * Kampfsimulation (Attacke 1–3, Abwehr, Fallen + Aufstehen, K.o., Sieg) mit DW2-Zeiten.
  * Geänderte Plätze bekommen den Status „Manuell zugeordnet“.
  * Speichern und Export laufen über den normalen Mod-Export.

## 4. Augen, Flammen, Flügel

* **Augen**: DW3 schließt die Augen in den Motions 4–11 (Treffer, Fallen, K.o.). DW2 hält sie bei
  B0, C0–C2 und K0 geschlossen (`Gfx_AnimAllowsBlink`). Das passt genau zusammen, das Spiel braucht
  dafür nichts Neues. In Standby, Attacken, Sieg und Aufstehen blinzeln die Augen wie in DW2.
* **Augen und HD**: Augenrechteck und HD-Textur werden unverändert aus 0.95 übernommen.
* **Meramon**:
  * Die Flammen sind **Texturanimation**: 5 Gesichtsteile, die in DW3 durchlaufen. Sie kommen als
    DW2-Zyklen herüber (`1 Auge / 5 Zyklen`).
  * Bekannte Grenze: DW2 wechselt alle 8 VBlanks, DW3 alle 6. Die Flammen laufen in DW2 also etwa ein
    Drittel langsamer. Eine Einstellung je Digimon im Port wäre möglich, ist aber nicht gebaut.
  * Der Körper bewegt sich über Knochen (10 von 17 Knochen > 10° im Standby).
* **Birdramon**: Die Flügel sind **Knochenanimation**: 8 von 16 Knochen bewegen sich im Standby um
  40–48°. Es gibt keine Texturanimation außer den Augen. In DW3 hat es nur ein Technikskript; Attacke 2
  ist der Standardangriff, Attacke 3 ist ungeklärt (Standby).
* **Bewegungsquellen**:
  * Bewegung kommt bei allen geprüften Digimon aus Knochen. Bei Meramon kommen zusätzlich die Flammen
    aus der Textur.
  * Effektteile (Feuerbälle usw.) sind DW3-Effekte und gehören nicht zum Modell. Sie werden nicht
    übertragen und nicht erfunden.

## 5. Geprüfte Digimon (Standardaktionen nach dem Import)

D = durch Daten bestätigt, A = automatisch erkannt, ? = noch ungeklärt (Standby), ⟲ = endet in
einer Schleife. Die Zahlen sind DW3-Motions; 1 ist das Standby, das DW3 nach einer Technik weiterspielt.
„Größter Sprung“ ist die größte Gelenkdrehung zwischen zwei Bildern in irgendeinem Kampfclip.

| Digimon | A0 | B0 | C0 | C1 | C2 | F0 | G0 | H0 | I0 | J0 | K0 | Augen / Zyklen | Knochen in Bewegung | Größter Sprung |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Meramon (M009MERA → #009) | D 1 ⟲ | A 4 | A 5 | A 6 | A 6 | D 1/15/16/17/18/19 ⟲ | A 1/39 ⟲ | ? 1 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 5 | 10/17 | 63.9° (J0) |
| Birdramon (M007AIRD → #021) | D 1 ⟲ | A 4 | A 5 | A 6 | A 6 | D 1/15 ⟲ | A 1/39 ⟲ | ? 1 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 0 | 8/16 | 34.4° (F0) |
| Greymon (M005GREY → #005) | D 1 ⟲ | A 4 | D 5 ⟲ | D 6 ⟲ | D 7 | D 1/15/16/17/18/19/20 ⟲ | D 1/21/22/23/24/25/26 ⟲ | D 1/27/28/29/30/31/32 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 0 | 10/22 | 25.6° (H0) |
| WarGreymon (M213WGRE → #213) | D 1 ⟲ | A 4 | A 5 | A 5 | A 5 | D 1/15/16/17/18/19 ⟲ | D 1/21/22/23/24/25 ⟲ | D 1/27/28/29/30/31 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 0 | 9/23 | 27.2° (H0) |
| Imperialdramon FM (M359IPDF → #150) | D 1 ⟲ | A 4 | A 5 | A 5 | A 5 | D 1/15 ⟲ | D 1/15 ⟲ | D 1/27 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 0 | 9/26 | 53.6° (H0) |
| Imperialdramon PM (M381IPDP → #246) | D 1 ⟲ | A 4 | A 5 | A 5 | A 5 | D 1/15 ⟲ | D 1/15 ⟲ | D 1/27 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 0 | 9/26 | 27.7° (H0) |
| Guilmon (M366GIRU → #084) | D 1 ⟲ | A 4 | D 5 ⟲ | D 6 ⟲ | D 7 | D 1/15/16/17/18/19 ⟲ | D 1/21/22/23/24/25 ⟲ | D 1/27/28/29/30/31 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 0 | 17/24 | 57.5° (C1) |
| Growlmon (M367GRAW → #048) | D 1 ⟲ | A 4 | D 5 ⟲ | D 6 ⟲ | D 7 | D 1/15/16/17/18/19 ⟲ | D 1/21/22/23/24/25 ⟲ | D 1/27/28/29/30/31 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 0 | 8/24 | 32.7° (I0) |
| MegaloGrowmon (M368MGRW → #131) | D 1 ⟲ | A 4 | A 5 | A 5 | A 5 | D 1/15 ⟲ | D 1/15 ⟲ | D 1/27 ⟲ | D 13 ⟲ | D 12 | D 11 | 1 / 0 | 8/26 | 40.8° (H0) |

Alle verbleibenden großen Sprünge liegen **innerhalb einer DW3-Motion**, also in den Originaldaten
(schnelle Schläge, Meramons Aufstehen, Guilmons zweiter Sprung samt Schleife von 28°). An keiner
Übergangsstelle gibt es noch einen Sprung über 25°. Imperialdramon und MegaloGrowmon benutzen in DW3
für Technik 1 und 2 dieselbe Motion 15; das sind DW3-Daten und keine falsche Zusammenfassung.

## 6. Grenzen

* **Sprünge auf der Stelle**:
  * DW3 springt bei Techniken zum Gegner und zurück; DW2 lässt den Angreifer an seinem Platz.
  * Die Sprungposen laufen deshalb auf der Stelle (Ausholen, Schlag, Rückkehr).
* **Kampfkamera**:
  * Die automatische Kampfkamera misst alle Posen von A0/F0/G0/H0.
  * Weil Attacken jetzt ganze Skripte sind, ändern sich die Kamerawerte bei manchen Digimon leicht
    gegenüber 0.95: WarGreymon braucht keine eigene Einstellung mehr, Imperialdramon PM ist 354 statt
    330 hoch, MegaloGrowmon 612 statt 578.
  * Modell, Texturen, HD und Licht bleiben unverändert.
* **Flammentempo**: siehe Abschnitt 4.
* **254 Posen je Knochen und Datei**: Das ist eine Grenze des DW2-Formats. Alle 247 Modelle bleiben mit
  den Vorgaben darunter. Bei sehr langen manuellen Ketten meldet der Editor einen Fehler, statt still
  zu kürzen.

## 7. Tests

* **Einheitstests** `tests/test_096_anim_actions.py` prüfen:
  * Skript-Zeitleiste mit Sprüngen;
  * Status;
  * keine doppelte Attacke;
  * Loop-Zeile und Wiederholungen;
  * Anfangsüberblendung aus der gezeigten Pose;
  * Einstieg von J0/K0 aus der Liegepose;
  * Glättung harter Schnitte;
  * Prüfregeln.
* **Gesamt**: 392 Tests bestanden.
* **UI-Test** `integration/uitest/animeditor.py` (headless Chrome, echte Oberfläche, Greymon), 13 von
  13 Prüfungen bestanden:
  * Plätze und Status;
  * Bild vor/zurück;
  * Ende/Loop setzen;
  * Übernehmen erzeugt einen DW2-Clip mit Loop ab Bild 2;
  * Speichern als manuell;
  * DW3-Original Bild für Bild;
  * Kampfsimulation A0 → C0 → C1 → C2 → J0;
  * zurücksetzen;
  * keine JS-Fehler.
* **0.95-Weg**: alte und neue Kodierung byte-identisch.
* **Alle 247 DW3-Modelle**: Standardaktionen kodiert, 0 Fehler.
* **Linux-PC-Port**:
  * Kampf 1P gegen 2P mit WarGreymon, Imperialdramon FM/PM gegen Greymon, Guilmon und Growlmon; drei
    Läufe mit je 16 Bildern.
  * Der Kampf läuft über mehrere Runden und Digimon-Wechsel ohne Hänger.
  * Das Testskript trifft fast nie. Es zeigt deshalb vor allem Standby, „Begin Attack“ und Fehlschlag.
  * Attacke, Fallen, K.o. und Sieg sind dort **noch nicht im Bild geprüft**.
* **Windows (GTX 1070)**: **noch nicht geprüft.**

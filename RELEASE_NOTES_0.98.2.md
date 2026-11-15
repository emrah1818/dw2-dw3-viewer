# DW2 Mod Studio 0.98.2 – manuelle Animationen

Autor: Codex, 15. November 2026. Korrektur auf Basis der veröffentlichten 0.98.

Zusätzliche Korrektur gegenüber 0.98.1: Wenn eine neu gewählte Motion zunächst ohne
Schleife übernommen wird, bleibt ihr ursprünglicher DW3-Loop-Beginn für späteres
Einschalten erhalten. 0.98.1 wurde während der abschließenden Prüfung bereits veröffentlicht;
die veröffentlichten Dateien werden nicht ersetzt.

## Behoben

Im einfachen DW3-Importdialog wurde zwar die ausgewählte Motion geändert, gleichzeitig
blieb die alte automatische Aktionskette im Auftrag. Der Import verwendete weiterhin diese
Kette. Die Motion-Auswahl und der Schleifenschalter konnten dadurch wirkungslos bleiben.

- Eine manuelle Auswahl ersetzt jetzt die automatische Kette – auch wenn du die Motion
  auswählst, die am Anfang der bisherigen Kette stand.
- F, G und H lassen sich unabhängig belegen und anschließend erneut ändern.
- Bei einer neu gewählten Motion dient ihr eigener DW3-Loop-Beginn als Vorgabe.
  Motions mit Standby-Übergang enden bei aktiver Schleife in der Standby-Schleife.
- Schleife aus: gewählte Motion einmal abspielen und letztes Bild halten.
  Schleife an bei einer Halte-Motion: die ganze Motion wiederholen.
- Die unveränderte automatische Vorgabe bleibt erhalten. Für eigene Bildbereiche,
  mehrteilige Aktionen und Loop-Bereiche steht weiterhin der Animationseditor bereit.
- Bereits konfigurierte Loop-Bereiche bleiben beim Aus-/Einschalten einer Aktion erhalten.

## Verwenden

`DW2_Mod_Studio_0.98.2_Windows_x64.zip` vollständig entpacken. Im DW3-Importdialog
für F/G/H die gewünschte Motion wählen, Schleifeneinstellung prüfen, vormerken und
als Mod exportieren. Neben jeder Motion steht nun, wie sie endet.
Der Begleit-Port ist funktional unverändert gegenüber 0.98; die vorhandene kompatible
Version kann weiterverwendet werden. Spieldaten sind nicht enthalten.

## Prüfstand

Siehe `TESTERGEBNISSE_0.98.2.md`. Der Release-Workflow verlangt automatische Tests,
Browserprüfung des tatsächlichen Dialogs, Windows-Builds und Startprüfung.
Die Browser- und Exportprüfungen verwenden selbst erstellte Daten. Sie ersetzen keinen
neuen Kampf auf dem Nutzer-PC. Die offenen echten Spielprüfungen aus 0.98 bleiben offen;
auch 0.98.2 wird daher als Vorabversion veröffentlicht.

# DW2 Mod Studio 0.98

Stand: 15. November 2026. **Vorabversion** auf Basis von 0.95 und Claudes
Animations-/Namensarbeiten im Branch `development/animation` bis Commit `54d363f`.

## Download und Installation

Unter **Assets** beide ZIPs herunterladen:
- `DW2_Mod_Studio_0.98_Windows_x64.zip`: Studio vollständig entpacken,
  `DW2_3D_Viewer_Studio.exe` starten.
- `DW2_PC_Port_API2_0.98_Windows_x64.zip`: passenden Port separat entpacken,
  eigene `dw2.pak` und `dw2.pak.slus` dazulegen.

Spieldaten sind nicht enthalten. Der Begleit-Port verwendet unverändert den
festgehaltenen Code aus 0.95 (`84d4379b4559d363091b8a87319442641913e03d`).
Die neuen Aktionen werden in das bestehende DW2-Animationsformat geschrieben.

## Neu gegenüber 0.95

- **Animationseditor:** Nach einem DW3-Import „Animationen bearbeiten“ öffnen.
  Abschnitte/Motions, Anfang/Ende, Wiederholungen und Übergänge bearbeiten;
  Loop ab einem beliebigen Bild setzen, Bild für Bild ansehen und Kampfaktionen
  im Viewer simulieren. Mit „Übernehmen und Vorschau“ vormerken, danach normal exportieren.
- **Kampfaktionen aus DW3-Skripten:** ganze Motion-Ketten mit Zeitablauf statt nur
  einer einzelnen Motion pro Platz. Nicht belegte Zuordnungen werden als offen angezeigt.
- **DW3-Namen:** aus dem Namenstext des USA-Abbilds; Varianten, alternative Suchnamen,
  Vorschaubilder und Name im Animationseditor. Wenn kein Name gelesen werden kann,
  bleibt das Dateikürzel mit entsprechendem Status sichtbar.
- **Suche:** Oberfläche und Backend finden Namen, Aliase, Dateikürzel sowie exakte
  Katalog-/Datei-/Kämpfer-IDs. Eine Zahl wie `35` findet nicht allein wegen des
  Dateinamens `M359IPDF` das Modell 359.
- **Übergänge korrigiert:** Auch nach einer abgeschnittenen DW3-Anfangsüberblendung
  startet der nächste Übergang aus der wirklich angezeigten Pose.
- **Windows-Build:** SciPy für Überblendungen direkt eingebunden; Versionsangaben
  und lokale Build-Prüfung auf 0.98 aktualisiert.

## Prüfgrenzen

Die automatischen Testergebnisse und der Windows-Startbericht liegen diesem Release bei.
Sie belegen keinen vollständigen Kampf auf dem Nutzer-PC. **Die neuen Aktionen wurden
in dieser Fortsetzung nicht im echten Spiel mit Originaldaten oder auf der GTX 1070 geprüft.**
Insbesondere Attacken, Fallen, K.o. und Sieg bleiben als echte Spielprüfung offen.
Die dokumentierten Windows-Kampfbilder aus 0.95 sind historische Belege für 0.95.
Deshalb wird 0.98 ausdrücklich als Vorabversion veröffentlicht.

Weitere Grenzen: fehlende DW3-Techniken können als Standby vorbelegt bleiben;
DW3-Effekte, Töne und Kamerafahrten werden nicht übertragen; Meramons Texturzyklus
hat weiterhin DW2s Tempo. Details: `ANIMATIONSSYSTEM_0.96.md`,
`EINSCHRAENKUNGEN_0.95.md`, `GRENZEN_ANALYSE_0.95.md`, `TESTERGEBNISSE_0.98.md`.

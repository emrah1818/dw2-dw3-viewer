# Untersuchung: Grafikfehler im Kampfvideo (`1000393182.mp4`), Stand 15.11.2026

**Ergebnis: Ursache noch nicht bestimmt, nicht nachgestellt. Kein Fix.**

## Befund im Video
- Story-Kampf im deutschen PC-Port: Hauptmenü „Befehle geben / Kanone / Fliehen“, Kamera hinter der Gruppe.
- Das rote Digimon links in der Gruppe ist ein DW3-Guilmon-Import.
- Vergrößerungen ab etwa 2 s sind Handy-Zoom, nicht die Spielkamera: Die Statusfenster werden mit vergrößert.
- In einzelnen Bildern ragt aus Guilmons linker Seite ein dünner, rosa Keil senkrecht nach oben. Er hat die Farbe des
  Modells und ist in den Bildern dazwischen weg; er flackert also im Standby.
- In den Bildern ohne Keil ist von hinten kein Schwanz zu sehen.
- In der späteren Nahaufnahme ist der Schwanz normal.
- Die grünen Drahtgitter sind die normale Auswahl des Spiels und kein Fehler.

## Geprüft, ohne Befund
- **Daten des Imports:** Guilmon (`M366GIRU`) mit den 0.98.3-Vorgaben nach #84 importiert.
  - Alle Clips: Knochenmatrizen ohne Skalierung (Singulärwerte 1,000).
  - Kein Knochen springt für ein einzelnes Bild weg und zurück.
- **Kampfkameras:** Alle Kampfkameras aus `battle_shots` (Gruppenplätze 0–2, Angriff, Ziel, Nahaufnahme), alle Bilder
  von A/F/G/H.
  - Kein Punkt kommt näher als z = 6765; die GTE begrenzt erst unter z = 750.
  - Kein Punkt liegt außerhalb ±1024.
- **Echtes Spiel (Linux-PC-Port, gepinnter Commit):**
  - Domain-Kampf mit Guilmon, Greymon und Growlmon in der Gruppe, Hauptmenü wie im Video, jeweils 90 Bilder.
  - Geprüft mit drei Einstellungen: Software-Renderer, GPU mit Scale 3, GPU mit PGXP und Smooth Frames.
  - In keinem Fall erscheint ein Keil.
  - Ein lokaler Debug-Build (nicht eingecheckt) meldet für Guilmon keinen Modellteil mit Bildpunkten weit außerhalb
    des Bildes und keinen verworfenen Teil.
- **Gemeinsame Animationsdateien:** Kein Digimon-Platz unter #300 teilt eine Datei mit einem anderen.

## Nachtrag 15.11.2026, 18 Uhr: mit dem Mod und den Einstellungen aus dem Video
Der Mod lag wieder in `Documents\DW2-PC\Mods`, nachdem du ihn wiederhergestellt hattest.
- Er enthält zwei DW3-Importe mit 24 Knochen: #4 (Platz von Betamon, im Video „KADIR“, Guilmon) und #133 (`DTRN`).
- Alle 22 Clips gemessen: keine Skalierung außer 1,5 in I0 von #133, kein Einzelbild-Ausreißer.

Deine Einstellungen (`%APPDATA%\DW2-Online\settings.ini`): GPU, Scale 5, 16:9 (wide 2), PGXP, Smooth Frames,
fps_limit 120, Sharpen 25, FXAA, bilinear.

Linux-Port, gleicher Port-Stand, dein Mod, deine Einstellungen (Scale 3 statt 5):
- Domain-Kampf mit #4, #133 und #5, Hauptmenü wie im Video, 90 Bilder.
- Je Bild auch die Smooth-Zwischenbilder bei 0, 33, 50 und 100 %.
- Automatisch gesucht: rosa Pixel, die nur im Zwischenbild und in keinem der beiden echten Bilder vorkommen.
  - Treffer gibt es nur in der Kameradrehung zu Kampfbeginn (dort sind die Zwischenbilder echte Bewegung).
  - Im ruhigen Menü gibt es höchstens 43 Pixel.
- **Kein Keil nachgestellt.**

Übrige Unterschiede zum Video:
- Windows mit NVIDIA-Treiber.
- Echte Bildausgabe mit Fenster-Thread bei 120 Hz; die Testbilder werden ohne diesen Thread berechnet.
- Anderer Spielstand und andere Domain.

## Offen
- Der Test benutzt einen Guilmon-Import, den ich selbst erzeugt habe, nicht den Mod aus dem Video. Ziel-Slot, Größe,
  manuell gewählte Motions (0.98–0.98.2), Einstellungen, Renderer und Port-Version des Videos sind unbekannt.
- Auf dem Windows-PC ist der im Video benutzte Mods-Ordner nicht gefunden worden: `Documents\DW2-PC\Mods` ist leer.
  Die 0.98-ZIPs in `Downloads` sind nicht entpackt.
- Ob „Maus“ oder „Mods“ gemeint war, ist ungeklärt.

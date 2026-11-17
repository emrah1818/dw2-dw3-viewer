# Testergebnisse 0.98.4 (17.11.2026)

Alle Läufe unter Linux mit eigenen Spielabbildern (DW2-USA `dw2.pak`, DW3-USA-BIN). Was nicht geprüft wurde, steht unten.

## Automatische Sprache

| Prüfung | Ergebnis |
|---|---|
| Web-Oberfläche, Browsersprache de-DE / en-US / fr-FR (`integration/uitest/language.py`) | Deutsch / Englisch / Englisch, 12 von 12 Prüfungen bestanden |
| Umschalten de → en → de, auch für Texte ohne `data-i18n` | bestanden, deutsche Texte werden wiederhergestellt |
| Eigene Wahl nach Neuladen | bleibt erhalten |
| Desktop-Fenster (PyQt6/QtWebEngine, Xvfb) mit `LANG=de_DE` / `en_US` / `fr_FR` | Oberfläche `de` / `en` / `en`, Menü „PC-Werkzeuge“ / „PC tools“ / „PC tools“ |
| Englischer Modus, alle Reiter, Digimon gewählt, DW3-Abbild geöffnet und Modell gewählt: sichtbare Texte mit deutschen Wörtern | vorher 54 (Suchmuster) bzw. rund 240 (Durchsicht), jetzt 0 von 2381 sichtbaren Texten |

Nicht übersetzt sind weiterhin Fehlermeldungen, die aus dem Python-Teil kommen (z. B. beim Mod-Export) und nicht
zu den bekannten Texten gehören, sowie die Inhalte der mitgelieferten Dokumente.

## Regression

| Prüfung | Ergebnis |
|---|---|
| `pytest` mit privaten Spieldaten (`DW2_TEST_PAK`, `DW3_TEST_DISC`) | 421 bestanden |
| JS-Tests (`tests/*.mjs`) | 3 von 3 bestanden |
| UI: manuelle Motion-Auswahl (`manual_selection.py`) | bestanden |
| UI: Animationseditor (`animeditor.py`, Greymon) | 13 von 13 |
| UI: DW3-Namen (`dw3names.py`) | 18 von 18 |

Die UI-Tests prüfen jetzt sprachunabhängig (vorher schlugen zwei Prüfungen bei englischer Browsersprache fehl).

## Linux-Pakete

Werden im Release-Workflow auf `ubuntu-22.04` gebaut:
- Studio mit PyInstaller, Starttest des fertigen Programms unter Xvfb (WebGL, Python-Brücke, neun Bereiche,
  SciPy-Matrixmischung), Bericht `linux-smoke.json` liegt dem Release bei.
- PC-Port aus dem festen Commit (`integration/pc_port_base.txt`), Prüfung von Mod-API 2, Schrift-, Text- und
  Cache-Tests.

**Nicht geprüft:** Start auf einem echten Linux-Desktop von Hand; ein Spiel mit dem Linux-Port und eigenem
`dw2.pak` unter dem Release-Paket. Windows-Pakete sind gegenüber 0.98.3 nur in Sprache und Versionsnummer geändert.

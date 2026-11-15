# Prüfstand 0.98.3

Autor: Codex, 15. November 2026.

## Mit Originaldaten ausgeführt

Vor der Korrektur: #304 reproduziert `FileExistsError(17, 'File exists')`.
MODELDT ordnet A/D/E dieselbe Datei `E304QTNK.BIN` zu. Die Extraktion verwendete den
zuletzt vergebenen Alias D304 mehrfach. #300, #301, #305 und #350 zeigen dieselbe Zuordnung.

Nach der Korrektur:

| Prüfung | Ergebnis |
|---|---|
| Alle katalogisierten Modelle ab #300 aus der Original-PAK | 192 bestanden, 0 Fehler (47,5 s) |
| DW3-Greymon in #300, #304, #305, #350 importieren | je Modell + eine E-Datei, beide Clips lesbar, sechs logische Vorschauanimationen |
| DW3-Greymon in #400 importieren | Modell + eine D-Datei, sieben physische Clips, 35 logische Vorschauanimationen |
| Fünf Projekte speichern, neu öffnen, Vorschau erneut laden | bestanden |
| Alle fünf als PC-Port-Mod exportieren | je zwei geänderte Dateien, HD-Pack vorhanden |
| #304: PNG exportieren, Farben bearbeiten, Vorschau, übernehmen, Modell neu konvertieren | bestanden |
| SHA-256 der Original-PAK vor/nach den fünf Importen | unverändert |

Mehrere logische Slots können denselben Clip derselben physischen Datei abspielen.
Die Auswahl beim Import ist deshalb pro physischem Clip erforderlich, nicht mehrfach
für denselben Inhalt. Die MODELDT-Verweise bleiben bei den Feld-Ersetzungen unverändert.

## Automatische Regression

`tests/test_field_models.py` verwendet selbst erstellte PAK-/Modell-/Animationsdaten:
- eindeutige physische Datei und vollständige A/D/E-Mehrfachzuordnung;
- direkte Vorschau, erneutes Öffnen, Größenprüfung und Animationsaudit;
- geänderte Animationsbytes, doppelte Eingabeeinträge und Desktop-Warteschlange;
- widersprüchliche Zieldateinamen werden abgewiesen;
- andere Knochenzahl beim Feld-Import, beide Clips, Feldrollen, Animationseditor;
- keine Kampfkamera und kein MODELDT-Schreibzugriff beim Feld-Import;
- Projekt-Rundlauf und Mod-Export, Original-PAK unverändert.

Vollständige lokale Python-Suite: **416 bestanden, 4 Spieldatentests übersprungen**.
Neue Feld-Regression zusätzlich nach Erweiterung des Editor-Tests ausgeführt: 4 bestanden.
Die Originaldatenprüfungen oben wurden separat ausgeführt und sind keine übersprungenen Tests.
JavaScript: 24 native Animations-, 22 Such- und 17 Auswahlprüfungen bestanden.
Syntaxprüfung der Oberfläche und `git diff --check` erfolgreich.

Der UI-Test `integration/uitest/manual_selection.py` prüft zusätzlich, dass ein
fehlgeschlagenes Laden von #304 die vorherige Vorschau und Animationenauswahl entfernt.
Der lokale Browserstart ist eingeschränkt; diese UI-Prüfung läuft verbindlich in GitHub Actions.
Der Release-Workflow verlangt erfolgreiche Tests, beide Windows-Builds, EXE-Startprüfung
(WebGL/Python-Brücke/SciPy) und Windows-Versionsressource 0.98.3.
Die genauen Protokolle liegen im Release: `test-results.xml`, `test-summary.txt`,
`ui-manual-selection.txt`, `windows-smoke.json`.

## Quellen und Grenze

Eigene Messungen an den vom Nutzer bereitgestellten Daten. Format und Nutzung der
Feldanimationen im festgehaltenen PC-Port-Quellstand
`84d4379b4559d363091b8a87319442641913e03d`:
- `src/main/digidata.c`: `Digi_GetAnimFile` liest MODELDT-Slots;
- `src/stag4000/enemy.c`: 0x28 (E0) Standby, 0x29 (E1) beim Gehen.

Quellcode/Regression: [Feldtests](https://github.com/emrah1818/dw2-dw3-viewer/blob/v0.98.3/tests/test_field_models.py),
[Workflow](https://github.com/emrah1818/dw2-dw3-viewer/blob/v0.98.3/.github/workflows/release.yml).
Kein neuer echter Domain-Spielablauf, GPU-Test auf dem Nutzer-PC oder PS1-Konsolentest.
Die Grafikglitches aus dem vorherigen Kampfvideo werden damit nicht als behoben behauptet.

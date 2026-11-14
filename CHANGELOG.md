# Änderungsprotokoll

## 0.17b – 14.11.2026 (DW2 Mod Studio)

Neu
- Oberfläche mit neun Bereichen: Dateien, 3D-Viewer, Digimon, Attacken, Digitation, Domains, DW3-Import, Texturen, Mod-Export.
- Eigene Techniken (`dw2studio/core/techniques.py`, `SkillTable.cloned`): Kopie eines WAZADATA-Datensatzes unter freier ID 1–255; Name und Beschreibung hinter dem Endeintrag, Dateilänge bleibt wenn möglich gleich. Zuweisung als erlernbare Technik (DIGIMNDT) und/oder an Gegnerplätze (ENEMYSET). Bearbeiten nur, wenn ausschließlich dieses Digimon die Technik nutzt.
- Domain-Editor (`dw2studio/core/domains.py`): Domain-Tabelle (Datei 0xE20, Eintrag 0xA), Etagen mit `enemySets[5]`, vollständige ENEMYSET-Gruppen, Gruppen kopieren, Verwendung je Gruppe.
- Digitationslinien (`evolution.change_line`): mehrere Arten in einem Schritt, alles oder nichts.
- DW3-Stapelimport (`dw3_batch_apply`) mit Namen; ein Rückgängig-Schritt.
- Kampfkamera und Treffereffekt-Höhe (`dw2studio/core/battle_camera.py`, MODELDT +0x1E/+0x20); automatisch beim DW3-Import aus dem Höhenunterschied, manuell im Digimon-Editor; Grenze 0xBFF wegen der 9-stufigen Kameratabelle.
- Mod-Export mit Prüfung, Konflikterkennung, Ersetzen und Wiedereinlesen (`dw2studio/mod_io.py`).
- HD-Vorschau bis 2048×4096 im 3D-Viewer; HD-Stufe 2048×4096 beim DW3-Import.
- Datei-Explorer mit Export von Original oder Änderung.
- Anzeige der festen Digitationslevel-Regel; Schnittstellenbeschreibung für den Port (`DIGITATIONSLEVEL_SCHNITTSTELLE.md`).

Behoben
- Auswahllisten zeigen unbekannte aktuelle Werte (z. B. Kartenfiguren wie #322) als eigene Option; vorher hätte „Übernehmen“ sie still durch den ersten Listeneintrag ersetzt.

Geändert
- Programmname in Titel und Windows-Versionsinfo: „DW2 Mod Studio“. Der interne Datenordner-Name bleibt, damit Projekte und Zwischenspeicher erhalten bleiben.
- Release enthält Testergebnisse (`test-results.xml`, `test-summary.txt`).

## 0.16b – 14.11.2026
Bewegungen aus DW3-Kampfskripten vorbelegt, Größe nach Standhöhe, HD 2048×4096 beim Import, Mods deaktivieren/aktivieren, Begleit-Port auf Basis 1.6.2-preview. Details: RELEASE_NOTES_0.16b.md.

## 0.15b und früher
RELEASE_NOTES_0.15b.md, RELEASE_NOTES_0.14b.md, PRUEFUNG_v4_0.md.

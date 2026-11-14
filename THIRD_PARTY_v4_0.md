# Drittanbieter und Herkunft

- PC-Grundlage: Nutzerpaket `DW2_3D_Viewer_v3_9_Typ_Aendern_Python.zip`.
- Android-Oberfläche und Ergänzungen: [emrah1818/dw2-viewer-android, v5.2.1](https://github.com/emrah1818/dw2-viewer-android/tree/v5.2.1), Commit `8125ccd894d552fb85ee59df51ff8a2b86745f37`, 09.11.2026.
- three.js r160 und zugehörige Loader/Controls: Three.js Authors, MIT; vollständiger Lizenztext in `licenses/three_MIT.txt`. [Originaltext](https://github.com/mrdoob/three.js/blob/r160/LICENSE).
- DW2-Konverter und Python-Port: Format nach `jype/dw2_model_converter`; vorhandene MIT-Lizenzen in `licenses/`, `tools/` und `third_party/` bleiben enthalten.
- Laufzeitabhängigkeiten aus `requirements.txt`: PyQt6, PyQt6-WebEngine (einschließlich Qt WebEngine/Chromium), VTK, Pillow, NumPy, trimesh, pyqtgraph und PyOpenGL. Ihre jeweiligen Lizenzbedingungen gelten zusätzlich; ein erzeugtes EXE-Paket enthält deren Laufzeitkomponenten.

Es sind keine Disc-Dateien oder Spielstände beigefügt. Die Testmodelle und
-tabellen sind synthetische Fixtures aus den Testprogrammen.

# PC-Port Overlay API 2

Quellbasis: emrah1818/dw2-pc-port, Commit in pc_port_base.txt. Der Patch erweitert den bestehenden Form-1-Mod-Lader um virtuelle CD-Dateibereiche, korrekte Sektorgrößen und einen 6-MiB-Spielheap im bestehenden 16-MiB-Fenster. Die ursprüngliche PAK und ihre Prüftabelle bleiben unverändert. PS1-Adressspiegelung bleibt bei 2 MiB; nur der native Heap wird separat erweitert.

Maximal 2 MiB je Ersatzdatei, 64 MiB Overlay-Speicher, virtuelle CD unter 450.000 Sektoren. Vergrößerte Dateien werden nur über die angepasste Dateitabelle gelesen. Audio-/Video-Ersatz ist weiterhin gesperrt. --no-mods stellt die Originaldaten bereit.

Anwenden: passende Quellbasis auschecken, git apply /absoluter/Pfad/pc_port_api2.patch ausführen und tools/build_native.py --release --no-disc verwenden. Die vorhandene Build-Anleitung des PC-Ports gilt. Keine Spieldaten in das Repository kopieren.

Das Begleitpaket der Viewer-Version enthält dw2.exe, SDL3.dll und dw2_mod_api.json. Das Paket in einen eigenen Ordner entpacken, die eigenen dw2.pak und dw2.pak.slus dazu legen und den Mod dorthin exportieren. Bestehende Spielstände/Originaldaten werden nicht geändert.

--mod-api gibt die API-Version ohne Spielstart aus. --check-model MODELLDATEI ANIMATIONSDATEI prüft nach echtem Spielstart das Laden, Gfx_AttachModel, 120 Schritte Anim_StepModelAnim und Gfx_CalcModelBoneMatrices. IDs dezimal oder mit 0x-Präfix. Das ist ein Integrationscheck und kein vollständiger Kampf-/Gameplay-Test.

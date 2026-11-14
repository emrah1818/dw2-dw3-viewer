"""UI translations and reproducible Windows version resource metadata."""
from pathlib import Path

from dw2studio.i18n import EN, translate

ROOT=Path(__file__).resolve().parents[1]


def test_core_translations_and_unknown_values():
    assert translate('3D-Objekt ersetzen','de') == '3D-Objekt ersetzen'
    assert translate('3D-Objekt ersetzen','en') == 'Replace 3D Object'
    assert translate('Textur ins Spiel-Image schreiben','en') == 'Write Texture to Game Image'
    assert translate('Automatische Rotation','en') == 'Auto Rotation'
    assert translate('Wiederholen','en') == 'Loop'
    assert translate('MetalGreymon','en') == 'MetalGreymon'
    assert translate('MetalGreymon','invalid') == 'MetalGreymon'


def test_dynamic_status_and_confirmation_preserve_filenames():
    assert translate('{image}\n{count} Digimon · {files} Dateien','en',image='dw2.bin',count=243,files=3675) == 'dw2.bin\n243 Digimon · 3675 files'
    assert translate('Geladen: {name}','en',name='MetalGreymon.glb') == 'Loaded: MetalGreymon.glb'
    de = ('Eine neue Spiel-BIN wird erstellt.\n\nDigimon: {digimon}\n'
          'Native TIM: {width}×{height}, {bpp}-Bit\n'
          'Quelle: {png}\nZiel: {dest}\n\n'
          'Die Farben werden pro Modellfläche auf deren originale PlayStation-Palette abgebildet. '
          'Die versteckten Farbpaletten bleiben unverändert. '
          'Nutze ausschließlich eine NEU exportierte native Vorlage aus v2.3. '
          '3D-Geometrie, UV-Koordinaten und Animationen werden NICHT aus der Projektdatei übernommen.\n\n'
          'Die Original-BIN bleibt unverändert. Fortfahren?')
    en = translate(de,'en',digimon='Agumon',width=128,height=256,bpp=4,png='new.png',dest='patched.bin')
    assert 'Agumon' in en and 'new.png' in en and 'patched.bin' in en
    assert 'original game BIN remains unchanged' in en
    assert 'not' in en.lower()


def test_standalone_source_package_assets():
    assert (ROOT/'assets'/'DW2_3D_Viewer.ico').is_file()
    assert (ROOT/'tools'/'dw2_model_converter'/'dw2_model_converter.exe').is_file()
    main=(ROOT/'main.py').read_text()
    assert 'DW2 / DW3 Viewer 0.16b' in main
    assert not (ROOT/'dw2studio'/'core'/'dungeon_editor.py').exists()
    assert not (ROOT/'dw2studio'/'core'/'memory_card.py').exists()


def test_all_main_controls_have_en_translations():
    labels=[
      'BIN / ISO öffnen','3D-Datei importieren','DIGIMON / MODELLE',
      'Ausgewähltes Digimon öffnen','MODELL & TEXTUREN','3D-Datei exportieren',
      '3D-Objekt ersetzen','Originalmodell wiederherstellen',
      'Textur als PNG exportieren','Textur ersetzen (PNG)','Original-TIM exportieren (PNG)',
      'Textur ins Spiel-Image schreiben','Vollständigen Augenatlas exportieren',
      'Augenatlas ins Spiel-Image schreiben','Augen blinzeln (experimentelle Vorschau)',
      'PROTOKOLL','Sprache:',
      'Kamera zurücksetzen','Automatische Rotation','Texturen anzeigen (aus = grünes Polygon-Drahtgitter)',
      'Wiederholen','▶ Abspielen',
    ]
    assert all(label in EN for label in labels)
    assert all(isinstance(translate(label,'en'), str) for label in labels)

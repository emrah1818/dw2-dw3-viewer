"""0.17b: texture sizes up to 2048x4096, the nine areas of the window, API registration."""
import io
import re
from pathlib import Path
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('k', [1, 2, 4, 8, 16])
def test_import_atlas_offers_every_size_up_to_2048x4096(tmp_path, k):
    from test_015_native import source
    from dw2studio.core.dw3_native import atlas
    _, hd, _, _ = atlas(source(tmp_path), tmp_path, k)
    assert hd.size == (128 * k, 256 * k)


def test_atlas_rejects_unsupported_factor(tmp_path):
    from test_015_native import source
    from dw2studio.core.dw3_native import atlas
    with pytest.raises(ValueError):
        atlas(source(tmp_path), tmp_path, 32)


def png(w, h):
    buf = io.BytesIO(); Image.new('RGBA', (w, h), (1, 2, 3, 255)).save(buf, format='PNG'); return buf.getvalue()


@pytest.mark.parametrize('w,h,ok', [(128, 256, True), (512, 1024, True), (1024, 2048, True), (2048, 4096, True),
                                    (4096, 8192, False), (2048, 2048, False), (130, 256, False)])
def test_hd_preview_sizes(tmp_path, monkeypatch, w, h, ok):
    import android_api as api
    monkeypatch.setattr(api, 'CACHE', tmp_path)
    if ok:
        r = api._hd_publish(png(w, h))
        assert r['size'] == [w, h] and (tmp_path / r['url']).is_file()
    else:
        with pytest.raises(ValueError, match='128×256'):
            api._hd_publish(png(w, h))


def test_hd_export_accepts_2048x4096(tmp_path):
    from test_015_native import source
    from dw2studio.core.dw3_native import encode_model
    from dw2studio.hd_pack import export
    native, _, _ = encode_model(source(tmp_path), tmp_path)
    picture = tmp_path / 'big.png'; picture.write_bytes(png(2048, 4096))
    port = tmp_path / 'port'; port.mkdir()
    assert export(native, picture, port)['scale'] == 16


AREAS = ['page-files', 'page-view', 'page-list', 'page-attacks', 'page-evo', 'page-domains', 'page-dw3', 'page-tex', 'page-changes']


def test_window_has_the_nine_areas_and_every_tab_has_a_page():
    html = (ROOT / 'www/index.html').read_text(encoding='utf-8')
    tabs = re.findall(r'data-page="([^"]+)" class="tab"', html)
    assert tabs[:9] == AREAS
    for page in tabs:
        assert page == 'page-tex' or f'id="{page}"' in html                   # page-tex opens the texture card
    js = (ROOT / 'www/app.js').read_text(encoding='utf-8')
    for button in ['fx-open', 'at-new', 'evo-save', 'grp-clone', 'dw3-run', 'b-mod-check', 'b-mod-replace', 'b-mod-import',
                   'b-hd-preview', 'cam-save']:
        assert f"'#{button}'" in js or f'id="{button}"' in js
        assert f'id="{button}"' in html or f"'#{button}'" in js


def test_every_ui_call_is_registered():
    import android_api as api
    js = (ROOT / 'www/app.js').read_text(encoding='utf-8')
    desktop_only = {'pick_image', 'pick_dw3', 'pick_file', 'pick_project', 'pick_roster', 'save_export', 'port_mods_dialog',
                    'export_port_dialog', 'export_hd_dialog', 'overwrite_original', 'pick_png', 'adopt_dialog',
                    'app_info', 'open_studio'}  # answered by desktop.py itself
    called = set(re.findall(r"native\('([a-z0-9_]+)'", js))
    api._register_edit()
    missing = {m for m in called if m not in api._METHODS and m not in desktop_only}
    assert not missing, missing


def test_paths_only_through_native_dialogs():
    desktop = (ROOT / 'desktop.py').read_text(encoding='utf-8')
    for method in ('mod_check', 'mod_export', 'mod_export_replace', 'mod_import'):
        assert f"'{method}'" in desktop.split('Diese Methode ist dem Desktop vorbehalten')[0]

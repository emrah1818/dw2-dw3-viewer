"""Regression: color edits must recolor native DW2 palette banks, not purple-map to old CLUTs."""

from io import BytesIO
from pathlib import Path
import struct

import pytest
from PIL import Image

from dw2studio.assets.tim import TIM
from dw2studio.core.dw2_native_atlas import decode_native_atlas, encode_native_atlas
from dw2studio.core.dw2_palette_recolor import (
    measure_native_quality, preview_native_texture,
)
from test_dw2_native_atlas import model_fixture


def test_new_colors_update_game_palette_and_native_pixels():
    model = model_fixture()
    original = decode_native_atlas(model, 128)
    target = original.copy()
    # The fixture's native face palette contains only RED and GREEN, not BLUE.
    # The v2.3 encoder silently approximated this using the old colors.
    for y in range(10, 40):
        for x in range(10, 40):
            target.putpixel((x,y),(8, 64, 248, 255))
    preserved = encode_native_atlas(model, 128, target, recolor=False)
    patched_tim, decoded, report = preview_native_texture(model,128,target,recolor=True)
    assert patched_tim != preserved
    assert patched_tim[-2048:] != model[128+16448-2048:128+16448]
    assert patched_tim[:64] == model[128:128+64]
    assert decoded.getpixel((15,15))[2] > 225
    assert decoded.getpixel((15,15))[0] < 25
    assert decoded.getpixel((15,15))[3] == 255
    assert report.mean_rgb_error < 12
    assert report.palettes_rewritten >= 1
    assert report.colors_rewritten >= 1
    assert model == model_fixture()  # source never mutated


def test_noop_native_atlas_remains_byte_identical_with_recoloring():
    model = model_fixture()
    original = decode_native_atlas(model,128)
    result, predicted, quality = preview_native_texture(model,128,original,recolor=True)
    assert result == model[128:128+16448]
    assert predicted.tobytes() == original.tobytes()
    assert quality.mean_rgb_error == 0
    assert quality.colors_rewritten == 0
    assert quality.palettes_rewritten == 0


def test_native_palette_recolor_rejects_accidental_alpha_removal():
    model=model_fixture()
    target=Image.new('RGBA',(128,256),(0,80,250,0))
    with pytest.raises(ValueError,match='Transparenz'):
        preview_native_texture(model,128,target,recolor=True)


def test_palette_encoder_preserves_non_tim_model_bytes():
    model = model_fixture()
    before, after = model[:128], model[128+16448:]
    target=decode_native_atlas(model,128).copy()
    target.putpixel((15,15),(8,40,240,255))
    tim = encode_native_atlas(model,128,target,recolor=True)
    updated = before+tim+after
    assert updated[:128]==before
    assert updated[128+16448:] == after
    assert len(updated)==len(model)
    TIM(updated[128:])


def test_palettization_of_many_png_colors_previews_expected_loss():
    model=model_fixture()
    target=decode_native_atlas(model,128).copy()
    for y in range(5,40):
        for x in range(5,40):
            target.putpixel((x,y),(x*3%256,y*4%256,(x+y)*3%256,255))
    tim,predicted,quality=preview_native_texture(model,128,target,recolor=True)
    assert quality.pixels_checked>500
    assert quality.colors_rewritten>0
    assert quality.alpha_mismatch_fraction==0
    assert predicted.getpixel((15,15))[3]==255


def test_native_preview_bad_color_limit_is_enforced(monkeypatch):
    model=model_fixture()
    target=decode_native_atlas(model,128).copy()
    target.putpixel((15,15),(8,40,240,255))
    from dw2studio.core import dw2_palette_recolor as recolor
    # A future regression must NOT write a badly-colored BIN without warning.
    original = recolor.measure_native_quality
    def pretend_bad(*args, **kwargs):
        data=original(*args, **kwargs)
        return recolor.PaletteQuality(55, .40, data.alpha_mismatch_fraction,
                                      data.colors_rewritten, data.palettes_rewritten, data.pixels_checked)
    monkeypatch.setattr(recolor,'measure_native_quality',pretend_bad)
    with pytest.raises(ValueError,match='nicht ausreichend genau'):
        recolor.preview_native_texture(model,128,target,recolor=True)

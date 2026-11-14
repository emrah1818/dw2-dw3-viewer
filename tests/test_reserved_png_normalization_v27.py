"""A graphics editor's changes to the final 32 rows must not corrupt DW2's CLUT.

Regression for the 2.6 "unteren 32 Zeilen" failure reported with an edited
Digimon PNG. These tests deliberately paint arbitrary opaque imagery into the
region that physically stores the console's 64 face palette banks.
"""
import struct
import pytest
from PIL import Image

from dw2studio.core.dw2_native_atlas import decode_native_atlas
from dw2studio.core.dw2_palette_recolor import (prepare_native_edit,
    native_edit_report, preview_native_texture)
from tests.test_eye_frames_v25 import synthetic_greymon_eye_layout
from tests.test_eye_variants_v26 import synthetic_agumon_style
from tests.test_dw2_native_atlas import model_fixture


@pytest.mark.parametrize('model_factory,eyes', [
    (model_fixture, False),
    (synthetic_greymon_eye_layout, True),
    (synthetic_agumon_style, True),
])
def test_palette_rows_changed_only_are_exact_native_noop(model_factory, eyes):
    model=model_factory()
    offset=struct.unpack_from('<I',model)[0]
    source=decode_native_atlas(model,offset,include_eye_frames=eyes)
    edited=source.copy()
    # Simulate Paint/Photoshop flattening/export changing the alpha AND RGB
    # of the forbidden bottom 32 rows, even when the user edited only eyes.
    for y in range(224,256):
        for x in range(128):
            edited.putpixel((x,y), ((x*13+y)%256,35,230,255))
    normalized,report,_,_=prepare_native_edit(model,offset,edited,eye_frames=eyes)
    assert report.palette_storage_ignored == 32*128
    assert normalized.tobytes() == source.tobytes()
    tim, predicted, quality=preview_native_texture(model,offset,edited,eye_frames=eyes)
    assert tim==model[offset:offset+16448]
    assert predicted.tobytes()==source.tobytes()
    assert quality.palettes_rewritten==0


@pytest.mark.parametrize('factory,eyes,point', [
    (model_fixture,False,(15,15)),
    (synthetic_greymon_eye_layout,True,(89,16)),
    (synthetic_agumon_style,True,(5,5)),
])
def test_real_body_or_eye_recolor_still_applies_with_repainted_palette_rows(factory,eyes,point):
    model=factory()
    offset=struct.unpack_from('<I',model)[0]
    image=decode_native_atlas(model,offset,include_eye_frames=eyes)
    x,y=point
    assert image.getpixel(point)[3] >= 100
    old=image.getpixel(point)
    changed=(8,64,240,old[3])
    image.putpixel(point,changed)
    # The exact error from v2.6: changed bottom rows should never veto an
    # otherwise valid recolor, or be interpreted as playable texture data.
    for py in range(224,256):
        for px in range(128):
            image.putpixel((px,py),(145,145,145,255))
    out,pred,quality=preview_native_texture(model,offset,image,eye_frames=eyes)
    assert out!=model[offset:offset+16448]
    assert pred.getpixel(point)[2]>170
    assert quality.alpha_mismatch_fraction==0


def test_unmapped_paint_is_ignored_and_reported():
    model=model_fixture()
    original=decode_native_atlas(model,128)
    painted=original.copy()
    painted.putpixel((110,140),(248,19,47,255))
    report=native_edit_report(model,128,painted)
    assert report.palette_storage_ignored==0
    assert report.unmapped_texture_ignored==1
    out,_,_=preview_native_texture(model,128,painted)
    assert out==model[128:128+16448]


def test_alpha_changes_on_real_body_pixels_are_still_blocked():
    model=model_fixture()
    painted=decode_native_atlas(model,128)
    for y in range(8,30):
        for x in range(8,30):
            painted.putpixel((x,y),(0,0,0,0))
    # A legitimate PNG cannot turn huge parts of a Digimon transparent.
    with pytest.raises(ValueError,match='Transparenz'):
        preview_native_texture(model,128,painted)

@pytest.mark.parametrize('model_factory', [synthetic_greymon_eye_layout, synthetic_agumon_style])
def test_normal_tim_and_complete_eyes_are_detected_independently(model_factory):
    from dw2studio.core.dw2_eyes import infer_full_eye_atlas
    model=model_factory()
    offset=struct.unpack_from('<I',model)[0]
    old_body_only=decode_native_atlas(model,offset,include_eye_frames=False)
    complete=decode_native_atlas(model,offset,include_eye_frames=True)
    assert infer_full_eye_atlas(model,old_body_only) is False
    assert infer_full_eye_atlas(model,complete) is True
    # The lower palette rows may be painted by an editor, but must never
    # affect which type of texture atlas the importer recognizes.
    patched=complete.copy()
    for y in range(224,256):
        for x in range(128):patched.putpixel((x,y),(255,255,255,255))
    assert infer_full_eye_atlas(model,patched) is True


def test_ambiguous_incomplete_eye_frames_are_not_silently_ignored():
    from dw2studio.core.dw2_eyes import infer_full_eye_atlas
    model=synthetic_greymon_eye_layout()
    offset=struct.unpack_from('<I',model)[0]
    full=decode_native_atlas(model,offset,include_eye_frames=True)
    # Crop the hidden frames so approximately half their visible pixels
    # disappear (e.g. an accidentally deleted alpha channel region).
    broken=full.copy()
    for y in range(0,48):
        for x in range(0,80):broken.putpixel((x,y),(0,0,0,0))
    with pytest.raises(ValueError,match='teilweise vorhanden'):
        infer_full_eye_atlas(model,broken)

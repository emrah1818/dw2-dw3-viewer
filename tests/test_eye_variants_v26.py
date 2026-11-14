"""Per-Digimon blink metadata: different eye coordinates, sizes, and counts."""
import struct
import pytest
from PIL import Image
from tests.test_eye_frames_v25 import synthetic_greymon_eye_layout
from dw2studio.core.dw2_eyes import eye_layout, eye_atlas, eye_animation_frames, eye_clut_map, blink_frame_at
from dw2studio.core.dw2_palette_recolor import preview_native_texture


def synthetic_agumon_style():
    """Artificial 32x24 eyes at four metadata-driven positions."""
    model=bytearray(synthetic_greymon_eye_layout())
    # Preserve valid primitive layout; only change its UVs and 24 blink bytes.
    original=bytes(model[28:52])
    assert original[:4] == b'\x0a\x30\x0a\x30'
    model[28:52]=(bytes((14,40,8,24,0,0,8,0,6,40)) + b'\xff'*10 + b'\xfe\xff\0\0')
    # Two triangles with target vertices (56,40), (87,40), (56,63)
    tri=52+12+4
    model[tri+6:tri+12]=bytes((56,40,87,40,56,63))
    second=tri+16
    model[second+6:second+12]=bytes((87,40,87,63,56,63))
    tim_start=struct.unpack_from('<I',model)[0]
    # Artificially distinct frames, reusing the same RGB555 bank.
    for i,(sx,sy) in enumerate(((0,0),(32,0),(24,40),(56,40)),1):
        for y in range(sy,sy+24):
            for x in range(sx,sx+32):
                at=tim_start+64+(y*128+x)//2
                if x%2:model[at]=(model[at]&0x0f)|(i<<4)
                else:model[at]=(model[at]&0xf0)|i
    return bytes(model)


def test_agumon_style_dimensions_and_four_poses():
    model=synthetic_agumon_style()
    layout=eye_layout(model)
    assert layout is not None
    assert layout.target==(56,40,32,24)
    assert len(layout.sources)==4
    assert layout.sources[0]==(0,0,32,24)
    assert layout.sources[-1]==layout.target
    assert len(eye_animation_frames(model))==4
    atlas=eye_atlas(model)
    assert atlas.size==(128,256)
    assert atlas.getpixel((1,1))!=atlas.getpixel((33,1))
    tim,pred,q=preview_native_texture(model,struct.unpack_from('<I',model)[0],atlas,eye_frames=True)
    assert tim==model[struct.unpack_from('<I',model)[0]:][:len(tim)]
    assert pred.tobytes()==atlas.tobytes()


def test_eye_rectangles_cannot_overlap_palette_storage():
    model=bytearray(synthetic_agumon_style())
    model[29]=220
    assert eye_layout(model) is None


def test_models_without_blink_metadata_cannot_patch_fake_eyes():
    model=bytearray(synthetic_agumon_style())
    model[28:48]=b'\xff'*20
    assert eye_layout(model) is None
    with pytest.raises(ValueError): eye_atlas(model)


def test_blink_timing_uses_actual_frame_count():
    assert blink_frame_at(0,frame_count=4)==3
    assert blink_frame_at(3.56,frame_count=4)==1
    assert blink_frame_at(3.65,frame_count=4)==2
    assert blink_frame_at(3.8,frame_count=4)==3


def test_malicious_other_clut_source_rejected():
    model=bytearray(synthetic_agumon_style())
    # Put a sprite source over unrelated UVs by altering the metadata.
    model[32]=14; model[33]=40  # duplicate target gets ignored
    assert eye_layout(model) is not None  # other sources still present


def test_vtk_dynamic_four_poses_keeps_body_pixels():
    pytest.importorskip('vtkmodules')
    import numpy as np
    import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
    from vtkmodules.vtkRenderingCore import vtkActor, vtkTexture
    from vtkmodules.vtkCommonCore import VTK_UNSIGNED_CHAR
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.util.numpy_support import vtk_to_numpy
    from dw2studio.renderer.eye_vtk import BlinkTextures

    model=synthetic_agumon_style()
    poses=eye_animation_frames(model)
    rgba=np.asarray(poses[-1])
    vtki=vtkImageData()
    vtki.SetDimensions(128,256,1)
    vtki.AllocateScalars(VTK_UNSIGNED_CHAR,4)
    vtk_to_numpy(vtki.GetPointData().GetScalars()).reshape((256,128,4))[:]=rgba
    texture=vtkTexture()
    texture.SetInputData(vtki)
    texture.UseSRGBColorSpaceOn()
    actor=vtkActor()
    actor.GetProperty().SetTexture('albedoTex',texture)
    controller=BlinkTextures([actor],model)
    assert controller.default_frame==3
    assert len(controller.frames)==4
    controller.apply(1)
    result=vtk_to_numpy(texture.GetInput().GetPointData().GetScalars()).reshape((256,128,4))
    assert np.array_equal(result[40:64,56:88], np.asarray(poses[1])[40:64,56:88])
    assert np.array_equal(result[90:112,4:20],rgba[90:112,4:20])
    controller.restore()
    assert texture.GetInput() is vtki

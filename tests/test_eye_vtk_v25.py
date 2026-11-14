"""Headless VTK PBR-albedo texture regression test; no Qt or OpenGL scene."""
import numpy as np
import pytest
from tests.test_eye_frames_v25 import synthetic_greymon_eye_layout
from dw2studio.core.dw2_eyes import eye_animation_frames

def test_vtk_blend_eyes_without_changing_other_texels():
    pytest.importorskip('vtkmodules')
    import vtkmodules.vtkRenderingOpenGL2  # register OpenGLProperty
    from vtkmodules.vtkRenderingCore import vtkActor, vtkTexture
    from vtkmodules.vtkCommonCore import VTK_UNSIGNED_CHAR
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.util.numpy_support import vtk_to_numpy
    from dw2studio.renderer.eye_vtk import BlinkTextures
    model=synthetic_greymon_eye_layout()
    frames=eye_animation_frames(model)
    original_image=np.asarray(frames[4])
    img=vtkImageData()
    img.SetDimensions(128,256,1)
    img.AllocateScalars(VTK_UNSIGNED_CHAR,4)
    vtk_to_numpy(img.GetPointData().GetScalars()).reshape((256,128,4))[:]=original_image
    tex=vtkTexture()
    tex.SetInputData(img)
    tex.UseSRGBColorSpaceOn()  # vtkOpenGLProperty checks color space
    actor=vtkActor()
    actor.GetProperty().SetTexture('albedoTex',tex)
    controller=BlinkTextures([actor],model)
    controller.apply(2)
    changed=vtk_to_numpy(tex.GetInput().GetPointData().GetScalars()).reshape((256,128,4))
    assert np.array_equal(changed[48:96,40:80],np.asarray(frames[2])[48:96,40:80])
    assert np.array_equal(changed[100:130,0:30],original_image[100:130,0:30])
    controller.restore()
    assert tex.GetInput() is img

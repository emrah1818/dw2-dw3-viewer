"""Update imported PBR base-color textures in place for native DW2 blinking.

No glTF mesh, skin, UV, or animation is changed. glTF has no built-in
KHR-independent material texture frame animation; animate the vtkTexture
objects on the GUI timer instead. Preserve the other image pixels exactly.
"""
from __future__ import annotations
import numpy as np
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.util.numpy_support import vtk_to_numpy
from dw2studio.core.dw2_eyes import eye_animation_frames, eye_layout


def _texture_for_actor(actor):
    prop=actor.GetProperty()
    for name in ('albedoTex','baseColorTex'):
        try:tex=prop.GetTexture(name)
        except (ValueError,TypeError):tex=None
        if tex is not None:return tex
    return actor.GetTexture()


class BlinkTextures:
    """Apply five eye poses to imported vtkTexture instances, then restore."""
    def __init__(self, actors, model, *, layout=None, frames=None):
        layout=layout or eye_layout(model)
        if layout is None:raise ValueError('Augenlayout nicht unterstützt.')
        self.rect=layout.target
        self.frames=frames if frames is not None else eye_animation_frames(model)
        self.default_frame=len(self.frames)-1
        self.items=[]
        visited=set()
        x,y,w,h=layout.target
        for actor in actors:
            texture=_texture_for_actor(actor)
            if texture is None or id(texture) in visited:continue
            visited.add(id(texture))
            original=texture.GetInput()
            if original is None or original.GetDimensions()[:2] != (128,256):continue
            scalars=original.GetPointData().GetScalars()
            if scalars is None or scalars.GetNumberOfComponents() not in (3,4):continue
            comps=scalars.GetNumberOfComponents()
            v=vtk_to_numpy(scalars).reshape((256,128,comps))
            source=np.asarray(self.frames[self.default_frame].convert('RGBA'))
            # Determine row direction from the original imported picture;
            # do not assume VTK's PNG reader convention on every platform.
            native=source[y:y+h,x:x+w,:3].astype(np.int16)
            direct=v[y:y+h,x:x+w,:3].astype(np.int16)
            flipped=v[256-(y+h):256-y,x:x+w,:3][::-1].astype(np.int16)
            err_direct=np.mean(np.abs(direct-native))
            err_flipped=np.mean(np.abs(flipped-native))
            flip=err_flipped<err_direct
            if min(err_direct,err_flipped)>45:
                # A custom/recolored atlas cannot safely receive original eyes.
                continue
            copy=vtkImageData()
            copy.DeepCopy(original)
            self.items.append((texture,original,copy,flip,comps))
        if not self.items:
            raise ValueError('Keine passende native Augen-Textur im VTK-Viewer gefunden.')
        self.current=None
        self.apply(self.default_frame)

    def apply(self, frame:int):
        if not 0<=frame<len(self.frames):raise IndexError('Augenframe unbekannt.')
        if frame==self.current:return
        x,y,w,h=self.rect
        patch=np.asarray(self.frames[frame].convert('RGBA'))[y:y+h,x:x+w]
        for texture,original,copy,flip,comps in self.items:
            # Start with the exact original image to avoid cumulative changes.
            dest=vtk_to_numpy(copy.GetPointData().GetScalars()).reshape((256,128,comps))
            src=vtk_to_numpy(original.GetPointData().GetScalars()).reshape((256,128,comps))
            dest[:]=src
            if flip:
                dest[256-(y+h):256-y,x:x+w,:]=patch[::-1,:,:comps]
            else:
                dest[y:y+h,x:x+w,:]=patch[:,:,:comps]
            copy.GetPointData().GetScalars().Modified()
            copy.Modified()
            texture.SetInputData(copy)
            texture.Modified()
        self.current=frame

    def restore(self):
        for texture,original,_,_,_ in self.items:
            texture.SetInputData(original)
            texture.Modified()
        self.current=None

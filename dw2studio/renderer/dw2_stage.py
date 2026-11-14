"""DW2-inspired blue technical backdrop and soft circular ground shadow.

Procedural artwork, not an extracted game texture. Y is up in VTK.
"""

def set_dw2_backdrop(renderer):
    from PIL import Image, ImageDraw
    import numpy as np
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.vtkRenderingCore import vtkTexture
    from vtkmodules.util.numpy_support import numpy_to_vtk
    w,h=1024,768
    im=Image.new('RGB',(w,h),(9,25,62));d=ImageDraw.Draw(im,'RGBA')
    # Blue grid from the DW2 status screens, with a transparent green panel.
    for x in range(0,w,44):
        d.line((x,0,x,h),fill=(23,111,194,85),width=2)
        d.line((x+2,0,x+2,h),fill=(61,170,225,24),width=1)
    for y in range(0,h,44):
        d.line((0,y,w,y),fill=(26,113,196,90),width=2)
    d.rectangle((90,95,w-90,h-95),fill=(5,108,67,85),outline=(63,214,152,145),width=3)
    for x in range(110,w-90,44):d.line((x,95,x,h-95),fill=(28,194,119,38),width=1)
    for y in range(110,h-95,44):d.line((90,y,w-90,y),fill=(28,194,119,38),width=1)
    arr=np.ascontiguousarray(np.flipud(np.asarray(im)))
    data=vtkImageData();data.SetDimensions(w,h,1)
    data.GetPointData().SetScalars(numpy_to_vtk(arr.reshape(-1,3),deep=True,array_type=3))
    texture=vtkTexture();texture.SetInputData(data);texture.InterpolateOn()
    renderer.SetBackgroundTexture(texture)
    renderer.TexturedBackgroundOn()
    return texture

def add_round_shadow(renderer,bounds):
    from vtkmodules.vtkFiltersSources import vtkDiskSource
    from vtkmodules.vtkRenderingCore import vtkActor,vtkPolyDataMapper
    if not bounds or bounds[1]<bounds[0] or bounds[3]<bounds[2]:return []
    x0,x1,y0,y1,z0,z1=bounds
    cx=(x0+x1)/2;cz=(z0+z1)/2
    radius=max(x1-x0,z1-z0,(y1-y0)*.3)*.65
    actors=[]
    # Concentric translucent disks approximate a soft round contact shadow.
    for i in range(6,0,-1):
        disk=vtkDiskSource();disk.SetInnerRadius(0);disk.SetOuterRadius(radius*i/6)
        disk.SetCircumferentialResolution(64);disk.SetRadialResolution(2)
        mapper=vtkPolyDataMapper();mapper.SetInputConnection(disk.GetOutputPort())
        actor=vtkActor();actor.SetMapper(mapper)
        actor.SetPosition(cx,y0-0.002*max(y1-y0,0.1)-i*1e-5,cz)
        actor.RotateX(-90)  # disk default is in XY, rotate into XZ
        actor.GetProperty().SetColor(.005,.012,.025)
        actor.GetProperty().SetOpacity(.065)
        actor.GetProperty().LightingOff()
        renderer.AddActor(actor);actors.append(actor)
    return actors

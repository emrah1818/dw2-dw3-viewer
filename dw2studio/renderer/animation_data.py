from pathlib import Path

def read_gltf_animation_durations(path):
 """Return each original glTF animation's duration separately (seconds).

 The DW2 converter exports multiple A-K animation clips into one glTF.
 Do not use a global maximum duration: that makes shorter clips freeze.
 """
 path=Path(path)
 if path.suffix.lower() not in ('.gltf','.glb'):return []
 try:
  from dw2studio.core.gltf_textures import document
  doc=document(path)
  accessors=doc.get('accessors',[])
  result=[]
  for animation in doc.get('animations',[]):
   ends=[]
   for sampler in animation.get('samplers',[]):
    idx=sampler.get('input')
    if not isinstance(idx,int) or idx<0 or idx>=len(accessors):continue
    accessor=accessors[idx]
    if accessor.get('max') and accessor.get('min'):
     ends.append(max(0.0,float(accessor['max'][0])-float(accessor['min'][0])))
    elif accessor.get('max'):
     ends.append(max(0.0,float(accessor['max'][0])))
   result.append(max(ends,default=0.0))
  return result
 except (OSError,ValueError,TypeError,IndexError,KeyError):return []


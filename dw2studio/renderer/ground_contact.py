"""Align imported DW2 model geometry to a stable Y=0 contact plane.

The VTK importer can apply animation transforms after loading. Re-evaluate the
visible model bounds after each animation update, excluding stage actors.
"""

def model_actors(renderer, excluded=()):
    excluded_ids = {id(a) for a in excluded}
    collection = renderer.GetActors()
    collection.InitTraversal()
    result = []
    for _ in range(collection.GetNumberOfItems()):
        actor = collection.GetNextActor()
        if actor is not None and id(actor) not in excluded_ids:
            result.append(actor)
    return result


def contact_bounds(actors):
    bounds = [a.GetBounds() for a in actors if a.GetVisibility()]
    bounds = [b for b in bounds if b and b[1] >= b[0] and b[3] >= b[2] and b[5] >= b[4]]
    if not bounds:
        return None
    return (min(b[0] for b in bounds), max(b[1] for b in bounds),
            min(b[2] for b in bounds), max(b[3] for b in bounds),
            min(b[4] for b in bounds), max(b[5] for b in bounds))


def align_ground(actors, ground_y=0.0, tolerance=1e-5):
    """Compatibility shim: NEVER translate individual rigged glTF actors.

    vtkGLTFImporter owns the per-node transforms and animation updates. Adding
    an offset to each actor corrupts the articulated model. The floor/shadow
    must instead follow the model's original bounds (see dw2_stage).
    """
    return 0.0

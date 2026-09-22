"""Build a lightweight Half Online village in the open level."""
import unreal

LEVEL = "/Game/HalfOpenWorld/Maps/L_World_V1"
MESH = "/Game/HalfOpenWorld/Geometry/SM_Block.SM_Block"
MATERIALS = {
    "stone": "/Game/HalfOpenWorld/Materials/M_Stone.M_Stone",
    "wood": "/Game/HalfOpenWorld/Materials/M_Wood.M_Wood",
    "road": "/Game/HalfOpenWorld/Materials/M_Road.M_Road",
    "roof": "/Game/HalfOpenWorld/Materials/M_Roof.M_Roof",
    "ground": "/Game/HalfOpenWorld/Materials/M_Ground.M_Ground",
}

def asset(path):
    value = unreal.load_asset(path)
    if not value:
        raise RuntimeError("Asset not found: " + path)
    return value

def block(location, scale, material, label):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(asset(MESH))
    actor.static_mesh_component.set_material(0, asset(MATERIALS[material]))
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor

def wall(x, y, z, length, height, material="stone"):
    block((x, y, z), (length, 1.0, height), material, "Village_House_Wall")

def build():
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if actor.get_actor_label().startswith("Village_"):
            unreal.EditorLevelLibrary.destroy_actor(actor)
    # Central fighting square.
    for x in range(-6, 7, 2):
        for y in range(-4, 5, 2):
            block((x * 180, y * 180, -80), (0.9, 0.9, 0.25), "road", "Village_Square")
    # Four small houses leave short lanes around the square.
    for x, y in [(-1500, -1100), (1500, -1100), (-1500, 1100), (1500, 1100)]:
        wall(x, y, 180, 3.0, 1.2)
        wall(x, y + 540, 180, 3.0, 1.2)
        wall(x - 540, y + 270, 180, 1.8, 1.2, "wood")
        wall(x + 540, y + 270, 180, 1.8, 1.2, "wood")
        block((x, y + 270, 480), (3.4, 2.0, 0.35), "roof", "Village_House_Roof")
    # Narrow lane and separate training yard.
    for y in range(-3, 4):
        block((2500, y * 240, -70), (0.6, 0.6, 0.22), "road", "Village_Narrow_Lane")
    for x in range(7, 12):
        for y in range(-2, 3):
            block((x * 180, y * 180, -80), (0.8, 0.8, 0.25), "ground", "Village_Training_Yard")
    unreal.EditorLevelLibrary.save_current_level()
    unreal.log("Half Online village built and saved")

build()

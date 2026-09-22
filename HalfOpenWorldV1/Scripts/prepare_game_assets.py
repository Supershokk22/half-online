"""Prepare self-contained, original map assets for the Half Sword test pak."""
import unreal

ROOT = "/Game/HalfOpenWorld"
MAP = ROOT + "/Maps/L_World_V1"
GEO = ROOT + "/Geometry"
MAT = ROOT + "/Materials"

for folder in (GEO, MAT):
    unreal.EditorAssetLibrary.make_directory(folder)

mesh_path = GEO + "/SM_Block"
if not unreal.EditorAssetLibrary.does_asset_exist(mesh_path):
    if not unreal.EditorAssetLibrary.duplicate_asset("/Engine/BasicShapes/Cube", mesh_path):
        raise RuntimeError("Could not duplicate block mesh")
mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
if not mesh or not unreal.EditorAssetLibrary.save_loaded_asset(mesh):
    raise RuntimeError("Could not save block mesh")

palette = {
    "M_Ground": (0.26, 0.30, 0.20),
    "M_Road": (0.38, 0.30, 0.21),
    "M_Stone": (0.42, 0.40, 0.35),
    "M_Wood": (0.29, 0.17, 0.09),
    "M_Roof": (0.16, 0.12, 0.10),
}
materials = {}
for name, color in palette.items():
    path = MAT + "/" + name
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT, unreal.Material, unreal.MaterialFactoryNew()
        )
        if not material:
            raise RuntimeError("Could not create " + path)
        node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -400, 0
        )
        node.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(
            node, "", unreal.MaterialProperty.MP_BASE_COLOR
        )
        unreal.MaterialEditingLibrary.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
    materials[name] = unreal.EditorAssetLibrary.load_asset(path)

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise RuntimeError("Map missing: " + MAP)

settings = world.get_world_settings()
override = settings.get_editor_property("default_game_mode")
unreal.log("[OWV1 Game Assets] map game mode override=" + str(override))
if override:
    raise RuntimeError("Map has a project-only GameMode override; clear it manually before packing")

count = 0
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("OWV1_") or not isinstance(actor, unreal.StaticMeshActor):
        continue
    if "Ground" in label:
        material = materials["M_Ground"]
    elif "Road" in label:
        material = materials["M_Road"]
    elif "Roof" in label:
        material = materials["M_Roof"]
    elif "Tavern" in label or "House" in label:
        material = materials["M_Wood"]
    else:
        material = materials["M_Stone"]
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(mesh)
    component.set_material(0, material)
    count += 1

unreal.EditorLevelLibrary.save_current_level()
unreal.log("[OWV1 Game Assets] prepared actors=" + str(count))

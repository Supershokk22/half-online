"""Run with UE 5.4: UnrealEditor-Cmd.exe HalfOpenWorldV1.uproject -run=pythonscript -script=..."""
import unreal

ROOT = "/Game/HalfOpenWorld"
MAPS = ROOT + "/Maps"
UI = ROOT + "/UI"


def log(message):
    unreal.log("[HalfOpenWorldV1] " + message)


def asset(path):
    result = unreal.EditorAssetLibrary.load_asset(path)
    if not result:
        raise RuntimeError("Asset do Engine ausente: " + path)
    return result


def make_actor(label, cls, location, scale=(1, 1, 1), rotation=(0, 0, 0)):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        cls,
        unreal.Vector(*location),
        unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]),
    )
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor


def cube(label, location, scale, material=None):
    actor = make_actor(label, unreal.StaticMeshActor, location, scale)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(asset("/Engine/BasicShapes/Cube.Cube"))
    if material:
        component.set_material(0, material)
    return actor


def save_level():
    unreal.EditorLevelLibrary.save_current_level()


def open_or_create_level(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorLoadingAndSavingUtils.load_map(path)
        return False
    if not unreal.EditorLevelLibrary.new_level(path):
        raise RuntimeError("Nao foi possivel criar " + path)
    return True


def clear_owv1_actors():
    removed = 0
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label().startswith("OWV1_"):
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed += 1
    if removed:
        log("Atores OWV1 antigos removidos: " + str(removed))


def basic_lighting():
    sun = make_actor("OWV1_Sun", unreal.DirectionalLight, (0, 0, 1200), rotation=(-42, 25, 0))
    sun_light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sun_light.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    sun_light.set_editor_property("atmosphere_sun_light", True)
    sun_light.set_intensity(10)
    sky = make_actor("OWV1_SkyLight", unreal.SkyLight, (0, 0, 700))
    sky_light = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_light.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    sky_light.set_editor_property("real_time_capture", True)
    make_actor("OWV1_Atmosphere", unreal.SkyAtmosphere, (0, 0, 0))
    make_actor("OWV1_Fog", unreal.ExponentialHeightFog, (0, 0, 0))


def build_menu_level():
    path = MAPS + "/L_Menu_V1"
    open_or_create_level(path)
    clear_owv1_actors()
    dark = asset("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")
    basic_lighting()
    cube("OWV1_MenuFloor", (0, 0, -50), (24, 24, 1), dark)
    cube("OWV1_MenuBackdrop", (750, 0, 450), (1, 24, 10), dark)
    make_actor("OWV1_MenuCamera", unreal.CameraActor, (-800, 0, 300), rotation=(0, 0, 0))
    save_level()
    log("Menu level: " + path)


def build_world_level():
    path = MAPS + "/L_World_V1"
    open_or_create_level(path)
    clear_owv1_actors()
    basic_lighting()
    ground = asset("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")
    cube("OWV1_Ground_Valley", (0, 0, -75), (82, 82, 1.5), ground)
    cube("OWV1_Ground_NorthRise", (0, 4700, 35), (82, 18, 2.2), ground)
    cube("OWV1_Ground_SouthWoods", (0, -4700, 25), (82, 18, 2.0), ground)
    cube("OWV1_Road_Main_West", (-2300, 0, 8), (38, 4, 0.15))
    cube("OWV1_Road_Main_East", (2300, 0, 8), (38, 4, 0.15))
    cube("OWV1_Road_North", (0, 1700, 12), (4, 34, 0.15))
    cube("OWV1_Road_South", (0, -1700, 12), (4, 34, 0.15))
    cube("OWV1_Hub_Plaza", (0, 0, 24), (12, 12, 0.4))
    cube("OWV1_Hub_Plaza_Ring_N", (0, 620, 55), (13, 0.7, 0.8))
    cube("OWV1_Hub_Plaza_Ring_S", (0, -620, 55), (13, 0.7, 0.8))
    cube("OWV1_Hub_Plaza_Ring_E", (620, 0, 55), (0.7, 13, 0.8))
    cube("OWV1_Hub_Plaza_Ring_W", (-620, 0, 55), (0.7, 13, 0.8))

    cube("OWV1_Tavern_Floor", (950, 1050, 44), (10, 8, 0.8))
    cube("OWV1_Tavern_NorthWall", (950, 1450, 245), (10, 0.5, 4.0))
    cube("OWV1_Tavern_SouthWall", (950, 650, 245), (10, 0.5, 4.0))
    cube("OWV1_Tavern_WestWall", (450, 1050, 245), (0.5, 8, 4.0))
    cube("OWV1_Tavern_EastWall", (1450, 1050, 245), (0.5, 8, 4.0))
    cube("OWV1_Tavern_Roof", (950, 1050, 500), (11, 9, 0.5))
    cube("OWV1_Tavern_Sign", (420, 1050, 360), (0.25, 2.2, 1.0))

    for index, pos in enumerate([(-1500, 1350), (-2100, 900), (-2550, 1550), (-1300, -1450), (-2200, -1050), (1700, -1300), (2350, -800), (2600, -1650)]):
        x, y = pos
        cube("OWV1_House_%02d_Base" % index, (x, y, 175), (4.8, 4.8, 3.4))
        cube("OWV1_House_%02d_Roof" % index, (x, y, 380), (5.4, 5.4, 0.7))

    for index, x in enumerate((-900, -300, 300, 900)):
        cube("OWV1_Market_Stall_%02d" % index, (x, -850, 95), (3.0, 1.4, 1.1))
        cube("OWV1_Market_Canopy_%02d" % index, (x, -850, 205), (3.4, 1.8, 0.25))

    cube("OWV1_Arena_Pit", (-900, 2350, 10), (11, 11, 0.25))
    for index, (x, y, sx, sy) in enumerate([(-900, 2950, 0.7, 12), (-900, 1750, 0.7, 12), (-1500, 2350, 12, 0.7), (-300, 2350, 12, 0.7)]):
        cube("OWV1_Arena_Wall_%02d" % index, (x, y, 130), (sx, sy, 2.2))

    for index, (x, y) in enumerate([(-3650, 0), (3650, 0), (0, -3650), (0, 3650)]):
        cube("OWV1_Gate_%02d_L" % index, (x - (0 if x else 350), y - (350 if x else 0), 245), (1.1, 1.1, 4.9))
        cube("OWV1_Gate_%02d_R" % index, (x + (0 if x else 350), y + (350 if x else 0), 245), (1.1, 1.1, 4.9))
        cube("OWV1_Gate_%02d_Beam" % index, (x, y, 520), (1.1 if x else 8.0, 8.0 if x else 1.1, 0.8))

    for index, (x, y, sx, sy) in enumerate([(-4300, 2100, 7, 18), (4300, 2300, 7, 18), (-4100, -2500, 8, 16), (4100, -2300, 8, 16), (0, 5200, 70, 4), (0, -5200, 70, 4)]):
        cube("OWV1_Cliff_Block_%02d" % index, (x, y, 250), (sx, sy, 5.0))

    for index, (x, y) in enumerate([(-600, -2850), (-1200, -3300), (-1800, -2750), (600, -3000), (1300, -3400), (2100, -2850)]):
        cube("OWV1_Tree_%02d_Trunk" % index, (x, y, 190), (0.55, 0.55, 3.8))
        cube("OWV1_Tree_%02d_Crown" % index, (x, y, 470), (2.0, 2.0, 1.8))

    cube("OWV1_Lookout_Tower_Base", (3100, 2100, 220), (3.0, 3.0, 4.4))
    cube("OWV1_Lookout_Tower_Top", (3100, 2100, 500), (4.2, 4.2, 0.7))
    cube("OWV1_SafeCamp_FirePit", (-250, -1850, 60), (1.5, 1.5, 0.35))
    cube("OWV1_SafeCamp_Bench_A", (-550, -1850, 95), (2.2, 0.45, 0.45))
    cube("OWV1_SafeCamp_Bench_B", (50, -1850, 95), (2.2, 0.45, 0.45))

    start = make_actor("OWV1_PlayerStart_Safe", unreal.PlayerStart, (0, 0, 180), rotation=(0, 0, 0))
    start.set_folder_path("HalfOpenWorld/Spawn")
    for name, pos in [
        ("Tavern", (950, 1050, 180)),
        ("Village", (-1800, 1250, 180)),
        ("Arena", (-900, 2350, 180)),
        ("Market", (0, -850, 180)),
        ("RoadEast", (3400, 0, 180)),
        ("RoadWest", (-3400, 0, 180)),
        ("ForestFuture", (0, -3200, 180)),
        ("Lookout", (3100, 2100, 560)),
    ]:
        point = make_actor("OWV1_POI_" + name, unreal.TargetPoint, pos)
        point.set_folder_path("HalfOpenWorld/POI")
    save_level()
    log("Editable world: " + path)


for folder in (ROOT, MAPS, UI):
    unreal.EditorAssetLibrary.make_directory(folder)
build_menu_level()
build_world_level()
log("Mapas V1 concluidos; widget gerado pelo commandlet C++ separado")

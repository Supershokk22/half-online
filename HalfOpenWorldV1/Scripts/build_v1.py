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


def new_level(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        log("Mapa existente preservado: " + path)
        unreal.EditorLoadingAndSavingUtils.load_map(path)
        return False
    if not unreal.EditorLevelLibrary.new_level(path):
        raise RuntimeError("Nao foi possivel criar " + path)
    return True


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
    if not new_level(path):
        return
    dark = asset("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")
    basic_lighting()
    cube("OWV1_MenuFloor", (0, 0, -50), (24, 24, 1), dark)
    cube("OWV1_MenuBackdrop", (750, 0, 450), (1, 24, 10), dark)
    make_actor("OWV1_MenuCamera", unreal.CameraActor, (-800, 0, 300), rotation=(0, 0, 0))
    save_level()
    log("Menu level: " + path)


def build_world_level():
    path = MAPS + "/L_World_V1"
    if not new_level(path):
        return
    basic_lighting()
    ground = asset("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")
    cube("OWV1_Ground_Valley", (0, 0, -75), (70, 70, 1.5), ground)
    cube("OWV1_Road_Main", (0, 0, 5), (50, 4, 0.15))
    cube("OWV1_Hub_Plaza", (0, 0, 20), (9, 9, 0.4))
    cube("OWV1_Tavern_Floor", (700, 900, 40), (9, 7, 0.8))
    cube("OWV1_Tavern_NorthWall", (700, 1250, 230), (9, 0.5, 3.8))
    cube("OWV1_Tavern_SouthWall", (700, 550, 230), (9, 0.5, 3.8))
    cube("OWV1_Tavern_WestWall", (250, 900, 230), (0.5, 7, 3.8))
    cube("OWV1_Tavern_EastWall", (1150, 900, 230), (0.5, 7, 3.8))
    cube("OWV1_Tavern_Roof", (700, 900, 460), (10, 8, 0.5))
    for side in (-1, 1):
        for index in range(4):
            x = -1600 + index * 900
            y = side * (1300 + (index % 2) * 350)
            cube("OWV1_House_%s_%s" % (side, index), (x, y, 170), (5, 5, 3.4))
    for x in (-2800, 2800):
        cube("OWV1_RoadGate_%s_L" % x, (x, -350, 225), (1, 1, 4.5))
        cube("OWV1_RoadGate_%s_R" % x, (x, 350, 225), (1, 1, 4.5))
        cube("OWV1_RoadGate_%s_Beam" % x, (x, 0, 475), (1, 8, 0.7))
    start = make_actor("OWV1_PlayerStart_Safe", unreal.PlayerStart, (0, 0, 180), rotation=(0, 0, 0))
    start.set_folder_path("HalfOpenWorld/Spawn")
    for name, pos in [
        ("Tavern", (700, 900, 180)),
        ("Village", (-1200, 1300, 180)),
        ("RoadEast", (2600, 0, 180)),
        ("RoadWest", (-2600, 0, 180)),
        ("ForestFuture", (0, -2600, 180)),
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

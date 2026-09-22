"""Repair existing V1 maps without replacing geometry or user edits.

Run only after closing the GUI Editor:
UnrealEditor-Cmd.exe HalfOpenWorldV1.uproject -run=pythonscript -script=Scripts/repair_v1_lighting.py
"""
import unreal


def repair(path):
    world = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not world:
        raise RuntimeError("Could not load " + path)

    found_sun = False
    found_sky = False
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor.get_actor_label()
        if label == "OWV1_Sun":
            light = actor.get_component_by_class(unreal.DirectionalLightComponent)
            if not light:
                raise RuntimeError("DirectionalLightComponent missing in " + path)
            actor.set_actor_rotation(unreal.Rotator(pitch=-42, yaw=25, roll=0), False)
            light.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            light.set_editor_property("atmosphere_sun_light", True)
            light.set_intensity(10)
            found_sun = True
        elif label == "OWV1_SkyLight":
            light = actor.get_component_by_class(unreal.SkyLightComponent)
            if not light:
                raise RuntimeError("SkyLightComponent missing in " + path)
            light.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            light.set_editor_property("real_time_capture", True)
            found_sky = True

    if not found_sun or not found_sky:
        raise RuntimeError("Expected lights missing in " + path)
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Could not save " + path)
    unreal.log("[HalfOpenWorldV1] Dynamic lighting repaired: " + path)


for map_name in ("L_Menu_V1", "L_World_V1"):
    repair("/Game/HalfOpenWorld/Maps/" + map_name)

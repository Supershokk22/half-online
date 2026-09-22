"""Read-only diagnostic for the V1 map. Does not save or change assets."""
import unreal

path = "/Game/HalfOpenWorld/Maps/L_World_V1"
world = unreal.EditorLoadingAndSavingUtils.load_map(path)
if not world:
    raise RuntimeError("Could not load " + path)

actors = unreal.EditorLevelLibrary.get_all_level_actors()
unreal.log("[OWV1 Inspect] actor_count=" + str(len(actors)))
for actor in actors:
    name = actor.get_actor_label()
    if name in ("OWV1_Sun", "OWV1_SkyLight"):
        component = actor.get_component_by_class(
            unreal.DirectionalLightComponent if name == "OWV1_Sun" else unreal.SkyLightComponent
        )
        properties = ["mobility", "intensity", "visible", "affects_world"]
        properties += ["atmosphere_sun_light"] if name == "OWV1_Sun" else ["real_time_capture"]
        values = {p: str(component.get_editor_property(p)) for p in properties}
        unreal.log("[OWV1 Inspect] %s %s rot=%s" % (name, values, actor.get_actor_rotation()))
    elif name in ("OWV1_Ground_Valley", "OWV1_Road_Main", "OWV1_Hub_Plaza"):
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        material = component.get_material(0)
        unreal.log("[OWV1 Inspect] %s material=%s location=%s scale=%s" % (
            name, material.get_path_name() if material else "None", actor.get_actor_location(), actor.get_actor_scale3d()
        ))

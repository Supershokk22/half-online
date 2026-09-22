using UnrealBuildTool;

public class HalfOpenWorldV1EditorTarget : TargetRules
{
    public HalfOpenWorldV1EditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_4;
        bOverrideBuildEnvironment = true;
        AdditionalCompilerArguments = "/wd4668 /wd4067";
        ExtraModuleNames.Add("HalfOpenWorldV1");
        ExtraModuleNames.Add("HalfOpenWorldV1Editor");
    }
}

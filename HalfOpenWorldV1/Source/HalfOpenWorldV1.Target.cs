using UnrealBuildTool;

public class HalfOpenWorldV1Target : TargetRules
{
    public HalfOpenWorldV1Target(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_4;
        bOverrideBuildEnvironment = true;
        AdditionalCompilerArguments = "/wd4668 /wd4067";
        ExtraModuleNames.Add("HalfOpenWorldV1");
    }
}

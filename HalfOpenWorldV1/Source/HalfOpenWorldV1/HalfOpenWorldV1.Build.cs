using UnrealBuildTool;

public class HalfOpenWorldV1 : ModuleRules
{
    public HalfOpenWorldV1(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "Slate", "SlateCore" });
    }
}

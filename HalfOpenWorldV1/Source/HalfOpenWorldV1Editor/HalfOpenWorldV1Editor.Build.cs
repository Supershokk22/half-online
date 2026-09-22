using UnrealBuildTool;

public class HalfOpenWorldV1Editor : ModuleRules
{
    public HalfOpenWorldV1Editor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PrivateDependencyModuleNames.AddRange(new[]
        {
            "Core", "CoreUObject", "Engine", "UMG", "UMGEditor", "UnrealEd",
            "AssetTools", "Kismet", "KismetCompiler", "Slate", "SlateCore",
            "EditorScriptingUtilities"
        });
    }
}

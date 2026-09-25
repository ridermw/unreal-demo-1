using UnrealBuildTool;

public class PlatformNine : ModuleRules
{
    public PlatformNine(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] {
            "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput"
        });
        PrivateDependencyModuleNames.AddRange(new[] { "Json", "Slate", "SlateCore" });
    }
}

using UnrealBuildTool;

public class PlatformNineEditorTarget : TargetRules
{
    public PlatformNineEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
        ExtraModuleNames.Add("PlatformNine");
    }
}

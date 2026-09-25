"""Bind screenshots and timings to the saved project state they actually measured."""

import hashlib
import configparser
from pathlib import Path

QUALITY_SETTINGS={f"sg.{name}Quality":2 for name in (
    "ViewDistance","AntiAliasing","Shadow","GlobalIllumination","Reflection",
    "PostProcess","Texture","Effects","Foliage","Shading")}


def assert_clean_editor(unreal):
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if levels.is_in_play_in_editor():
        raise RuntimeError("End PIE before capturing the saved editor scene")
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world is None or world.get_path_name().split(".")[0]!="/Game/Platform/Maps/HiddenPlatform":
        raise RuntimeError("Expected the saved HiddenPlatform map in the editor")
    dirty=list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
    dirty+=list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
    names=[package.get_path_name() for package in dirty
           if package.get_path_name().startswith("/Game/Platform/")]
    if names:
        raise RuntimeError("Save platform changes before capturing: "+", ".join(names))


def pacing_defaults(root):
    config=configparser.ConfigParser(strict=False)
    with (Path(root)/"Config/DefaultEngine.ini").open() as source:
        config.read_file(source)
    cap=config.getfloat("SystemSettings","t.MaxFPS")
    lag=config.getint("SystemSettings","r.OneFrameThreadLag")
    if cap<0 or lag not in (0,1):
        raise ValueError("Project frame cap/thread-lag settings are invalid")
    return cap,bool(lag)


def scene_identity(root):
    root=Path(root)
    content=root/"Content/Platform"
    packages=sorted(path for path in content.rglob("*") if path.suffix in (".uasset",".umap"))
    map_file=content/"Maps/HiddenPlatform.umap"
    if not packages or not map_file.is_file():
        raise RuntimeError("Saved HiddenPlatform packages are required for evidence")
    files=packages+[root/"PlatformNine.uproject",root/"Config/DefaultEngine.ini",root/"Config/DefaultInput.ini"]
    digest=hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        with path.open("rb") as source:
            while chunk:=source.read(1024*1024):
                digest.update(chunk)
    return {"sha256":digest.hexdigest(),"package_count":len(packages),
            "map_sha256":hashlib.sha256(map_file.read_bytes()).hexdigest()}

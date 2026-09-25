"""Build, cook and archive the Apple Silicon walkthrough without deleting prior builds."""

import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_ENGINE=Path("/Users/Shared/Epic Games/UE_5.8")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=["Development","Shipping"],default="Shipping")
    args=parser.parse_args()
    engine=Path(os.environ.get("UNREAL_ENGINE_ROOT",str(DEFAULT_ENGINE)))
    uat=engine/"Engine/Build/BatchFiles/RunUAT.sh"
    if not uat.is_file():
        raise FileNotFoundError(f"Unreal Automation Tool missing: {uat}")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    archive=ROOT/"Builds"/f"PlatformNine-Mac-{args.configuration}-{stamp}"
    archive.mkdir(parents=True,exist_ok=False)
    work=ROOT/".dream-loop"
    work.mkdir(exist_ok=True)
    log=work/f"package-mac-{stamp}.log"
    report={"status":"running","started_utc":datetime.now(timezone.utc).isoformat(),
            "platform":"Mac","architecture":"arm64","configuration":args.configuration,
            "archive":str(archive.relative_to(ROOT)),"map":"/Game/Platform/Maps/HiddenPlatform",
            "log":str(log.relative_to(ROOT)),"runtime_verified":False}
    destination=ROOT/"Evidence/app-package-report.json"
    destination.write_text(json.dumps(report,indent=2)+"\n")
    command=[str(uat),"BuildCookRun",f"-project={ROOT/'PlatformNine.uproject'}",
             "-noP4","-platform=Mac","-architecture=arm64",f"-clientconfig={args.configuration}",
             "-target=PlatformNine","-build","-cook","-map=/Game/Platform/Maps/HiddenPlatform",
             "-stage","-pak","-iostore","-compressed","-package","-createappbundle",
             "-archive",f"-archivedirectory={archive}",
             "-unattended","-utf8output"]
    try:
        with log.open("w") as output:
            subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,check=True)
        text=log.read_text(errors="replace")
        if re.search(r"BUILD FAILED|AutomationTool exiting with ExitCode=[1-9]|LogCook: Error:",text):
            raise RuntimeError("Packaging log contains a build/cook failure")
        apps=[path for path in archive.rglob("*.app") if "CrashReportClient" not in path.name]
        apps=[path for path in apps if (path/"Contents/MacOS").is_dir()]
        if len(apps)!=1:
            raise RuntimeError(f"Expected one application bundle, found {len(apps)}")
        executables=[path for path in (apps[0]/"Contents/MacOS").iterdir()
                     if path.is_file() and os.access(path,os.X_OK)]
        if len(executables)!=1:
            raise RuntimeError("Cannot identify the packaged game executable")
        paks=list(archive.rglob("*.pak"))+list(archive.rglob("*.utoc"))
        if not paks:
            raise RuntimeError("No cooked content containers were archived")
        report.update(status="packaged-not-yet-run",app=str(apps[0].relative_to(ROOT)),
                      executable=str(executables[0].relative_to(ROOT)),cooked_container_count=len(paks),
                      completed_utc=datetime.now(timezone.utc).isoformat())
        destination.write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2))
    except Exception as error:
        report.update(status="failed",error=str(error))
        destination.write_text(json.dumps(report,indent=2)+"\n")
        print(f"Packaging failed; full log: {log}")
        if log.exists():
            print("\n".join(log.read_text(errors="replace").splitlines()[-50:]))
        raise


if __name__=="__main__":
    main()

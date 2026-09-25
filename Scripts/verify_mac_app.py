"""Run the archived Mac app and require fresh runtime/control/screenshot evidence."""

from datetime import datetime,timezone
import json
from pathlib import Path
import struct
import subprocess
import plistlib
import shutil

ROOT=Path(__file__).resolve().parents[1]


def main():
    package_path=ROOT/"Evidence/app-package-report.json"
    package=json.loads(package_path.read_text())
    app=ROOT/package["app"]
    executable=ROOT/package["executable"]
    if not app.is_dir() or not executable.is_file():
        raise RuntimeError("A complete packaged application is required")
    subprocess.run(["codesign","--verify","--deep","--strict",str(app)],check=True)
    stamp="packaged-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    evidence=ROOT/"Evidence/App"/stamp
    if evidence.exists():
        raise RuntimeError("Verification destination already exists")
    bundle=plistlib.loads((app/"Contents/Info.plist").read_bytes())["CFBundleIdentifier"]
    run=Path.home()/"Library/Containers"/bundle/"Data/Library/Caches/PlatformNineVerification"/stamp
    run.mkdir(parents=True,exist_ok=False)
    stdout=ROOT/".dream-loop"/(stamp+"-stdout.log")
    command=[str(executable),"-RenderOffscreen","-unattended","-nosplash","-nosound",
             "-ResX=1536","-ResY=864","-ForceRes","-ViewerSmokeTest",
             "-ViewerEvidenceDir="+str(run)]
    with stdout.open("w") as output:
        result=subprocess.run(command,cwd=executable.parent,stdout=output,stderr=subprocess.STDOUT,timeout=120)
    report_path=run/"report.json"
    if result.returncode or not report_path.is_file():
        raise RuntimeError(f"Packaged runtime failed: exit={result.returncode}; output={stdout}")
    report=json.loads(report_path.read_text())
    checks=("preset_key_verified","movement_key_verified","look_axis_verified","menu_key_verified")
    if report.get("status")!="success" or not all(report.get(key) is True for key in checks):
        raise RuntimeError(f"Packaged controls did not pass: {report}")
    if report.get("map")!="HiddenPlatform" or report.get("view_count")!=5:
        raise RuntimeError("Packaged app did not load the expected scene and views")
    for name in ("01-main.png","02-locomotive.png","03-explored.png"):
        data=(run/name).read_bytes()
        if data[:8]!=b"\x89PNG\r\n\x1a\n" or struct.unpack(">II",data[16:24])!=(1536,864):
            raise RuntimeError(f"Invalid packaged screenshot: {name}")
    shutil.copytree(run,evidence)
    package.update(status="packaged-runtime-verified",runtime_verified=True,
                   verification_report=str((evidence/"report.json").relative_to(ROOT)),
                   verification_source="App-sandbox output copied unchanged into repository evidence",
                   verified_utc=datetime.now(timezone.utc).isoformat(),
                   signing="Ad-hoc signed for local running; not Apple-notarized",
                   manual_ui_check="Mouse hit boxes and fullscreen remain manual checks")
    package_path.write_text(json.dumps(package,indent=2)+"\n")
    print(json.dumps(package,indent=2))


if __name__=="__main__":
    main()

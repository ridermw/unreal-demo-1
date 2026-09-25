"""Run a checked Unreal Python commandlet; a zero exit alone is not success."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENGINE = "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["import", "scene", "verify"])
    args = parser.parse_args()
    work = ROOT / ".dream-loop"
    work.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    log = work / f"{args.stage}-{stamp}.log"
    report = ROOT / "Evidence" / f"{args.stage}-report.json"
    if report.exists():
        (work / f"{args.stage}-report-before-{stamp}.json").write_bytes(report.read_bytes())
    started = datetime.now(timezone.utc)
    command = [
        os.environ.get("UNREAL_EDITOR_CMD", DEFAULT_ENGINE), str(ROOT / "PlatformNine.uproject"),
        "-run=pythonscript",
        f"-script={ROOT / 'Scripts/build_unreal.py'} --stage {args.stage}",
        "-unattended", "-nullrhi", "-nosplash", "-stdout", f"-abslog={log}",
    ]
    with (work / f"{args.stage}-{stamp}-stdout.log").open("w") as stdout:
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=subprocess.STDOUT)
    text = log.read_text() if log.exists() else ""
    failures = [line for line in text.splitlines()
                if re.search(r"LogPython: Error:|LogPythonScriptCommandlet: Error:|Fatal error:|Assertion failed:", line)]
    data = json.loads(report.read_text()) if report.exists() else {}
    fresh = data.get("utc") and datetime.fromisoformat(data["utc"]) >= started
    if result.returncode or failures or data.get("status") != "success" or not fresh:
        raise RuntimeError(
            f"Unreal {args.stage} failed: exit={result.returncode}, "
            f"status={data.get('status')}, fresh_report={bool(fresh)}; log={log}\n"
            + "\n".join(failures[-15:]))
    print(f"PASS {args.stage}: {report.relative_to(ROOT)}; log={log.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""Profile rendered standalone game frames with Unreal CSV; discard startup frames."""

import csv
from datetime import datetime, timezone
import io
import argparse
import json
import os
from pathlib import Path
import re
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def summarize(rows):
    header = rows[-2] if rows[-2] and rows[-2][0] == "EVENTS" else rows[0]
    frame_index = header.index("FrameTime")
    frames = [row for row in rows[1:-2] if len(row) > frame_index
              and row[frame_index].replace(".", "", 1).isdigit()]
    if len(frames) < 720:
        raise RuntimeError(f"Expected 720 actual captured frames, got {len(frames)}")
    samples = frames[360:720]
    values = [float(row[frame_index]) for row in samples]
    if min(values) <= 0:
        raise RuntimeError("Invalid frame duration in engine CSV")
    median = statistics.median(values)
    p95 = sorted(values)[int(len(values) * .95) - 1]
    return {"median_fps": 1000 / median, "average_fps": 1000 / statistics.mean(values),
            "median_frame_ms": median, "p95_frame_ms": p95,
            "meets_target": median <= 1000/30 and p95 <= 50}, header, samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing-log", type=Path)
    args = parser.parse_args()
    work = ROOT / ".dream-loop"
    work.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    log = args.existing_log.resolve() if args.existing_log else work / f"profile-{stamp}.log"
    quality = ",".join(f"sg.{name}Quality 2" for name in (
        "ViewDistance", "AntiAliasing", "Shadow", "GlobalIllumination", "Reflection",
        "PostProcess", "Texture", "Effects", "Foliage", "Shading"))
    command = [
        os.environ.get("UNREAL_EDITOR_CMD", "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"),
        str(ROOT / "PlatformNine.uproject"), "/Game/Platform/Maps/HiddenPlatform",
        "-game", "-RenderOffscreen", "-unattended", "-nosplash", "-nosound", "-novsync",
        "-ResX=1536", "-ResY=864", "-ForceRes", "-csvCaptureFrames=720",
        "-csvGpuStats", "-ExitAfterCsvProfiling",
        f"-ExecCmds={quality},r.ScreenPercentage 100,t.MaxFPS 0",
        f"-abslog={log}", "-stdout",
    ]
    report = {"status": "running", "utc": datetime.now(timezone.utc).isoformat(),
              "mode": "standalone game, Metal SM6 offscreen rendering; not NullRHI",
              "resolution": [1536, 864], "screen_percentage": 100, "quality": "High (all sg.* = 2)",
              "warmup_frames": 360, "measurement_frames": 360,
              "target": {"median_fps_minimum": 30, "p95_frame_ms_maximum": 50},
              "log": str(log.relative_to(ROOT))}
    destination = ROOT / "Evidence/performance-report.json"
    if destination.exists():
        (work / f"performance-before-{stamp}.json").write_bytes(destination.read_bytes())
    destination.write_text(json.dumps(report, indent=2) + "\n")
    try:
        if not args.existing_log:
            with (work / f"profile-{stamp}-stdout.log").open("w") as output:
                subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                               timeout=300, check=True)
        text = log.read_text()
        if re.search(r"Fatal error:|Assertion failed:|Failed to compile Material", text):
            raise RuntimeError("Engine runtime or material compile failure; inspect profiling log")
        match = re.search(r"Writing CSV to file : (.+\.csv)", text)
        if not match:
            raise RuntimeError("Engine did not report a completed CSV capture")
        source = Path(match.group(1))
        if not source.is_absolute():
            engine_base = Path(command[0]).parent
            source = (engine_base / source).resolve()
        csv.field_size_limit(10_000_000)
        rows = list(csv.reader(io.StringIO(source.read_text())))
        metrics, header, samples = summarize(rows)
        metadata = rows[-1]
        for key, value in (("[systemresolution.resx]", "1536"), ("[systemresolution.resy]", "864")):
            if key not in metadata or metadata[metadata.index(key) + 1] != value:
                raise RuntimeError(f"Engine metadata does not confirm {key}={value}")
        columns = [key for key in ("FrameTime", "GameThreadTime", "RenderThreadTime",
                                  "GPUTime", "GPU/FrameTime", "RHIThreadTime") if key in header]
        temporary = work / f"frames-{stamp}.csv"
        with temporary.open("w") as output:
            writer = csv.writer(output, lineterminator="\n")
            writer.writerow(["MeasuredFrame", *columns])
            for index, row in enumerate(samples):
                writer.writerow([index, *[row[header.index(key)] if header.index(key) < len(row) else ""
                                          for key in columns]])
        temporary.replace(ROOT / "Evidence/performance-frames.csv")
        report.update(metrics, status="success", frame_source="Native Unreal CSV FrameTime",
                      device="Apple M4 Pro, 20 GPU cores, 48 GB",
                      engine="5.8.3", frame_evidence="Evidence/performance-frames.csv")
        destination.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    except Exception as error:
        report.update(status="failed", error=str(error))
        destination.write_text(json.dumps(report, indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()

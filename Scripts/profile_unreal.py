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
import hashlib
from evidence_identity import scene_identity, pacing_defaults, QUALITY_SETTINGS

ROOT = Path(__file__).resolve().parents[1]


def captured_pacing(text):
    values=confirmed_settings(text,("t.MaxFPS","r.OneFrameThreadLag"))
    return values["t.MaxFPS"],bool(values["r.OneFrameThreadLag"]) if values["r.OneFrameThreadLag"] is not None else None


def confirmed_settings(text,names):
    window=text.split("LogCsvProfiler: Display: Capture Stop requested",1)[0]
    result={}
    for name in names:
        matches=re.findall(r"\b"+re.escape(name)+r'\s*=\s*"?(-?\d+(?:\.\d+)?)"?',window)
        result[name]=float(matches[-1]) if matches else None
    return result


def finalized_identity(provenance,log_bytes,csv_bytes):
    if provenance.get("status")!="success":
        raise RuntimeError("Profile capture provenance is not finalized successfully")
    if (provenance.get("log_sha256")!=hashlib.sha256(log_bytes).hexdigest()
            or provenance.get("csv_sha256")!=hashlib.sha256(csv_bytes).hexdigest()):
        raise RuntimeError("Profile log or CSV differs from finalized provenance")
    if not provenance.get("scene_identity"):
        raise RuntimeError("Finalized profile lacks its captured scene identity")
    return provenance["scene_identity"]


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
    parser.add_argument("--frame-cap", type=float)
    parser.add_argument("--frame-lag", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--gpu-stats", action="store_true",
                        help="Enable detailed GPU instrumentation for diagnosis, not the default timing gate")
    args = parser.parse_args()
    if args.frame_cap is not None and args.frame_cap < 0:
        parser.error("--frame-cap must be nonnegative; zero means uncapped")
    default_cap,default_lag=pacing_defaults(ROOT)
    frame_cap=default_cap if args.frame_cap is None else args.frame_cap
    frame_lag=default_lag if args.frame_lag is None else args.frame_lag
    work = ROOT / ".dream-loop"
    work.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    log = args.existing_log.resolve() if args.existing_log else work / f"profile-{stamp}.log"
    quality = ",".join(f"{name} {value}" for name,value in QUALITY_SETTINGS.items())
    queries=",".join([*QUALITY_SETTINGS,"r.ScreenPercentage","t.MaxFPS","r.OneFrameThreadLag"])
    command = [
        os.environ.get("UNREAL_EDITOR_CMD", "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"),
        str(ROOT / "PlatformNine.uproject"), "/Game/Platform/Maps/HiddenPlatform",
        "-game", "-RenderOffscreen", "-unattended", "-nosplash", "-nosound", "-novsync",
        "-ResX=1536", "-ResY=864", "-ForceRes", "-csvCaptureFrames=720",
        "-ExitAfterCsvProfiling",
        f"-ExecCmds={quality},r.ScreenPercentage 100,t.MaxFPS {frame_cap:g},"
        f"r.OneFrameThreadLag {1 if frame_lag else 0},{queries}",
        f"-abslog={log}", "-stdout",
    ]
    if args.gpu_stats:
        command.append("-csvGpuStats")
    report = {"status": "running", "utc": datetime.now(timezone.utc).isoformat(),
              "mode": "standalone game, Metal SM6 offscreen rendering; not NullRHI",
              "view":"target","camera_label":"PN_TargetCamera","camera_fov":70,
              "resolution": [1536, 864], "screen_percentage": 100, "quality": "High (all sg.* = 2)",
              "frame_cap": None, "one_frame_thread_lag": None,
              "warmup_frames": 360, "measurement_frames": 360,
              "target": {"median_fps_minimum": 30, "p95_frame_ms_maximum": 50},
              "log": str(log.relative_to(ROOT))}
    destination = ROOT / "Evidence/performance-report.json"
    if destination.exists():
        (work / f"performance-before-{stamp}.json").write_bytes(destination.read_bytes())
    destination.write_text(json.dumps(report, indent=2) + "\n")
    try:
        identity_file=log.with_suffix(".scene.json")
        if not args.existing_log:
            identity=scene_identity(ROOT)
            provenance={"status":"pending","scene_identity":identity}
            identity_file.write_text(json.dumps(provenance,indent=2)+"\n")
        else:
            if not identity_file.exists():
                raise RuntimeError("Existing log lacks finalized capture provenance")
            provenance=json.loads(identity_file.read_text())
            if provenance.get("status")!="success":
                raise RuntimeError("Existing log belongs to a pending, failed or legacy unfinalized capture")
            identity=provenance.get("scene_identity")
        if not args.existing_log:
            with (work / f"profile-{stamp}-stdout.log").open("w") as output:
                subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                               timeout=300, check=True)
            if scene_identity(ROOT)!=identity:
                raise RuntimeError("Saved scene changed while performance was being captured")
        text = log.read_text()
        observed_cap, observed_lag = captured_pacing(text)
        expected=dict(QUALITY_SETTINGS,**{"r.ScreenPercentage":100})
        runtime=confirmed_settings(text,[*expected,"t.MaxFPS","r.OneFrameThreadLag"])
        if any(runtime[name]!=value for name,value in expected.items()):
            raise RuntimeError("Capture log does not confirm the requested High/100% rendering settings")
        if observed_cap is None or observed_lag is None:
            raise RuntimeError("Capture log lacks confirmed pacing readbacks")
        if not args.existing_log and (observed_cap!=frame_cap or observed_lag!=frame_lag):
            raise RuntimeError("Engine pacing readbacks differ from the requested capture conditions")
        if args.existing_log:
            if args.frame_cap is not None and args.frame_cap != observed_cap:
                raise RuntimeError("Requested frame cap conflicts with the existing captured log")
            if args.frame_lag is not None and args.frame_lag!=observed_lag:
                raise RuntimeError("Requested thread-lag setting conflicts with the existing captured log")
        report.update(frame_cap=observed_cap,one_frame_thread_lag=observed_lag,
                      pacing_source="Confirmed engine readbacks before capture stop",
                      runtime_settings=runtime,
                      detailed_gpu_instrumentation=bool(re.search(r"(?i)-csvGpuStats\b",text)))
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
        csv_bytes=source.read_bytes()
        log_bytes=log.read_bytes()
        if args.existing_log:
            identity=finalized_identity(provenance,log_bytes,csv_bytes)
        rows = list(csv.reader(io.StringIO(csv_bytes.decode())))
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
                      engine="5.8.3", frame_evidence="Evidence/performance-frames.csv",
                      scene_identity=identity,provenance_finalized=True)
        if not args.existing_log:
            provenance.update(status="success",log_sha256=hashlib.sha256(log_bytes).hexdigest(),
                              csv_sha256=hashlib.sha256(csv_bytes).hexdigest(),
                              runtime_settings=runtime,finished_utc=datetime.now(timezone.utc).isoformat())
            identity_file.write_text(json.dumps(provenance,indent=2)+"\n")
        destination.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    except Exception as error:
        if not args.existing_log and "identity_file" in locals():
            identity_file.write_text(json.dumps({"status":"failed","error":str(error)},indent=2)+"\n")
        report.update(status="failed", error=str(error))
        destination.write_text(json.dumps(report, indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()

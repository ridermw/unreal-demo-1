"""Generate explicit, resumable surface maps using only the installed mockui CLI."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import threading


ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / "Art/Textures"
WORK = ROOT / ".dream-loop/texture-generation"
STATE = WORK / "jobs.json"
LOCK = threading.Lock()
PROVENANCE_KEYS = ("rendered_at", "size", "quality", "model_name", "model_version",
                   "prompt_char_count", "prompt")


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    specs = json.loads((TEXTURES / "surfaces.json").read_text())
    jobs = json.loads(STATE.read_text()) if STATE.exists() else {}

    def persist():
        temporary = STATE.with_suffix(".tmp")
        temporary.write_text(json.dumps(jobs, indent=2) + "\n")
        temporary.replace(STATE)

    def generate(name, prompt, source=None):
        output = TEXTURES / (name + ".png")
        with LOCK:
            previous = jobs.get(name)
            if output.exists():
                if not output.with_suffix(".png.metadata.json").exists():
                    raise RuntimeError(f"Image lacks generation receipt: {output}")
                return output
            if previous:
                raise RuntimeError(f"Do not duplicate unresolved prior job {name}: {previous['status']}")
            model = "sunburst" if source else "flare"
            jobs[name] = {"status": "submitted", "model": model,
                          "started_utc": datetime.now(timezone.utc).isoformat(),
                          "output": str(output.relative_to(ROOT)), "prompt": prompt,
                          "request_id": None}
            persist()
        command = ["mockui", "edit", str(source)] if source else ["mockui", "render"]
        command += ["--prompt", prompt, "--output", str(output),
                    "--model", model, "--quality", "high", "--size", "1024x1024"]
        with (WORK / (name + ".log")).open("w") as log:
            result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        with LOCK:
            receipt = output.with_suffix(".png.metadata.json")
            succeeded = result.returncode == 0 and output.is_file() and receipt.is_file()
            jobs[name]["status"] = "completed" if succeeded else "failed-needs-reconciliation"
            jobs[name]["exit_code"] = result.returncode
            if succeeded:
                metadata = json.loads(receipt.read_text())
                receipt.write_text(json.dumps(
                    {key: metadata[key] for key in PROVENANCE_KEYS if key in metadata}, indent=2) + "\n")
                jobs[name]["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
            persist()
        if not succeeded:
            raise RuntimeError(f"mockui did not produce {name}; inspect {WORK / (name + '.log')}")
        print("GENERATED", name, model, flush=True)
        return output

    def surface(item):
        name, spec = item
        albedo = TEXTURES / (name + ".png")
        if not spec.get("existing"):
            albedo = generate(name,
                "A seamless tileable physically based game material BASE COLOR / ALBEDO texture. "
                "Perfectly orthographic flat square surface, edge to edge, uniform diffuse neutral lighting, "
                "no baked highlights or shadows, no perspective, no vignette, no text. "
                "Photoreal close material microdetail: " + spec["description"] + ".")
        if not albedo.is_file():
            raise FileNotFoundError(albedo)
        generate(name + "_normal",
            "Convert this exact surface into its corresponding seamless tangent-space NORMAL MAP for Unreal. "
            "Keep every feature in precisely the same pixel positions; do not invent a different arrangement. "
            "This is technical RGB normal data, not a color image: flat areas RGB (128,128,255), blue dominant, "
            "red/green encode surface slopes, DirectX Y orientation. Recess mortar, cracks or pores and give "
            "the material realistic subtle raised microdetail. No lighting, shadows, text or colored albedo. "
            "Do not exaggerate relief on metal, glass, leather or fabric.", albedo)
        generate(name + "_roughness",
            "Convert this exact material image into its precisely aligned seamless grayscale ROUGHNESS map "
            "for physically based Unreal shading. White means rough matte, black means glossy. "
            "Preserve feature positions. Use medium-dark values for polished metal or glass, medium values "
            "for worn leather/varnish, light grey for stone, brick, cloth, rust and dust; darker rubbed areas. "
            "Natural nuanced variation, no lighting, shadows, color, text, border or large invented stains. "
            "Material: " + spec["description"] + ".", albedo)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(surface, specs.items()))
    generate("steam",
        "A single photoreal soft white steam plume sprite for a real-time Victorian steam locomotive. "
        "Wispy turbulent translucent vapor rising vertically, fine feathery strands and soft curling eddies, "
        "thin at base, gently wider in upper half, diffuse cool white. Pure solid black background, "
        "all four image edges fully black with wide margins. No engine, no objects, no text, no border. "
        "Grayscale density sprite, not thick opaque smoke; smooth soft fade to black.")
    print("TEXTURE_SET_COMPLETE", len(jobs), flush=True)


if __name__ == "__main__":
    main()

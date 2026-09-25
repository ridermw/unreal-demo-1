"""Rectify the user-authorized target sign crop; no new image generation."""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "Art/Reference/target.png"
output = ROOT / "Art/Textures/sign_face.png"
box = (1013, 88, 1156, 227)
with Image.open(source) as image:
    face = image.crop(box).resize((512, 512), Image.Resampling.LANCZOS)
    face.save(output)
metadata = {
    "kind": "reference-derived-image-crop-not-new-generation",
    "source": "Art/Reference/target.png",
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "source_rectangle_pixels": box,
    "operation": "Crop the circular target sign face and rectify its elliptical extent to square UV space",
    "output_pixels": [512, 512],
    "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    "limitation": "The crop contains target lighting and perspective; rim and bracket remain real geometry.",
    "authorization": "User explicitly suggested cropping the target sign and using it on the Unreal sign.",
}
output.with_suffix(".png.provenance.json").write_text(json.dumps(metadata, indent=2) + "\n")
print("SIGN_REFERENCE_EXTRACTED", output)

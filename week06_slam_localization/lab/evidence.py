from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from analysis.map_metrics import analyze_pixels, read_pgm_bytes
from lab_config import WORLD_ID

ROOT = Path(__file__).resolve().parents[1]


def evidence_id(*values):
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class Artifact:
    name: str
    data: bytes

    def getvalue(self):
        return self.data


def artifact(upload, local: Path | None = None):
    if upload is not None:
        return Artifact(Path(upload.name).name, upload.getvalue())
    if local is not None and local.is_file():
        return Artifact(local.name, local.read_bytes())
    return None


def load_json(item):
    if item is None:
        return None
    try:
        value = json.loads(item.getvalue().decode("utf-8"))
        return value if isinstance(value, dict) else None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def validate_map_bundle(evidence, yaml_item, image_item):
    """Return the checked map metrics or an actionable error message."""
    if not all((evidence, yaml_item, image_item)):
        return None, "Save the map, then run the analyzer. The guide needs the analysis JSON, map YAML, and map PGM in the shared runtime folder."
    if evidence.get("world_id") != WORLD_ID:
        return None, "This map analysis is not marked as TurtleBot3 House. Make a new map in the House world and rerun the analyzer. Earlier map files are preserved."
    try:
        lines = yaml_item.getvalue().decode("utf-8").splitlines()
        metadata = {}
        for line in lines:
            line = line.split("#", 1)[0].strip()
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip("'\"")
        if Path(metadata["image"]).name != image_item.name:
            return None, "The map YAML image name does not match the selected PGM file."
        resolution = float(metadata["resolution"])
        width, height, maximum, pixels = read_pgm_bytes(image_item.getvalue())
        computed = analyze_pixels(width, height, maximum, pixels, resolution)
        reported = evidence.get("metrics", {})
        if not isinstance(reported, dict):
            return None, "Analysis JSON has no metrics object."
        for key in ("width", "height", "resolution", "known_fraction"):
            if abs(float(reported[key]) - float(computed[key])) > (0.005 if key == "known_fraction" else 1e-8):
                return None, f"Analysis JSON {key} does not match this map pair. Analyze the selected YAML again."
        if evidence.get("map_image") and Path(evidence["map_image"]).name != image_item.name:
            return None, "Analysis JSON refers to a different map image."
        return computed, None
    except (KeyError, ValueError, UnicodeDecodeError, IndexError, ZeroDivisionError) as error:
        return None, f"Could not verify map YAML/PGM pair: {error}"


def runtime_map(mission):
    root = ROOT / "runtime" / "maps" / mission
    from lab.autosave import submission_root
    saved = submission_root() / ("mission_1" if mission == "mission1" else "mission_2")
    return (
        artifact(None, root / "evidence.json") or artifact(None, saved / "analysis.json"),
        artifact(None, root / "map.yaml") or artifact(None, saved / "map.yaml"),
        artifact(None, root / "map.pgm") or artifact(None, saved / "map.pgm"),
    )

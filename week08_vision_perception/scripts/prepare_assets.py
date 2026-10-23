"""Extract the legacy coffee asset for historical evidence, not the active tabletop source.

The current source and license are documented in assets/conditions/TABLETOP_SOURCE.md.
"""
from pathlib import Path
from PIL import Image
from skimage import data

if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "assets" / "conditions" / "coffee.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(data.coffee()).save(target)
    print(data.coffee.__doc__)

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from analysis.map_metrics import analyze_pixels, quality_score, read_pgm, read_pgm_bytes
from scripts.analyze_map import parse_map_metadata

class AnalysisTests(unittest.TestCase):
    def test_ascii_pgm_and_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.pgm"; path.write_bytes(b"P2\n# test\n4 2\n255\n0 0 254 205 254 254 205 0\n")
            width, height, maximum, pixels = read_pgm(path); metrics = analyze_pixels(width, height, maximum, pixels, .05)
            self.assertEqual((width, height, maximum), (4, 2, 255)); self.assertAlmostEqual(metrics["known_fraction"], .75); self.assertGreaterEqual(quality_score(metrics), 0)
    def test_map_yaml_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.yaml"; path.write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n", encoding="utf-8")
            self.assertEqual(parse_map_metadata(path)["image"], "map.pgm")

    def test_analyzer_runs_as_documented_from_another_directory(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "analyze_map.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "map.pgm").write_bytes(b"P2\n2 2\n255\n0 254 205 254\n")
            (root / "map.yaml").write_text("image: map.pgm\nresolution: 0.05\n", encoding="utf-8")
            output = root / "evidence.json"
            result = subprocess.run(
                [sys.executable, str(script), "--yaml", str(root / "map.yaml"),
                 "--strategy", "test_route", "--duration-min", "7", "--output", str(output)],
                cwd=root, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["strategy"], "test_route")
    def test_binary_pgm_preserves_whitespace_valued_first_pixel(self):
        width, height, maximum, pixels = read_pgm_bytes(b"P5\n2 1\n255\n\x0a\xfe")
        self.assertEqual((width, height, maximum, pixels), (2, 1, 255, [10, 254]))

    def test_binary_pgm_crlf_header(self):
        self.assertEqual(read_pgm_bytes(b"P5\r\n2 1\r\n255\r\n\x0a\xfe"), (2, 1, 255, [10, 254]))


if __name__ == "__main__": unittest.main()

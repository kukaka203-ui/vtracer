import base64
import os
import subprocess
import tempfile

import requests
import runpod


def handler(event):
    inp = event.get("input", {})
    image_url = inp.get("image_url")

    if not image_url:
        return {"success": False, "error": "Missing input.image_url"}

    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, "input.png")
        output_path = os.path.join(tmp, "output.svg")

        r = requests.get(image_url, timeout=120)
        r.raise_for_status()

        with open(input_path, "wb") as f:
            f.write(r.content)

        cmd = [
            "vtracer",
            "--input", input_path,
            "--output", output_path,
            "--colormode", inp.get("colormode", "binary"),
            "--mode", inp.get("mode", "spline"),
            "--filter_speckle", str(inp.get("filter_speckle", 8)),
            "--color_precision", str(inp.get("color_precision", 6)),
            "--corner_threshold", str(inp.get("corner_threshold", 60)),
            "--segment_length", str(inp.get("segment_length", 4)),
            "--splice_threshold", str(inp.get("splice_threshold", 45)),
        ]

        subprocess.run(cmd, check=True)

        with open(output_path, "rb") as f:
            svg_base64 = base64.b64encode(f.read()).decode("utf-8")

        return {
            "success": True,
            "format": "svg",
            "svg_base64": svg_base64,
        }


runpod.serverless.start({"handler": handler})

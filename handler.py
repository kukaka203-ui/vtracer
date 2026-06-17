import base64
import os
import tempfile
import requests
import runpod
import vtracer


def handler(job):
    inp = job.get("input", {})

    try:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "input.png")
            output_path = os.path.join(tmp, "output.svg")

            if "image_base64" in inp:
                with open(input_path, "wb") as f:
                    f.write(base64.b64decode(inp["image_base64"]))

            elif "image_url" in inp:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(inp["image_url"], headers=headers, timeout=120)
                r.raise_for_status()
                with open(input_path, "wb") as f:
                    f.write(r.content)
            else:
                return {"success": False, "error": "Missing image_base64 or image_url"}

            vtracer.convert_image_to_svg_py(
                input_path,
                output_path,
                colormode=inp.get("colormode", "binary"),
                hierarchical=inp.get("hierarchical", "stacked"),
                mode=inp.get("mode", "spline"),
                filter_speckle=int(inp.get("filter_speckle", 8)),
                color_precision=int(inp.get("color_precision", 6)),
                layer_difference=int(inp.get("layer_difference", 16)),
                corner_threshold=int(inp.get("corner_threshold", 60)),
                length_threshold=float(inp.get("length_threshold", 4.0)),
                max_iterations=int(inp.get("max_iterations", 10)),
                splice_threshold=int(inp.get("splice_threshold", 45)),
                path_precision=int(inp.get("path_precision", 3)),
            )

            with open(output_path, "r", encoding="utf-8") as f:
                svg = f.read()

            return {"success": True, "svg": svg}

    except Exception as e:
        return {"success": False, "error": str(e)}


runpod.serverless.start({"handler": handler})

import base64
import os
import tempfile
import requests
import runpod
import vtracer

def _decode_base64_image(data: str) -> bytes:
    # Hỗ trợ dạng: "data:image/png;base64,AAAA..."
    if "," in data and data.strip().lower().startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data, validate=False)

def handler(job):
    inp = job.get("input", {}) or {}

    try:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "input.png")
            output_path = os.path.join(tmp, "output.svg")

            if inp.get("image_base64"):
                img_bytes = _decode_base64_image(inp["image_base64"])
                with open(input_path, "wb") as f:
                    f.write(img_bytes)

            elif inp.get("image_url"):
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(inp["image_url"], headers=headers, timeout=120)
                r.raise_for_status()

                # Optional nhưng rất hữu ích để tránh tải HTML
                ct = (r.headers.get("Content-Type") or "").lower()
                if "image" not in ct:
                    return {"success": False, "error": f"URL did not return an image. Content-Type={ct}"}

                with open(input_path, "wb") as f:
                    f.write(r.content)
            else:
                return {"success": False, "error": "Missing image_base64 or image_url"}

            # Chốt chặn quan trọng
            if (not os.path.exists(input_path)) or os.path.getsize(input_path) == 0:
                return {"success": False, "error": "Input image file was not created or is empty"}

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

            if (not os.path.exists(output_path)) or os.path.getsize(output_path) == 0:
                return {"success": False, "error": "vtracer did not produce output.svg"}

            with open(output_path, "r", encoding="utf-8") as f:
                svg = f.read()

            return {"success": True, "svg": svg}

    except Exception as e:
        return {"success": False, "error": str(e)}

runpod.serverless.start({"handler": handler})

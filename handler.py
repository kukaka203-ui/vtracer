import base64
import os
import tempfile
import subprocess
import requests
import runpod

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

            # chạy vtracer
            p = subprocess.run(
                ["vtracer", "--input", input_path, "--output", output_path],
                capture_output=True,
                text=True
            )
            if p.returncode != 0:
                return {"success": False, "error": p.stderr or p.stdout}

            svg = open(output_path, "r", encoding="utf-8").read()
            return {"success": True, "svg": svg}

    except Exception as e:
        return {"success": False, "error": str(e)}

# QUAN TRỌNG: dòng này làm worker không thoát ngay
runpod.serverless.start({"handler": handler})

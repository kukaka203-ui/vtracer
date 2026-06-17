import base64
import os
import tempfile
import subprocess
import requests

def handler(event):
    inp = event["input"]

    with tempfile.TemporaryDirectory() as tmp:

        input_path = os.path.join(tmp, "input.png")
        output_path = os.path.join(tmp, "output.svg")

        if "image_base64" in inp:

            with open(input_path, "wb") as f:
                f.write(base64.b64decode(inp["image_base64"]))

        elif "image_url" in inp:

            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            r = requests.get(
                inp["image_url"],
                headers=headers,
                timeout=120
            )

            r.raise_for_status()

            with open(input_path, "wb") as f:
                f.write(r.content)

        else:
            return {
                "success": False,
                "error": "Missing image_base64 or image_url"
            }

        subprocess.run([
            "vtracer",
            "--input", input_path,
            "--output", output_path
        ], check=True)

        with open(output_path, "rb") as f:
            svg = f.read().decode("utf8")

        return {
            "success": True,
            "svg": svg
        }

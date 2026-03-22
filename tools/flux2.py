#!/usr/bin/env python3
"""
AI image generation and editing using FLUX.2 Klein 4B.

Capabilities:
- Text-to-image generation (--prompt)
- Scene presets for video production (--preset)
- Brand-aware generation (--brand)
- Image editing with reference (--input + --prompt)
- Multi-image editing (multiple --input files)

Examples:
  # Text-to-image generation
  python tools/flux2.py --prompt "A sunset over mountains, oil painting style"

  # Scene presets for video production
  python tools/flux2.py --preset title-bg
  python tools/flux2.py --preset problem --prompt "legacy API migration"
  python tools/flux2.py --preset cta --brand digital-samba

  # With custom size and seed
  python tools/flux2.py --prompt "A cat in a spacesuit" --width 1280 --height 720 --seed 42

  # Image editing (pass reference image)
  python tools/flux2.py --input photo.jpg --prompt "Add a party hat"

  # List available presets
  python tools/flux2.py --list-presets

  # Setup RunPod endpoint (first-time)
  python tools/flux2.py --setup
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import requests
    from PIL import Image
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install requests Pillow python-dotenv")
    sys.exit(1)

load_dotenv()

def _get_r2_config() -> Optional[dict]:
    """Get R2 config for result upload. Returns None if not configured."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from config import get_r2_config
        return get_r2_config()
    except ImportError:
        return None


def _download_r2_result(url: str, output_path: str):
    """Download result image from R2 presigned URL."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)


RUNPOD_GRAPHQL_URL = "https://api.runpod.io/graphql"
DOCKER_IMAGE = "ghcr.io/conalmullan/video-toolkit-flux2:latest"
TEMPLATE_NAME = "video-toolkit-flux2"
ENDPOINT_NAME = "video-toolkit-flux2"
ENV_VAR_NAME = "RUNPOD_FLUX2_ENDPOINT_ID"

# --- Scene presets for video production ---
# Each preset defines a prompt template, dimensions, and style.
# {subject} is replaced by the user's --prompt (optional extra context).
# {brand_colors} is replaced by brand color descriptions (or removed if no --brand).

SCENE_PRESETS = {
    "title-bg": {
        "description": "Dark moody background for title slides — text overlay friendly",
        "template": (
            "Dark moody abstract background, {brand_colors}"
            "glowing geometric patterns and subtle bokeh particles, "
            "cinematic lighting, depth of field, {subject}"
            "no text, no words, no letters, no watermark"
        ),
        "width": 1920,
        "height": 1080,
    },
    "problem": {
        "description": "Editorial illustration depicting a pain point or challenge",
        "template": (
            "Editorial illustration, {subject}"
            "dark moody atmosphere with dramatic red and amber warning tones, "
            "{brand_colors}"
            "isometric or low-poly style, cinematic lighting, "
            "no text, no words, no letters"
        ),
        "width": 1920,
        "height": 1080,
    },
    "solution": {
        "description": "Clean optimistic visual showing the fix or product",
        "template": (
            "Clean modern tech illustration, {subject}"
            "bright optimistic color scheme, {brand_colors}"
            "smooth gradients, floating UI elements with glowing edges, "
            "professional product marketing style, "
            "no text, no words, no letters"
        ),
        "width": 1920,
        "height": 1080,
    },
    "demo-bg": {
        "description": "Subtle background texture behind browser/terminal chrome",
        "template": (
            "Minimal dark background with very subtle geometric grid pattern, "
            "{brand_colors}"
            "soft ambient glow, clean and understated, {subject}"
            "no text, no distracting elements"
        ),
        "width": 1920,
        "height": 1080,
    },
    "stats-bg": {
        "description": "Data-themed abstract background for stats/metrics slides",
        "template": (
            "Abstract data visualization background, "
            "flowing lines and glowing nodes suggesting a network graph, "
            "{brand_colors}"
            "depth of field, dark background with luminous accents, {subject}"
            "no text, no numbers, no letters"
        ),
        "width": 1920,
        "height": 1080,
    },
    "cta": {
        "description": "Warm inviting gradient background for call-to-action slides",
        "template": (
            "Minimal abstract background with soft warm gradient, "
            "{brand_colors}"
            "gentle flowing light streaks, professional and inviting, "
            "clean and spacious with room for text overlay, {subject}"
            "no text, no words, no letters"
        ),
        "width": 1920,
        "height": 1080,
    },
    "thumbnail": {
        "description": "Bold eye-catching hero image for YouTube/social thumbnails",
        "template": (
            "Bold eye-catching hero image, {subject}"
            "{brand_colors}"
            "high contrast, vibrant colors, dramatic lighting, "
            "YouTube thumbnail style, attention-grabbing, "
            "no text, no words, no letters"
        ),
        "width": 1280,
        "height": 720,
    },
    "portrait-bg": {
        "description": "Clean backdrop for talking head / NarratorPiP presenter",
        "template": (
            "Clean professional backdrop for video presenter, "
            "{brand_colors}"
            "soft out-of-focus background, subtle depth, {subject}"
            "studio lighting, no text"
        ),
        "width": 1024,
        "height": 1024,
    },
}

# Approximate color name mapping for brand integration
_COLOR_NAMES = {
    "red": [(180, 0, 0), (255, 80, 80)],
    "orange": [(200, 80, 0), (255, 170, 80)],
    "amber": [(180, 120, 0), (255, 200, 50)],
    "yellow": [(200, 200, 0), (255, 255, 100)],
    "lime": [(80, 200, 0), (180, 255, 80)],
    "green": [(0, 130, 0), (80, 220, 80)],
    "teal": [(0, 140, 140), (80, 220, 220)],
    "cyan": [(0, 180, 200), (80, 230, 255)],
    "blue": [(0, 50, 200), (100, 150, 255)],
    "indigo": [(50, 0, 180), (120, 80, 255)],
    "purple": [(120, 0, 180), (180, 80, 255)],
    "pink": [(200, 0, 130), (255, 120, 200)],
    "coral": [(220, 80, 60), (255, 150, 130)],
    "slate": [(50, 60, 80), (120, 140, 170)],
    "white": [(220, 220, 220), (255, 255, 255)],
    "black": [(0, 0, 0), (40, 40, 40)],
}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)


def _color_distance(rgb1: tuple, rgb2: tuple) -> float:
    """Simple Euclidean distance between two RGB colors."""
    return sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)) ** 0.5


def _hex_to_name(hex_color: str) -> str:
    """Convert hex color to approximate English name."""
    if hex_color.startswith("rgba"):
        return ""
    try:
        rgb = _hex_to_rgb(hex_color)
    except (ValueError, IndexError):
        return ""
    best_name = "gray"
    best_dist = float("inf")
    for name, (low, high) in _COLOR_NAMES.items():
        center = tuple((a + b) // 2 for a, b in zip(low, high))
        dist = _color_distance(rgb, center)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


def load_brand_colors(brand_name: str) -> str:
    """Load brand.json and return color description string for prompt injection."""
    workspace = Path(__file__).parent.parent
    brand_path = workspace / "brands" / brand_name / "brand.json"
    if not brand_path.exists():
        log(f"Brand not found: {brand_path}", "warn")
        return ""
    try:
        brand = json.loads(brand_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        log(f"Error reading brand: {e}", "warn")
        return ""

    colors = brand.get("colors", {})
    primary = _hex_to_name(colors.get("primary", ""))
    accent = _hex_to_name(colors.get("accent", ""))

    parts = []
    if primary:
        parts.append(primary)
    if accent and accent != primary:
        parts.append(accent)

    if not parts:
        return ""
    return f"{' and '.join(parts)} color tones, "


def build_preset_prompt(
    preset_name: str,
    user_prompt: Optional[str] = None,
    brand_name: Optional[str] = None,
) -> str:
    """Build a full prompt from preset template, optional user context, and brand."""
    preset = SCENE_PRESETS.get(preset_name)
    if not preset:
        raise ValueError(f"Unknown preset: {preset_name}. Use --list-presets to see options.")

    brand_colors = load_brand_colors(brand_name) if brand_name else ""
    subject = f"{user_prompt}, " if user_prompt else ""

    prompt = preset["template"].format(
        subject=subject,
        brand_colors=brand_colors,
    )
    # Clean up double spaces and trailing commas
    prompt = " ".join(prompt.split())
    return prompt


def list_presets():
    """Print available scene presets."""
    print("\nScene Presets (for video production)")
    print("=" * 55)
    for name, preset in SCENE_PRESETS.items():
        size = f"{preset['width']}x{preset['height']}"
        print(f"  {name:<14} {size:>10}  {preset['description']}")
    print()
    print("Usage:")
    print("  flux2.py --preset title-bg")
    print("  flux2.py --preset problem --prompt 'legacy API migration'")
    print("  flux2.py --preset cta --brand digital-samba")
    print()


def log(msg: str, level: str = "info"):
    """Print formatted log message."""
    colors = {
        "info": "\033[94m",
        "success": "\033[92m",
        "error": "\033[91m",
        "warn": "\033[93m",
        "dim": "\033[90m",
    }
    reset = "\033[0m"
    prefix = {"info": "->", "success": "OK", "error": "!!", "warn": "??", "dim": "  "}
    color = colors.get(level, "")
    print(f"{color}{prefix.get(level, '->')} {msg}{reset}")


def get_config() -> dict:
    """Get RunPod configuration from environment."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from config import get_runpod_api_key
        api_key = get_runpod_api_key()
    except ImportError:
        api_key = os.getenv("RUNPOD_API_KEY")

    endpoint_id = os.getenv(ENV_VAR_NAME)

    return {
        "api_key": api_key,
        "endpoint_id": endpoint_id,
    }


def encode_image(path: str) -> str:
    """Encode image file to base64."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def decode_and_save(base64_data: str, output_path: str):
    """Decode base64 and save to file."""
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(base64_data))


def call_endpoint(payload: dict, timeout: int = 600) -> tuple[dict, float]:
    """Call RunPod endpoint and return (result, elapsed_seconds)."""
    config = get_config()
    api_key = config.get("api_key")
    endpoint_id = config.get("endpoint_id")

    if not api_key:
        return {"error": "RUNPOD_API_KEY not set in .env"}, 0
    if not endpoint_id:
        return {"error": f"{ENV_VAR_NAME} not set. Run with --setup first."}, 0

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    start = time.time()

    try:
        run_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        response = requests.post(run_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        job_id = result.get("id")
        status = result.get("status")

        if status == "COMPLETED":
            return result.get("output", result), time.time() - start

        if status == "FAILED":
            return {"error": result.get("error", "Unknown error")}, time.time() - start

        # Poll for completion
        log("Processing... (cold start may take 3-5 min on first run)", "warn")
        status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"

        poll_interval = 5
        queue_timeout = 300  # Cancel job if stuck in queue for 5 min
        queue_start = time.time()
        last_status = None
        while time.time() - start < timeout:
            time.sleep(poll_interval)
            elapsed = time.time() - start

            status_resp = requests.get(status_url, headers=headers, timeout=30)
            status_data = status_resp.json()
            status = status_data.get("status")

            if status != last_status:
                if status == "IN_PROGRESS":
                    log(f"[{elapsed:.0f}s] Generating...", "dim")
                    queue_start = None  # No longer queued
                elif status == "IN_QUEUE":
                    log(f"[{elapsed:.0f}s] Waiting for GPU...", "dim")
                last_status = status

            if status == "COMPLETED":
                return status_data.get("output", status_data), time.time() - start

            if status == "FAILED":
                error = status_data.get("error", "Unknown error")
                return {"error": error}, time.time() - start

            if status in ("CANCELLED", "TIMED_OUT"):
                return {"error": f"Job {status}"}, time.time() - start

            # Cancel jobs stuck in queue too long (prevents runaway billing)
            if status == "IN_QUEUE" and queue_start and (time.time() - queue_start > queue_timeout):
                log(f"Job stuck in queue for {queue_timeout}s — cancelling to prevent runaway charges", "warn")
                cancel_url = f"https://api.runpod.ai/v2/{endpoint_id}/cancel/{job_id}"
                try:
                    requests.post(cancel_url, headers=headers, timeout=10)
                except Exception:
                    pass
                return {"error": f"Cancelled: no GPU available after {queue_timeout}s in queue"}, time.time() - start

        # Timeout — cancel the job so it doesn't linger in RunPod's queue
        log("Polling timeout — cancelling job on RunPod", "warn")
        cancel_url = f"https://api.runpod.ai/v2/{endpoint_id}/cancel/{job_id}"
        try:
            requests.post(cancel_url, headers=headers, timeout=10)
        except Exception:
            pass
        return {"error": "polling timeout (job cancelled)"}, time.time() - start

    except requests.exceptions.Timeout:
        return {"error": "timeout"}, time.time() - start
    except Exception as e:
        return {"error": str(e)}, time.time() - start


def generate_image(
    prompt: str,
    output_path: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    seed: Optional[int] = None,
    steps: Optional[int] = None,
    guidance: Optional[float] = None,
    open_result: bool = True,
    verbose: bool = False,
) -> Optional[str]:
    """
    Generate image from text prompt.

    Returns output path on success, None on failure.
    """
    if output_path is None:
        # Generate filename from first few words of prompt
        slug = prompt[:40].strip().replace(" ", "_").lower()
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        output_path = f"{slug}.png"

    log(f"Prompt: {prompt}", "info")
    log(f"Size: {width}x{height}", "dim")

    payload = {
        "input": {
            "operation": "generate",
            "prompt": prompt,
            "width": width,
            "height": height,
        }
    }

    if seed is not None:
        payload["input"]["seed"] = seed
    if steps is not None:
        payload["input"]["num_inference_steps"] = steps
    if guidance is not None:
        payload["input"]["guidance_scale"] = guidance

    r2_config = _get_r2_config()
    if r2_config:
        payload["input"]["r2"] = {
            "endpoint_url": r2_config["endpoint_url"],
            "access_key_id": r2_config["access_key_id"],
            "secret_access_key": r2_config["secret_access_key"],
            "bucket_name": r2_config["bucket_name"],
        }

    result, elapsed = call_endpoint(payload)

    if "error" in result:
        log(f"Generation failed: {result['error']}", "error")
        return None

    if "output_url" in result:
        log("Downloading from R2...", "dim")
        _download_r2_result(result["output_url"], output_path)
    else:
        decode_and_save(result["image_base64"], output_path)

    inference_ms = result.get("inference_time_ms", 0)
    output_size = result.get("image_size", [0, 0])

    log(f"Saved: {output_path}", "success")
    log(f"Time: {elapsed:.1f}s total, {inference_ms/1000:.1f}s inference", "dim")
    log(f"Output: {output_size[0]}x{output_size[1]}", "dim")
    log(f"Seed: {result.get('seed', 'unknown')}", "dim")

    if verbose:
        cost = (elapsed / 3600) * 0.34
        log(f"Est. cost: ${cost:.4f}", "dim")

    if open_result and sys.platform == "darwin":
        import subprocess
        subprocess.run(["open", output_path], check=False)

    return output_path


def edit_image(
    input_paths: list[str],
    prompt: str,
    output_path: Optional[str] = None,
    seed: Optional[int] = None,
    steps: Optional[int] = None,
    guidance: Optional[float] = None,
    open_result: bool = True,
    verbose: bool = False,
) -> Optional[str]:
    """
    Edit image(s) with the given prompt.

    Returns output path on success, None on failure.
    """
    for path in input_paths:
        if not Path(path).exists():
            log(f"File not found: {path}", "error")
            return None

    with Image.open(input_paths[0]) as img:
        log(f"Input: {input_paths[0]} ({img.size[0]}x{img.size[1]})", "info")

    if len(input_paths) > 1:
        log(f"Additional inputs: {', '.join(input_paths[1:])}", "dim")

    log(f"Prompt: {prompt}", "info")

    if output_path is None:
        input_stem = Path(input_paths[0]).stem
        output_path = f"{input_stem}_flux2.png"

    payload = {
        "input": {
            "operation": "edit",
            "image_base64": encode_image(input_paths[0]),
            "prompt": prompt,
        }
    }

    if len(input_paths) > 1:
        log(f"Multi-image mode: {len(input_paths)} images", "info")
        payload["input"]["images_base64"] = [encode_image(p) for p in input_paths[1:3]]

    if seed is not None:
        payload["input"]["seed"] = seed
    if steps is not None:
        payload["input"]["num_inference_steps"] = steps
    if guidance is not None:
        payload["input"]["guidance_scale"] = guidance

    r2_config = _get_r2_config()
    if r2_config:
        payload["input"]["r2"] = {
            "endpoint_url": r2_config["endpoint_url"],
            "access_key_id": r2_config["access_key_id"],
            "secret_access_key": r2_config["secret_access_key"],
            "bucket_name": r2_config["bucket_name"],
        }

    result, elapsed = call_endpoint(payload)

    if "error" in result:
        log(f"Edit failed: {result['error']}", "error")
        return None

    if "output_url" in result:
        log("Downloading from R2...", "dim")
        _download_r2_result(result["output_url"], output_path)
    else:
        decode_and_save(result["image_base64"], output_path)

    inference_ms = result.get("inference_time_ms", 0)
    output_size = result.get("image_size", [0, 0])

    log(f"Saved: {output_path}", "success")
    log(f"Time: {elapsed:.1f}s total, {inference_ms/1000:.1f}s inference", "dim")
    log(f"Output: {output_size[0]}x{output_size[1]}", "dim")
    log(f"Seed: {result.get('seed', 'unknown')}", "dim")

    if verbose:
        cost = (elapsed / 3600) * 0.34
        log(f"Est. cost: ${cost:.4f}", "dim")

    if open_result and sys.platform == "darwin":
        import subprocess
        subprocess.run(["open", output_path], check=False)

    return output_path


# --- RunPod setup ---

def runpod_graphql_query(api_key: str, query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query against RunPod API."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(
        RUNPOD_GRAPHQL_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed: HTTP {response.status_code}: {response.text}")

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")

    return data.get("data", {})


def list_runpod_templates(api_key: str) -> list[dict]:
    """List all serverless templates."""
    query = """
    query {
        myself {
            podTemplates {
                id
                name
                imageName
                isServerless
            }
        }
    }
    """
    data = runpod_graphql_query(api_key, query)
    templates = data.get("myself", {}).get("podTemplates", [])
    return [t for t in templates if t.get("isServerless")]


def find_template(api_key: str) -> dict | None:
    """Find existing Flux2 template."""
    templates = list_runpod_templates(api_key)
    for t in templates:
        if t.get("name") == TEMPLATE_NAME:
            return t
        if t.get("imageName") == DOCKER_IMAGE:
            return t
    return None


def create_template(api_key: str, verbose: bool = True) -> dict:
    """Create a serverless template for Flux2."""
    if verbose:
        print(f"Creating template '{TEMPLATE_NAME}'...")

    mutation = """
    mutation SaveTemplate($input: SaveTemplateInput!) {
        saveTemplate(input: $input) {
            id
            name
            imageName
            isServerless
        }
    }
    """

    variables = {
        "input": {
            "name": TEMPLATE_NAME,
            "imageName": DOCKER_IMAGE,
            "isServerless": True,
            "containerDiskInGb": 20,
            "volumeInGb": 0,
            "dockerArgs": "",
            "env": [],
        }
    }

    data = runpod_graphql_query(api_key, mutation, variables)
    template = data.get("saveTemplate")

    if not template or not template.get("id"):
        raise Exception(f"Failed to create template: {data}")

    if verbose:
        print(f"  Template created: {template['id']}")

    return template


def list_runpod_endpoints(api_key: str) -> list[dict]:
    """List all user endpoints."""
    query = """
    query {
        myself {
            endpoints {
                id
                name
                templateId
                gpuIds
                workersMin
                workersMax
                idleTimeout
            }
        }
    }
    """
    data = runpod_graphql_query(api_key, query)
    return data.get("myself", {}).get("endpoints", [])


def find_endpoint(api_key: str, template_id: str) -> dict | None:
    """Find existing Flux2 endpoint."""
    endpoints = list_runpod_endpoints(api_key)
    for e in endpoints:
        if e.get("name") == ENDPOINT_NAME:
            return e
        if e.get("templateId") == template_id:
            return e
    return None


def create_endpoint(
    api_key: str,
    template_id: str,
    gpu_id: str = "AMPERE_24,ADA_24",
    verbose: bool = True,
) -> dict:
    """Create a serverless endpoint for Flux2."""
    if verbose:
        print(f"Creating endpoint '{ENDPOINT_NAME}'...")

    mutation = """
    mutation SaveEndpoint($input: EndpointInput!) {
        saveEndpoint(input: $input) {
            id
            name
            templateId
            gpuIds
            workersMin
            workersMax
            idleTimeout
        }
    }
    """

    variables = {
        "input": {
            "name": ENDPOINT_NAME,
            "templateId": template_id,
            "gpuIds": gpu_id,
            "workersMin": 0,
            "workersMax": 1,
            "idleTimeout": 5,
            "scalerType": "QUEUE_DELAY",
            "scalerValue": 4,
        }
    }

    data = runpod_graphql_query(api_key, mutation, variables)
    endpoint = data.get("saveEndpoint")

    if not endpoint or not endpoint.get("id"):
        raise Exception(f"Failed to create endpoint: {data}")

    if verbose:
        print(f"  Endpoint created: {endpoint['id']}")

    return endpoint


def save_endpoint_to_env(endpoint_id: str, verbose: bool = True) -> bool:
    """Save endpoint ID to .env file."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from config import find_workspace_root
        env_path = find_workspace_root() / ".env"
    except ImportError:
        env_path = Path(__file__).parent.parent / ".env"

    if verbose:
        print(f"Saving endpoint ID to {env_path}...")

    env_content = ""
    if env_path.exists():
        env_content = env_path.read_text()

    lines = env_content.split("\n")
    updated = False
    new_lines = []

    for line in lines:
        if line.startswith(f"{ENV_VAR_NAME}="):
            new_lines.append(f"{ENV_VAR_NAME}={endpoint_id}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(f"{ENV_VAR_NAME}={endpoint_id}")

    env_path.write_text("\n".join(new_lines))

    if verbose:
        print(f"  Saved: {ENV_VAR_NAME}={endpoint_id}")

    return True


def setup_runpod(gpu_id: str = "AMPERE_24,ADA_24", verbose: bool = True) -> dict:
    """Set up RunPod endpoint for Flux2."""
    result = {
        "success": False,
        "template_id": None,
        "endpoint_id": None,
        "created_template": False,
        "created_endpoint": False,
    }

    config = get_config()
    api_key = config.get("api_key")

    if not api_key:
        result["error"] = "RUNPOD_API_KEY not set. Add to .env file first."
        return result

    if verbose:
        print("=" * 60)
        print("RunPod Setup (FLUX.2 Klein 4B)")
        print("=" * 60)
        print(f"Docker Image: {DOCKER_IMAGE}")
        print(f"GPU Type: {gpu_id}")
        print()

    try:
        if verbose:
            print("[1/3] Checking for existing template...")

        template = find_template(api_key)
        if template:
            if verbose:
                print(f"  Found existing template: {template['id']}")
            result["template_id"] = template["id"]
        else:
            template = create_template(api_key, verbose=verbose)
            result["template_id"] = template["id"]
            result["created_template"] = True

        if verbose:
            print("[2/3] Checking for existing endpoint...")

        endpoint = find_endpoint(api_key, result["template_id"])
        if endpoint:
            if verbose:
                print(f"  Found existing endpoint: {endpoint['id']}")
            result["endpoint_id"] = endpoint["id"]
        else:
            endpoint = create_endpoint(
                api_key,
                result["template_id"],
                gpu_id=gpu_id,
                verbose=verbose,
            )
            result["endpoint_id"] = endpoint["id"]
            result["created_endpoint"] = True

        if verbose:
            print("[3/3] Saving configuration...")

        save_endpoint_to_env(result["endpoint_id"], verbose=verbose)

        result["success"] = True

        if verbose:
            print()
            print("=" * 60)
            print("Setup Complete!")
            print("=" * 60)
            print(f"Template ID:  {result['template_id']}")
            print(f"Endpoint ID:  {result['endpoint_id']}")
            print()
            print("You can now run:")
            print('  python tools/flux2.py --prompt "A cat in a spacesuit"')
            print('  python tools/flux2.py --input photo.jpg --prompt "Add sunglasses"')
            print()

    except Exception as e:
        result["error"] = str(e)
        if verbose:
            print(f"Error: {e}", file=sys.stderr)

    return result


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="AI image generation and editing using FLUX.2 Klein 4B",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --prompt "A sunset over mountains"
  %(prog)s --preset title-bg
  %(prog)s --preset problem --prompt "legacy API migration"
  %(prog)s --preset cta --brand digital-samba
  %(prog)s --input photo.jpg --prompt "Add a party hat"
  %(prog)s --list-presets
  %(prog)s --setup
        """
    )

    # Input options
    input_group = parser.add_argument_group("Input")
    input_group.add_argument("--input", "-i", nargs="+", help="Input image(s) for editing")

    # Preset options
    preset_group = parser.add_argument_group("Presets")
    preset_group.add_argument("--preset", choices=list(SCENE_PRESETS.keys()),
                              help="Scene preset for video production")
    preset_group.add_argument("--brand", help="Brand name (loads colors from brands/<name>/brand.json)")
    preset_group.add_argument("--list-presets", action="store_true", help="List available scene presets")

    # Generation/edit options
    gen_group = parser.add_argument_group("Generation")
    gen_group.add_argument("--prompt", "-p", help="Text prompt (required, or use --preset)")
    gen_group.add_argument("--width", "-W", type=int, default=None, help="Image width (default: 1024, or from preset)")
    gen_group.add_argument("--height", "-H", type=int, default=None, help="Image height (default: 1024, or from preset)")

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--output", "-o", help="Output file path")
    output_group.add_argument("--no-open", action="store_true", help="Don't open result automatically")

    # Advanced options
    adv_group = parser.add_argument_group("Advanced")
    adv_group.add_argument("--seed", type=int, help="Random seed for reproducibility")
    adv_group.add_argument("--steps", type=int, help="Inference steps (default: 4 for generate, 50 for edit)")
    adv_group.add_argument("--guidance", "-g", type=float, help="Guidance scale (default: 1.0 for generate, 4.0 for edit)")
    adv_group.add_argument("--verbose", action="store_true", help="Show detailed output")

    # Setup
    setup_group = parser.add_argument_group("Setup")
    setup_group.add_argument("--setup", action="store_true", help="Set up RunPod endpoint")
    setup_group.add_argument("--setup-gpu", type=str, default="AMPERE_24,ADA_24",
                             help="GPU type(s) for endpoint, comma-separated for fallback (default: AMPERE_24,ADA_24)")

    # Output format
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    # Handle --list-presets
    if args.list_presets:
        list_presets()
        sys.exit(0)

    # Handle --setup
    if args.setup:
        result = setup_runpod(gpu_id=args.setup_gpu, verbose=not args.json)
        if args.json:
            print(json.dumps(result, indent=2))
        if result.get("error"):
            sys.exit(1)
        sys.exit(0)

    # Resolve preset into prompt + dimensions
    if args.preset:
        preset = SCENE_PRESETS[args.preset]
        prompt = build_preset_prompt(args.preset, args.prompt, args.brand)
        width = args.width or preset["width"]
        height = args.height or preset["height"]
        log(f"Preset: {args.preset}", "info")
        if args.brand:
            log(f"Brand: {args.brand}", "dim")
    elif args.prompt:
        prompt = args.prompt
        width = args.width or 1024
        height = args.height or 1024
    else:
        parser.print_help()
        print("\n\033[91m!! --prompt or --preset is required\033[0m")
        sys.exit(1)

    print()
    log("FLUX.2 Klein 4B", "info")
    log("=" * 40, "dim")

    if args.input:
        # Edit mode
        edit_image(
            input_paths=args.input,
            prompt=prompt,
            output_path=args.output,
            seed=args.seed,
            steps=args.steps,
            guidance=args.guidance,
            open_result=not args.no_open,
            verbose=args.verbose,
        )
    else:
        # Generate mode
        generate_image(
            prompt=prompt,
            output_path=args.output,
            width=width,
            height=height,
            seed=args.seed,
            steps=args.steps,
            guidance=args.guidance,
            open_result=not args.no_open,
            verbose=args.verbose,
        )


if __name__ == "__main__":
    main()

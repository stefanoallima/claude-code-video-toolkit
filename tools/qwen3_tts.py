#!/usr/bin/env python3
"""
Generate speech using Qwen3-TTS (via RunPod serverless).

Supports built-in speakers with emotion control and voice cloning from reference audio.

Usage:
    # Built-in speaker
    python tools/qwen3_tts.py --text "Hello world" --speaker Ryan --output hello.mp3

    # With tone preset
    python tools/qwen3_tts.py --text "Hello world" --tone warm --output hello.mp3

    # With custom emotion/style instruction (overrides --tone)
    python tools/qwen3_tts.py --text "I'm so excited!" --instruct "Speak enthusiastically" --output excited.mp3

    # List tone presets
    python tools/qwen3_tts.py --list-tones

    # Voice cloning
    python tools/qwen3_tts.py --text "Hello" --ref-audio sample.wav --ref-text "transcript" --output cloned.mp3

    # List built-in voices
    python tools/qwen3_tts.py --list-voices

    # Setup endpoint
    python tools/qwen3_tts.py --setup

Setup:
    1. Create account at runpod.io
    2. Run: python tools/qwen3_tts.py --setup
    3. Or manually deploy docker/runpod-qwen3-tts/ and add endpoint ID to .env

Cost:
    - ~$0.005 per sentence
    - ~$0.05-0.10 per page of text
    - Uses RTX 4090 ($0.00074/sec) by default
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

# Docker image for RunPod endpoint
QWEN3_TTS_DOCKER_IMAGE = "ghcr.io/conalmullan/video-toolkit-qwen3-tts:latest"
QWEN3_TTS_TEMPLATE_NAME = "video-toolkit-qwen3-tts"
QWEN3_TTS_ENDPOINT_NAME = "video-toolkit-qwen3-tts"

# Built-in speakers
BUILTIN_SPEAKERS = {
    "Ryan": "English",
    "Aiden": "English",
    "Vivian": "Chinese",
    "Serena": "Chinese",
    "Uncle_Fu": "Chinese",
    "Dylan": "Chinese",
    "Eric": "Chinese",
    "Ono_Anna": "Japanese",
    "Sohee": "Korean",
}

SUPPORTED_LANGUAGES = [
    "Auto", "English", "Chinese", "French", "German",
    "Italian", "Japanese", "Korean", "Portuguese", "Russian", "Spanish",
]

# Named instruct presets for common voice tones
INSTRUCT_PRESETS = {
    "neutral": "",
    "warm": "Speak warmly and naturally, like talking to a friend.",
    "professional": "Speak in a clear, professional tone with measured pacing.",
    "excited": "Speak with enthusiasm and energy, conveying excitement.",
    "calm": "Speak slowly and calmly, with a soothing, relaxed delivery.",
    "serious": "Speak in a serious, authoritative tone with gravitas.",
    "storyteller": "Speak like a narrator telling a captivating story, with varied pacing and emphasis.",
    "tutorial": "Speak clearly and patiently, like explaining something step by step.",
}


def resolve_tone(tone: str | None, instruct: str) -> str:
    """Resolve a tone preset name and/or raw instruct text into final instruct string.

    Priority: explicit instruct > tone preset > empty string.
    Unknown tone names are treated as raw instruct text.
    """
    if instruct:
        return instruct
    if tone:
        if tone in INSTRUCT_PRESETS:
            return INSTRUCT_PRESETS[tone]
        return tone  # treat unknown tone as raw instruct text
    return ""


def get_runpod_config() -> dict:
    """Get RunPod configuration from environment."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from config import get_runpod_api_key
        api_key = get_runpod_api_key()
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("RUNPOD_API_KEY")

    from dotenv import load_dotenv
    load_dotenv()
    endpoint_id = os.getenv("RUNPOD_QWEN3_TTS_ENDPOINT_ID")

    return {
        "api_key": api_key,
        "endpoint_id": endpoint_id,
    }


def _get_r2_client():
    """Get boto3 S3 client configured for Cloudflare R2."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from config import get_r2_config
        r2_config = get_r2_config()
    except ImportError:
        r2_config = None

    if not r2_config:
        return None, None

    try:
        import boto3
        from botocore.config import Config

        client = boto3.client(
            "s3",
            endpoint_url=r2_config["endpoint_url"],
            aws_access_key_id=r2_config["access_key_id"],
            aws_secret_access_key=r2_config["secret_access_key"],
            config=Config(signature_version="s3v4"),
        )
        return client, r2_config
    except ImportError:
        print("  boto3 not installed, skipping R2", file=sys.stderr)
        return None, None


def _upload_to_r2(file_path: str, prefix: str) -> tuple[str | None, str | None]:
    """Upload to Cloudflare R2 and return presigned download URL."""
    client, config = _get_r2_client()
    if not client:
        return None, None

    import uuid
    file_name = Path(file_path).name
    object_key = f"{prefix}/{uuid.uuid4().hex[:8]}_{file_name}"

    try:
        client.upload_file(file_path, config["bucket_name"], object_key)

        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": config["bucket_name"], "Key": object_key},
            ExpiresIn=7200,
        )
        return url, object_key
    except Exception as e:
        print(f"  R2 upload error: {e}", file=sys.stderr)
        return None, None


def _delete_from_r2(object_key: str) -> bool:
    """Delete object from R2 after job completion."""
    client, config = _get_r2_client()
    if not client or not object_key:
        return False

    try:
        client.delete_object(Bucket=config["bucket_name"], Key=object_key)
        return True
    except Exception:
        return False


def _download_from_r2(object_key: str, output_path: str) -> bool:
    """Download object from R2 to local path."""
    client, config = _get_r2_client()
    if not client:
        return False

    try:
        client.download_file(config["bucket_name"], object_key, output_path)
        return True
    except Exception as e:
        print(f"  R2 download error: {e}", file=sys.stderr)
        return False


def upload_to_storage(file_path: str, prefix: str) -> tuple[str | None, str | None]:
    """Upload a file to temporary storage for job input."""
    file_size = Path(file_path).stat().st_size
    file_name = Path(file_path).name

    print(f"Uploading {file_name} ({file_size // 1024}KB)...", file=sys.stderr)

    url, r2_key = _upload_to_r2(file_path, prefix)
    if url:
        print(f"  Upload complete (R2)", file=sys.stderr)
        return url, r2_key

    # Fall back to free services
    for service_name, upload_func in [("litterbox", _upload_to_litterbox), ("0x0.st", _upload_to_0x0)]:
        try:
            url = upload_func(file_path, file_name)
            if url:
                print(f"  Upload complete ({service_name})", file=sys.stderr)
                return url, None
        except Exception as e:
            print(f"  {service_name} failed: {e}", file=sys.stderr)
            continue

    print("All upload services failed", file=sys.stderr)
    return None, None


def _upload_to_litterbox(file_path: str, file_name: str) -> str | None:
    """Upload to litterbox.catbox.moe (200MB limit, 24h retention)."""
    import subprocess
    result = subprocess.run(
        [
            "curl", "-s",
            "-F", "reqtype=fileupload",
            "-F", "time=24h",
            "-F", f"fileToUpload=@{file_path}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode == 0:
        url = result.stdout.strip()
        if url.startswith("http"):
            return url
    return None


def _upload_to_0x0(file_path: str, file_name: str) -> str | None:
    """Upload to 0x0.st (512MB limit, 30 day retention)."""
    import subprocess
    result = subprocess.run(
        ["curl", "-s", "-F", f"file=@{file_path}", "https://0x0.st"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode == 0:
        url = result.stdout.strip()
        if url.startswith("http"):
            return url
    return None


def get_audio_duration(file_path: str) -> float | None:
    """Get audio duration in seconds using ffprobe."""
    import subprocess
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                file_path,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except (FileNotFoundError, ValueError):
        pass  # ffprobe not installed or invalid output
    return None


def submit_runpod_job(
    endpoint_id: str,
    api_key: str,
    text: str,
    mode: str = "custom_voice",
    speaker: str = "Ryan",
    language: str = "Auto",
    instruct: str = "",
    ref_audio_url: str | None = None,
    ref_text: str | None = None,
    output_format: str = "mp3",
    r2_config: dict | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
) -> dict | None:
    """Submit a Qwen3-TTS job to RunPod serverless endpoint."""
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"

    payload = {
        "input": {
            "text": text,
            "mode": mode,
            "language": language,
            "output_format": output_format,
        }
    }

    if mode == "clone":
        payload["input"]["ref_audio_url"] = ref_audio_url
        payload["input"]["ref_text"] = ref_text
    else:
        payload["input"]["speaker"] = speaker
        if instruct:
            payload["input"]["instruct"] = instruct

    if temperature is not None:
        payload["input"]["temperature"] = temperature
    if top_p is not None:
        payload["input"]["top_p"] = top_p

    if r2_config:
        payload["input"]["r2"] = {
            "endpoint_url": r2_config["endpoint_url"],
            "access_key_id": r2_config["access_key_id"],
            "secret_access_key": r2_config["secret_access_key"],
            "bucket_name": r2_config["bucket_name"],
        }

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Job submission failed: HTTP {response.status_code}", file=sys.stderr)
            print(f"  Response: {response.text[:500]}", file=sys.stderr)
            return None

    except Exception as e:
        print(f"Job submission error: {e}", file=sys.stderr)
        return None


def poll_runpod_job(
    endpoint_id: str,
    api_key: str,
    job_id: str,
    timeout: int = 300,
    poll_interval: int = 3,
    verbose: bool = True,
) -> dict | None:
    """Poll RunPod job until completion or timeout."""
    url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    start_time = time.time()
    last_status = None
    queue_timeout = 300  # Cancel job if stuck in queue for 5 min
    queue_start = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                print(f"Status check failed: HTTP {response.status_code}", file=sys.stderr)
                time.sleep(poll_interval)
                continue

            data = response.json()
            status = data.get("status")

            if verbose and status != last_status:
                elapsed = int(time.time() - start_time)
                print(f"  [{elapsed}s] Status: {status}", file=sys.stderr)
                last_status = status

            if status == "COMPLETED":
                return data
            elif status == "FAILED":
                print(f"Job failed: {data.get('error', 'Unknown error')}", file=sys.stderr)
                return data

            # Track queue-to-progress transition
            if status == "IN_PROGRESS" and queue_start is not None:
                queue_start = None

            # Cancel jobs stuck in queue too long (prevents runaway billing)
            if status == "IN_QUEUE" and queue_start is not None and (time.time() - queue_start > queue_timeout):
                print(f"Job stuck in queue for {queue_timeout}s — cancelling to prevent runaway charges", file=sys.stderr)
                cancel_url = f"https://api.runpod.ai/v2/{endpoint_id}/cancel/{job_id}"
                try:
                    requests.post(cancel_url, headers=headers, timeout=10)
                except Exception:
                    pass
                return {"status": "FAILED", "error": f"Cancelled: no GPU available after {queue_timeout}s in queue"}

            time.sleep(poll_interval)

        except Exception as e:
            print(f"Status check error: {e}", file=sys.stderr)
            time.sleep(poll_interval)

    # Overall timeout — cancel the job so it doesn't linger in RunPod's queue
    print(f"Job timed out after {timeout}s — cancelling on RunPod", file=sys.stderr)
    cancel_url = f"https://api.runpod.ai/v2/{endpoint_id}/cancel/{job_id}"
    try:
        requests.post(cancel_url, headers=headers, timeout=10)
    except Exception:
        pass
    return None


def download_from_url(url: str, output_path: str, verbose: bool = True) -> bool:
    """Download file from URL to local path."""
    try:
        if verbose:
            print(f"Downloading result...", file=sys.stderr)

        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if verbose:
            size_kb = Path(output_path).stat().st_size // 1024
            print(f"  Downloaded: {output_path} ({size_kb}KB)", file=sys.stderr)

        return True

    except Exception as e:
        print(f"Download error: {e}", file=sys.stderr)
        return False


def generate_audio(
    text: str,
    output_path: str,
    speaker: str = "Ryan",
    language: str = "Auto",
    instruct: str = "",
    ref_audio: str | None = None,
    ref_text: str | None = None,
    output_format: str = "mp3",
    timeout: int = 300,
    verbose: bool = True,
    temperature: float | None = None,
    top_p: float | None = None,
) -> dict:
    """Generate audio using Qwen3-TTS via RunPod.

    This is the main entry point, importable by voiceover.py.
    Returns dict with: success, output, duration_seconds, duration_frames_30fps
    """
    start_time = time.time()
    r2_keys_to_cleanup = []

    config = get_runpod_config()
    api_key = config.get("api_key")
    endpoint_id = config.get("endpoint_id")

    if not api_key:
        return {"success": False, "error": "RUNPOD_API_KEY not set. Add to .env file."}
    if not endpoint_id:
        return {"success": False, "error": "RUNPOD_QWEN3_TTS_ENDPOINT_ID not set. Run with --setup first."}

    # Get R2 config
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from config import get_r2_config
        r2_config = get_r2_config()
    except ImportError:
        r2_config = None

    # Determine mode
    mode = "clone" if ref_audio else "custom_voice"

    # Upload reference audio for clone mode
    ref_audio_url = None
    if mode == "clone":
        if not Path(ref_audio).exists():
            return {"success": False, "error": f"Reference audio not found: {ref_audio}"}
        if not ref_text:
            return {"success": False, "error": "ref_text is required for voice cloning"}

        ref_audio_url, ref_r2_key = upload_to_storage(ref_audio, "qwen3-tts/input")
        if not ref_audio_url:
            return {"success": False, "error": "Failed to upload reference audio"}
        if ref_r2_key:
            r2_keys_to_cleanup.append(ref_r2_key)

    if verbose:
        print(f"Using RunPod endpoint: {endpoint_id}", file=sys.stderr)
        if mode == "clone":
            print(f"Mode: voice clone", file=sys.stderr)
        else:
            print(f"Speaker: {speaker}, Language: {language}", file=sys.stderr)

    # Submit job
    job_response = submit_runpod_job(
        endpoint_id=endpoint_id,
        api_key=api_key,
        text=text,
        mode=mode,
        speaker=speaker,
        language=language,
        instruct=instruct,
        ref_audio_url=ref_audio_url,
        ref_text=ref_text,
        output_format=output_format,
        r2_config=r2_config,
        temperature=temperature,
        top_p=top_p,
    )

    if not job_response:
        return {"success": False, "error": "Failed to submit job"}

    job_id = job_response.get("id")
    if not job_id:
        return {"success": False, "error": f"No job ID in response: {job_response}"}

    if verbose:
        print(f"Job submitted: {job_id}", file=sys.stderr)

    # Poll for completion
    result = poll_runpod_job(
        endpoint_id=endpoint_id,
        api_key=api_key,
        job_id=job_id,
        timeout=timeout,
        verbose=verbose,
    )

    if not result:
        return {"success": False, "error": "Job timed out or failed to get status"}

    status = result.get("status")
    if status != "COMPLETED":
        error = result.get("error") or result.get("output", {}).get("error") or "Unknown error"
        return {"success": False, "error": f"Job failed: {error}"}

    output = result.get("output", {})
    if isinstance(output, dict) and output.get("error"):
        return {"success": False, "error": output["error"]}

    # Download result
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    downloaded = False

    output_r2_key = output.get("r2_key") if isinstance(output, dict) else None
    output_url = output.get("audio_url") if isinstance(output, dict) else None

    if output_r2_key:
        if verbose:
            print(f"Downloading result from R2...", file=sys.stderr)
        downloaded = _download_from_r2(output_r2_key, output_path)
        if downloaded:
            r2_keys_to_cleanup.append(output_r2_key)
            if verbose:
                size_kb = Path(output_path).stat().st_size // 1024
                print(f"  Downloaded: {output_path} ({size_kb}KB)", file=sys.stderr)

    if not downloaded and output_url:
        downloaded = download_from_url(output_url, output_path, verbose=verbose)

    if not downloaded:
        audio_base64 = output.get("audio_base64")
        if audio_base64:
            Path(output_path).write_bytes(base64.b64decode(audio_base64))
            downloaded = True
            if verbose:
                size_kb = Path(output_path).stat().st_size // 1024
                print(f"  Decoded from base64: {output_path} ({size_kb}KB)", file=sys.stderr)

    if not downloaded:
        return {"success": False, "error": f"No audio in result: {list(output.keys()) if isinstance(output, dict) else output}"}

    # Cleanup R2 objects
    for key in r2_keys_to_cleanup:
        _delete_from_r2(key)

    duration = get_audio_duration(output_path)

    result_dict = {
        "success": True,
        "output": output_path,
        "script_chars": len(text),
    }
    if duration:
        result_dict["duration_seconds"] = round(duration, 2)
        result_dict["duration_frames_30fps"] = int(duration * 30)

    return result_dict


# =============================================================================
# RunPod Setup (GraphQL API)
# =============================================================================

RUNPOD_GRAPHQL_URL = "https://api.runpod.io/graphql"


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
    """List all user templates."""
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
    """Find existing Qwen3-TTS template."""
    templates = list_runpod_templates(api_key)
    for t in templates:
        if t.get("name") == QWEN3_TTS_TEMPLATE_NAME:
            return t
        if t.get("imageName") == QWEN3_TTS_DOCKER_IMAGE:
            return t
    return None


def create_runpod_template(api_key: str, verbose: bool = True) -> dict:
    """Create a serverless template for Qwen3-TTS."""
    if verbose:
        print(f"Creating template '{QWEN3_TTS_TEMPLATE_NAME}'...")

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
            "name": QWEN3_TTS_TEMPLATE_NAME,
            "imageName": QWEN3_TTS_DOCKER_IMAGE,
            "isServerless": True,
            "containerDiskInGb": 30,
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
    """Find existing Qwen3-TTS endpoint."""
    endpoints = list_runpod_endpoints(api_key)
    for e in endpoints:
        if e.get("name") == QWEN3_TTS_ENDPOINT_NAME:
            return e
        if e.get("templateId") == template_id:
            return e
    return None


def create_runpod_endpoint(
    api_key: str,
    template_id: str,
    gpu_id: str = "AMPERE_24",
    verbose: bool = True,
) -> dict:
    """Create a serverless endpoint for Qwen3-TTS."""
    if verbose:
        print(f"Creating endpoint '{QWEN3_TTS_ENDPOINT_NAME}'...")

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
            "name": QWEN3_TTS_ENDPOINT_NAME,
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
        if line.startswith("RUNPOD_QWEN3_TTS_ENDPOINT_ID="):
            new_lines.append(f"RUNPOD_QWEN3_TTS_ENDPOINT_ID={endpoint_id}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(f"RUNPOD_QWEN3_TTS_ENDPOINT_ID={endpoint_id}")

    env_path.write_text("\n".join(new_lines))

    if verbose:
        print(f"  Saved: RUNPOD_QWEN3_TTS_ENDPOINT_ID={endpoint_id}")

    return True


def setup_runpod(gpu_id: str = "AMPERE_24", verbose: bool = True) -> dict:
    """Set up RunPod endpoint for Qwen3-TTS."""
    result = {
        "success": False,
        "template_id": None,
        "endpoint_id": None,
        "created_template": False,
        "created_endpoint": False,
    }

    config = get_runpod_config()
    api_key = config.get("api_key")

    if not api_key:
        result["error"] = "RUNPOD_API_KEY not set. Add to .env file first."
        return result

    if verbose:
        print("=" * 60)
        print("RunPod Setup (Qwen3-TTS Speech Generation)")
        print("=" * 60)
        print(f"Docker Image: {QWEN3_TTS_DOCKER_IMAGE}")
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
            template = create_runpod_template(api_key, verbose=verbose)
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
            endpoint = create_runpod_endpoint(
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
            print('  python tools/qwen3_tts.py --text "Hello world" --speaker Ryan --output hello.mp3')
            print()

    except Exception as e:
        result["error"] = str(e)
        if verbose:
            print(f"Error: {e}", file=sys.stderr)

    return result


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate speech using Qwen3-TTS (via RunPod)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Built-in speaker
  python tools/qwen3_tts.py --text "Hello world" --speaker Ryan --output hello.mp3

  # With emotion control
  python tools/qwen3_tts.py --text "Great news!" --instruct "Speak enthusiastically" --output excited.mp3

  # Voice cloning
  python tools/qwen3_tts.py --text "Hello" --ref-audio sample.wav --ref-text "transcript" --output cloned.mp3

  # List voices
  python tools/qwen3_tts.py --list-voices

  # Setup endpoint
  python tools/qwen3_tts.py --setup
        """,
    )

    parser.add_argument(
        "--text", "-t",
        type=str,
        help="Text to synthesize",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output audio file path (.mp3 or .wav)",
    )
    parser.add_argument(
        "--speaker", "-s",
        type=str,
        default="Ryan",
        help="Built-in speaker name (default: Ryan). Use --list-voices to see options.",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="Auto",
        choices=[l.lower() for l in SUPPORTED_LANGUAGES],
        help="Language hint (default: auto)",
    )
    parser.add_argument(
        "--instruct",
        type=str,
        default="",
        help="Natural-language emotion/style instruction (e.g., 'Speak warmly'). Overrides --tone.",
    )
    parser.add_argument(
        "--tone",
        type=str,
        help="Named tone preset (e.g., 'warm', 'professional'). Use --list-tones to see options.",
    )

    # Voice cloning
    parser.add_argument(
        "--ref-audio",
        type=str,
        help="Reference audio file for voice cloning",
    )
    parser.add_argument(
        "--ref-text",
        type=str,
        help="Transcript of reference audio (required with --ref-audio)",
    )

    # Output format
    parser.add_argument(
        "--format",
        type=str,
        default="mp3",
        choices=["mp3", "wav"],
        help="Output format (default: mp3)",
    )

    # Generation parameters
    parser.add_argument(
        "--temperature",
        type=float,
        help="Expressiveness (default: model default ~0.7, range: 0.3-1.5)",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        help="Nucleus sampling (default: model default ~0.8, range: 0.1-1.0)",
    )

    # RunPod options
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="RunPod job timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Set up RunPod endpoint automatically",
    )
    parser.add_argument(
        "--setup-gpu",
        type=str,
        default="AMPERE_24",
        choices=["AMPERE_16", "AMPERE_24", "ADA_24", "AMPERE_48"],
        help="GPU type for RunPod endpoint (default: AMPERE_24)",
    )

    # Utility
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List built-in speakers and exit",
    )
    parser.add_argument(
        "--list-tones",
        action="store_true",
        help="List available tone presets and exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    verbose = not args.json

    # Handle --list-voices
    if args.list_voices:
        print("Built-in speakers:")
        print()
        print(f"  {'Speaker':<12} {'Language'}")
        print(f"  {'-'*12} {'-'*10}")
        for speaker, lang in BUILTIN_SPEAKERS.items():
            print(f"  {speaker:<12} {lang}")
        print()
        print("Supported languages: " + ", ".join(SUPPORTED_LANGUAGES))
        print()
        print("Tip: Use --instruct to control emotion/style:")
        print('  --instruct "Speak warmly and calmly"')
        print('  --instruct "Whisper mysteriously"')
        print('  --instruct "Sound excited and energetic"')
        sys.exit(0)

    # Handle --list-tones
    if args.list_tones:
        print("Tone presets:")
        print()
        print(f"  {'Tone':<15} {'Instruct text'}")
        print(f"  {'-'*15} {'-'*50}")
        for name, text in INSTRUCT_PRESETS.items():
            display = text if text else "(no instruction)"
            print(f"  {name:<15} {display}")
        print()
        print("Usage: --tone warm")
        print("Override with: --instruct \"your custom instruction\"")
        print("Unknown --tone values are treated as raw instruct text.")
        sys.exit(0)

    # Handle --setup
    if args.setup:
        result = setup_runpod(gpu_id=args.setup_gpu, verbose=verbose)
        if args.json:
            print(json.dumps(result, indent=2))
        if result.get("error"):
            sys.exit(1)
        sys.exit(0)

    # Validate required arguments
    if not args.text:
        print("Error: --text is required", file=sys.stderr)
        sys.exit(1)
    if not args.output:
        print("Error: --output is required", file=sys.stderr)
        sys.exit(1)

    # Validate clone mode
    if args.ref_audio and not args.ref_text:
        print("Error: --ref-text is required with --ref-audio", file=sys.stderr)
        sys.exit(1)
    if args.ref_audio and not Path(args.ref_audio).exists():
        print(f"Error: Reference audio not found: {args.ref_audio}", file=sys.stderr)
        sys.exit(1)

    # Capitalize language for API
    language = args.language.capitalize()

    # Resolve tone preset → instruct text
    instruct = resolve_tone(args.tone, args.instruct)

    # Warn if tone/instruct used with clone (clone mode ignores instruct)
    if args.ref_audio and instruct:
        print(
            "Note: --tone/--instruct is ignored when using a cloned voice.\n"
            "  The clone's tone comes from your reference recording.\n"
            "  Tip: Record a new reference with the tone you want.",
            file=sys.stderr,
        )
        instruct = ""

    if verbose:
        print("Generating speech with Qwen3-TTS...")
        if instruct:
            print(f"  Tone: {instruct}")

    result = generate_audio(
        text=args.text,
        output_path=args.output,
        speaker=args.speaker,
        language=language,
        instruct=instruct,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        output_format=args.format,
        timeout=args.timeout,
        verbose=verbose,
        temperature=args.temperature,
        top_p=args.top_p,
    )

    if not result.get("success"):
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        duration = result.get("duration_seconds", 0)
        print(f"Generated: {result['output']}")
        if duration:
            print(f"  Duration: {duration:.1f}s ({int(duration * 30)} frames @ 30fps)")


if __name__ == "__main__":
    main()

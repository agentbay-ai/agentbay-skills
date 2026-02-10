#!/usr/bin/env python3
"""Generate manga/comic-style images using Alibaba DashScope wan2.6-t2i (Tongyi Wanxiang).

This script is designed for use inside the OpenClaw "qwen-wanx-comic-gen" skill.
It calls the asynchronous text-to-image API, polls for completion, downloads
result images, and prints MEDIA: lines that OpenClaw can attach to replies.

API key resolution:
  - Read the primary agent's model provider API key from the OpenClaw config
    (~/.openclaw/openclaw.json). If that value is a "${VARNAME}" placeholder,
    the script will resolve VARNAME from the current environment.

Model: wan2.6-t2i (does NOT support style parameter; describe style in prompt instead)

Example:
  python3 gen.py --prompt "动漫风格，四格校园日常漫画，Q版角色，小龙虾吉祥物" --n 1
"""

import argparse
import json
import os
import sys
import time
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import request, error


# wan2.6-t2i uses the new async protocol endpoint
CREATE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
TASK_STATUS_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"


def default_out_dir() -> Path:
    now = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    base = Path("./tmp")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"qwen-wanx-comic-{now}"


def _resolve_openclaw_config_path() -> Path:
    return Path.home() / ".openclaw" / "openclaw.json"

# def _resolve_openclaw_config_path() -> Path:
#     return Path.home() / ".clawdbot" / "clawdbot.json"

def _load_openclaw_config() -> Optional[Dict[str, Any]]:
    path = _resolve_openclaw_config_path()
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw)
    except Exception:
        return None


def _extract_primary_model_provider(cfg: Dict[str, Any]) -> Optional[str]:
    agents = cfg.get("agents") or {}
    if not isinstance(agents, dict):
        return None

    model_id: Optional[str] = None
    defaults = agents.get("defaults") or {}
    if isinstance(defaults, dict):
        model_field = defaults.get("model")
        if isinstance(model_field, str) and model_field.strip():
            model_id = model_field.strip()
        elif isinstance(model_field, dict):
            primary_val = model_field.get("primary")
            if isinstance(primary_val, str) and primary_val.strip():
                model_id = primary_val.strip()

    if not model_id:
        primary = agents.get("primary") or agents.get("main")
        if isinstance(primary, dict):
            val = primary.get("model")
            if isinstance(val, str) and val.strip():
                model_id = val.strip()

    if not model_id or "/" not in model_id:
        return None

    provider = model_id.split("/", 1)[0].strip()
    return provider or None


def _extract_provider_api_key(cfg: Dict[str, Any], provider: str) -> Optional[str]:
    models = cfg.get("models") or {}
    if not isinstance(models, dict):
        return None
    providers = models.get("providers") or {}
    if not isinstance(providers, dict):
        return None

    entry = providers.get(provider) or {}
    if not isinstance(entry, dict):
        return None

    api_key_val = entry.get("apiKey")
    if not isinstance(api_key_val, str) or not api_key_val.strip():
        return None

    value = api_key_val.strip()
    if value.startswith("${") and value.endswith("}") and len(value) > 3:
        env_name = value[2:-1]
        env_val = os.environ.get(env_name, "").strip()
        return env_val or None

    return value


def get_api_key() -> Optional[str]:
    cfg = _load_openclaw_config()
    if cfg is not None:
        provider = _extract_primary_model_provider(cfg)
        if provider:
            key = _extract_provider_api_key(cfg, provider)
            if key:
                return key
    else:
        key = (os.environ.get("DASHSCOPE_API_KEY") or "").strip()
    return key


def http_post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code} error: {msg}") from e
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"HTTP POST failed: {e}") from e
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response: {e}: {body[:400]}") from e


def http_get_json(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    req = request.Request(url, method="GET")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code} error: {msg}") from e
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"HTTP GET failed: {e}") from e
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response: {e}: {body[:400]}") from e


def _build_prompt_with_style(prompt: str, style: str) -> str:
    """Prepend style hint to prompt for wan2.6-t2i (no style parameter support)."""
    val = (style or "").strip().lower()
    if not val or val == "auto":
        return prompt
    
    # Map common style keywords to Chinese/English descriptive prefixes
    style_prefix_map = {
        "anime": "动漫风格，",
        "3d cartoon": "3D卡通风格，",
        "oil painting": "油画风格，",
        "watercolor": "水彩画风格，",
        "sketch": "素描风格，",
        "chinese painting": "中国画风格，",
        "flat illustration": "扁平插画风格，",
        "portrait": "肖像画风格，",
        "photography": "摄影写实风格，",
    }
    
    prefix = style_prefix_map.get(val, f"{style}风格，")
    return prefix + prompt


def create_task(
    api_key: str,
    prompt: str,
    negative_prompt: Optional[str],
    style: str,
    size: str,
    n: int,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }

    # wan2.6-t2i does NOT support style parameter; merge style hint into prompt
    final_prompt = _build_prompt_with_style(prompt, style)
    
    parameters: Dict[str, Any] = {
        "size": size,
        "n": n,
    }
    
    # New async protocol for wan2.6-t2i requires input.messages format
    input_obj: Dict[str, Any] = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": final_prompt}
                ]
            }
        ]
    }
    
    # Add negative_prompt to parameters (not in messages)
    if negative_prompt:
        parameters["negative_prompt"] = negative_prompt

    payload = {
        "model": "wan2.6-t2i",
        "input": input_obj,
        "parameters": parameters,
    }

    resp = http_post_json(CREATE_TASK_URL, headers, payload)
    output = resp.get("output") or {}
    task_id = output.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise RuntimeError(f"Failed to create task, unexpected response: {json.dumps(resp)[:400]}")
    task_status = output.get("task_status")
    print(f"Created task: {task_id} (status={task_status})")
    return task_id


def wait_for_task(api_key: str, task_id: str, timeout_s: int = 300, poll_interval_s: float = 3.0) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + timeout_s

    while True:
        if time.time() > deadline:
            raise RuntimeError(f"Timed out waiting for task {task_id}")

        url = TASK_STATUS_URL.format(task_id=task_id)
        resp = http_get_json(url, headers)
        output = resp.get("output") or {}
        status = output.get("task_status")
        if status in {"PENDING", "RUNNING"}:
            print(f"Task {task_id} status={status}, waiting...")
            time.sleep(poll_interval_s)
            continue
        if status == "SUCCEEDED":
            print(f"Task {task_id} succeeded")
            return output
        if status in {"FAILED", "CANCELED", "UNKNOWN"}:
            raise RuntimeError(f"Task {task_id} failed with status={status}: {json.dumps(resp)[:400]}")

        # Unexpected status
        print(f"Task {task_id} unknown status={status}, sleeping...")
        time.sleep(poll_interval_s)


def download_images(task_output: Dict[str, Any], out_dir: Path) -> List[Path]:
    """Download images from wan2.6-t2i task output (new protocol format)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: List[Path] = []
    
    # New protocol: output.choices[].message.content[] contains image URLs
    choices = task_output.get("choices") or []
    if not isinstance(choices, list):
        return saved_paths
    
    idx = 0
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message") or {}
        if not isinstance(message, dict):
            continue
        content = message.get("content") or []
        if not isinstance(content, list):
            continue
        
        for item in content:
            if not isinstance(item, dict):
                continue
            url = item.get("image")
            if not isinstance(url, str) or not url:
                continue
            
            idx += 1
            filename = f"{idx:03d}-qwen-wanx-comic.png"
            path = out_dir / filename
            try:
                print(f"Downloading image {idx} from {url} ...")
                request.urlretrieve(url, path.as_posix())
                saved_paths.append(path.resolve())
            except Exception as e:  # noqa: BLE001
                print(f"Failed to download image {idx}: {e}", file=sys.stderr)
    
    return saved_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate manga/comic-style images via DashScope wan2.6-t2i")
    parser.add_argument("--prompt", required=True, help="Main prompt describing the manga/comic scene")
    parser.add_argument("--negative-prompt", default="", help="Negative prompt to avoid unwanted styles")
    parser.add_argument("--style", default="anime", help="Style hint (anime, 3d cartoon, sketch, etc; will be prepended to prompt)")
    parser.add_argument("--size", default="1280*1280", help="Image size (wan2.6 supports 1280*1280~1440*1440 total pixels, ratio 1:4~4:1)")
    parser.add_argument("--n", type=int, default=1, help="Number of images to generate (1-4)")
    parser.add_argument("--output-dir", default="", help="Output directory (default: ./tmp/qwen-wanx-comic-<timestamp>)")
    
    args = parser.parse_args()
    
    if args.n < 1 or args.n > 4:
        print("Error: --n must be between 1 and 4", file=sys.stderr)
        return 1
    
    api_key = get_api_key()
    if not api_key:
        print("Error: missing API key for DashScope/wan2.6-t2i.", file=sys.stderr)
        return 1
    
    out_dir = Path(args.output_dir).expanduser() if args.output_dir else default_out_dir()

    try:
        task_id = create_task(
            api_key=api_key,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt or None,
            style=args.style,
            size=args.size,
            n=args.n,
        )
        output = wait_for_task(api_key, task_id)
        
        # wan2.6-t2i returns images in output.choices[].message.content[]
        saved_paths = download_images(output, out_dir)
        if not saved_paths:
            raise RuntimeError("No images were successfully downloaded.")

        print("\nImages saved:")
        for path in saved_paths:
            print(f" - {path}")
            # OpenClaw parses MEDIA tokens and will attach the files on supported providers.
            print(f"MEDIA: {path}")

        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"Error generating images: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

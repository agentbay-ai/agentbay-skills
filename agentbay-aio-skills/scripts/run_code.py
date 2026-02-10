#!/usr/bin/env python3
import argparse
import asyncio
import base64
import json
import os
import sys
import time

from agentbay import AsyncAgentBay, CreateSessionParams


def _api_key_config_path() -> str:
    """Return the API key config file path for the current platform."""
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        # Windows: %USERPROFILE%\.config\agentbay\api_key
        base = os.environ.get("USERPROFILE", home)
        return os.path.join(base, ".config", "agentbay", "api_key")
    # Unix-like: $XDG_CONFIG_HOME/agentbay/api_key or ~/.config/agentbay/api_key
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    return os.path.join(xdg, "agentbay", "api_key")


def _read_api_key_from_config() -> str:
    """Read API key from config file if present. Returns empty string if not found or on error."""
    path = _api_key_config_path()
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return (f.read() or "").strip()
    except OSError:
        pass
    return ""


def _load_code(args: argparse.Namespace) -> str:
    if args.code and args.code_file:
        raise ValueError("Use only one of --code or --code-file.")
    if args.code:
        return args.code
    if args.code_file:
        with open(args.code_file, "r", encoding="utf-8") as f:
            return f.read()
    raise ValueError("Either --code or --code-file is required.")


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run code in AgentBay code_latest sandbox via run_code."
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("AGENTBAY_API_KEY", ""),
        help="AgentBay API key (or set AGENTBAY_API_KEY).",
    )
    parser.add_argument(
        "--language",
        default="python",
        help="Language for run_code (python/javascript/r/java).",
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=60,
        help="Execution timeout in seconds (<= 60).",
    )
    parser.add_argument("--code", help="Inline code to execute.")
    parser.add_argument("--code-file", help="Path to a file containing code to execute.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output.",
    )

    args = parser.parse_args()

    if not args.api_key:
        args.api_key = _read_api_key_from_config()
    if not args.api_key:
        path = _api_key_config_path()
        print(
            f"Missing API key. Apply for an API key at the AgentBay console:\n"
            f"  https://agentbay.console.aliyun.com/service-management\n"
            f"Then save it to the local config file: {path}\n"
            f"(Alternatively, set the AGENTBAY_API_KEY environment variable.)",
            file=sys.stderr,
        )
        return 2

    try:
        code = _load_code(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    agent_bay = AsyncAgentBay(api_key=args.api_key)
    session_result = await agent_bay.create(CreateSessionParams(image_id="code_latest"))

    try:
        code_result = await session_result.session.code.run_code(
            code, args.language, timeout_s=args.timeout_s
        )
        if args.json:
            payload = {
                "success": code_result.success,
                "result": code_result.result,
                "logs": {
                    "stdout": code_result.logs.stdout,
                    "stderr": code_result.logs.stderr,
                },
                "error_message": code_result.error_message,
            }
            print(json.dumps(payload, ensure_ascii=True))
        else:
            if code_result.success:
                # Check for rich output in results
                if hasattr(code_result, 'results') and code_result.results:
                    for res in code_result.results:
                        # Handle Images (PNG, JPEG, SVG)
                        img_data = None
                        ext = ""
                        if hasattr(res, 'png') and res.png:
                            img_data = res.png
                            ext = "png"
                        elif hasattr(res, 'jpeg') and res.jpeg:
                            img_data = res.jpeg
                            ext = "jpg"
                        elif hasattr(res, 'svg') and res.svg:
                            img_data = res.svg
                            ext = "svg"

                        if img_data:
                            try:
                                timestamp = int(time.time())
                                filename = f"chart_{timestamp}.{ext}"
                                if ext == "svg":
                                    with open(filename, "w", encoding="utf-8") as f:
                                        f.write(img_data)
                                    print(f"Successfully saved {filename}")
                                else:
                                    if isinstance(img_data, str):
                                        img_bytes = base64.b64decode(img_data)
                                    else:
                                        img_bytes = img_data
                                    with open(filename, "wb") as f:
                                        f.write(img_bytes)
                                    print(f"Successfully saved {filename} ({len(img_bytes)} bytes)")
                            except Exception as e:
                                print(f"Error saving image: {e}", file=sys.stderr)

                        # Handle HTML
                        if hasattr(res, 'html') and res.html:
                            print(f"\n[HTML Output]:\n{res.html}")

                        # Handle Markdown
                        if hasattr(res, 'markdown') and res.markdown:
                            print(f"\n[Markdown Output]:\n{res.markdown}")

                        # Handle LaTeX
                        if hasattr(res, 'latex') and res.latex:
                            print(f"\n[LaTeX Output]:\n{res.latex}")

                        # Handle JSON
                        if hasattr(res, 'json') and res.json:
                            print(f"\n[JSON Output]:\n{json.dumps(res.json, indent=2)}")

                        # Handle Chart Data
                        if hasattr(res, 'chart') and res.chart:
                            print(f"\n[Chart Data]:\n{json.dumps(res.chart, indent=2)}")

                        # Handle Text (if not main result, to avoid duplication)
                        if hasattr(res, 'text') and res.text and not getattr(res, 'is_main_result', False):
                             print(f"\n[Text Output]:\n{res.text}")

                if code_result.result:
                    print(code_result.result)
                if code_result.logs.stdout:
                    print("".join(code_result.logs.stdout), end="")
                if code_result.logs.stderr:
                    print("".join(code_result.logs.stderr), end="", file=sys.stderr)
            else:
                print(code_result.error_message or "run_code failed", file=sys.stderr)
                return 1
    finally:
        await session_result.session.delete()

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import sys

from agentbay import AsyncAgentBay, CreateSessionParams


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
        print("Missing API key. Provide --api-key or set AGENTBAY_API_KEY.", file=sys.stderr)
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

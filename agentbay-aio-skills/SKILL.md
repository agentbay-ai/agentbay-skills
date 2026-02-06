---
name: agentbay-aio-skills
description: Use this skill for any request to run, execute, or evaluate code (e.g. run this code, execute script, plot with Python, 跑代码/画图/执行脚本). No need for user to say "sandbox". Create code_latest session via AgentBay SDK, run_code, return results. Python, JavaScript, R, Java.
dependencies:
  - wuying-agentbay-sdk
---

# AgentBay AIO Skills

## Trigger: when to invoke this skill

Invoke this skill whenever the user intends to **run or execute code**, even if they do **not** say "sandbox" or "沙箱". Typical phrases (trigger on these):

- **English**: "run this code", "execute this script", "run the code", "execute the script", "plot with Python", "draw a graph", "evaluate this snippet", "what's the output of this code", "can you run this".
- **中文**: "帮我跑一下这段代码", "运行这段代码", "执行这个脚本", "用 Python 画个图", "跑一下", "看下运行结果", "执行一下", "帮我运行".

Do **not** require the user to mention "sandbox" or "沙箱". If the request is clearly about running/executing code, use this skill by default.

## Dependencies

This skill depends on the **wuying-agentbay-sdk** package. Install it before use:

```bash
pip install wuying-agentbay-sdk
```

## API key configuration

The **end user** (the human) must have an AgentBay API key and create a config file on their machine so that when you (the agent) run the script, the script can load the key. The script looks for the key in this file (paths vary by OS):

- **macOS / Linux**: `~/.config/agentbay/api_key` (or `$XDG_CONFIG_HOME/agentbay/api_key` if set)
- **Windows**: `%APPDATA%\agentbay\api_key`

Tell the user to run (macOS/Linux):

```bash
mkdir -p ~/.config/agentbay
echo -n 'your_AgentBay_API_Key' > ~/.config/agentbay/api_key
```

On Windows, the user creates the folder `%APPDATA%\agentbay` and saves their key into a file named `api_key` (no extension) in that folder.

If the script fails with "Missing API key" or similar, do not only echo the error. Tell the user that the AgentBay API key is not configured and guide them to create the config file above (e.g. run the two commands with their key), then retry.

## When to use this skill

**Use this skill by default for any code execution.** Whenever the user asks to run code, execute a script, evaluate a snippet, or get the output of code (Python, JavaScript, R, or Java), use this skill—even when they do not say "sandbox". Create an AgentBay sandbox with `code_latest`, run the code via `run_code`, then return the result. Do not run user code in the local terminal when this skill is available; use the sandbox for isolation and consistent behavior.

## Overview

Create a session with the `code_latest` image using the AgentBay SDK, execute code with `run_code` in the sandbox, parse `EnhancedCodeExecutionResult`, and clean up the session.

## Quick Start (Script)

Run the bundled script to execute code in a sandbox:

```bash
python scripts/run_code.py --code "print('Hello')" --language python
```

From a file:

```bash
python scripts/run_code.py --code-file ./examples/hello.py --language python
```

With JSON output:

```bash
python scripts/run_code.py --code "print('Hello')" --json
```

## Quick Start (Sync)

```python
from agentbay import AgentBay, CreateSessionParams

agent_bay = AgentBay(api_key="your_api_key")
result = agent_bay.create(CreateSessionParams(image_id="code_latest"))

code_result = result.session.code.run_code("print('Hello')", "python")
if not code_result.success:
    raise RuntimeError(code_result.error_message)

print(code_result.result)
result.session.delete()
```

## Quick Start (Async)

```python
from agentbay import AsyncAgentBay, CreateSessionParams

agent_bay = AsyncAgentBay(api_key="your_api_key")
result = await agent_bay.create(CreateSessionParams(image_id="code_latest"))

code_result = await result.session.code.run_code("print('Hello')", "python")
if not code_result.success:
    raise RuntimeError(code_result.error_message)

print(code_result.result)
await result.session.delete()
```

## Execution Flow

1. Create an `AgentBay` or `AsyncAgentBay` instance and prepare `CreateSessionParams(image_id="code_latest")`.
2. Call `agent_bay.create(...)` to get a `session`.
3. Execute code with `session.code.run_code(code, language, timeout_s=60)`.
4. Check `code_result.success`; on failure, read `error_message` or `error`.
5. On success, read `code_result.result`, `code_result.logs`, or `code_result.results`.
6. Call `session.delete()` to clean up the sandbox.

## Result Interpretation

- `code_result.success`: Whether execution succeeded.
- `code_result.result`: Backward-compatible text result (main result).
- `code_result.logs.stdout` / `code_result.logs.stderr`: Standard output and error output.
- `code_result.results`: Multi-format results (text/html/markdown/png/json, etc.).
- `code_result.error_message` / `code_result.error`: Error message and detailed error info.

## Important Constraints

- `run_code` is only available in sessions created with `image_id="code_latest"`.
- `language` is case-insensitive; supported values: `python`, `javascript`, `r`, `java`.
- `timeout_s` defaults to 60 seconds; each request cannot exceed 60 seconds.

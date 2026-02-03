---
name: agentbay-aio-skills
description: Use the AgentBay SDK to create a code_latest session in an agentbay sandbox, run code via run_code, and return results. Use when executing Python/JavaScript/R/Java in an isolated sandbox and reading outputs/logs/errors.
---

# AgentBay AIO Skills

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

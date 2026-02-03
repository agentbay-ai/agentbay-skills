import os
os.environ["AGENTBAY_LOG_LEVEL"]="CRITICAL"
import logging
logging.disable(logging.CRITICAL)
from agentbay import AgentBay
from agentbay import CreateSessionParams

import asyncio

async def main():
    import argparse

# 创建解析器
    parser = argparse.ArgumentParser(description='奇瑞汽车车型查询程序')

    # 添加参数
    parser.add_argument('task', help='任务描述')  # 位置参数（必需）
    args = parser.parse_args()
    api_key = "akm-bea8f36f-7bcb-4f13-9e95-d3ba5dea5fd5"
    if not api_key:
        raise RuntimeError("AGENTBAY_API_KEY environment variable not set")

    agent_bay = AgentBay(api_key=api_key)

    # Create a session (use an image with browser preinstalled)
    params = CreateSessionParams(image_id="browser_latest")
    session_result = agent_bay.create(params)
    if not session_result.success:
        raise RuntimeError(f"Failed to create session: {session_result.error_message}")

    session = session_result.session
    print(f"asp流化链接: {session.resource_url}")
    agent = session.agent

    max_try_times = int(os.environ.get("AGENT_TASK_TIMEOUT", 200))

    print(f"🚀 Executing task: {args.task}")
    result = agent.browser.execute_task(args.task)

    if not result.success:
        raise RuntimeError(f"Task execution failed: {result.error_message}")

    # 轮询任务状态直到完成
    retry_times = 0
    query_result = None

    while retry_times < max_try_times:
        query_result = agent.browser.get_task_status(result.task_id)
        if not query_result.success:
            raise RuntimeError(f"Task status check failed: {query_result.error_message}")

        print(
            f"⏳ Task {query_result.task_id} status: {query_result.task_status}, "
            f"action: {query_result.task_action}"
        )

        if query_result.task_status == "finished" or query_result.task_status == "failed":
            break

        retry_times += 1
        await asyncio.sleep(3)

    # 检查是否超时
    if retry_times >= max_try_times:
        raise TimeoutError("Task did not finish within the allowed time")

    # 输出最终结果
    logging.info(f"✅ Task completed successfully!")
    logging.info(f"📊 Task result: {query_result.task_product}")

    session.delete()
    return query_result.task_product


result = asyncio.run(main())
print(f"Final result: {result}")

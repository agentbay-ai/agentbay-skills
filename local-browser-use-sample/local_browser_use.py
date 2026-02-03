from browser_use import Agent, Controller, ActionResult
from dotenv import load_dotenv
import os
from pydantic import SecretStr
import asyncio
from browser_use.browser import BrowserProfile, BrowserSession
from wuying_mllm_service import config
import argparse
import json
import logging
logging.disable(logging.CRITICAL)

browser_profile = BrowserProfile(
    headless=True,
    no_viewport=False,
    highlight_elements=False,
    enable_default_extensions=False,
)

load_dotenv()
api_key = os.getenv('QWEN_API_KEY', '')
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# client = OpenAI(name='gpt-4o', base_url='https://api.wentuo.ai/v1', api_key="sk-TuZoDBisg3etxZAxbf5AX1uJu9Af5Ysdo8ph6pS7E3eh7fML")

# controller = Controller(exclude_actions=['search_google', 'open_tab', 'go_to_url', 'extract_content'])

task = {
    "task_id": "easy026",
    "confirmed_task": "Find the next available date for Albion Basin.",
    "website": "https://www.recreation.gov/",
    "reference_length": 3,
    "level": "easy"
  }

task_ins = """1. 导航到 https://www.instagram.com/ 使用15605190875登录账号，密码是xiao123，如果遇到消息选项卡外观更新，请点击确认
2. 滚动网页到推荐帖子的部分
3. 在推荐帖子中开始寻找粉丝数大于10000的博主账号（在每个头像处悬停，会出现博主信息弹窗，查看粉丝数是否大于10000，找到一个就停止滚动网页
4. 在头像处悬停，会出现博主信息弹窗，如果未关注则点击关注（如果点击到取关弹窗，不要点击取关按钮，点击取消），然后点击发消息按钮进行私信聊天弹窗
5. 在私信聊天弹窗输入 Hello！ 之后点击发送
6. 发送成功后，关闭私信聊天弹窗
7. 继续在推荐帖子中向下滚动，寻找下一个粉丝数大于10000的博主账号
8. 重复步骤3-7，至少完成3位博主账号的消息发送
"""

new_task = "1. 打开携程 2. 输入出发站杭州 并选择杭州 3. 输入到达站上海 并选择上海 4. 日期选择后天 5. 点击 只搜高铁动车 6. 点击搜索按钮，等待5秒之后，提取最近一班从杭州到上海的列车信息"

async def main():
    config.add_llm(model_service="browser", api_key="sk-813cb5ece43340cdad016d6af739e10d", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", model="qwen3-vl-32b-instruct")
    import argparse

# 创建解析器
    parser = argparse.ArgumentParser(description='程序描述信息')

    # 添加参数
    parser.add_argument('task', help='任务描述')  # 位置参数（必需）
    args = parser.parse_args()
    
    # Create agent with the model
    browser_session = BrowserSession(
        browser_profile=browser_profile,
    )
    await browser_session.start()
    agent = Agent(
        task=args.task,
        # task=task,
        # controller=controller,
        llm=config.get_llm('browser'),
        # page_extraction_llm=client,
        # planner_llm=client,
        save_conversation_path="logs/conversation",
        browser_session=browser_session,
        use_vision=True,
        use_thinking=True,
    )
    await agent.run()
    final_res = agent.history.final_result()
    final_result_str = json.dumps(final_res, ensure_ascii=False) if final_res is not None else None
    print(final_result_str)

asyncio.run(main())

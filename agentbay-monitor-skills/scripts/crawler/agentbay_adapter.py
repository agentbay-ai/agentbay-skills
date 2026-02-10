"""
AgentBay 适配器模块
提供与 AgentBay 交互的核心功能，用于社交媒体平台爬取
"""
import asyncio
import json
from typing import Dict, Any, Optional

# AgentBay imports
try:
    from agentbay import AsyncAgentBay, CreateSessionParams, BrowserOption, BrowserContext
    AGENTBAY_AVAILABLE = True
except ImportError as e:
    AGENTBAY_AVAILABLE = False
    print("⚠️ 警告: wuying-agentbay-sdk 未安装，无法使用 AgentBay")
    print(f"   导入错误详情: {e}")

from .platform_config import PlatformConfig


class AgentBayAdapter:
    """AgentBay适配器类"""

    def __init__(self, api_key: str, context_name: str = "sentiment-analysis"):
        """
        初始化适配器

        Args:
            api_key: AgentBay API密钥
            context_name: Browser Context 名称
        """
        if not AGENTBAY_AVAILABLE:
            raise ImportError("wuying-agentbay-sdk 未安装，无法使用 AgentBay")

        self.api_key = api_key
        self.context_name = context_name
        self.agent_bay = None
        self.session = None
        self.context = None

    async def create_session(self, platform_config: PlatformConfig) -> Dict[str, Any]:
        """
        创建浏览器会话

        Args:
            platform_config: 平台配置

        Returns:
            包含 session、context、agent_bay 的字典，如果失败返回错误信息
        """
        try:
            self.agent_bay = AsyncAgentBay(api_key=self.api_key)

            # 创建或获取 Browser Context
            print(f"📦 创建/获取 Browser Context: {self.context_name}")
            context_result = await self.agent_bay.context.get(self.context_name, create=False)
            context_is_new = False

            if not context_result.success or not context_result.context:
                print(f"   Context 不存在，正在创建新的 Context...")
                context_result = await self.agent_bay.context.get(self.context_name, create=True)
                context_is_new = True

            if not context_result.success or not context_result.context:
                error_msg = context_result.error_message or 'Unknown error'
                return {
                    "success": False,
                    "error": f"创建 Context 失败: {error_msg}"
                }

            self.context = context_result.context
            if context_is_new:
                print(f"✅ 新 Context 已创建，ID: {self.context.id}")
            else:
                print(f"✅ 已存在的 Context 已加载，ID: {self.context.id}")

            # 创建 BrowserContext 配置
            browser_context = BrowserContext(self.context.id, auto_upload=True)

            # 创建浏览器会话
            print("📡 正在创建 AgentBay 浏览器会话...")
            params = CreateSessionParams(
                image_id="linux_latest",
                browser_context=browser_context
            )
            session_result = await self.agent_bay.create(params)

            if not session_result.success:
                return {
                    "success": False,
                    "error": session_result.error_message or "Failed to create session"
                }

            self.session = session_result.session
            print(f"✅ 会话已创建: {self.session.session_id}\n")

            # 初始化浏览器
            print("🌐 正在初始化浏览器...")
            browser_option = BrowserOption()
            browser_init = await self.session.browser.initialize(browser_option)
            if not browser_init:
                return {
                    "success": False,
                    "error": "Browser initialization failed"
                }
            print("✅ 浏览器已初始化\n")

            return {
                "success": True,
                "agent_bay": self.agent_bay,
                "session": self.session,
                "context": self.context
            }

        except Exception as e:
            error_msg = f"创建 Session 失败: {str(e)}"
            print(f"\n❌ 错误: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

    async def execute_crawl_task(
        self,
        task_prompt: str,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        执行爬取任务

        Args:
            task_prompt: 任务提示词
            timeout: 超时时间（秒）

        Returns:
            任务执行结果
        """
        if not self.session:
            return {
                "success": False,
                "error": "Session 未创建，请先调用 create_session"
            }

        try:
            print(f"🚀 正在执行爬取任务...")
            result = await self.session.agent.browser.execute_task_and_wait(
                task_prompt,
                timeout,
                True,
                None
            )

            if not result.success:
                return {
                    "success": False,
                    "error": result.error_message or result.task_status,
                    "task_status": result.task_status
                }

            # 解析结果
            task_result = result.task_result
            if isinstance(task_result, str):
                try:
                    task_result = json.loads(task_result)
                except json.JSONDecodeError:
                    pass

            return {
                "success": True,
                "result": task_result,
                "raw_result": result.task_result
            }

        except Exception as e:
            import traceback
            error_msg = f"执行爬取任务失败: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"   详细错误:\n{traceback.format_exc()}")
            return {
                "success": False,
                "error": error_msg
            }

    async def close(self):
        """关闭会话"""
        if self.session and self.agent_bay:
            try:
                await asyncio.sleep(2)

                # 显式同步 Context（保存浏览器状态）
                try:
                    sync_result = await self.session.context.sync()
                    if sync_result.success:
                        print("✅ Context 已同步")
                except Exception as sync_error:
                    print(f"⚠️ Context 同步出错: {sync_error}")

                # 删除 session
                await self.agent_bay.delete(self.session, sync_context=False)
                print("✅ 会话已关闭")
            except Exception as e:
                print(f"⚠️ 关闭会话时出错: {e}")


async def create_crawler_session(
    api_key: str,
    context_name: str,
    platform_config: PlatformConfig
) -> AgentBayAdapter:
    """
    创建爬取会话的便捷函数

    Args:
        api_key: AgentBay API密钥
        context_name: Browser Context 名称
        platform_config: 平台配置

    Returns:
        AgentBayAdapter实例
    """
    adapter = AgentBayAdapter(api_key, context_name)
    result = await adapter.create_session(platform_config)
    if not result.get("success"):
        raise Exception(result.get("error", "创建会话失败"))
    return adapter

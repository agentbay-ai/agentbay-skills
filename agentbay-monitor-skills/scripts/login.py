#!/usr/bin/env python3
"""
登录模块

提供社交媒体平台的登录功能，使用 AgentBay 沙箱和 CDP 协议进行登录。

API Key 从 ~/.config/agentbay/api_key 或环境变量 AGENTBAY_API_KEY 读取。

使用方法：
    python scripts/login.py [--platform xhs] [--context-name sentiment-analysis]
"""

import asyncio
import os
import sys
import traceback
from pathlib import Path

# 从技能根目录运行 python scripts/login.py 时，将 scripts 加入 path 以便导入
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))


def get_api_key():
    """从 ~/.config/agentbay/api_key 或环境变量 AGENTBAY_API_KEY 获取 API Key"""
    file_path = Path.home() / ".config" / "agentbay" / "api_key"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.touch()
    if os.environ.get("AGENTBAY_API_KEY"):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(os.environ.get("AGENTBAY_API_KEY"))
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
        if not api_key:
            api_key = None
    except Exception as e:
        api_key = None
    return api_key

# AgentBay imports
try:
    from agentbay import AsyncAgentBay, CreateSessionParams, BrowserOption, BrowserContext
    AGENTBAY_AVAILABLE = True
except ImportError as e:
    AGENTBAY_AVAILABLE = False
    print("⚠️ 警告: wuying-agentbay-sdk 未安装，无法使用 AgentBay")
    print(f"   导入错误详情: {e}")

# 导入平台配置
from crawler.platform_config import get_platform_config


async def login_only(
    agentbay_api_key: str,
    platform: str = None,
    context_name: str = None
) -> bool:
    """
    只执行登录流程，登录完成后保存状态并退出

    简化流程：
    1. 创建 Session 并初始化浏览器
    2. 使用 CDP 直接导航到登录页面（不使用 agent）
    3. 打开流化页面让用户登录
    4. 等待用户回车确认
    5. 保存登录状态到 Context

    Args:
        agentbay_api_key: AgentBay API密钥
        platform: 平台标识（"xhs", "weibo", "douyin", "zhihu"等），必需
        context_name: Browser Context 名称，必需

    Returns:
        True: 流程完成
        False: 流程失败
    """
    if not AGENTBAY_AVAILABLE:
        print("❌ wuying-agentbay-sdk 未安装，无法使用 AgentBay")
        return False

    # 获取平台配置
    if platform is None:
        platform = "xhs"

    try:
        platform_config = get_platform_config(platform)
    except ValueError as e:
        print(f"❌ {e}")
        return False

    # context_name 必须由调用方传入
    if context_name is None:
        print("❌ 错误: 未提供 context_name 参数")
        return False

    login_url = platform_config.base_url  # 使用平台首页作为登录入口
    platform_name = platform_config.display_name

    print(f"\n{'='*60}")
    print(f"🔐 登录模式：只执行登录流程")
    print(f"   平台: {platform_name}")
    print(f"   Context: {context_name}")
    print(f"{'='*60}\n")

    agent_bay = None
    session = None
    context = None

    try:
        # 创建 AgentBay 实例
        agent_bay = AsyncAgentBay(api_key=agentbay_api_key)

        # 创建或获取持久化的 Browser Context
        print(f"📦 创建/获取 Browser Context: {context_name}")
        context_result = await agent_bay.context.get(context_name, create=False)
        context_is_new = False

        if not context_result.success or not context_result.context:
            print(f"   Context 不存在，正在创建新的 Context...")
            context_result = await agent_bay.context.get(context_name, create=True)
            context_is_new = True

        if not context_result.success or not context_result.context:
            error_msg = context_result.error_message or 'Unknown error'
            print(f"❌ 创建 Context 失败: {error_msg}")
            return False

        context = context_result.context
        if context_is_new:
            print(f"✅ 新 Context 已创建，ID: {context.id}")
        else:
            print(f"✅ 已存在的 Context 已加载，ID: {context.id}")

        # 创建 BrowserContext 配置
        browser_context = BrowserContext(context.id, auto_upload=True)

        # 创建浏览器会话
        print("📡 正在创建 AgentBay 浏览器会话...")
        params = CreateSessionParams(
            image_id="linux_latest",
            browser_context=browser_context
        )
        session_result = await agent_bay.create(params)

        if not session_result.success:
            print(f"❌ 创建会话失败: {session_result.error_message}")
            return False

        session = session_result.session
        print(f"✅ 会话已创建: {session.session_id}\n")

        # 初始化浏览器
        print("🌐 正在初始化浏览器...")
        browser_init = await session.browser.initialize(BrowserOption())
        if not browser_init:
            print("❌ 浏览器初始化失败")
            return False
        print("✅ 浏览器已初始化\n")

        # 获取流化页面 URL
        resource_url = None
        try:
            if hasattr(session_result, 'resource_url') and session_result.resource_url:
                resource_url = session_result.resource_url
            elif hasattr(session, 'resource_url') and session.resource_url:
                resource_url = session.resource_url
        except:
            pass

        if resource_url:
            print(f"📱 流化页面 URL: {resource_url}")
            try:
                import webbrowser
                webbrowser.open(resource_url)
                print("✅ 流化页面已打开\n")
            except:
                print(f"   请手动复制以下链接在浏览器中打开: {resource_url}\n")

        # 使用 CDP 直接导航到登录页面（不使用 agent）
        print("=" * 60)
        print("🔐 登录流程")
        print("=" * 60)
        print(f"🚀 正在使用 CDP 导航到{platform_name}登录页面: {login_url}")

        try:
            from playwright.async_api import async_playwright

            # 获取 CDP endpoint URL
            endpoint_url = session.browser.get_endpoint_url()
            if asyncio.iscoroutine(endpoint_url):
                endpoint_url = await endpoint_url

            if endpoint_url:
                async with async_playwright() as p:
                    browser_pw = await p.chromium.connect_over_cdp(endpoint_url)
                    context_pw = browser_pw.contexts[0] if browser_pw.contexts else await browser_pw.new_context()
                    page_pw = context_pw.pages[0] if context_pw.pages else await context_pw.new_page()

                    # 使用 CDP 直接导航
                    await page_pw.goto(login_url, wait_until="domcontentloaded", timeout=30000)
                    print(f"✅ 已导航到登录页面\n")

                    await browser_pw.close()
            else:
                print(f"⚠️ 无法获取 CDP endpoint URL，跳过自动导航")
                print(f"   请在流化页面中手动导航到: {login_url}\n")
        except Exception as e:
            print(f"⚠️ CDP 导航失败: {e}")
            print(f"   请在流化页面中手动导航到: {login_url}\n")
            print(f"   详细错误:\n{traceback.format_exc()}")

        # 提示用户完成登录
        print(f"💡 请在已打开的流化页面中完成登录操作")
        print(f"   登录完成后，请在终端按 Enter 键继续\n")

        try:
            input("👉 登录完成后，请按 Enter 键继续: ")
            print("\n✅ 登录流程完成\n")
            return True
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️ 用户取消操作")
            return False

    except Exception as e:
        print(f"❌ 登录过程中出错: {str(e)}")
        print(f"   详细错误:\n{traceback.format_exc()}")
        return False

    finally:
        # 删除 session 并同步 Context（保存登录状态）
        if session and agent_bay:
            try:
                await asyncio.sleep(2)  # 等待浏览器数据落盘

                # 显式同步 Context（保存登录状态）
                print("\n🔄 正在同步登录状态到 Context...")
                try:
                    sync_result = await session.context.sync()
                    if sync_result.success:
                        print("✅ Context 同步成功")
                    else:
                        print(f"⚠️ Context 同步失败: {sync_result.error_message if hasattr(sync_result, 'error_message') else 'Unknown error'}")
                except Exception as sync_error:
                    print(f"⚠️ Context 同步出错: {sync_error}")

                # 删除 session（不再需要 sync_context=True，因为已经手动同步了）
                delete_result = await agent_bay.delete(session, sync_context=False)
                if delete_result.success:
                    print(f"✅ Session 已删除 (RequestID: {delete_result.request_id})")
                    print("   💡 登录状态已保存，下次运行爬虫时会自动使用已保存的登录状态")
                else:
                    print(f"\n⚠️ 删除 Session 失败: {delete_result.error_message}")
            except Exception as e:
                print(f"\n⚠️ 删除会话/同步 Context 时出错: {e}")
                print(f"   详细错误:\n{traceback.format_exc()}")


def _parse_args():
    import argparse
    p = argparse.ArgumentParser(description="登录目标平台并保存 Browser Context。仅 AGENTBAY_API_KEY 从环境读取，其余传参。")
    p.add_argument("--platform", "-p", default="xhs", help="平台: xhs/weibo/douyin/zhihu")
    p.add_argument("--context-name", "-c", default="sentiment-analysis", help="Browser Context 名称")
    return p.parse_args()


async def main():
    """主函数：仅 AGENTBAY_API_KEY 从 ~/.config/agentbay/api_key 或环境变量读取，platform/context_name 由主 Agent 传参"""
    args = _parse_args()
    api_key = get_api_key()
    if not api_key:
        print("❌ 错误: 未提供 AgentBay API 密钥")
        print("请设置环境变量 AGENTBAY_API_KEY 或创建 ~/.config/agentbay/api_key 文件")
        print("获取 API Key: https://agentbay.console.aliyun.com/service-management")
        sys.exit(1)

    try:
        success = await login_only(
            agentbay_api_key=api_key,
            platform=args.platform,
            context_name=args.context_name,
        )
        if success:
            print("\n" + "=" * 60)
            print("✅ 登录流程完成")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ 登录流程失败")
            print("=" * 60)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

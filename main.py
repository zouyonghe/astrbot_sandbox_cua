import asyncio

from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.computer.computer_client import (
    cleanup_sandbox_provider,
    detach_sandbox_provider,
    register_sandbox_provider,
)

from .provider import CuaSandboxProvider
from .tools import CuaKeyboardTypeTool, CuaMouseClickTool, CuaScreenshotTool


@register(
    "astrbot_sandbox_cua",
    "AstrBot Team",
    "为 AstrBot 提供 CUA 沙盒运行时。",
    "0.1.0",
)
class CuaSandboxRuntimePlugin(Star):
    def __init__(self, context: Context, config=None) -> None:
        super().__init__(context)
        self.provider = CuaSandboxProvider(plugin_config=config)
        register_sandbox_provider(
            self.provider,
            replace=True,
            tools=[
                CuaScreenshotTool(),
                CuaMouseClickTool(),
                CuaKeyboardTypeTool(),
            ],
        )

    async def terminate(self) -> None:
        provider = getattr(self, "provider", None)
        if provider is None:
            return
        provider_id = getattr(provider, "provider_id", None)
        if not provider_id:
            return
        try:
            await cleanup_sandbox_provider(provider_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning(
                "CUA sandbox provider cleanup failed during termination: provider=%s",
                provider_id,
                exc_info=True,
            )
            raise
        finally:
            detach_sandbox_provider(provider_id)

    @filter.command("cua_sandbox_runtime")
    async def runtime_status(self, event):
        yield event.plain_result("CUA 沙盒运行时提供器已注册。")

from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.computer.computer_client import (
    register_sandbox_provider,
    unregister_sandbox_provider,
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
        unregister_sandbox_provider(self.provider.provider_id, force=True)

    @filter.command("cua_sandbox_runtime")
    async def runtime_status(self, event):
        yield event.plain_result("CUA 沙盒运行时已注册。")

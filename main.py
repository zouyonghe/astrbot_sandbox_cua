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
    "CUA sandbox runtime provider for AstrBot",
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
        await cleanup_sandbox_provider(self.provider.provider_id)
        detach_sandbox_provider(self.provider.provider_id)

    @filter.command("cua_sandbox_runtime")
    async def runtime_status(self, event):
        yield event.plain_result("CUA sandbox runtime provider is registered.")

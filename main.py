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
    "CUA sandbox runtime provider for AstrBot",
    "0.1.0",
)
class CuaSandboxRuntimePlugin(Star):
    def __init__(self, context: Context, config=None) -> None:
        super().__init__(context)
        self.provider = CuaSandboxProvider()
        self.provider.plugin_config = config or {}
        register_sandbox_provider(self.provider, replace=True)
        tool_mgr = context.get_llm_tool_manager()
        tool_mgr.func_list.append(CuaScreenshotTool())
        tool_mgr.func_list.append(CuaMouseClickTool())
        tool_mgr.func_list.append(CuaKeyboardTypeTool())

    async def terminate(self) -> None:
        tool_mgr = self.context.get_llm_tool_manager()
        for tool_name in self.provider.tool_names:
            tool_mgr.remove_func(tool_name)
        unregister_sandbox_provider(self.provider.provider_id, force=True)

    @filter.command("cua_sandbox_runtime")
    async def runtime_status(self, event):
        yield event.plain_result("CUA sandbox runtime provider is registered.")

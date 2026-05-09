from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from astrbot.api import logger
from astrbot.core.computer.booters.base import ComputerBooter
from astrbot.core.star.context import Context

from .booters import cua as cua_booter

BootHook = Callable[[Context, str, str, dict], Awaitable[ComputerBooter]]


async def _sync_skills_to_sandbox(booter: ComputerBooter) -> None:
    from astrbot.core.computer.computer_client import _sync_skills_to_sandbox as sync

    await sync(booter)


class CuaSandboxProvider:
    provider_id = "cua"
    capabilities = {"shell", "python", "filesystem", "screenshot", "mouse", "keyboard"}
    tool_names = {
        "astrbot_cua_screenshot",
        "astrbot_cua_mouse_click",
        "astrbot_cua_keyboard_type",
    }

    def __init__(self, boot_hook: BootHook | None = None) -> None:
        self._boot_hook = boot_hook

    def build_create_config(self, context: Context, session_id: str) -> dict:
        config = context.get_config(umo=session_id)
        sandbox_cfg = config.get("provider_settings", {}).get("sandbox", {})
        plugin_cfg = getattr(self, "plugin_config", None)
        if plugin_cfg:
            merged = dict(plugin_cfg)
            merged.update(sandbox_cfg)
            sandbox_cfg = merged
        return cua_booter.build_cua_booter_kwargs(sandbox_cfg)

    def build_connect_info(self, sandbox_name: str, config: dict) -> dict:
        return {
            "name": sandbox_name,
            "local": config.get("local", True),
            "image": config.get("image"),
            "os_type": config.get("os_type"),
        }

    def update_connect_info(self, record: dict, *, sandbox_name: str) -> dict:
        connect_info = dict(record.get("connect_info") or {})
        connect_info["name"] = sandbox_name
        return connect_info

    def get_idle_timeout(self, context: Context, session_id: str) -> float:
        config = context.get_config(umo=session_id)
        sandbox_cfg = config.get("provider_settings", {}).get("sandbox", {})
        plugin_cfg = getattr(self, "plugin_config", None)
        value = sandbox_cfg.get(
            "cua_idle_timeout",
            plugin_cfg.get("cua_idle_timeout", 0) if plugin_cfg else 0,
        )
        try:
            timeout = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(timeout, 0.0)

    async def create_booter(
        self,
        context: Context,
        session_id: str,
        sandbox_id: str,
        config: dict,
    ) -> ComputerBooter:
        if self._boot_hook is not None:
            return await self._boot_hook(context, session_id, sandbox_id, config)
        uuid_str = uuid.uuid5(uuid.NAMESPACE_DNS, session_id).hex
        client = cua_booter.CuaBooter(**config)
        started_at = time.monotonic()
        logger.info(
            "[Computer] CUA managed sandbox boot start: sandbox_id=%s session_id=%s boot_session_id=%s image=%s os_type=%s local=%s ttl=%s",
            sandbox_id,
            session_id,
            uuid_str,
            config.get("image"),
            config.get("os_type"),
            config.get("local"),
            config.get("ttl"),
        )
        try:
            await client.boot(uuid_str)
            setattr(client, "sandbox_id", sandbox_id)
            await _sync_skills_to_sandbox(client)
        except Exception:
            logger.warning(
                "[Computer] CUA managed sandbox boot failed: sandbox_id=%s session_id=%s elapsed_ms=%d",
                sandbox_id,
                session_id,
                int((time.monotonic() - started_at) * 1000),
                exc_info=True,
            )
            try:
                await client.shutdown()
            except Exception as shutdown_error:
                logger.warning(
                    "Failed to shutdown CUA sandbox after boot error for session %s: %s",
                    session_id,
                    shutdown_error,
                )
            raise
        logger.info(
            "[Computer] CUA managed sandbox boot done: sandbox_id=%s session_id=%s elapsed_ms=%d",
            sandbox_id,
            session_id,
            int((time.monotonic() - started_at) * 1000),
        )
        return client

    async def destroy_booter(self, booter: ComputerBooter, record: dict) -> None:
        await booter.shutdown()

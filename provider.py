from __future__ import annotations

import os
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from astrbot.api import logger
from astrbot.core.computer.booters.base import ComputerBooter
from astrbot.core.computer.sandbox_timeouts import resolve_sandbox_timeout
from astrbot.core.star.context import Context

from .booters import cua as cua_booter

BootHook = Callable[[Context, str, str, dict], Awaitable[ComputerBooter]]
_CUA_TTL_TIMEOUT_KEY = "sandbox_ttl"
_CUA_LEGACY_TTL_KEY = "cua_ttl"
_CUA_TTL_TIMEOUT_ALIASES = (_CUA_LEGACY_TTL_KEY,)
_CUA_DEFAULT_TTL_SECONDS = 3600
_CUA_IDLE_TIMEOUT_KEY = "sandbox_idle_timeout"
_CUA_LEGACY_IDLE_TIMEOUT_KEY = "cua_idle_timeout"
_CUA_IDLE_TIMEOUT_ALIASES = (_CUA_LEGACY_IDLE_TIMEOUT_KEY,)
_CUA_DEFAULT_IDLE_TIMEOUT_SECONDS = 0.0
DOCKER_UNAVAILABLE_ERROR = "Docker is not installed or not running"


def _is_docker_unavailable_error(exc: Exception) -> bool:
    detail = str(exc).lower()
    return (
        "cannot connect to docker engine" in detail
        or "failed to connect to docker daemon" in detail
        or DOCKER_UNAVAILABLE_ERROR.lower() in detail
        or ("cannot connect to unix socket" in detail and "docker.sock" in detail)
    )


def _resolve_cua_ttl(config: Mapping[str, Any]) -> int:
    return int(
        resolve_sandbox_timeout(
            config,
            _CUA_TTL_TIMEOUT_KEY,
            aliases=_CUA_TTL_TIMEOUT_ALIASES,
            default=_CUA_DEFAULT_TTL_SECONDS,
        )
    )


def _resolve_cua_idle_timeout(config: Mapping[str, Any]) -> float:
    return resolve_sandbox_timeout(
        config,
        _CUA_IDLE_TIMEOUT_KEY,
        aliases=_CUA_IDLE_TIMEOUT_ALIASES,
        default=_CUA_DEFAULT_IDLE_TIMEOUT_SECONDS,
    )


class CuaSandboxProvider:
    provider_id = "cua"
    capabilities = {"shell", "python", "filesystem", "screenshot", "mouse", "keyboard"}
    supports_persistent_reconnect = True
    tool_names = {
        "astrbot_cua_screenshot",
        "astrbot_cua_mouse_click",
        "astrbot_cua_keyboard_type",
    }

    def __init__(
        self,
        boot_hook: BootHook | None = None,
        *,
        plugin_config: Mapping[str, Any] | None = None,
    ) -> None:
        self.plugin_config: dict[str, Any] = (
            dict(plugin_config) if plugin_config is not None else {}
        )
        self._boot_hook = boot_hook

    @staticmethod
    def _persistent_name(config: dict, fallback: str) -> str:
        return str(config.get("persistent_name") or fallback).strip()

    def _merged_sandbox_config(self, context: Context, session_id: str) -> dict:
        """Return sandbox config with plugin_config as base and user settings overriding."""
        config = context.get_config(umo=session_id)
        merged = dict(self.plugin_config)
        sandbox_cfg = config.get("provider_settings", {}).get("sandbox", {})
        if isinstance(sandbox_cfg, dict):
            merged.update(sandbox_cfg)
        else:
            logger.warning(
                "[Computer] Expected dict for provider_settings.sandbox, got %s. Ignoring.",
                type(sandbox_cfg).__name__,
            )
        return merged

    def build_create_config(self, context: Context, session_id: str) -> dict:
        sandbox_cfg = self._merged_sandbox_config(context, session_id)
        sandbox_cfg = {
            **sandbox_cfg,
            _CUA_LEGACY_TTL_KEY: _resolve_cua_ttl(sandbox_cfg),
            _CUA_LEGACY_IDLE_TIMEOUT_KEY: _resolve_cua_idle_timeout(sandbox_cfg),
        }
        booter_kwargs = cua_booter.build_cua_booter_kwargs(sandbox_cfg)
        if not booter_kwargs.get("api_key") and not os.environ.get("CUA_API_KEY"):
            booter_kwargs["local"] = True
        return booter_kwargs

    def build_connect_info(self, sandbox_name: str, config: dict) -> dict:
        return {
            "name": sandbox_name,
            "local": config.get("local", True),
            "image": config.get("image"),
            "os_type": config.get("os_type"),
            "persistent_name": self._persistent_name(config, sandbox_name),
        }

    def update_connect_info(self, record: dict, *, sandbox_name: str) -> dict:
        connect_info = dict(record.get("connect_info") or {})
        connect_info["name"] = sandbox_name
        return connect_info

    def get_idle_timeout(self, context: Context, session_id: str) -> float:
        sandbox_cfg = self._merged_sandbox_config(context, session_id)
        return _resolve_cua_idle_timeout(sandbox_cfg)

    async def check_persistent_sandbox_exists(self, record: dict) -> bool:
        try:
            from cua import Sandbox
        except ImportError as exc:
            raise RuntimeError(
                "CUA sandbox support requires the optional `cua` package. "
                "Install it with `pip install cua` in the AstrBot environment."
            ) from exc

        connect_info = dict(record.get("connect_info") or {})
        sandbox_name = str(
            connect_info.get("persistent_name")
            or connect_info.get("name")
            or record.get("sandbox_id")
            or ""
        ).strip()
        if not sandbox_name:
            return False

        connect = getattr(Sandbox, "connect", None)
        if not callable(connect):
            return True

        connect_kwargs = {"local": connect_info.get("local", True)}
        api_key = connect_info.get("api_key") or self.plugin_config.get("api_key")
        if api_key:
            connect_kwargs["api_key"] = api_key
        try:
            sandbox = await connect(sandbox_name, **connect_kwargs)
        except Exception as exc:
            if cua_booter._is_missing_persistent_sandbox_error(exc):
                resume = getattr(Sandbox, "resume", None)
                if not callable(resume):
                    return False
                try:
                    sandbox = await resume(sandbox_name, **connect_kwargs)
                except Exception as resume_exc:
                    if cua_booter._is_missing_persistent_sandbox_error(resume_exc):
                        return False
                    raise
                else:
                    disconnect = getattr(sandbox, "disconnect", None)
                    if callable(disconnect):
                        await disconnect()
                    return True
            raise

        disconnect = getattr(sandbox, "disconnect", None)
        if callable(disconnect):
            await disconnect()
        return True

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
        persistent = True
        persistent_name = self._persistent_name(config, sandbox_id)
        booter_config = {
            **config,
            "persistent": persistent,
            "persistent_name": persistent_name,
            "resume": bool(config.get("resume", False)),
        }
        client = cua_booter.CuaBooter(
            **booter_config,
        )
        started_at = time.monotonic()
        logger.info(
            "[Computer] CUA managed sandbox boot start: sandbox_id=%s session_id=%s boot_session_id=%s image=%s os_type=%s local=%s ttl=%s persistent=%s persistent_name=%s resume=%s",
            sandbox_id,
            session_id,
            uuid_str,
            config.get("image"),
            config.get("os_type"),
            config.get("local"),
            config.get("ttl"),
            persistent,
            persistent_name,
            bool(config.get("resume", False)),
        )
        try:
            await client.boot(uuid_str)
            setattr(client, "sandbox_id", sandbox_id)
        except Exception as exc:
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
            if isinstance(exc, RuntimeError) and _is_docker_unavailable_error(exc):
                raise RuntimeError(DOCKER_UNAVAILABLE_ERROR) from exc
            raise
        logger.info(
            "[Computer] CUA managed sandbox boot done: sandbox_id=%s session_id=%s elapsed_ms=%d persistent=%s persistent_name=%s",
            sandbox_id,
            session_id,
            int((time.monotonic() - started_at) * 1000),
            persistent,
            persistent_name,
        )
        return client

    async def destroy_booter(self, booter: ComputerBooter, record: dict) -> None:
        destroy = getattr(booter, "destroy", None)
        if callable(destroy):
            await destroy()
            return
        await booter.shutdown()

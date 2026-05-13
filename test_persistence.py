import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from data.plugins.astrbot_sandbox_cua import provider as provider_module
from data.plugins.astrbot_sandbox_cua import main as plugin_main
from data.plugins.astrbot_sandbox_cua.booters.cua import (
    CuaBooter,
    _write_base64_via_shell,
)


@pytest.mark.asyncio
async def test_cua_booter_uses_persistent_create_and_disconnects_on_shutdown(
    monkeypatch,
):
    calls = []

    class FakeSandbox:
        def __init__(self, name: str):
            self.name = name
            self.shell = SimpleNamespace(exec=lambda *args, **kwargs: None)
            self.python = SimpleNamespace(exec=lambda *args, **kwargs: None)
            self.filesystem = SimpleNamespace()
            self.mouse = SimpleNamespace(click=lambda *args, **kwargs: None)
            self.keyboard = SimpleNamespace(type=lambda *args, **kwargs: None)

        async def disconnect(self):
            calls.append(("disconnect", self.name))

    class FakeImage:
        @staticmethod
        def linux():
            return "linux-image"

    class FakeSandboxApi:
        @staticmethod
        async def create(image, *, name=None, local=False, **kwargs):
            calls.append(("create", image, {"name": name, "local": local, **kwargs}))
            return FakeSandbox(name)

        @staticmethod
        def ephemeral(*args, **kwargs):
            raise AssertionError("persistent mode must not use Sandbox.ephemeral")

    fake_module = SimpleNamespace(Image=FakeImage, Sandbox=FakeSandboxApi)

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cua":
            return fake_module
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    booter = CuaBooter(
        image="linux",
        os_type="linux",
        local=True,
        persistent_name="cua-persistent-1",
        persistent=True,
    )

    await booter.boot("ignored-session")
    await booter.shutdown()

    assert calls[0] == (
        "create",
        "linux-image",
        {
            "name": "cua-persistent-1",
            "local": True,
        },
    )
    assert calls[1] == ("disconnect", "cua-persistent-1")


@pytest.mark.asyncio
async def test_cua_terminate_detaches_even_if_cleanup_fails(monkeypatch):
    calls = []

    class FakeProvider:
        provider_id = "cua"

    async def fake_cleanup(provider_id):
        calls.append(("cleanup", provider_id))
        raise RuntimeError("cleanup failed")

    def fake_detach(provider_id):
        calls.append(("detach", provider_id))

    monkeypatch.setattr(plugin_main, "cleanup_sandbox_provider", fake_cleanup)
    monkeypatch.setattr(plugin_main, "detach_sandbox_provider", fake_detach)

    plugin = plugin_main.CuaSandboxRuntimePlugin.__new__(
        plugin_main.CuaSandboxRuntimePlugin
    )
    plugin.provider = FakeProvider()

    with pytest.raises(RuntimeError, match="cleanup failed"):
        await plugin.terminate()

    assert calls == [("cleanup", "cua"), ("detach", "cua")]


@pytest.mark.asyncio
async def test_cua_terminate_noops_when_provider_missing(monkeypatch):
    calls = []

    def fake_detach(provider_id):
        calls.append(("detach", provider_id))

    monkeypatch.setattr(plugin_main, "detach_sandbox_provider", fake_detach)

    plugin = plugin_main.CuaSandboxRuntimePlugin.__new__(
        plugin_main.CuaSandboxRuntimePlugin
    )
    plugin.provider = None

    await plugin.terminate()

    assert calls == []


@pytest.mark.asyncio
async def test_cua_booter_resumes_persistent_runtime_when_resume_enabled(monkeypatch):
    calls = []

    class FakeSandbox:
        def __init__(self, name: str):
            self.name = name
            self.shell = SimpleNamespace(exec=lambda *args, **kwargs: None)
            self.python = SimpleNamespace(exec=lambda *args, **kwargs: None)
            self.filesystem = SimpleNamespace()
            self.mouse = SimpleNamespace(click=lambda *args, **kwargs: None)
            self.keyboard = SimpleNamespace(type=lambda *args, **kwargs: None)

        async def disconnect(self):
            calls.append(("disconnect", self.name))

    class FakeImage:
        @staticmethod
        def linux():
            return "linux-image"

    class FakeSandboxApi:
        connect = None

        @staticmethod
        async def resume(name, **kwargs):
            calls.append(("resume", name, kwargs))
            return FakeSandbox(name)

        @staticmethod
        async def create(*args, **kwargs):
            raise AssertionError("resume path must not create a new sandbox")

        @staticmethod
        def ephemeral(*args, **kwargs):
            raise AssertionError("resume path must not use Sandbox.ephemeral")

    fake_module = SimpleNamespace(Image=FakeImage, Sandbox=FakeSandboxApi)

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cua":
            return fake_module
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    booter = CuaBooter(
        image="linux",
        os_type="linux",
        local=True,
        persistent_name="cua-persistent-1",
        persistent=True,
        resume=True,
    )

    await booter.boot("ignored-session")

    assert calls == [("resume", "cua-persistent-1", {"local": True})]


@pytest.mark.asyncio
async def test_cua_provider_passes_persistent_runtime_name_for_persistent_sandbox(
    monkeypatch,
):
    recorded = {}

    class FakeBooter:
        def __init__(self, **kwargs):
            recorded.update(kwargs)

        async def boot(self, session_id: str):
            recorded["boot_session_id"] = session_id

        async def shutdown(self):
            return None

    monkeypatch.setattr(
        provider_module, "cua_booter", SimpleNamespace(CuaBooter=FakeBooter)
    )

    provider = provider_module.CuaSandboxProvider()
    booter = await provider.create_booter(
        context=object(),
        session_id="dashboard",
        sandbox_id="cua-123",
        config={
            "image": "linux",
            "os_type": "linux",
            "local": True,
            "persistent": True,
            "persistent_name": "cua-123",
        },
    )

    assert recorded["persistent"] is True
    assert recorded["persistent_name"] == "cua-123"
    assert recorded["resume"] is False
    assert (
        recorded["boot_session_id"] == uuid.uuid5(uuid.NAMESPACE_DNS, "dashboard").hex
    )
    assert getattr(booter, "sandbox_id") == "cua-123"


@pytest.mark.asyncio
async def test_cua_booter_destroy_disconnects_before_delete(monkeypatch):
    calls = []

    class FakeSandbox:
        def __init__(self, name: str):
            self.name = name
            self.shell = SimpleNamespace(exec=lambda *args, **kwargs: None)
            self.python = SimpleNamespace(exec=lambda *args, **kwargs: None)
            self.filesystem = SimpleNamespace()
            self.mouse = SimpleNamespace(click=lambda *args, **kwargs: None)
            self.keyboard = SimpleNamespace(type=lambda *args, **kwargs: None)

        async def disconnect(self):
            calls.append(("disconnect", self.name))

    class FakeImage:
        @staticmethod
        def linux():
            return "linux-image"

    class FakeSandboxApi:
        @staticmethod
        async def create(image, *, name=None, local=False, **kwargs):
            return FakeSandbox(name)

        @staticmethod
        async def delete(name, **kwargs):
            calls.append(("delete", name, kwargs))

    fake_module = SimpleNamespace(Image=FakeImage, Sandbox=FakeSandboxApi)

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cua":
            return fake_module
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    booter = CuaBooter(
        image="linux",
        os_type="linux",
        local=True,
        persistent_name="cua-persistent-1",
        persistent=True,
    )

    await booter.boot("ignored-session")
    await booter.destroy()

    assert calls == [
        ("disconnect", "cua-persistent-1"),
        ("delete", "cua-persistent-1", {"local": True}),
    ]


@pytest.mark.asyncio
async def test_cua_booter_destroy_ignores_missing_sandbox(monkeypatch):
    class FakeSandbox:
        def __init__(self, name: str):
            self.name = name
            self.shell = SimpleNamespace(exec=lambda *args, **kwargs: None)
            self.python = SimpleNamespace(exec=lambda *args, **kwargs: None)
            self.filesystem = SimpleNamespace()
            self.mouse = SimpleNamespace(click=lambda *args, **kwargs: None)
            self.keyboard = SimpleNamespace(type=lambda *args, **kwargs: None)

        async def disconnect(self):
            return None

    class FakeImage:
        @staticmethod
        def linux():
            return "linux-image"

    class FakeSandboxApi:
        @staticmethod
        async def create(image, *, name=None, local=False, **kwargs):
            return FakeSandbox(name)

        @staticmethod
        async def delete(name, **kwargs):
            raise ValueError(f"No local sandbox named '{name}' found in state files.")

    fake_module = SimpleNamespace(Image=FakeImage, Sandbox=FakeSandboxApi)

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cua":
            return fake_module
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    booter = CuaBooter(
        image="linux",
        os_type="linux",
        local=True,
        persistent_name="cua-persistent-1",
        persistent=True,
    )

    await booter.boot("ignored-session")
    await booter.destroy()


@pytest.mark.asyncio
async def test_cua_booter_resume_raises_unexpected_connect_error(monkeypatch):
    class FakeImage:
        @staticmethod
        def linux():
            return "linux-image"

    class FakeSandboxApi:
        @staticmethod
        async def connect(name, **kwargs):
            raise RuntimeError(f"permission denied for {name}")

        @staticmethod
        async def resume(*args, **kwargs):
            raise AssertionError("unexpected errors must not fall through to resume")

        @staticmethod
        async def create(*args, **kwargs):
            raise AssertionError("unexpected errors must not fall through to create")

    fake_module = SimpleNamespace(Image=FakeImage, Sandbox=FakeSandboxApi)

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cua":
            return fake_module
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    booter = CuaBooter(
        image="linux",
        os_type="linux",
        local=True,
        persistent_name="cua-persistent-1",
        persistent=True,
        resume=True,
    )

    with pytest.raises(RuntimeError, match="permission denied"):
        await booter.boot("ignored-session")


@pytest.mark.asyncio
async def test_cua_provider_destroy_booter_ignores_non_callable_destroy():
    shutdown_calls = []

    class FakeBooter:
        destroy = True

        async def shutdown(self):
            shutdown_calls.append("shutdown")

    provider = provider_module.CuaSandboxProvider()

    await provider.destroy_booter(FakeBooter(), {"retention_policy": "temporary"})

    assert shutdown_calls == ["shutdown"]


@pytest.mark.asyncio
async def test_cua_provider_reports_persistent_sandbox_exists(monkeypatch):
    calls = []

    class FakeSandboxApi:
        @staticmethod
        async def connect(name, **kwargs):
            calls.append((name, kwargs))

            class FakeSandbox:
                async def disconnect(self):
                    calls.append(("disconnect", name))

            return FakeSandbox()

    fake_module = SimpleNamespace(Sandbox=FakeSandboxApi)

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cua":
            return fake_module
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    provider = provider_module.CuaSandboxProvider()

    exists = await provider.check_persistent_sandbox_exists(
        {"connect_info": {"persistent_name": "cua-persistent-1", "local": True}}
    )

    assert exists is True
    assert calls == [
        ("cua-persistent-1", {"local": True}),
        ("disconnect", "cua-persistent-1"),
    ]


@pytest.mark.asyncio
async def test_cua_provider_reports_missing_persistent_sandbox(monkeypatch):
    class FakeSandboxApi:
        @staticmethod
        async def connect(name, **kwargs):
            raise ValueError(f"No local sandbox named '{name}' found in state files.")

    fake_module = SimpleNamespace(Sandbox=FakeSandboxApi)

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cua":
            return fake_module
        return original_import(name, globals, locals, fromlist, level)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)

    provider = provider_module.CuaSandboxProvider()

    exists = await provider.check_persistent_sandbox_exists(
        {"connect_info": {"persistent_name": "cua-persistent-1", "local": True}}
    )

    assert exists is False


@pytest.mark.asyncio
async def test_cua_shell_upload_fallback_chunks_large_payloads(tmp_path):
    commands = []

    class FakeShell:
        async def exec(self, command, **kwargs):
            commands.append((command, kwargs))
            return {"stdout": "", "stderr": "", "exit_code": 0, "success": True}

    target_path = "/tmp/uploaded.bin"
    data = b"a" * 200_000

    result = await _write_base64_via_shell(FakeShell(), target_path, data)

    assert result["success"] is True
    assert len(commands) > 2
    assert all(len(command) < 100_000 for command, _kwargs in commands)
    assert commands[0][0].startswith("mkdir -p ")
    assert "python3 - <<'PY'" in commands[-1][0]
    assert str(Path(target_path).parent) in commands[0][0]

import uuid
from types import SimpleNamespace

import pytest

from data.plugins.astrbot_sandbox_cua import provider as provider_module
from data.plugins.astrbot_sandbox_cua.booters.cua import CuaBooter


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

    monkeypatch.setattr(provider_module, "cua_booter", SimpleNamespace(CuaBooter=FakeBooter))

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

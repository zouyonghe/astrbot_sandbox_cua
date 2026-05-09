# astrbot_sandbox_cua

Chinese version: [`README_cn.md`](./README_cn.md)

`astrbot_sandbox_cua` is an AstrBot sandbox runtime plugin built on top of the generic sandbox provider API.

It adds the `cua` sandbox provider and registers GUI-oriented tools for screenshot, mouse click, and keyboard typing.

## Features

- Provides the `cua` sandbox runtime for AstrBot.
- Supports shell, Python, and filesystem operations inside the sandbox.
- Adds GUI-oriented tools for screenshot, mouse click, and keyboard typing.
- Supports both local-preferred and cloud-backed CUA environments.
- Supports managed sandbox idle cleanup through `cua_idle_timeout`.

## Requirements

- An AstrBot build that supports external sandbox provider plugins.
- The plugin dependency from `requirements.txt`: `cua-computer`.
- A compatible CUA runtime environment.
- A CUA API key if you run with `cua_local=false`.

## Installation

Clone the plugin into AstrBot's plugin directory:

```bash
git clone https://github.com/zouyonghe/astrbot_sandbox_cua.git data/plugins/astrbot_sandbox_cua
```

Then restart AstrBot or reload plugins.

## Configuration

Enable sandbox runtime in AstrBot and select this provider:

```json
{
  "provider_settings": {
    "computer_use_runtime": "sandbox",
    "sandbox": {
      "booter": "cua"
    }
  }
}
```

Provider-specific options:

| Key | Description |
| --- | --- |
| `cua_image` | Sandbox image or system type. |
| `cua_os_type` | OS type, such as `linux`, `macos`, `windows`, or `android`. |
| `cua_ttl` | Sandbox lifetime in seconds. |
| `cua_idle_timeout` | Idle cleanup timeout in seconds. `0` disables idle cleanup. |
| `cua_telemetry_enabled` | Enables SDK telemetry when supported. |
| `cua_local` | Prefer a local CUA sandbox. |
| `cua_api_key` | API key for cloud CUA usage. `CUA_API_KEY` is also supported. |

## Usage Notes

- This plugin is best when you need GUI interaction instead of browser-only automation.
- After the plugin is enabled, AstrBot can mount CUA tools automatically when the active sandbox provider is `cua`.
- If you want cloud execution, set `cua_local` to `false` and provide `cua_api_key`.
- If you want AstrBot to recycle idle managed sandboxes, set `cua_idle_timeout` to a positive value.

## Limitations

- This plugin depends on the behavior and compatibility of the upstream CUA SDK.
- GUI capability depends on the selected CUA image and OS type.
- This plugin does not add browser-specific Bay or Shipyard Neo lifecycle features.

## Repository

- GitHub: https://github.com/zouyonghe/astrbot_sandbox_cua

# astrbot_sandbox_cua

<div align="center">

English ｜ <a href="./README_cn.md">简体中文</a>

</div>

`astrbot_sandbox_cua` is the CUA sandbox driver plugin for AstrBot. It is designed for Agent workflows that need real computer interaction: shell commands, Python execution, file access, screenshots, mouse clicks, and keyboard input inside a sandbox.

## Key Features

1. 🛡️ Provides the `cua` sandbox driver for AstrBot.
2. 💻 Supports shell, Python, and file operations.
3. 🖱️ Adds GUI tools for screenshots, mouse clicks, and keyboard input.
4. ☁️ Supports local-first execution and cloud-backed CUA runtimes.
5. ♻️ Can recycle idle sandboxes through `cua_idle_timeout`.

## Quick Start

### Install the Plugin

Clone the plugin into AstrBot's plugin directory:

```bash
git clone https://github.com/zouyonghe/astrbot_sandbox_cua.git data/plugins/astrbot_sandbox_cua
```

Then restart AstrBot, or reload plugins from the plugin management page.

### Enable the CUA Sandbox Driver

In the AstrBot dashboard, enable sandbox mode and select the `cua` driver.

Configuration path:

- `provider_settings.computer_use_runtime`: `sandbox`
- `provider_settings.sandbox.booter`: `cua`

## Configuration

| Key | Description |
| --- | --- |
| `cua_image` | Sandbox image or system type. Keep it aligned with `cua_os_type` unless you know the target runtime needs a different image. |
| `cua_os_type` | Supported OS types: `linux`, `macos`, `windows`, `android`. |
| `cua_ttl` | Sandbox lifetime in seconds. |
| `cua_idle_timeout` | Idle cleanup timeout in seconds. `0` disables idle cleanup. |
| `cua_telemetry_enabled` | Allows the upstream CUA SDK to send anonymous usage and diagnostic data to improve stability and compatibility. |
| `cua_local` | Prefer a local CUA sandbox. Set this to `false` for cloud CUA. |
| `cua_api_key` | API key for cloud CUA usage. `CUA_API_KEY` is also supported. |

## Best For

- Use this plugin when you need real GUI interaction instead of browser-only automation.
- After the plugin is enabled, AstrBot mounts CUA tools automatically when the active sandbox driver is `cua`.
- If you want cloud execution, set `cua_local` to `false` and provide `cua_api_key`.
- If you want AstrBot to recycle idle managed sandboxes, set `cua_idle_timeout` to a positive value.

## Requirements and Limitations

- AstrBot must support external sandbox driver plugins.
- The plugin dependency from `requirements.txt`: `cua-computer`.
- A compatible CUA runtime environment is required.
- A CUA API key is required when `cua_local=false`.
- This plugin depends on the behavior and compatibility of the upstream CUA SDK.
- GUI capability depends on the selected CUA image and OS type.
- This plugin does not add browser-specific Bay or Shipyard Neo lifecycle features.

## Troubleshooting

- If cloud mode does not start, make sure `cua_local=false` and `cua_api_key` are both set.
- If GUI tools fail inside the sandbox, verify that the selected image matches the requested OS type.
- If you care about privacy or want to minimize external reporting, keep `cua_telemetry_enabled` disabled.

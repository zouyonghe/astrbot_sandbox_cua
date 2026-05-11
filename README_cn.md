# astrbot_sandbox_cua

英文版说明：[`README.md`](./README.md)

`astrbot_sandbox_cua` 是 AstrBot 的 CUA 沙盒驱动插件。

它适合需要完整电脑操作能力的场景，例如截图、鼠标点击、键盘输入，以及在沙盒里运行 Shell 或 Python。

## 功能特性

- 提供 `cua` 沙盒驱动。
- 支持沙盒内的 Shell、Python 和文件操作。
- 提供截图、鼠标点击、键盘输入等 GUI 工具。
- 支持本地优先和云端 CUA 运行模式。
- 可通过 `cua_idle_timeout` 自动回收空闲沙盒。

## 依赖要求

- 需要使用支持外部沙盒驱动插件的 AstrBot 版本。
- 依赖 `requirements.txt` 中的 `cua-computer`。
- 需要可用的 CUA 环境。
- 当 `cua_local=false` 时，需要提供 CUA API Key。

## 安装方式

把插件克隆到 AstrBot 的插件目录：

```bash
git clone https://github.com/zouyonghe/astrbot_sandbox_cua.git data/plugins/astrbot_sandbox_cua
```

然后重启 AstrBot，或重新加载插件。

## 配置方法

先在 AstrBot 核心配置中启用沙盒模式，并把沙盒驱动设置为 `cua`：

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

插件支持的配置项：

| 键名 | 说明 |
| --- | --- |
| `cua_image` | 沙盒镜像或系统类型。 |
| `cua_os_type` | 操作系统类型，例如 `linux`、`macos`、`windows`、`android`。 |
| `cua_ttl` | 沙盒生命周期，单位秒。 |
| `cua_idle_timeout` | 空闲回收时间，单位秒。`0` 表示不自动回收。 |
| `cua_telemetry_enabled` | 是否允许 SDK 发送遥测。 |
| `cua_local` | 是否优先使用本地 CUA 沙箱。 |
| `cua_api_key` | 云端 CUA 使用的 API Key，也支持环境变量 `CUA_API_KEY`。 |

## 使用说明

- 当你需要真实 GUI 操作，而不是单纯的浏览器自动化时，优先使用这个插件。
- 插件启用后，只要当前沙盒驱动是 `cua`，AstrBot 就会自动挂载对应的 CUA 工具。
- 如果需要云端运行，请把 `cua_local` 设为 `false`，并提供 `cua_api_key`。
- 如果希望 AstrBot 自动回收空闲沙盒，请把 `cua_idle_timeout` 设置为大于 `0` 的值。

## 限制说明

- 该插件的可用能力受上游 CUA SDK 兼容性影响。
- GUI 能力是否完整可用，取决于所选镜像和 OS 类型。
- 该插件不提供 Bay / Shipyard Neo 的浏览器技能生命周期能力。

## 仓库地址

- GitHub: https://github.com/zouyonghe/astrbot_sandbox_cua

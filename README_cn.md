# astrbot_sandbox_cua

英文版说明：[`README.md`](./README.md)

`astrbot_sandbox_cua` 是一个基于 AstrBot 通用 sandbox provider 机制实现的插件。

它为 AstrBot 提供 `cua` 运行时，并注册面向 GUI 的截图、鼠标点击、键盘输入工具。

## 功能特性

- 为 AstrBot 提供 `cua` 沙箱运行时。
- 支持沙箱内的 shell、Python、文件系统操作。
- 提供 GUI 能力相关工具：截图、鼠标点击、键盘输入。
- 支持本地优先和云端 CUA 运行模式。
- 支持通过 `cua_idle_timeout` 回收空闲托管沙箱。

## 依赖要求

- 需要使用已经支持外部 sandbox provider 插件的 AstrBot 版本。
- 依赖 `requirements.txt` 中的 `cua-computer`。
- 需要可用的 CUA 运行环境。
- 当 `cua_local=false` 时，需要提供 CUA API Key。

## 安装方式

把插件克隆到 AstrBot 的插件目录：

```bash
git clone https://github.com/zouyonghe/astrbot_sandbox_cua.git data/plugins/astrbot_sandbox_cua
```

然后重启 AstrBot，或重新加载插件。

## 配置方法

先在 AstrBot 核心配置中启用 sandbox，并把运行时设置为 `cua`：

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
| `cua_image` | 沙箱镜像或系统类型。 |
| `cua_os_type` | 操作系统类型，例如 `linux`、`macos`、`windows`、`android`。 |
| `cua_ttl` | 沙箱生命周期，单位秒。 |
| `cua_idle_timeout` | 空闲回收时间，单位秒。`0` 表示不自动回收。 |
| `cua_telemetry_enabled` | 是否允许 SDK 发送遥测。 |
| `cua_local` | 是否优先使用本地 CUA 沙箱。 |
| `cua_api_key` | 云端 CUA 使用的 API Key，也支持环境变量 `CUA_API_KEY`。 |

## 使用说明

- 当你需要真正的 GUI 交互，而不是纯浏览器自动化时，优先使用这个插件。
- 插件启用后，只要当前 sandbox provider 是 `cua`，AstrBot 就可以自动挂载对应的 CUA 工具。
- 如果需要云端运行，请把 `cua_local` 设为 `false`，并提供 `cua_api_key`。
- 如果希望 AstrBot 自动回收空闲托管沙箱，请把 `cua_idle_timeout` 设置为大于 `0` 的值。

## 限制说明

- 该插件的可用能力受上游 CUA SDK 兼容性影响。
- GUI 能力是否完整可用，取决于所选镜像和 OS 类型。
- 该插件不提供 Bay / Shipyard Neo 的浏览器技能生命周期能力。

## 仓库地址

- GitHub: https://github.com/zouyonghe/astrbot_sandbox_cua

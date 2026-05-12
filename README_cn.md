# astrbot_sandbox_cua

<div align="center">

<a href="./README.md">English</a> ｜ 简体中文

</div>

`astrbot_sandbox_cua` 是 AstrBot 的 CUA 沙盒驱动插件，适合需要真实电脑操作能力的 Agent 场景。它可以在沙盒中运行 Shell、Python，读写文件，也能提供截图、鼠标点击和键盘输入等 GUI 工具。

## 主要功能

1. 🛡️ 为 AstrBot 提供 `cua` 沙盒驱动。
2. 💻 支持 Shell、Python 和文件操作。
3. 🖱️ 提供截图、鼠标点击、键盘输入等 GUI 工具。
4. ☁️ 支持本地优先，也可以切换到云端 CUA。
5. ♻️ 可通过 `cua_idle_timeout` 自动回收空闲沙盒。

## 快速开始

### 安装插件

把插件克隆到 AstrBot 插件目录：

```bash
git clone https://github.com/zouyonghe/astrbot_sandbox_cua.git data/plugins/astrbot_sandbox_cua
```

然后重启 AstrBot，或在插件管理页重新加载插件。

### 启用 CUA 沙盒驱动

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

## 配置项

| 键名 | 说明 |
| --- | --- |
| `cua_image` | 沙盒镜像或系统类型。通常和 `cua_os_type` 保持一致，除非你明确知道目标运行时需要不同镜像。 |
| `cua_os_type` | 支持的操作系统类型：`linux`、`macos`、`windows`、`android`。 |
| `cua_ttl` | 沙盒生命周期，单位秒。 |
| `cua_idle_timeout` | 空闲回收时间，单位秒。`0` 表示不自动回收。 |
| `cua_telemetry_enabled` | 是否允许 SDK 发送遥测。 |
| `cua_local` | 是否优先使用本地 CUA 沙盒。设为 `false` 时改用云端 CUA。 |
| `cua_api_key` | 云端 CUA 使用的 API Key，也支持环境变量 `CUA_API_KEY`。 |

## 适合场景

- 当你需要真实 GUI 操作，而不是单纯的浏览器自动化时，优先使用这个插件。
- 插件启用后，只要当前沙盒驱动是 `cua`，AstrBot 就会自动挂载对应的 CUA 工具。
- 如果需要云端运行，请把 `cua_local` 设为 `false`，并提供 `cua_api_key`。
- 如果希望 AstrBot 自动回收空闲沙盒，请把 `cua_idle_timeout` 设置为大于 `0` 的值。

## 依赖与限制

- 需要使用支持外部沙盒驱动插件的 AstrBot 版本。
- 依赖 `requirements.txt` 中的 `cua-computer`。
- 需要可用的 CUA 环境。
- 当 `cua_local=false` 时，需要提供 CUA API Key。
- 该插件的可用能力受上游 CUA SDK 兼容性影响。
- GUI 能力是否完整可用，取决于所选镜像和 OS 类型。
- 该插件不提供 Bay / Shipyard Neo 的浏览器技能生命周期能力。

## 排查建议

- 如果云端模式没有启动，请确认 `cua_local=false` 且已经填写 `cua_api_key`。
- 如果沙盒内 GUI 工具不可用，请确认你选的镜像和 `cua_os_type` 匹配。

## 仓库地址

- GitHub: https://github.com/zouyonghe/astrbot_sandbox_cua

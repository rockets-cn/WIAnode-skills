# WIAnode-skills

[中文](#zh-cn) | [English](#english)

<a id="zh-cn"></a>

## 中文

面向 [DFRobot WIAnode](https://wiki.dfrobot.com.cn/WIAnode) 的 Codex skills 集合，覆盖设备配置、TouchDesigner 自然语言交互，以及 UNIHIKER K10 的 PlatformIO 与 MicroPython 开发。

| Skill | 用途 |
| --- | --- |
| `$wianode-config` | 引导配置设备、校验 `config.txt`、诊断网络和 MQTT |
| `$wianode-touchdesigner` | 通过 [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) 用自然语言搭建、修改和排查 WIAnode 交互网络 |
| `$wianode-k10-platformio` | 用 PlatformIO 创建、烧录和验证 UNIHIKER K10 与 WIAnode 的 MQTT 交互项目 |
| `$wianode-k10-micropython` | 用 MicroPython 创建、上传和验证 UNIHIKER K10 与 WIAnode 的 MQTT 交互项目 |

> ⚠️ **实机测试状态**
>
> - `$wianode-k10-micropython`：**尚未与真实 WIAnode 设备完成实机联调验证**。2026-08 已在真实 K10（MicroPython 1.26 / 固件 v0.9.2）上验证了与本机 MQTT broker 的双向收发；但 WIAnode 特有的 MQTT 行为（双连接规则、QoS、按 client_id 的会话状态等）、传感器/执行器实测，以及固件版本间的兼容性，仍需在真实 WIAnode 上确认。相关内容仅供参考。
> - `$wianode-touchdesigner`：**已完成实机验证**。2026-09 在 Windows、TouchDesigner `2025.33070`、touchdesigner-mcp `v2.0.0` 与真实 WIAnode 上验证了组件导入、回环 API、MCP 注册、现有项目修复、P1 旋钮精确控制 `0–300` 粒子，以及 P5 `SER0053` (`servo300`) 在确认的 `30–270°` 行程内随粒子数量连续运动。其他 TouchDesigner/固件版本与机械结构仍需重新确认参数。

### `$wianode-config` 主要能力

- 用户只说“我要配置 WIAnode”时，主动给出连接设备、安装模块和确认 SKU 的指示。
- 通过 `config.txt` 识别 WIAnode 移动盘，不依赖固定卷标或盘符。
- 支持 Wi-Fi、DHCP/静态 IPv4、P1–P6、I2C、发送间隔和状态灯设置。
- 根据官方传感器清单匹配配置标签、I2C 地址和数据字段。
- 写盘前展示目标路径、备份位置和端口/SKU 表，并等待用户明确确认。
- 写入后运行只读校验器，报告错误、警告和后续物理验证步骤。
- 支持 MQTT 连接与 `topic_input`、`topic_output` 数据格式排查。

本项目不负责 WIAnode 固件开发，也不会把“我要配置”视为写盘授权。

### `$wianode-touchdesigner` 主要能力

- 检查并复用现有 TouchDesigner 网络、WIAnode 数据桥和 MQTT 节点，识别 `mcp_webserver_base1` 等静默重名组件。
- 自动准备官方 TouchDesigner MCP 组件、导入当前项目并注册 Codex；注册后的当前 Codex 进程仍需重启才能获得 MCP tools。
- 用可检查的 CHOP/POP/TOP 数据流映射真实传感器值；需要精确数量时使用显式点数，而不是把 Particle SOP 出生率误当作当前粒子数。
- 对视觉映射做端点/中间值和输出画面验证，并检查整个节点树错误。
- 真实执行器采用“单次指令确认 → 物理确认 → 连续输出授权”的流程；支持范围限制、平滑、死区、发送间隔、双层输出锁和明确停止方法。

### `$wianode-k10-platformio` 主要能力

- 生成标准 `platformio.ini + src/main.cpp` 的 K10 Arduino/C++ 项目。
- 让 K10 订阅 WIAnode 传感器数据，并通过屏幕、RGB、蜂鸣器或串口呈现。
- 将 K10 按键、加速度计或光线传感器映射到 WIAnode 执行器。
- 自动构建、USB 烧录并通过串口验证 Wi-Fi、MQTT 和真实数据包。
- 默认禁用 `topic_output`；生成或烧录执行器逻辑前展示端口、SKU、范围、速率和失效保护并单独确认。

### `$wianode-k10-micropython` 主要能力

- 生成 `main.py + secrets.py` 的 K10 MicroPython 项目，上传后开机自动运行。
- 让 K10 订阅 WIAnode 传感器数据，并通过屏幕（局部刷新）、RGB、蜂鸣器或串口呈现。
- 将 K10 按键、加速度计或光线传感器映射到 WIAnode 执行器。
- 处理 MicroPython 固件互斥（与 Arduino 二选一）、`main.py` 自动运行规则和上传/REPL 验证。
- 默认禁用 `topic_output`；生成或上传执行器逻辑前展示端口、SKU、范围、速率和失效保护并单独确认。
- 注意 V0.9.2 固件中 AI 与 Wi-Fi 不能同时使用；语音合成仅存在于中文版固件。

### 安装

将仓库克隆到 Codex 的本地源码目录，再把四个 skill 分别链接到个人 skills 目录。Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\repos" | Out-Null
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
git clone https://github.com/rockets-cn/WIAnode-skills.git "$env:USERPROFILE\.codex\repos\WIAnode-skills"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\wianode-config" `
  -Target "$env:USERPROFILE\.codex\repos\WIAnode-skills\skills\wianode-config"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\wianode-touchdesigner" `
  -Target "$env:USERPROFILE\.codex\repos\WIAnode-skills\skills\wianode-touchdesigner"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\wianode-k10-platformio" `
  -Target "$env:USERPROFILE\.codex\repos\WIAnode-skills\skills\wianode-k10-platformio"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\wianode-k10-micropython" `
  -Target "$env:USERPROFILE\.codex\repos\WIAnode-skills\skills\wianode-k10-micropython"
```

macOS/Linux：

```bash
mkdir -p "$HOME/.codex/repos" "$HOME/.codex/skills"
git clone https://github.com/rockets-cn/WIAnode-skills.git "$HOME/.codex/repos/WIAnode-skills"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-config" \
  "$HOME/.codex/skills/wianode-config"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-touchdesigner" \
  "$HOME/.codex/skills/wianode-touchdesigner"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-k10-platformio" \
  "$HOME/.codex/skills/wianode-k10-platformio"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-k10-micropython" \
  "$HOME/.codex/skills/wianode-k10-micropython"
```

更新已有安装只需拉取仓库。Windows PowerShell：

```powershell
git -C "$env:USERPROFILE\.codex\repos\WIAnode-skills" pull
```

macOS/Linux：

```bash
git -C "$HOME/.codex/repos/WIAnode-skills" pull
```

安装后检查 Codex 的 skill 列表中是否同时出现 `wianode-config`、`wianode-touchdesigner`、`wianode-k10-platformio` 和 `wianode-k10-micropython`。曾按旧版说明把整个仓库克隆为 `wianode-config` 的用户，需要先保留本地改动，再迁移到上述多目录结构。

`$wianode-touchdesigner` 还需要 TouchDesigner MCP。首次调用时，skill 可以自动下载官方组件、通过 Computer Use 把 `mcp_webserver_base.tox` 导入当前 TouchDesigner 项目的 `/project1`，并为 Codex 注册服务：

```powershell
codex mcp add touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
```

如果当前环境无法控制 TouchDesigner UI，skill 会返回已校验的 `.tox` 绝对路径，只保留一次拖入 `/project1` 的手动步骤。完成注册后仍需重启 Codex，并保持 TouchDesigner 与 `mcp_webserver_base` 运行。实测中已有组件可能位于画布外，重复导入还可能无提示地生成 `mcp_webserver_base1`；新版 skill 会先探测 `127.0.0.1:9981`，并在导入后重新枚举同名前缀组件。

### 使用

可以直接说：

```text
我要配置 WIAnode。
```

或显式调用：

```text
使用 $wianode-config 引导我配置 WIAnode，写入前向我确认，完成后生成含 SKU 的报告。
```

TouchDesigner 中可以直接描述目标，例如：

```text
使用 $wianode-touchdesigner，把 P1 的按钮映射到当前项目的 switch1，按下时切换到第二路画面。
```

```text
使用 $wianode-touchdesigner，把 SEN0224 加速度计 X 轴映射成立方体旋转，并加一点平滑。
```

```text
使用 $wianode-touchdesigner，让 P5 上的 SER0053 舵机转到 200°；发送前先向我展示 MQTT 指令并确认。
```

```text
使用 $wianode-touchdesigner，让 P1 旋钮精确控制 0–300 个粒子，再让 P5 的 SER0053 像秤的指针一样随粒子数量在 30–270° 之间运动；先锁定输出并验证画面，单次测试和连续输出分别向我确认。
```

TouchDesigner skill 会先检查当前项目与 MQTT 连接，优先复用已有节点；传感器读取可直接构建，向 `topic_output` 发送真实执行器指令前则必须单独确认。

实测经验：Particle SOP 的出生率不是精确粒子数量；TouchDesigner 保存可能生成 `.1.toe`、`.2.toe` 并弹出覆盖窗口；发布请求若在返回前断开，指令可能已经生效，不能盲目重发。这些恢复与验证步骤已整理进 [field-tested-workflow.md](skills/wianode-touchdesigner/references/field-tested-workflow.md)。

UNIHIKER K10 可以直接描述目标，例如：

```text
使用 $wianode-k10-platformio，创建一个 K10 项目，在屏幕上显示 WIAnode 的温湿度数据，并通过 USB 烧录后检查串口输出。
```

```text
使用 $wianode-k10-platformio，让 K10 的 A 键控制 WIAnode P5 上的 SER0053 舵机转到 200°；生成输出固件前展示 MQTT 指令并向我确认。
```

```text
使用 $wianode-k10-micropython，创建一个 K10 MicroPython 项目，在屏幕上显示 WIAnode 的传感器数据，上传后检查 REPL 输出。
```

```text
使用 $wianode-k10-micropython，让 K10 的 A 键控制 WIAnode P5 上的 SER0053 舵机转到 200°；生成上传执行器逻辑前展示 MQTT 指令并向我确认。
```

MicroPython skill 会先确认 K10 处于 MicroPython 固件（与 Arduino 互斥），上传 `main.py` 后自动运行；执行器发布同样遵循独立的确认门禁。

典型流程：

1. Agent 指示连接 Type-C 数据线、安装传感器并记录接口和 SKU。
2. Agent 只读查找包含 `config.txt` 的候选移动盘。
3. Agent 采集缺少的 Wi-Fi、网络、端口、SKU、发送间隔和 LED 设置。
4. Agent 展示配置预览并询问：`确认按上述内容写入 <目标路径> 吗？`
5. 用户明确确认后，Agent 才备份、写入并校验。
6. 用户重新上电，Agent 根据指示灯、OLED 和可选 MQTT 测试生成完成报告。

报告中的接口表固定包含 SKU。无法确认的型号会写成 `未提供（待确认）`，不会被猜测为已确认。

### 给 Agent 的说明

[`skills/wianode-config/SKILL.md`](skills/wianode-config/SKILL.md) 是配置 skill 的执行入口和行为规范。加载后应完整读取它，并按任务需要路由到对应参考文件：

| 资源 | 读取时机 |
| --- | --- |
| [`skills/wianode-config/references/config-format.md`](skills/wianode-config/references/config-format.md) | 创建、修改或审查 `config.txt` 前 |
| [`skills/wianode-config/references/sensors.md`](skills/wianode-config/references/sensors.md) | 映射模块 SKU、端口标签或 I2C 地址时 |
| [`skills/wianode-config/references/mqtt.md`](skills/wianode-config/references/mqtt.md) | 连接 MQTT 客户端或诊断数据流时 |
| [`skills/wianode-config/references/completion-report.md`](skills/wianode-config/references/completion-report.md) | 每次引导配置尝试结束时 |
| [`skills/wianode-config/scripts/validate_config.py`](skills/wianode-config/scripts/validate_config.py) | 配置编辑完成后进行只读校验 |

[`skills/wianode-k10-platformio/SKILL.md`](skills/wianode-k10-platformio/SKILL.md) 是 K10 PlatformIO skill 的执行入口，按需路由到 MQTT 契约、工程流程和交互映射参考。

[`skills/wianode-k10-micropython/SKILL.md`](skills/wianode-k10-micropython/SKILL.md) 是 K10 MicroPython skill 的执行入口，按需路由到 MicroPython 工程流程、MQTT 契约和交互映射参考；MicroPython API 细节遵循已安装的 `$unihiker-k10-micropython` skill。

Agent 必须遵守以下约束：

- 优先修改设备现有 `config.txt`，保留注释、顺序、未知键、编码和换行风格。
- 不臆造 Wi-Fi 凭据、静态网络参数、移动盘路径、传感器型号或 SKU。
- 不在摘要、报告或命令输出中复述 Wi-Fi 密码。
- 允许在确认前执行只读检查，但不得备份、编辑、复制或覆盖目标文件。
- 写盘前必须展示准确目标路径、计划备份路径、隐藏密码的网络摘要以及端口/SKU 表，并取得该预览之后的明确确认。
- 确认后只执行批准的变更；一次写入或校验失败后停止，报告错误，不循环覆盖设备。
- SKU 未经用户标签或可靠设备信息确认时，必须标记为 `未提供（待确认）` 或“未确认”。
- 无法直接观察重新上电、指示灯、OLED 或硬件动作时，报告为 `待用户确认`，不能声称成功。
- 普通配置流程不得扩展为固件更新。

建议按以下状态推进，不跳过确认门禁：

```text
意图 → 只读识别 → 信息采集 → SKU/标签解析 → 写入预览 → 用户确认
     → 备份与单次写入 → 校验 → 重新上电/观察 → SKU 完成报告
```

### 配置校验器

需要 Python 3.9 或更高版本。校验现有配置：

```powershell
python skills/wianode-config/scripts/validate_config.py <WIAnode盘符>:\config.txt
```

校验器不会显示 Wi-Fi 密码值。成功返回退出码 `0`，配置错误返回 `1`，文件读取或编码错误返回 `2`。未知字段只产生警告，以便保留新固件可能增加的配置项。

### 仓库结构

```text
.
├── README.md
├── projects/
│   ├── wianode-k10-dashboard/               # PlatformIO + LVGL 实测示例
│   └── wianode-k10-micropython-dashboard/   # MicroPython 移植版
└── skills/
    ├── wianode-config/
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml
    │   ├── references/
    │   │   ├── completion-report.md
    │   │   ├── config-format.md
    │   │   ├── mqtt.md
    │   │   └── sensors.md
    │   └── scripts/
    │       └── validate_config.py
    ├── wianode-k10-platformio/
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml
    │   ├── assets/
    │   │   └── template/wianode-k10/
    │   ├── references/
    │   │   ├── interaction-patterns.md
    │   │   ├── mqtt-contract.md
    │   │   └── platformio-project.md
    │   └── tests/
    │       └── test_template.py
    ├── wianode-k10-micropython/
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml
    │   ├── assets/
    │   │   └── template/wianode-k10-micropython/
    │   ├── references/
    │   │   ├── interaction-patterns.md
    │   │   ├── micropython-project.md
    │   │   └── mqtt-contract.md
    │   └── tests/
    │       └── test_template.py
    └── wianode-touchdesigner/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── references/
        │   ├── automatic-install.md
        │   ├── interaction-patterns.md
        │   ├── touchdesigner-mcp.md
        │   └── wianode-bridge.md
        ├── scripts/
        │   └── prepare_touchdesigner_mcp.py
        └── tests/
            └── test_prepare_touchdesigner_mcp.py
```

### 文档依据

配置字段、接口类型、传感器清单、MQTT 主题和指示灯含义整理自 [DFRobot WIAnode 官方 Wiki](https://wiki.dfrobot.com.cn/WIAnode)。K10 PlatformIO 环境基于 [DFRobot/platform-unihiker](https://github.com/DFRobot/platform-unihiker)，MQTT 和 JSON 模板分别使用 [PubSubClient](https://github.com/knolleary/pubsubclient) 与 [ArduinoJson](https://github.com/bblanchon/ArduinoJson)。K10 MicroPython 项目使用固件内置的 `k10_base.WiFi` / `k10_base.MqttClient` 和 `unihiker_k10` 屏幕 API。

<a id="english"></a>

## English

A collection of Codex skills for [DFRobot WIAnode](https://wiki.dfrobot.com.cn/WIAnode), covering device configuration, natural-language TouchDesigner workflows, and UNIHIKER K10 PlatformIO and MicroPython development.

| Skill | Purpose |
| --- | --- |
| `$wianode-config` | Guide device setup, validate `config.txt`, and diagnose network or MQTT issues |
| `$wianode-touchdesigner` | Use [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) to build, modify, and troubleshoot WIAnode interactions from natural-language requests |
| `$wianode-k10-platformio` | Create, flash, and verify UNIHIKER K10 PlatformIO projects that interact with WIAnode over MQTT |
| `$wianode-k10-micropython` | Create, upload, and verify UNIHIKER K10 MicroPython projects that interact with WIAnode over MQTT |

> ⚠️ **Hardware test status**
>
> - `$wianode-k10-micropython`: **not yet validated end-to-end with a real WIAnode device.** In 2026-08, the K10 side (MicroPython 1.26 / firmware v0.9.2) was verified against a local MQTT broker with bidirectional data flow; however, WIAnode-specific MQTT behavior (the two-connection rule, QoS handling, per-client session state), sensor/actuator tests, and cross-firmware compatibility still need confirmation on a real WIAnode. Treat the content as reference only.
> - `$wianode-touchdesigner`: **field-tested in a real project.** In 2026-09, Windows, TouchDesigner `2025.33070`, touchdesigner-mcp `v2.0.0`, and a real WIAnode were used to verify component import, the loopback API, MCP registration, repair of an existing project, exact P1-driven `0–300` particle counts, and continuous P5 `SER0053` (`servo300`) motion over a confirmed `30–270°` mechanical range. Reconfirm parameters for other TouchDesigner/firmware versions and mechanisms.

### `$wianode-config` capabilities

- Starts a guided setup when the user only says they want to configure WIAnode.
- Finds the WIAnode removable volume by `config.txt` instead of assuming a fixed volume label or drive letter.
- Configures Wi-Fi, DHCP or static IPv4, P1–P6, I2C, send interval, and status LED settings.
- Maps documented sensor SKUs to configuration tags, ports, and I2C addresses.
- Shows the exact target, backup path, and port/SKU table before requesting write confirmation.
- Runs a read-only validator after writing and reports errors, warnings, and required physical checks.
- Diagnoses MQTT connections and the `topic_input` / `topic_output` payload formats.

This project does not develop WIAnode firmware, and a general request to configure the device is not treated as permission to write to it.

### `$wianode-touchdesigner` capabilities

- Inspects and reuses existing TouchDesigner networks, WIAnode data bridges, and MQTT nodes, including detection of silently suffixed components such as `mcp_webserver_base1`.
- Prepares and imports the official TouchDesigner MCP component and registers it with Codex; the current Codex host still needs a restart before newly registered MCP tools appear.
- Builds inspectable CHOP/POP/TOP mappings from observed sensor values, using explicit point populations instead of treating Particle SOP birth rate as an exact current count.
- Verifies visual mappings at endpoints/interior values, inspects output images, and checks the complete node tree for errors.
- Uses a staged actuator flow—single-command confirmation, physical confirmation, then continuous-output authorization—with clamps, smoothing, dead zones, publish intervals, dual interlocks, and an explicit stop method.

### `$wianode-k10-platformio` capabilities

- Generates a standard K10 Arduino/C++ project with `platformio.ini` and `src/main.cpp`.
- Subscribes to WIAnode sensor data and presents it through the K10 screen, RGB LEDs, buzzer, or serial output.
- Maps K10 buttons, accelerometer, or light sensor to WIAnode actuators.
- Builds, uploads over USB, and verifies Wi-Fi, MQTT, and real packets through serial monitoring.
- Disables `topic_output` by default and requires a separate preview and confirmation of the port, SKU, range, publish rate, and fail-safe before output-capable firmware is generated or uploaded.

### `$wianode-k10-micropython` capabilities

- Generates a K10 MicroPython project with `main.py` and `secrets.py`; `main.py` auto-runs after upload and reset.
- Subscribes to WIAnode sensor data and presents it through the K10 screen (partial redraws), RGB LEDs, buzzer, or REPL output.
- Maps K10 buttons, accelerometer, or light sensor to WIAnode actuators.
- Handles MicroPython firmware exclusivity (cannot coexist with Arduino), the `main.py` auto-run rule, and upload/REPL verification.
- Disables `topic_output` by default and requires a separate preview and confirmation of the port, SKU, range, publish rate, and fail-safe before output-capable firmware is generated or uploaded.
- Notes that V0.9.2 firmware cannot run AI and Wi-Fi together, and that TTS exists only in the Chinese firmware.

### Installation

Clone the repository into a local Codex source directory, then link each skill into the personal skills directory.

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\repos" | Out-Null
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
git clone https://github.com/rockets-cn/WIAnode-skills.git "$env:USERPROFILE\.codex\repos\WIAnode-skills"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\wianode-config" `
  -Target "$env:USERPROFILE\.codex\repos\WIAnode-skills\skills\wianode-config"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\wianode-touchdesigner" `
  -Target "$env:USERPROFILE\.codex\repos\WIAnode-skills\skills\wianode-touchdesigner"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\wianode-k10-platformio" `
  -Target "$env:USERPROFILE\.codex\repos\WIAnode-skills\skills\wianode-k10-platformio"
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\wianode-k10-micropython" `
  -Target "$env:USERPROFILE\.codex\repos\WIAnode-skills\skills\wianode-k10-micropython"
```

macOS/Linux:

```bash
mkdir -p "$HOME/.codex/repos" "$HOME/.codex/skills"
git clone https://github.com/rockets-cn/WIAnode-skills.git "$HOME/.codex/repos/WIAnode-skills"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-config" \
  "$HOME/.codex/skills/wianode-config"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-touchdesigner" \
  "$HOME/.codex/skills/wianode-touchdesigner"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-k10-platformio" \
  "$HOME/.codex/skills/wianode-k10-platformio"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-k10-micropython" \
  "$HOME/.codex/skills/wianode-k10-micropython"
```

To update on Windows:

```powershell
git -C "$env:USERPROFILE\.codex\repos\WIAnode-skills" pull
```

To update on macOS/Linux:

```bash
git -C "$HOME/.codex/repos/WIAnode-skills" pull
```

After installation, confirm that `wianode-config`, `wianode-touchdesigner`, `wianode-k10-platformio`, and `wianode-k10-micropython` appear in the Codex skill list. Users who previously cloned the whole repository directly as `wianode-config` should preserve any local changes and migrate to the multi-directory layout above.

`$wianode-touchdesigner` also requires TouchDesigner MCP. On first use, the skill can download the official component, use Computer Use to import `mcp_webserver_base.tox` into `/project1` in the current TouchDesigner project, and register the MCP server with Codex:

```text
codex mcp add touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
```

If TouchDesigner UI control is unavailable, the skill returns a validated absolute path to the `.tox` file, leaving only the drag-and-drop into `/project1` as a manual step. Restart Codex after registration, and keep TouchDesigner and `mcp_webserver_base` running. A healthy existing component can be off-screen, and importing again may silently create `mcp_webserver_base1`; the updated skill probes `127.0.0.1:9981` first and re-enumerates matching components after import.

### Usage

Start a guided device configuration:

```text
I want to configure WIAnode.
```

Or invoke the skill explicitly:

```text
Use $wianode-config to guide me through configuring WIAnode. Ask before writing and produce a report that includes every SKU.
```

Describe a TouchDesigner interaction directly:

```text
Use $wianode-touchdesigner to map the button on P1 to switch1 in the current project. Show the second input while the button is pressed.
```

```text
Use $wianode-touchdesigner to map the X axis of the SEN0224 accelerometer to cube rotation with some smoothing.
```

```text
Use $wianode-touchdesigner to move the SER0053 servo on P5 to 200 degrees. Show me the MQTT command and ask for confirmation before sending it.
```

```text
Use $wianode-touchdesigner to make the P1 knob control exactly 0–300 particles, then drive the P5 SER0053 like a scale pointer over 30–270 degrees. Keep output locked while verifying the visuals, and ask separately before the single test and continuous output.
```

The TouchDesigner skill inspects the current project and MQTT connection before editing, and reuses existing nodes where possible. Sensor-driven networks may be built directly; publishing a real actuator command to `topic_output` always requires a separate confirmation.

Field-tested lessons: Particle SOP birth rate is not an exact population control; TouchDesigner saves may create `.1.toe` / `.2.toe` siblings and block on an overwrite modal; and a publish request that loses its response may already have moved the device, so it must not be retried blindly. The recovery and verification workflow is documented in [field-tested-workflow.md](skills/wianode-touchdesigner/references/field-tested-workflow.md).

Describe a UNIHIKER K10 project directly:

```text
Use $wianode-k10-platformio to create a K10 project that displays WIAnode temperature and humidity on screen, uploads it over USB, and checks the serial output.
```

```text
Use $wianode-k10-platformio to make K10 button A move the SER0053 servo on WIAnode P5 to 200 degrees. Show me the MQTT command and ask before generating output-enabled firmware.
```

```text
Use $wianode-k10-micropython to create a K10 MicroPython project that displays WIAnode sensor data on screen, uploads it, and checks the REPL output.
```

```text
Use $wianode-k10-micropython to make K10 button A move the SER0053 servo on WIAnode P5 to 200 degrees. Show me the MQTT command and ask before generating output-enabled firmware.
```

The MicroPython skill first confirms that the K10 runs MicroPython firmware (it cannot coexist with Arduino), uploads `main.py` so it auto-runs on boot, and applies the same separate confirmation gate before any actuator publishing.

The guided configuration flow is:

1. Connect WIAnode with a Type-C data cable, attach the modules, and record each port and SKU.
2. Find removable volumes containing `config.txt` with read-only checks.
3. Collect only missing Wi-Fi, network, port, SKU, interval, and LED settings.
4. Show the exact write preview and ask for confirmation.
5. After confirmation, create the announced backup, write once, and validate the result.
6. Power-cycle the device and produce a completion report from the LED, OLED, and optional MQTT checks.

Every interface table in the report includes an SKU column. Unknown models remain marked as unconfirmed instead of being guessed.

### Agent guidance

[`skills/wianode-config/SKILL.md`](skills/wianode-config/SKILL.md) is the configuration skill entry point. Read it completely after loading the skill, then open only the reference needed for the task:

| Resource | Read when |
| --- | --- |
| [`skills/wianode-config/references/config-format.md`](skills/wianode-config/references/config-format.md) | Creating, editing, or reviewing `config.txt` |
| [`skills/wianode-config/references/sensors.md`](skills/wianode-config/references/sensors.md) | Mapping a module SKU, port tag, or I2C address |
| [`skills/wianode-config/references/mqtt.md`](skills/wianode-config/references/mqtt.md) | Connecting an MQTT client or diagnosing data flow |
| [`skills/wianode-config/references/completion-report.md`](skills/wianode-config/references/completion-report.md) | Finishing a guided configuration attempt |
| [`skills/wianode-config/scripts/validate_config.py`](skills/wianode-config/scripts/validate_config.py) | Running the read-only configuration validator |

[`skills/wianode-k10-platformio/SKILL.md`](skills/wianode-k10-platformio/SKILL.md) is the K10 PlatformIO skill entry point and routes to the MQTT contract, project workflow, and interaction mapping references as needed.

[`skills/wianode-k10-micropython/SKILL.md`](skills/wianode-k10-micropython/SKILL.md) is the K10 MicroPython skill entry point and routes to the MicroPython project workflow, MQTT contract, and interaction mapping references as needed; MicroPython API details follow the installed `$unihiker-k10-micropython` skill.

Agents must follow these constraints:

- Prefer editing the device's existing `config.txt`; preserve comments, ordering, unknown keys, encoding, and line endings.
- Never invent Wi-Fi credentials, static-network values, removable-volume paths, sensor models, or SKUs.
- Never repeat a Wi-Fi password in summaries, reports, or command output.
- Read-only inspection is allowed before confirmation, but backup, copy, edit, or overwrite operations are not.
- Before writing, show the exact target and backup paths, a password-hidden network summary, and the port/SKU table. Obtain confirmation after showing that preview.
- After confirmation, make only the approved changes. Stop after one failed write or validation attempt instead of repeatedly overwriting the device.
- Mark an unverified SKU as unconfirmed. Do not turn a likely match into a confirmed model.
- Report physical actions that cannot be observed directly as pending user confirmation.
- Do not expand an ordinary configuration workflow into a firmware update.

The configuration state progression is:

```text
intent → read-only discovery → information intake → SKU/tag resolution
       → write preview → user confirmation → backup and one write
       → validation → power-cycle/observation → SKU completion report
```

### Configuration validator

Python 3.9 or newer is required. Validate an existing file with:

```text
python skills/wianode-config/scripts/validate_config.py <WIAnode-volume>:\config.txt
```

The validator never displays the Wi-Fi password value. It returns exit code `0` for a valid configuration, `1` for configuration errors, and `2` for file-read or encoding errors. Unknown fields produce warnings so settings added by newer firmware can be preserved.

### Repository structure

```text
.
├── README.md
├── projects/
│   ├── wianode-k10-dashboard/               # Field-tested PlatformIO + LVGL example
│   └── wianode-k10-micropython-dashboard/   # MicroPython port
└── skills/
    ├── wianode-config/
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml
    │   ├── references/
    │   │   ├── completion-report.md
    │   │   ├── config-format.md
    │   │   ├── mqtt.md
    │   │   └── sensors.md
    │   └── scripts/
    │       └── validate_config.py
    ├── wianode-k10-platformio/
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml
    │   ├── assets/
    │   │   └── template/wianode-k10/
    │   ├── references/
    │   │   ├── interaction-patterns.md
    │   │   ├── mqtt-contract.md
    │   │   └── platformio-project.md
    │   └── tests/
    │       └── test_template.py
    ├── wianode-k10-micropython/
    │   ├── SKILL.md
    │   ├── agents/
    │   │   └── openai.yaml
    │   ├── assets/
    │   │   └── template/wianode-k10-micropython/
    │   ├── references/
    │   │   ├── interaction-patterns.md
    │   │   ├── micropython-project.md
    │   │   └── mqtt-contract.md
    │   └── tests/
    │       └── test_template.py
    └── wianode-touchdesigner/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── references/
        │   ├── automatic-install.md
        │   ├── interaction-patterns.md
        │   ├── touchdesigner-mcp.md
        │   └── wianode-bridge.md
        ├── scripts/
        │   └── prepare_touchdesigner_mcp.py
        └── tests/
            └── test_prepare_touchdesigner_mcp.py
```

### Documentation sources

Configuration fields, interface types, supported sensors, MQTT topics, and indicator meanings are based on the [official DFRobot WIAnode Wiki](https://wiki.dfrobot.com.cn/WIAnode). The K10 PlatformIO environment follows [DFRobot/platform-unihiker](https://github.com/DFRobot/platform-unihiker); the MQTT and JSON templates use [PubSubClient](https://github.com/knolleary/pubsubclient) and [ArduinoJson](https://github.com/bblanchon/ArduinoJson). The K10 MicroPython project uses the firmware's built-in `k10_base.WiFi` / `k10_base.MqttClient` and the `unihiker_k10` screen API.

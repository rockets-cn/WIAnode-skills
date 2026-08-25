# WIAnode-skills

面向 [DFRobot WIAnode](https://wiki.dfrobot.com.cn/WIAnode) 的 Codex skills 集合，覆盖设备配置与 TouchDesigner 自然语言交互。

| Skill | 用途 |
| --- | --- |
| `$wianode-config` | 引导配置设备、校验 `config.txt`、诊断网络和 MQTT |
| `$wianode-touchdesigner` | 通过 [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) 用自然语言搭建、修改和排查 WIAnode 交互网络 |

## `$wianode-config` 主要能力

- 用户只说“我要配置 WIAnode”时，主动给出连接设备、安装模块和确认 SKU 的指示。
- 通过 `config.txt` 识别 WIAnode 移动盘，不依赖固定卷标或盘符。
- 支持 Wi-Fi、DHCP/静态 IPv4、P1–P6、I2C、发送间隔和状态灯设置。
- 根据官方传感器清单匹配配置标签、I2C 地址和数据字段。
- 写盘前展示目标路径、备份位置和端口/SKU 表，并等待用户明确确认。
- 写入后运行只读校验器，报告错误、警告和后续物理验证步骤。
- 支持 MQTT 连接与 `topic_input`、`topic_output` 数据格式排查。

本项目不负责 WIAnode 固件开发，也不会把“我要配置”视为写盘授权。

## 安装

将仓库克隆到 Codex 的本地源码目录，再把两个 skill 分别链接到个人 skills 目录。Windows PowerShell：

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
```

macOS/Linux：

```bash
mkdir -p "$HOME/.codex/repos" "$HOME/.codex/skills"
git clone https://github.com/rockets-cn/WIAnode-skills.git "$HOME/.codex/repos/WIAnode-skills"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-config" \
  "$HOME/.codex/skills/wianode-config"
ln -s "$HOME/.codex/repos/WIAnode-skills/skills/wianode-touchdesigner" \
  "$HOME/.codex/skills/wianode-touchdesigner"
```

更新已有安装只需拉取仓库。Windows PowerShell：

```powershell
git -C "$env:USERPROFILE\.codex\repos\WIAnode-skills" pull
```

macOS/Linux：

```bash
git -C "$HOME/.codex/repos/WIAnode-skills" pull
```

安装后检查 Codex 的 skill 列表中是否同时出现 `wianode-config` 和 `wianode-touchdesigner`。曾按旧版说明把整个仓库克隆为 `wianode-config` 的用户，需要先保留本地改动，再迁移到上述双目录结构。

`$wianode-touchdesigner` 还需要 TouchDesigner MCP。首次调用时，skill 可以自动下载官方组件、通过 Computer Use 把 `mcp_webserver_base.tox` 导入当前 TouchDesigner 项目的 `/project1`，并为 Codex 注册服务：

```powershell
codex mcp add touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
```

如果当前环境无法控制 TouchDesigner UI，skill 会返回已校验的 `.tox` 绝对路径，只保留一次拖入 `/project1` 的手动步骤。完成注册后仍需重启 Codex，并保持 TouchDesigner 与 `mcp_webserver_base` 运行。

## 使用

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

TouchDesigner skill 会先检查当前项目与 MQTT 连接，优先复用已有节点；传感器读取可直接构建，向 `topic_output` 发送真实执行器指令前则必须单独确认。

典型流程：

1. Agent 指示连接 Type-C 数据线、安装传感器并记录接口和 SKU。
2. Agent 只读查找包含 `config.txt` 的候选移动盘。
3. Agent 采集缺少的 Wi-Fi、网络、端口、SKU、发送间隔和 LED 设置。
4. Agent 展示配置预览并询问：`确认按上述内容写入 <目标路径> 吗？`
5. 用户明确确认后，Agent 才备份、写入并校验。
6. 用户重新上电，Agent 根据指示灯、OLED 和可选 MQTT 测试生成完成报告。

报告中的接口表固定包含 SKU。无法确认的型号会写成 `未提供（待确认）`，不会被猜测为已确认。

## 给 Agent 的说明

[`skills/wianode-config/SKILL.md`](skills/wianode-config/SKILL.md) 是配置 skill 的执行入口和行为规范。加载后应完整读取它，并按任务需要路由到对应参考文件：

| 资源 | 读取时机 |
| --- | --- |
| [`skills/wianode-config/references/config-format.md`](skills/wianode-config/references/config-format.md) | 创建、修改或审查 `config.txt` 前 |
| [`skills/wianode-config/references/sensors.md`](skills/wianode-config/references/sensors.md) | 映射模块 SKU、端口标签或 I2C 地址时 |
| [`skills/wianode-config/references/mqtt.md`](skills/wianode-config/references/mqtt.md) | 连接 MQTT 客户端或诊断数据流时 |
| [`skills/wianode-config/references/completion-report.md`](skills/wianode-config/references/completion-report.md) | 每次引导配置尝试结束时 |
| [`skills/wianode-config/scripts/validate_config.py`](skills/wianode-config/scripts/validate_config.py) | 配置编辑完成后进行只读校验 |

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

## 配置校验器

需要 Python 3.9 或更高版本。校验现有配置：

```powershell
python skills/wianode-config/scripts/validate_config.py <WIAnode盘符>:\config.txt
```

校验器不会显示 Wi-Fi 密码值。成功返回退出码 `0`，配置错误返回 `1`，文件读取或编码错误返回 `2`。未知字段只产生警告，以便保留新固件可能增加的配置项。

## 仓库结构

```text
.
├── README.md
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

## 文档依据

配置字段、接口类型、传感器清单、MQTT 主题和指示灯含义整理自 [DFRobot WIAnode 官方 Wiki](https://wiki.dfrobot.com.cn/WIAnode)。

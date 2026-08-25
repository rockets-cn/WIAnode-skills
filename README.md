# WIAnode Config Skill

面向 [DFRobot WIAnode](https://wiki.dfrobot.com.cn/WIAnode) 的 Codex 配置 skill。它把设备配置整理成一个有确认门禁的引导流程：识别配置盘、采集 Wi-Fi 与传感器信息、根据 SKU 映射接口、备份和写入 `config.txt`、校验结果，并生成包含 SKU 的完成报告。

## 主要能力

- 用户只说“我要配置 WIAnode”时，主动给出连接设备、安装模块和确认 SKU 的指示。
- 通过 `config.txt` 识别 WIAnode 移动盘，不依赖固定卷标或盘符。
- 支持 Wi-Fi、DHCP/静态 IPv4、P1–P6、I2C、发送间隔和状态灯设置。
- 根据官方传感器清单匹配配置标签、I2C 地址和数据字段。
- 写盘前展示目标路径、备份位置和端口/SKU 表，并等待用户明确确认。
- 写入后运行只读校验器，报告错误、警告和后续物理验证步骤。
- 支持 MQTT 连接与 `topic_input`、`topic_output` 数据格式排查。

本项目不负责 WIAnode 固件开发，也不会把“我要配置”视为写盘授权。

## 安装

将仓库克隆到 Codex 的个人 skills 目录，并把目标文件夹命名为 `wianode-config`：

```powershell
git clone https://github.com/rockets-cn/WAInode-skill.git "$env:USERPROFILE\.codex\skills\wianode-config"
```

更新已有安装：

```powershell
git -C "$env:USERPROFILE\.codex\skills\wianode-config" pull
```

安装后检查 Codex 的 skill 列表中是否出现 `wianode-config`。

## 使用

可以直接说：

```text
我要配置 WIAnode。
```

或显式调用：

```text
使用 $wianode-config 引导我配置 WIAnode，写入前向我确认，完成后生成含 SKU 的报告。
```

典型流程：

1. Agent 指示连接 Type-C 数据线、安装传感器并记录接口和 SKU。
2. Agent 只读查找包含 `config.txt` 的候选移动盘。
3. Agent 采集缺少的 Wi-Fi、网络、端口、SKU、发送间隔和 LED 设置。
4. Agent 展示配置预览并询问：`确认按上述内容写入 <目标路径> 吗？`
5. 用户明确确认后，Agent 才备份、写入并校验。
6. 用户重新上电，Agent 根据指示灯、OLED 和可选 MQTT 测试生成完成报告。

报告中的接口表固定包含 SKU。无法确认的型号会写成 `未提供（待确认）`，不会被猜测为已确认。

## 给 Agent 的说明

[`SKILL.md`](SKILL.md) 是执行入口和行为规范。加载本 skill 后应完整读取它，并按任务需要路由到对应参考文件：

| 资源 | 读取时机 |
| --- | --- |
| [`references/config-format.md`](references/config-format.md) | 创建、修改或审查 `config.txt` 前 |
| [`references/sensors.md`](references/sensors.md) | 映射模块 SKU、端口标签或 I2C 地址时 |
| [`references/mqtt.md`](references/mqtt.md) | 连接 MQTT 客户端或诊断数据流时 |
| [`references/completion-report.md`](references/completion-report.md) | 每次引导配置尝试结束时 |
| [`scripts/validate_config.py`](scripts/validate_config.py) | 配置编辑完成后进行只读校验 |

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
python scripts/validate_config.py <WIAnode盘符>:\config.txt
```

校验器不会显示 Wi-Fi 密码值。成功返回退出码 `0`，配置错误返回 `1`，文件读取或编码错误返回 `2`。未知字段只产生警告，以便保留新固件可能增加的配置项。

## 仓库结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── completion-report.md
│   ├── config-format.md
│   ├── mqtt.md
│   └── sensors.md
└── scripts/
    └── validate_config.py
```

## 文档依据

配置字段、接口类型、传感器清单、MQTT 主题和指示灯含义整理自 [DFRobot WIAnode 官方 Wiki](https://wiki.dfrobot.com.cn/WIAnode)。官方页面的 MQTT 用户名存在不一致：本 skill 优先采用主 MQTT 与 TouchDesigner 章节一致的 `wianode`，仅在认证失败时把 `mqtt` 作为显式诊断备选。

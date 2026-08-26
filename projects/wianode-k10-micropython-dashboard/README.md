# WIAnode × UNIHIKER K10 — MicroPython dashboard

MicroPython 移植版仪表盘，对应 `../wianode-k10-dashboard`（PlatformIO + LVGL）的实测功能：

- **P1 旋钮 → P5 舵机**：旋钮（DFR0054）动态范围映射到 P5 300° 离合舵机（SER0053）30–270°，死区 1°，仅在真实转动时发布 `{"p5":"<角度>"}`。
- **P2 声音** 与 **SEN0228 光照**（I2C，键名按真实报文中的 `lux` 片段发现）。
- **LUX 趋势图**：滚动折线，按观测最大值归一化到 0–100。
- **系统状态卡**：Wi-Fi / MQTT 连接状态、K10 IP、P5 角度。
- 局部刷新（只重绘变化的行/区域），回调中不渲染；每 5 s 输出无凭据诊断行。

## 上传运行

K10 必须先刷 MicroPython 固件（与 Arduino 互斥），且仅 `main.py` 开机自动运行。

```text
k10-micropython upload-mp main.py      # 或 mpremote cp main.py :main.py
k10-micropython upload-mp secrets.py   # 若之前未上传
k10-micropython flash-mp               # 需要刷固件时（先按 BOOT 再按 RST）
```

上传后按 `RST` 复位，通过 REPL 观察 `Status WiFi=... MQTT=... RX=... UI=...` 诊断行。

## 凭据

复制 `secrets.example.py` 为 `secrets.py` 并填入 Wi-Fi 与 WIAnode 值（WIAnode IP 按 `WKUP` 键从 OLED 查看）。`secrets.py` 已被 `.gitignore` 排除，不得提交。

## 执行器门禁

P1→P5 舵机发布已按
[`skills/wianode-k10-micropython/SKILL.md`](../../skills/wianode-k10-micropython/SKILL.md)
的确认门禁预览并获用户确认，`ENABLE_ACTUATOR_OUTPUT` 当前为 `True`
（P5 SER0053、30–270°、死区 3°、`{"p5":"<角度>"}`、断开即停发）。
如需回到只读模式，改为 `False`。

## 实测经验（2026-08 上板验证）

- **不要用 `k10_base.MqttClient`**：该包装层在本固件上会陷入重连循环、破坏 QoS 1
  PUBACK 流程，导致 WIAnode 输出乱动。`main.py` 直接用固件的 `umqtt.simple`
  + QoS 0 紧凑载荷，行为与 PlatformIO 版一致。
- **WIAnode 只应用“未订阅 `topic_input`”的连接的输出指令**：实测订阅后同一条
  `topic_output` 指令不再驱动 P5；且 broker 按 client_id 保留会话，曾订阅过的
  client_id 重连后仍被当作订阅者。因此本项目拆成两个连接：`k10i-*` 只接收、
  `k10o-*` 只发布（从不订阅）。
- **WIAnode 输出失效时先断电重启 WIAnode**：会清除按 client_id 积累的异常会话
  状态（实测重启后 K10 指令立即恢复生效）。
- **旋钮值量化到 0.01（≈2.4°）**：死区须大于一个量化步长（本项目用 3°），否则
  ADC 噪声会让舵机在两档之间振荡（30°↔32° 交替发布）。
- 接收速率：WIAnode 以 50 Hz 发布，K10 主循环 `check_msg()` 排空实测约 20 Hz
  （UI 渲染会占用主线程）；数据按最新值合并显示，不影响仪表盘观感。

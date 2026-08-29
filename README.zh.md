# Phone-Eye 📱👁️

[English](README.md) | **简体中文**

**让你的 AI 助手真正"看见"并"操作"一台真实的安卓手机。**

```
phone_look("屏幕上是什么?登录按钮在哪?")
  → "登录按钮在 (540, 1830)——绿色 Sign in …"
phone_tap(540, 1830)
phone_look("下一页加载出来了吗?")
```

适配任何 MCP 客户端——Claude Code、Codex、Cursor、dsh 等。

---

## 你需要准备什么(大白话)

| 你要提供 | 一次性还是每次? | 难度? |
|---|---|---|
| **一台开了 USB 调试的安卓手机** | **一次性,约 60 秒**(连点"版本号"7 次→打开 USB 调试) | 简单,下面有分步指引 |
| **插一次 USB 线** | **一次性**——之后工具把手机切成 Wi-Fi 模式,线可以永久收起来(恢复出厂才需要再来一次) | 零难度 |
| **一台装了 Python 3.10+ 和 git 的电脑**(或者只用 Docker,见第 3 步) | — | — |
| **一个会看图的模型** | 一次配置——**任选其一**:<br>• OpenAI 的 API key(或任何 OpenAI 兼容:GLM、DeepSeek、本地 llama.cpp/Ollama…)<br>• 你已有的 MCP 视觉服务器 | 一个环境变量,大多数人手上就有 key |

就这些。**手机上不用装任何 App。不需要 root。不需要额外起服务器。**

## 能做什么 / 不能做什么(诚实表)

| ✅ 稳定 | ⚠️ 能用但有保留 | ❌ 不可能(所有同类工具都一样) |
|---|---|---|
| 看屏幕(截图+读懂它) | 锁屏可以"读"但不能"操作" | 你自己没开 USB 调试的全新手机,任何工具都摸不到 |
| 点击 / 滑动 / 输入 | 输入只支持 ASCII(中文要走剪贴板方案——adb 的已知限制) | 新电脑密钥第一次弹出的"允许 USB 调试?"——那一下必须你自己点 |
| Wi-Fi adb 断线自动重连 | 部分厂商 ROM 限制锁屏下的输入(如 MIUI) | iOS——另一个宇宙 |
| 7×24 无人值守;计划外弹窗由你的 agent 读懂并处理 | 视觉质量取决于你带来的模型 | |
| 多手机(每台手机一个 phone-eye 进程,各设 `ANDROID_SERIAL`) | | |

**60 秒规则**:每台安卓需要人类的一次性时刻——开调试+授权一次。之后,手机就属于你的 agent 了,Wi-Fi 也行,电脑重启也不怕。

## 安装(3 步)

### 1. 打开 USB 调试(每台手机一次)

设置 → 关于手机 → 连点**"版本号" 7 次**(解锁开发者选项)→ 开发者选项 → 打开 **USB 调试**。
(卡住了?到 [Discussions](https://github.com/boheastill/phone-eye/discussions) 报你的手机型号,我们带你走。MIUI/HyperOS 可能还要求先登录小米账号。)

### 2. 装 adb(如果还没有),插一次 USB,然后转无线

```bash
# macOS: brew install android-platform-tools · Ubuntu/Debian: sudo apt install adb
# Windows: scoop install adb(或下载 Android platform-tools)
adb devices          # 手机出现了?在手机弹窗上点"允许"——勾选"一律允许"
adb shell ip route   # ← 趁还插着线,记下手机的 Wi-Fi IP(如 192.168.1.23)
adb tcpip 5555       # 切到 Wi-Fi 模式(adb 会重启,USB 条目消失——正常)
adb connect 192.168.1.23:5555   # 用上面的 IP;然后拔线,永久无线
```

<details><summary><code>ip route</code> 没输出?其他找手机 IP 的办法</summary>

设置 → WLAN → 你的网络 → 详情里有 IP;或 `adb shell ip addr show wlan0 | grep inet`。
</details>

### 3. 启动 phone-eye

```bash
git clone https://github.com/boheastill/phone-eye && cd phone-eye
pip install -r requirements.txt

# 眼睛——三选一:
export PHONE_EYE_VISION_API_KEY=<key>                    # OpenAI / GLM / 任何兼容
#   (可选: PHONE_EYE_VISION_BASE_URL, PHONE_EYE_VISION_MODEL)
#   本地离线: ..._API_KEY=sk-noauth ..._BASE_URL=http://<主机>:8080/v1 ..._MODEL=<你的 qwen-vl>

python server.py       # stdio MCP 服务器——接进你的客户端:
```

接入客户端——挑你的:

```bash
# Claude Code(最简单):
claude mcp add phone-eye -- python /path/to/phone-eye/server.py
```

```jsonc
// 任何 MCP 客户端(通用 stdio 形状):
{ "mcpServers": { "phone-eye": { "command": "python", "args": ["/path/to/phone-eye/server.py"] } } }
```

### Docker(可选——宿主机不需要 Python)

仓库自带 `Dockerfile`(Python 3.12 + adb):

```bash
podman build -t phone-eye .        # 或: docker build -t phone-eye .
# 冒烟:stdout 打出 JSON-RPC initialize 回复即说明能跑:
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}\n' \
  | podman run --rm -i phone-eye
```

用 `--network host` 让 adb 能摸到 Wi-Fi 手机和视觉端点:

```jsonc
"phone-eye": { "command": "podman", "args": ["run","--rm","-i","--network","host",
  "-e","ANDROID_SERIAL=192.168.1.23:5555","-e","PHONE_EYE_VISION_API_KEY=<key>","phone-eye"] }
```

**推荐视觉模型**(任何能看图的对话模型都行):`gpt-4o-mini`(默认)、GLM `glm-4.6v-flash`(便宜)、或本地 Qwen-VL(经 llama.cpp)——截图一个字节都不出你的局域网。

## 出问题了怎么办

- **"No Android device reachable"** → 工具已经自动重连过一次了;再跑 `adb connect <ip>:5555`,或重新插线。
- **"No vision server reachable"** → 你没设 key;错误信息里有两条具体修法。
- 手机重启了 → 大多数 ROM 上 Wi-Fi adb 能活;不行就再 `adb connect` 一次。
- 还卡着?**[开个 Discussion](https://github.com/boheastill/phone-eye/discussions)——我们会回,并且陪你把环境调通。**报 bug 和"我的 X 型号能用"的留言同样欢迎。

## 工具一览

| 工具 | 干什么 |
|---|---|
| `phone_look(question?)` | 问视觉模型"屏幕现在什么样";融合 UI 树拿到精确文字/按钮坐标 |
| `phone_tap(x, y)` | 点击 |
| `phone_swipe(x1, y1, x2, y2, ms?)` | 滑动 |
| `phone_type(text)` | 输入 ASCII 文本 |
| `phone_key(key)` | 按硬件键——`wake` 唤醒睡着的手机(无人值守刚需),back/home/recents 导航 |
| `phone_intent(action, uri?, component?)` | 按 Android intent 直达任意页面(系统深页/应用页),无需坐标 |
| `phone_screenshot()` | 截图存盘,返回路径 |

## 示例

- [移动 Web QA 循环](examples/loop-mobile-web-qa.md)——agent 在真机上验收自己的活
- [走过 OEM 设置向导](examples/device-setup-wizard.md)——弹什么都能视觉应对
- [表单回归检查](examples/form-regression.md)
- [无人值守哨兵](examples/unattended-sentinel.md)——你的 agent 值夜班:唤醒→解锁→直达→查看→存证

想了解原理、想改代码?[工作原理白皮书](docs/how-it-works.md)。要以常驻 HTTP 服务跑?[docs/fleet.md](docs/fleet.md)。

## 为什么叫"看"?这不就是 adb 吗?

只读 UI 树的工具看不见游戏画面、图片、无障碍树里没有的东西;只靠视觉的工具坐标会飘。`phone_look` 融合两者:模型回答"这是什么",UI 树给出"具体在哪"。我们 dogfood 的第一天,它发现自己屏幕上挂着一个 USB 调试授权弹窗,读出按钮坐标,自己点了"允许"——[故事在这里](https://github.com/deepseek-ai/deepseek-harness/discussions/4743)。

## 许可

MIT。已在 Redmi K40 Gaming / Android 13 上验证——欢迎 PR 补充你的机型。

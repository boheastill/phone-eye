# Phone-Eye 📱👁️

**English | [简体中文](README.zh.md)**


**Your AI agent can finally *see* and *operate* a real Android phone.**

```
phone_look("what's on screen, where is the login button?")
  → "Login button at (540, 1830) — a green 'Sign in' …"
phone_tap(540, 1830)
phone_look("did the next page load?")
```

Works with any MCP client — Claude Code, Codex, Cursor, dsh, and friends.

---

## What you need (plain words)

| You provide | One-time or every time? | How hard? |
|---|---|---|
| **An Android phone with USB debugging on** | **one-time, ~60 seconds** (tap "Build number" 7× → enable USB debugging) | easy, [step-by-step below](#1-enable-usb-debugging-once-per-phone) |
| **Plug the USB cable once** | **one-time** — after that the tool switches the phone to Wi-Fi and you never need the cable again (unless the phone factory-resets) | trivial |
| **A computer with Python 3.10+ and git** (or just Docker — see step 3) | — | n/a |
| **A vision model** | one-time setup — **bring any one of these**:<br>• an OpenAI API key (or any OpenAI-compatible: GLM, DeepSeek, local llama.cpp/Ollama…)<br>• an existing MCP vision server | one env var, most people already have a key |

That's everything. **No app to install on the phone. No root. No extra server.**

## What it can and can't do (honest table)

| ✅ Stable | ⚠️ Works but with caveats | ❌ Not possible (any tool, not just us) |
|---|---|---|
| See the screen (screenshot + read it) | Locked screens can be *read* but not operated | Fully control a brand-new phone before you enable USB debugging yourself |
| Tap / swipe / type | Typing is ASCII (Chinese input needs a clipboard trick — known adb limit) | The very first "allow USB debugging?" popup on a *new* computer key — that one tap is yours |
| Survive Wi-Fi adb drops (auto-reconnect) | Some vendor ROMs restrict input on lock screens (e.g. MIUI) | iOS — different universe |
| Run 24/7 unattended; unexpected popups get read & handled by your agent | Vision quality depends on the model you bring | |
| Multiple phones (one phone-eye process per phone, set `ANDROID_SERIAL` for each) | | |

**The 60-second rule:** every Android requires one human moment — enable debugging + authorize once. After that, the phone belongs to your agent, even over Wi-Fi, even after reboots of the *computer*.

## Setup (3 steps)

### 1. Enable USB debugging (once per phone)

Settings → About phone → tap **Build number** 7× (unlocks Developer options) → Developer options → **USB debugging ON**.
(Got stuck? Tell us your phone model in Discussions — we'll walk you through it. MIUI/HyperOS may also ask you to sign into a Xiaomi account first.)

### 2. Install adb (if you don't have it), plug USB once, then go wireless

```bash
# macOS: brew install android-platform-tools · Ubuntu/Debian: sudo apt install adb
# Windows: scoop install adb  (or download Android platform-tools)
adb devices          # phone shows up? tap "Allow" on its popup — check "always allow"
adb shell ip route   # ← note the phone's Wi-Fi IP (e.g. 192.168.1.23) while still plugged
adb tcpip 5555       # switch to Wi-Fi mode (adb restarts; the USB entry disappears — normal)
adb connect 192.168.1.23:5555   # use the IP from above; then unplug the cable, forever
```

<details><summary>Phone IP alternatives if <code>ip route</code> prints nothing</summary>

Settings → Wi-Fi → your network → details shows the IP; or `adb shell ip addr show wlan0 | grep inet`.
</details>

### 3. Start phone-eye

```bash
git clone https://github.com/boheastill/phone-eye && cd phone-eye
pip install -r requirements.txt

# your eyes — pick ONE:
export PHONE_EYE_VISION_API_KEY=<key>                    # OpenAI / GLM / any compatible
#   (optional: PHONE_EYE_VISION_BASE_URL, PHONE_EYE_VISION_MODEL)
#   local & offline: ..._API_KEY=sk-noauth ..._BASE_URL=http://<host>:8080/v1 ..._MODEL=<your qwen-vl>

python server.py       # stdio MCP server — wire into your client:
```

Wire it into your client — pick yours:

```bash
# Claude Code (easiest):
claude mcp add phone-eye -- python /path/to/phone-eye/server.py
# Codex:
codex mcp add phone-eye --url stdio://python /path/to/phone-eye/server.py  # or see codex docs
```

```jsonc
// any MCP client (generic stdio shape):
{ "mcpServers": { "phone-eye": { "command": "python", "args": ["/path/to/phone-eye/server.py"] } } }
```

### Docker (optional — no Python needed on the host)

The repo ships a `Dockerfile` (Python 3.12 + adb):

```bash
podman build -t phone-eye .        # or: docker build -t phone-eye .
# smoke: a JSON-RPC initialize reply on stdout means it boots:
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}\n' \
  | podman run --rm -i phone-eye
```

Use `--network host` so adb reaches a Wi-Fi phone and your vision endpoint:

```jsonc
"phone-eye": { "command": "podman", "args": ["run","--rm","-i","--network","host",
  "-e","ANDROID_SERIAL=192.168.1.23:5555","-e","PHONE_EYE_VISION_API_KEY=<key>","phone-eye"] }
```

**Recommended vision models** (any vision-capable chat model works): `gpt-4o-mini` (default),
GLM `glm-4.6v-flash` (cheap), or run a local Qwen-VL via llama.cpp for fully-offline —
screenshots then never leave your LAN.

## What happens when something breaks

- **"No Android device reachable"** → the tool already tried reconnecting; run `adb connect <ip>:5555`, or replug USB.
- **"No vision server reachable"** → you haven't set a key; the error message tells you the exact two fixes.
- Phone rebooted → Wi-Fi adb survives phone reboots on most ROMs; if not, one `adb connect` again.
- Still stuck? **[Open a discussion](https://github.com/boheastill/phone-eye/discussions) — we answer, and we'll debug your setup with you.** Bug reports and "it works on my X" notes are equally welcome.

## Tools

| Tool | What it does |
|---|---|
| `phone_look(question?)` | Ask a vision model about the live screen; fuses a UI-tree dump for exact text/button bounds |
| `phone_tap(x, y)` | Tap |
| `phone_swipe(x1, y1, x2, y2, ms?)` | Swipe |
| `phone_type(text)` | Type ASCII text |
| `phone_key(key)` | Press a hardware key — `wake` revives a sleeping phone (the unattended essential), back/home/recents navigate |
| `phone_intent(action, uri?, component?)` | Open any screen by Android intent (deep settings pages, app pages) without coordinates |
| `phone_screenshot()` | Save screenshot to disk, return path |

## Examples

- [Mobile web QA loop](examples/loop-mobile-web-qa.md) — the agent verifies its own work on a real screen
- [Surviving an OEM setup wizard](examples/device-setup-wizard.md) — vision handles whatever pops up
- [Form regression check](examples/form-regression.md)
- [Unattended sentinel](examples/unattended-sentinel.md) — your agent on night watch: wake → unlock → intent → look → screenshot

Curious how it works — or want to modify it? Read the [whitepaper](docs/how-it-works.md)
(architecture, failure-classification decision tree, security model, how to add a verb).
Running it as an always-on HTTP service behind your own fleet? [docs/fleet.md](docs/fleet.md).

## Why "see", isn't this just adb?

UI-tree-only tools are blind to game canvases, images, and anything the accessibility tree can't show. Vision-only tools drift on coordinates. `phone_look` fuses both: the model answers *what is this*, the UI tree supplies *exactly where*. The day we dogfooded it, it discovered a USB-debugging popup on its own screen, read the buttons, and tapped "Allow" by itself — [the story](https://github.com/deepseek-ai/deepseek-harness/discussions/4743).

## License

MIT. Verified on Redmi K40 Gaming / Android 13 — add your device to the table via PR.

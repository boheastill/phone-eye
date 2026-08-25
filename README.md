# Phone-Eye 📱👁️

**Let your AI agent see — and operate — a real Android phone.**

Your coding agent can read code, run commands, and browse docs. Can it see the
app it's building, on a real phone, with real pixels? **Phone-Eye gives it eyes
and a finger.**

```
phone_look("what's on screen, and where is the login button?")
  → "Login button at (540, 1830) — a green 'Sign in' …"
phone_tap(540, 1830)
phone_look("did the next page load?")
```

Five verbs, no framework: your agent composes them into whatever workflow it
needs. Works with **any MCP client** — Claude Code, Codex, Cursor, dsh, and
friends.

## Why

If you build or test anything that ends up on a phone, you know this loop:
the layout is broken on the real device, you screenshot by hand, describe
screens in words ("the gear, top right, next to the account thing"), and play
coordinate-decoder between your agent and your phone. Phone-Eye closes that
loop — the agent iterates with the device the way it already iterates with
your codebase.

Two channels, fused:

- **Vision** — a vision model answers natural-language questions about the
  live screenshot (works on game canvases, images, anything pixels can show).
- **UI tree** — `uiautomator` dump for exact text and bounds when the
  accessibility tree has them.

**Vision is pluggable.** Any MCP server exposing `describe_image(path,
question)` works — cloud GLM vision out of the box, or point it at a local
Qwen-VL endpoint so no pixel ever leaves your LAN.

## Install

Requirements: Python 3.10+, `adb` (platform-tools / android-tools) on PATH,
a phone with USB debugging on, and any MCP vision server.

```bash
git clone https://github.com/boheastill/phone-eye
cd phone-eye
pip install -r requirements.txt

# env (defaults shown):
export ANDROID_SERIAL=""                      # empty = first adb device; or 192.168.x.x:5555
export PHONE_EYE_VISION_URL="http://127.0.0.1:8102/mcp"  # your vision MCP
```

Wire it into your client (stdio):

```jsonc
// Claude Code / dsh-mcp-client / any stdio MCP config
{
  "mcpServers": {
    "phone-eye": { "command": "python", "args": ["/path/to/phone-eye/server.py"] }
  }
}
```

Or run it as an HTTP service (streamable-http) behind your own fleet and add
`http://<host>:8122/mcp` — see [docs/fleet.md](docs/fleet.md).

### Connect the phone (one-time)

USB once, then Wi-Fi forever:

```bash
adb devices                      # USB: accept the debugging prompt on the phone
adb tcpip 5555                   # switch to Wi-Fi mode
adb connect <phone-ip>:5555      # unplug and go
```

## Tools

| Tool | What it does |
|---|---|
| `phone_look(question?, use_tree?)` | Ask a vision model about the live screen; fuses UI-tree text + bounds |
| `phone_tap(x, y)` | Tap |
| `phone_swipe(x1, y1, x2, y2, ms?)` | Swipe |
| `phone_type(text)` | Type ASCII (spaces ok; CJK needs clipboard route — known adb quirk) |
| `phone_screenshot()` | Save screenshot to disk, return path |

## What it is / isn't

✔ agent eyes + hands on one real Android device, zero on-device install, no root
✔ vision-first (works where UI trees can't see) with tree-fusion for precision
✔ privacy option: point vision at a LAN-only model

✘ not a test framework (no DSL/recorder — the agent is the logic)
✘ not iOS, not device farms (yet)
✘ not a mobile UI for humans (that's a different product)

## Status & roadmap

**Phase 1 (now):** the five verbs, single device, pluggable vision — verified
end-to-end on real hardware (Redmi K40 Gaming / Android 13). Its favorite
party trick so far: it discovered a USB-debugging authorization dialog on its
own screen, read the buttons, and tapped "Allow" itself.

- [ ] Phase 2: offline vision quick-start, multi-device addressing,
      retry/verify wrappers
- [ ] Everything else: request-driven — open an issue and it moves up the queue.

## License

MIT

## FAQ

**Vision server? I don't have one.** Any MCP server exposing
`describe_image(path, question)` works. The quickest cloud option is a GLM
vision endpoint; for fully-offline, a local Qwen-VL (llama.cpp / Ollama
OpenAI-compatible + a 20-line adapter) keeps every pixel on your LAN.

**Why not a dsh-native plugin?** MCP-first means the same five verbs work in
every client. dsh users can wire it via `@deepseek-ai/dsh-mcp-client` or
`dsh plugin add`.

## Verified on

| Device | Android | Connection | Notes |
|---|---|---|---|
| Redmi K40 Gaming (ares) | 13 (HyperOS) | Wi-Fi adb (`adb tcpip 5555`) | daily driver of the author's fleet |

Add yours via a PR to this table.

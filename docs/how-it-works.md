# How Phone-Eye Works — a whitepaper for modifiers

> Read this if you want to understand the moving parts well enough to change
> them. It maps every behavior to its code location and explains *why* each
> design decision was made — including the ones we'd do differently today.
> (~10 min read. Code references are to `server.py`, a single ~300-line file.)

## The whole system in one picture

```
┌─ your AI agent (Claude Code / Codex / dsh / …) ─────────────┐
│  calls MCP tools: phone_look / tap / swipe / type / shot    │
└──────────────┬──────────────────────────────────────────────┘
               │ stdio (JSON-RPC, FastMCP)
┌──────────────▼──────────────────────────────────────────────┐
│  server.py — phone-eye                                      │
│                                                             │
│  HAND  ── subprocess ──► adb ──(Wi-Fi or USB)──► 📱 phone   │
│        tap/swipe/type:      `adb shell input …`             │
│        screenshot:          `adb exec-out screencap -p`     │
│        UI tree:             `adb shell uiautomator dump`    │
│                                                             │
│  EYES  ── two routes, picked at call time:                  │
│        a) built-in direct:  OpenAI-compatible HTTP          │
│           (PHONE_EYE_VISION_API_KEY set)                    │
│        b) MCP vision server: streamable-http + SSE          │
│           (PHONE_EYE_VISION_URL, e.g. a fleet member)       │
│                                                             │
│  FUSION: phone_look = vision answer + UI-tree bounds        │
└─────────────────────────────────────────────────────────────┘
```

Design stance: **five verbs, nothing else.** No DSL, no recorder, no workflow
engine. Whatever orchestration you need, your agent already does it better
than a config format we could invent. Our job is to make each verb reliable
and let the intelligence live in the caller.

## The three subsystems, in the order a modifier cares

### 1. The adb layer (`_adb`, ~line 43)

Everything the hand does goes through one function so that **failure
classification lives in exactly one place**. Read it as a decision tree:

```
subprocess.run(["adb", …])
├─ FileNotFoundError        → "install platform-tools first" (with per-OS hints)
├─ "more than one device"   → "set ANDROID_SERIAL; one phone per process"
├─ "no devices/offline/not found"
│    ├─ ANDROID_SERIAL is ip:port (Wi-Fi) and not yet retried
│    │    └─ adb connect <serial> once
│    │         ├─ command is read-only (screencap/cat/uiautomator/…)
│    │         │    → replay it (safe: no side effects)
│    │         └─ command is `input …` (tap/swipe/type)
│    │              → DO NOT replay. Raise "reconnected; call the tool again."
│    │                (A dropped ack after execution would double-tap —
│    │                 for "tap Confirm Payment" that's a real hazard.)
│    └─ else → "No Android device reachable … adb connect <ip>:5555"
└─ other error → surfaced with stderr excerpt
```

Why replay at all? Wi-Fi adb drops silently after days of uptime — it's the
#1 cause of "worked yesterday" reports. Auto-reconnect turns that from a
crash into a one-second hiccup — but only for idempotent commands.

**If you modify:** keep the read-only allowlist (`exec-out`, `cat`,
`uiautomator`, `getprop`, `dumpsys`) honest. Anything not on it must never be
auto-replayed.

### 2. The eyes: two routes, one seam (`_vision_look`, ~line 120)

Route selection is deliberately trivial — **one env var**:

```python
if VISION_API_KEY:  return _vision_direct(...)   # built-in, zero deps
else:               return _vision_mcp(...)      # your MCP vision server
```

- **Built-in direct** (`_vision_direct`): plain OpenAI-compatible
  `POST /chat/completions` with the screenshot as a base64 `image_url`.
  No SDK, no MCP — so it works with OpenAI, GLM, DeepSeek, vLLM, llama.cpp's
  `llama-server`, Ollama's OpenAI shim, anything. This is the route we
  recommend to newcomers; it exists because "first set up an MCP vision
  server" was silently killing our install funnel.
- **MCP server route** (`_vision_mcp`): full client handshake
  (`initialize` → `notifications/initialized` → `tools/call
  describe_image`). This is how a fleet shares one vision member across
  many machines; also how you keep vision swappable per project.

**The seam is the point**: vision is a *policy* choice (cloud vs local vs
private), so it's routed by configuration, not code. Adding a third route
(say, a local ONNX model) means adding one function and one branch — nothing
else changes.

#### The SSE parsing wart (know before you touch)

MCP streamable-http replies arrive as Server-Sent Events. Our parser
(`_vision_mcp` tail) aggregates `data:` lines until a blank line, then
`json.loads` the joined blob. Two known imperfections, kept deliberately
small:

- SSE spec says join multi-line `data:` with `\n`; we join with `""`.
  JSON split across `data:` boundaries mid-token parses fine either way in
  practice (the frames we've seen split at pretty-print boundaries), but if
  you chase a weird `JSONDecodeError`, look here first.
- A `data:` line without the trailing space (`data:{…}`) is accepted; a
  response that is plain JSON (not SSE) falls through to `return raw[:1500]`
  — ugly but visible, which beats silent loss.

**If you modify:** resist the urge to import an SSE library for this; the
hand parser is 15 lines and has no dependencies — that's worth more than
spec-perfection here.

### 3. The fusion (`phone_look`, the only interesting tool)

`phone_look` runs both channels and concatenates with section markers:

```
[vision]   ← semantic answer, natural language, coordinates-ish
[ui-tree]  ← `text @ [x1,y1][x2,y2]` lines, exact bounds
```

Why both:

| | vision | UI tree |
|---|---|---|
| Sees games/Canvas/images | ✅ | ❌ (invisible to accessibility) |
| Exact coordinates | drifts | ✅ pixel-perfect |
| Semantics ("this is a login error") | ✅ | ❌ strings only |
| Cost | API call | free |

The agent (not us) reconciles them — in practice it reads the vision
answer, then snaps to the nearest tree bounds for the tap. That division of
labor is why five verbs stay five.

The tree comes from `adb shell uiautomator dump` + two regexes (`_ui_tree`).
Yes, regex over XML — deliberately. The dump's attribute order is fixed by
uiautomator itself, the file is bounded (~100KB), and a real XML parser
buys nothing here but a dependency. Cap: 40 items, to keep the tool result
small enough for agent context.

## Security model — read before exposing this to anyone

1. **The hand is remote shell execution.** `adb shell input …` runs as the
   phone's `shell` user (uid 2000). "No app, no root" is true; "no code
   execution on the phone" is NOT — never claim it. We deliberately expose
   only `input tap/swipe/text`, `screencap`, `uiautomator` — no arbitrary
   shell passthrough.
2. **Injection guard in `phone_type`.** `adb shell` joins argv and runs it
   through the phone's `sh -c`, so `;`, `$()`, backticks in typed text
   would execute *on the phone*. We wrap text in single quotes with
   `'` → `'\''` escaping and reject control characters. Found by an AI
   audit, fixed in 86a7ce9 — keep that logic if you touch typing.
3. **Screenshots are screen contents.** They land in `PHONE_EYE_SHOTS`
   (default `/tmp/phone-eye`) and go to whatever vision endpoint you
   configured. Private data? Use the built-in route with a LAN-local
   model. (Roadmap: auto-scrub after the vision call — see R7.)
4. **Keys**: vision keys live only in env vars → `Authorization` headers;
   they never appear in error messages (the error paths print URLs and
   status codes only).

## How to add a verb (the modification you'll actually do)

Say you want `phone_key(keycode)` for hardware keys:

```python
@mcp.tool()
def phone_key(keycode: int) -> str:
    """Press a hardware key (4=Back, 3=Home, 224=Wake…)."""
    try:
        _adb("shell", "input", "keyevent", str(int(keycode)), timeout=15)
        return f"key {keycode}"
    except Exception as e:
        return f"phone_key failed: {e}"
```

That's the pattern: thin, typed, timeout'd, error-as-string (agents read
strings better than tracebacks), side-effect-free of our state. Then:
`grep README* for the tools table` and add a row — the docs table and the
code must stay in lockstep; the CI smoke test asserts the tool list, so add
your verb there too (`.github/workflows/smoke.yml`).

## Test harness without a phone

```bash
# tools/list smoke (what CI runs):
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"ci","version":"0"}}}' \
 '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python server.py
```

Failure-path testing (no phone needed): `ANDROID_SERIAL=192.0.2.99:5555`
(dead address) and call any tool — you should get the classified error, not
a traceback.

## Known warts we haven't fixed (honest list)

- `phone_look` leaves the screenshot on disk after the vision call (leak,
  ~1-3MB each) — cleanup is queued (R7).
- Multi-phone = multi-process; no `--phone` argument yet.
- `phone_type` can't type CJK (adb limit; clipboard route documented in
  README's honest table).
- The MIUI screencap quirk (empty PNG after long sessions) is detected and
  reported but not self-healed; a phone reboot restores it.
- SSE spec deviations noted above.

## FAQ for modifiers

**Why FastMCP stdio and not HTTP?** Stdio is the lowest common denominator —
every client spawns it. Our own fleet runs the same code behind an HTTP
wrapper (see `docs/fleet.md`), which proves the transport choice doesn't
leak into the tools.

**Why `requests` and not `httpx`/`aiohttp`?** One dependency, synchronous
world, zero surprises. The tools are inherently serial (look → act → look);
async would buy nothing and cost readability.

**Why is `ANDROID_SERIAL` read at import time?** One process = one phone is
the deployment unit (see the multi-device error). Per-call serial would
invite cross-phone race conditions in agent loops that assume state
continuity.

**Can I run the eyes without the hand / hand without the eyes?** Yes —
that's what happens de facto when vision env is unset (all look-capable
tools return the classified error) or no device is attached. The verbs fail
independently and say so.

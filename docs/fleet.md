# Running Phone-Eye in an MCP fleet (streamable-http)

`server.py` is transport-agnostic stdio. For an always-on HTTP deployment,
wrap it with any FastMCP-compatible host. In our home fleet it runs behind a
small PM2-managed wrapper on port 8122 with:

- `ANDROID_SERIAL=192.168.x.x:5555` (Wi-Fi adb to the phone)
- `PHONE_EYE_VISION_URL=http://127.0.0.1:8102/mcp` (fleet vision member)

Example systemd-ish wrapper:

```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"
exec python -m phone_eye_http   # or: uvicorn-style host of your choice
```

The tool surface is identical either way — packaging is convenience, not API.

## Why not a native dsh plugin?

phone-eye's public surface is MCP-first (works with Claude Code, Codex, Cursor,
dsh, anything). A native dsh-only bundle would lock the same five verbs to one
client. The `dsh.bundle` manifest in package.json exists so `dsh plugin add`
works for dsh-first users, but the recommended wiring for dsh is the official
`@deepseek-ai/dsh-mcp-client` entry pointing at this server (stdio or
streamable-http) — see the README's install section.

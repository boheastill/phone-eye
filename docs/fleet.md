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

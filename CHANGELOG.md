# Changelog

## Unreleased

- **`phone_key`** — whitelisted hardware keys + raw keycode. `wake` revives a
  sleeping phone; the unattended-sentinel essential.
- **`phone_intent`** — open any screen by Android intent (action / data /
  component). Metacharacters refused, args shell-quoted.
- **Security hardening** (from a dual-AI audit): device-side shell injection
  in typed text fixed (single-quote escaping + control-char rejection);
  action verbs are never auto-replayed after a Wi-Fi reconnect (double-tap
  guard); read-only commands still self-heal.
- **Stranger-first fixes**: built-in OpenAI-compatible vision (set
  `PHONE_EYE_VISION_API_KEY` — no MCP server needed); actionable errors for
  missing adb / no device / no vision endpoint; Wi-Fi adb auto-reconnect.
- **Docs**: bilingual README (English | 简体中文), how-it-works whitepaper,
  honest can/can't tables, unattended-sentinel example, Docker support.

## 0.1.0 (2026-08-25)

- Initial release: `phone_look / phone_tap / phone_swipe / phone_type /
  phone_screenshot`, vision+UI-tree fusion, verified on real hardware
  (Redmi K40 Gaming / Android 13). Listed in awesome-dsh-plugin (vision).

# Security notes

- phone-eye runs `adb` against the device you designate (`ANDROID_SERIAL`); it
  does not discover or touch other devices.
- **What the hand can do on the phone is a fixed verb set** — `tap / swipe /
  type / key(event) / intent(am start) / screencap / uiautomator` — executed as
  the phone's `shell` user (uid 2000), same as any adb automation. There is no
  arbitrary-shell passthrough; if you need one, wire adb yourself — keeping it
  out was a decision, not an omission.
- **Injection guards**: `adb shell` joins arguments and runs them through the
  phone's `sh -c`, so typed text and intent args are single-quote-escaped
  (`_shq`), shell metacharacters in intent args are refused outright, and
  non-ASCII/control characters are rejected before reaching the device.
- **Actions are never auto-replayed.** If Wi-Fi adb drops mid-command, the
  tool reconnects but refuses to replay `input*` verbs — a dropped ack after
  execution would double-tap. Read-only commands are replayed safely.
- Screenshots are screen contents: they are written to `PHONE_EYE_SHOTS`
  (default `/tmp/phone-eye`) and sent to the vision endpoint you configured.
  For private screens use the built-in route with a LAN-local model so no
  pixel leaves your network.
- Vision keys live only in environment variables → `Authorization` headers;
  they never appear in error messages.

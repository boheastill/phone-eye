# Example: your agent on night watch (unattended sentinel)

The pattern: an external watcher (cron, systemd timer, your agent's own loop)
fires on an event; phone-eye executes the on-phone sequence and files the
evidence. Nobody is awake.

```
# 1. The phone fell asleep hours ago — wake it (no coordinates needed)
phone_key("wake")

# 2. Swipe up to unlock (no-password lockscreen; for always-on rigs prefer
#    Developer options → "Stay awake while charging" instead)
phone_swipe(540, 1600, 540, 400)

# 3. Jump straight to the deep page you care about — no navigation taps
phone_intent("android.bluetooth.devicepicker.action.LAUNCH")
#    (other favorites: android.settings.BLUETOOTH_SETTINGS,
#     android.settings.WIFI_SETTINGS, any app page via component)

# 4. See what's there and decide
phone_look("is the device I care about in the list? give its row bounds")

# 5. Evidence, timestamped, for the morning report
phone_screenshot()
```

Why this works unattended where raw adb scripts die: Wi-Fi adb drops are
auto-recovered (read-only steps replay; action verbs ask you to re-call),
the vision channel reads whatever unplanned popup hijacked the screen, and
`phone_key`/`phone_intent` don't depend on yesterday's screen state.

Origin: this exact sequence (minus phone-eye) was used to capture bluetooth
RF evidence when a keyboard went zombie at night. phone-eye exists to make
that class of "sentinel with eyes" a five-line recipe instead of a shell script.

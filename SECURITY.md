# Security notes

- phone-eye runs `adb` against a device you designate; it does not discover
  or touch other devices.
- Screenshots are written to /tmp/phone-eye (override: PHONE_EYE_SHOTS) and
  sent to the vision endpoint you configure. Use a LAN-local vision server
  if screenshots must not leave your network.
- The tool surface deliberately excludes shell execution on the device:
  phone_look/tap/swipe/type/screenshot only. If you need shell, wire adb
  yourself — keeping it out was a decision, not an omission.

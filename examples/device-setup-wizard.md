# Example: surviving an OEM setup wizard

Phone freshly reset. The wizard screens are unknown ahead of time — vision
handles whatever appears:

```
Until setup completes:
  phone_look("what is this screen asking? where do I tap to continue?")
  phone_tap(...)   # or phone_type for Wi-Fi password (ASCII)
```

Real-world note: phone-eye once discovered a USB-debugging authorization
dialog on its own screen, read the buttons via UI-tree, and tapped "Allow"
by itself. Setup loops are where vision + tree fusion pays off most.

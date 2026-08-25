# Example: form regression check after a UI change

You changed a mobile web form's CSS. Instead of trusting the desktop preview:

```
phone_look("is the submit button fully visible and not overlapping the keyboard?")
phone_look("read back the values shown in the form fields")
phone_tap(...)  # submit
phone_look("did the success toast appear? any layout shift?")
```

Pairs well with a git hook: after each deploy, run the same look-sequence and
diff the answers.

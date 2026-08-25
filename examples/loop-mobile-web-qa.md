# Example: mobile web QA loop

Ask your agent (any MCP client) to verify its own work on a real phone:

```
Open http://192.168.31.109:3080 on the phone (Chrome), then:
1. phone_look("did the page load? what's the title?")
2. phone_look("where is the workspace selector? give exact coords")
3. phone_tap(x, y)
4. phone_look("is the main UI visible now?")
```

The agent iterates exactly like it does with code — look, act, look again.

#!/usr/bin/env python3
"""Phone-Eye — let your AI agent see and operate a real Android phone.

Tools (the whole product):
  phone_look(question?, use_tree?)   ask a vision model about the live screen
  phone_tap(x, y)                    tap
  phone_swipe(x1,y1,x2,y2,ms?)       swipe
  phone_type(text)                   type ASCII text (space = %s)
  phone_screenshot()                 save screenshot, return path

Design:
  - adb against the device named by ANDROID_SERIAL (default: first device).
  - Vision via any MCP vision server exposing describe_image(path, question?)
    (default: a local glmvision-style server; set PHONE_EYE_VISION_URL).
  - uiautomator dump is fused with pixels for exact bounds when available.

Standalone (this file has zero fleet dependencies):
  pip install "mcp[cli]" requests
  python server.py            # stdio, works with any MCP client

In the hua-mcp fleet, a thin wrapper (fleet.py) re-exports this module under
huamcp's HTTP transport — same tools, one fewer process for fleet users.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Optional

import requests

# ---------------------------------------------------------------- config ----
ADB_SERIAL = os.environ.get("ANDROID_SERIAL", "")  # empty = first device
VISION_URL = os.environ.get("PHONE_EYE_VISION_URL", "http://127.0.0.1:8102/mcp")
VISION_TOOL = os.environ.get("PHONE_EYE_VISION_TOOL", "describe_image")
SHOT_DIR = os.environ.get("PHONE_EYE_SHOTS", "/tmp/phone-eye")


def _adb(*args: str, timeout: int = 30, binary: bool = False) -> bytes:
    cmd = ["adb"]
    if ADB_SERIAL:
        cmd += ["-s", ADB_SERIAL]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if r.returncode != 0 and not binary:
        raise RuntimeError(
            f"adb {' '.join(args)} -> rc={r.returncode}: "
            f"{r.stderr.decode(errors='ignore')[:200]}"
        )
    return r.stdout


def _shot_path() -> str:
    d = pathlib.Path(SHOT_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return str(d / f"screen_{int(time.time())}.png")


# ------------------------------------------------------------- vision MCP ----
def _vision_look(png_path: str, question: str) -> str:
    """Call describe_image on any MCP vision server (streamable-http)."""
    base = VISION_URL.rstrip("/")
    h = {"Content-Type": "application/json",
         "Accept": "application/json, text/event-stream"}

    r = requests.post(base, headers=h, timeout=30, json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "phone-eye", "version": "1.0"}},
    })
    r.raise_for_status()
    sid = r.headers.get("mcp-session-id", "")
    if sid:
        h["mcp-session-id"] = sid
    requests.post(base, headers=h, timeout=15, json={
        "jsonrpc": "2.0", "method": "notifications/initialized"})

    r = requests.post(base, headers=h, timeout=180, json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": VISION_TOOL,
                   "arguments": {"path": png_path, "question": question}},
    })
    r.raise_for_status()
    # SSE frames are separated by blank lines; data: lines may wrap JSON.
    raw = r.content.decode("utf-8", errors="replace")  # never trust .text charset
    frame: list[str] = []
    for line in raw.splitlines():
        if line == "":
            if frame:
                blob = "".join(x[6:] if x.startswith("data: ") else x.lstrip()
                               for x in frame)
                try:
                    d = json.loads(blob)
                    txt = "\n".join(c.get("text", "")
                                    for c in d.get("result", {}).get("content", [])
                                    if c.get("type") == "text")
                    if txt:
                        return txt
                except Exception:
                    pass
                frame = []
        elif line.startswith("data:"):
            frame.append(line)
    return raw[:1500]


def _ui_tree() -> str:
    """Optional uiautomator dump: text/desc nodes with bounds."""
    try:
        _adb("shell", "uiautomator", "dump", "/sdcard/phone-eye.xml", timeout=25)
        xml = _adb("shell", "cat", "/sdcard/phone-eye.xml",
                   timeout=15, binary=True).decode(errors="ignore")
        items = []
        for m in re.finditer(
                r'<node[^>]*?text="([^"]{1,60})"[^>]*?bounds="(\[[^\]]+\]\[[^\]]+\])"', xml):
            if m.group(1).strip():
                items.append(f"{m.group(1)} @{m.group(2)}")
        for m in re.finditer(
                r'<node[^>]*?content-desc="([^"]{1,40})"[^>]*?bounds="(\[[^\]]+\]\[[^\]]+\])"', xml):
            if m.group(1).strip():
                items.append(f"[{m.group(1)}] @{m.group(2)}")
        return "\n".join(items[:40])
    except Exception:
        return ""


def _grab_png() -> bytes:
    data = _adb("exec-out", "screencap", "-p", timeout=40, binary=True)
    if not data or data[:4] != b"\x89PNG":
        raise RuntimeError(
            "screencap returned empty/non-PNG (known MIUI quirk after long "
            "sessions; reboot the phone to restore, or use use_tree=True)")
    return data


# ------------------------------------------------------------------ MCP ----
from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("phone-eye")


@mcp.tool()
def phone_look(question: str = "Describe the current phone screen; give approximate coordinates (x,y) for interactive elements",
               use_tree: bool = True) -> str:
    """Let the agent "see" the phone's current screen.

    Takes a screenshot, asks a vision model your question, and (by default)
    fuses a uiautomator UI-tree dump for exact text/bounds.

    Use for: mobile QA loops, device setup wizards, "what is this screen
    telling me" moments.

    Args:
        question: What to ask about the screen.
        use_tree: Also include the native UI tree (more precise; skipped on failure).
    """
    try:
        png = _shot_path()
        pathlib.Path(png).write_bytes(_grab_png())
        out = f"[vision]\n{_vision_look(png, question)}"
        tree = _ui_tree() if use_tree else ""
        if tree:
            out += "\n[ui-tree]\n" + tree
        return out
    except Exception as e:  # noqa: BLE001
        return f"phone_look failed: {type(e).__name__}: {e}"


@mcp.tool()
def phone_tap(x: int, y: int) -> str:
    """Tap the screen at (x, y). Pair with phone_look's coordinates:
    look -> tap -> look again."""
    try:
        _adb("shell", "input", "tap", str(int(x)), str(int(y)), timeout=15)
        return f"tapped ({x},{y})"
    except Exception as e:  # noqa: BLE001
        return f"phone_tap failed: {e}"


@mcp.tool()
def phone_swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
    """Swipe from (x1,y1) to (x2,y2) over duration_ms milliseconds."""
    try:
        _adb("shell", "input", "swipe", str(int(x1)), str(int(y1)),
             str(int(x2)), str(int(y2)), str(int(duration_ms)), timeout=15)
        return f"swiped ({x1},{y1})->({x2},{y2})"
    except Exception as e:  # noqa: BLE001
        return f"phone_swipe failed: {e}"


@mcp.tool()
def phone_type(text: str) -> str:
    """Type text (ASCII only; adb silently drops non-ASCII — for CJK use the
    clipboard route on the device). Spaces are sent as %s."""
    try:
        if not text.isascii():
            return ("refused: non-ASCII text is silently dropped by adb input; "
                    "use a clipboard-based method for CJK")
        _adb("shell", "input", "text", text.replace(" ", "%s"), timeout=15)
        return f"typed {len(text)} chars"
    except Exception as e:  # noqa: BLE001
        return f"phone_type failed: {e}"


@mcp.tool()
def phone_screenshot() -> str:
    """Save a screenshot to disk and return its path (for human eyes or
    archives; agents should prefer phone_look)."""
    try:
        png = _shot_path()
        pathlib.Path(png).write_bytes(_grab_png())
        return png
    except Exception as e:  # noqa: BLE001
        return f"phone_screenshot failed: {e}"


if __name__ == "__main__":
    mcp.run()

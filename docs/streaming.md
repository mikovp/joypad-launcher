# Streaming and screen resolution

## Sunshine (Moonlight)

Add Joypad Launcher as an application in Sunshine:

| Field | Value |
|-------|-------|
| Command | `cmd /C path\to\JoypadLauncher.exe` |
| Working Directory | `path\to\dist` |

To build the exe, see [development.md](development.md).

### Do / Undo (example)

If the PC is on the lock screen (`logonui`), reconnect the session to the physical console before launch — **Do**:

```powershell
powershell -NoProfile -ExecutionPolicy unrestricted -Command "if (tasklist | findstr -i logonui) { tsdiscon ((quser $env:USERNAME | select -Skip 1) -split '\s+')[2]; Start-Sleep 1; tscon ((quser $env:USERNAME | select -Skip 1) -split '\s+')[1] /dest:console; New-Item -Path '$env:TEMP\apollo_unlock.lock' -ItemType File -Force; exit 1; }"
```

---

## QRes (resolution switching)

[**QRes**](https://sourceforge.net/projects/qres/) changes screen resolution from the command line. Place `QRes.exe` in the launcher folder or on PATH.

In Sunshine **Do** / **Undo**:

| When | Command |
|------|---------|
| **Do** | `cmd /C C:\path\to\JoypadLauncher\QRes.exe /x:1280 /y:960` |
| **Undo** | `cmd /C C:\path\to\JoypadLauncher\QRes.exe /x:3840 /y:1080 /r:144` |

Adjust resolution and refresh rate for your setup.

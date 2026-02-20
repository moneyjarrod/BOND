#Requires AutoHotkey v2.0
#SingleInstance Force

; ═══════════════════════════════════════════════════════
;   BOND Bridge — HTTP Poll → Type in Claude
;   Polls Express sidecar for queued commands,
;   types them into Claude Desktop or browser window.
; ═══════════════════════════════════════════════════════

; ─── CONFIG ───────────────────────────────────────────
POLL_URL := "http://localhost:3000/api/bridge/pending"
POLL_INTERVAL := 500   ; ms
AUTO_SEND := false     ; true = press Enter after typing
BACKGROUND_MODE := false  ; ControlSend doesn't work with Claude — use foreground

; ─── TRAY ─────────────────────────────────────────────
A_IconTip := "BOND Bridge"
TraySetIcon("shell32.dll", 14)

tray := A_TrayMenu
tray.Delete()
tray.Add("BOND Bridge", (*) => "")
tray.Disable("BOND Bridge")
tray.Add()
tray.Add("Status", ShowStatus)
tray.Add("Toggle Auto-Send", ToggleAutoSend)
tray.Add()
tray.Add("Exit", (*) => ExitApp())

; ─── HOTKEYS ──────────────────────────────────────────
^+p:: {
    if WinExist("BOND Control Panel") {
        WinSetAlwaysOnTop(-1, "BOND Control Panel")
        ToolTip("📌 Panel pin toggled")
        SetTimer(() => ToolTip(), -1500)
    } else {
        ToolTip("⚠ Panel window not found")
        SetTimer(() => ToolTip(), -2000)
    }
}

; ─── STATE ────────────────────────────────────────────
commandsTyped := 0
lastError := ""

; ─── MAIN LOOP ────────────────────────────────────────
SetTimer(PollBridge, POLL_INTERVAL)

PollBridge() {
    global lastError, commandsTyped
    try {
        whr := ComObject("WinHttp.WinHttpRequest.5.1")
        whr.Open("GET", POLL_URL, false)
        whr.SetTimeouts(1000, 1000, 1000, 1000)
        whr.Send()

        if (whr.Status != 200) {
            lastError := "HTTP " . whr.Status
            return
        }

        lastError := ""
        response := whr.ResponseText

        ; Parse commands from JSON response
        commands := ParseCommands(response)
        for cmd in commands {
            TypeInClaude(cmd)
            commandsTyped++
        }
    } catch as err {
        lastError := err.Message
        ; Server not running — silent fail, keep polling
    }
}

TypeInClaude(command) {
    global AUTO_SEND, BACKGROUND_MODE

    ; Find Claude window
    claudeWin := FindClaudeWindow()
    if (!claudeWin) {
        ToolTip("⚠ Claude window not found")
        SetTimer(() => ToolTip(), -2000)
        return
    }

    if (BACKGROUND_MODE) {
        ; Send to Claude WITHOUT stealing focus
        try {
            ControlSendText(command, , claudeWin)
            if (AUTO_SEND) {
                Sleep(50)
                ControlSend("{Enter}", , claudeWin)
            }
        } catch {
            ; ControlSend failed — fall back to foreground
            WinActivate(claudeWin)
            Sleep(150)
            SendText(command)
            if (AUTO_SEND) {
                Sleep(50)
                Send("{Enter}")
            }
        }
    } else {
        ; Original foreground behavior
        WinActivate(claudeWin)
        Sleep(150)
        SendText(command)
        if (AUTO_SEND) {
            Sleep(50)
            Send("{Enter}")
        }
    }

    ToolTip("📡 Typed: " . command)
    SetTimer(() => ToolTip(), -1500)
}

FindClaudeWindow() {
    ; Try Claude Desktop app first
    if WinExist("Claude ahk_exe Claude.exe")
        return "Claude ahk_exe Claude.exe"
    ; Try browser tabs with Claude in title
    if WinExist("Claude ahk_exe chrome.exe")
        return "Claude ahk_exe chrome.exe"
    if WinExist("Claude ahk_exe msedge.exe")
        return "Claude ahk_exe msedge.exe"
    if WinExist("Claude ahk_exe firefox.exe")
        return "Claude ahk_exe firefox.exe"
    ; Fallback: any window with Claude in title
    if WinExist("Claude")
        return "Claude"
    return ""
}

ParseCommands(jsonText) {
    ; Extract command values from JSON
    ; Response format: {"commands":[{"command":"{Save}","timestamp":123}]}
    commands := []
    pos := 1
    while (pos := InStr(jsonText, '"command":"', , pos)) {
        pos += 11  ; skip past '"command":"'
        endPos := InStr(jsonText, '"', , pos)
        if (endPos > pos) {
            cmd := SubStr(jsonText, pos, endPos - pos)
            ; Unescape JSON strings
            cmd := StrReplace(cmd, "\\", "\")
            cmd := StrReplace(cmd, '\"', '"')
            commands.Push(cmd)
            pos := endPos
        }
    }
    return commands
}

; ─── TRAY ACTIONS ─────────────────────────────────────

ShowStatus(*) {
    global commandsTyped, lastError, AUTO_SEND, POLL_URL
    status := "BOND Bridge Status`n"
    status .= "───────────────`n"
    status .= "Polling: " . POLL_URL . "`n"
    status .= "Commands typed: " . commandsTyped . "`n"
    status .= "Auto-send: " . (AUTO_SEND ? "ON" : "OFF") . "`n"
    status .= "Background mode: " . (BACKGROUND_MODE ? "ON" : "OFF") . "`n"
    status .= "Last error: " . (lastError ? lastError : "none") . "`n"
    MsgBox(status, "BOND Bridge", "Iconi")
}

ToggleAutoSend(*) {
    global AUTO_SEND
    AUTO_SEND := !AUTO_SEND
    ToolTip("Auto-send: " . (AUTO_SEND ? "ON" : "OFF"))
    SetTimer(() => ToolTip(), -1500)
}

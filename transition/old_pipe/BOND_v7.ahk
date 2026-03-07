; ═══════════════════════════════════════════════════════
;   BOND v7 — Unified Counter + Bridge
;   Counter: tags messages with «tN/L emoji» on Enter
;   Bridge: polls panel for commands, types into Claude
;   One script, one tray icon, one process.
; ═══════════════════════════════════════════════════════
;
; TAG FORMAT: «tN/LIMIT emoji»
; Examples: «t3/10 🗒️»  «t12/10 🟡»  «t15/10 🟠»  «t20/10 🔴»
;
; EMOJI RULES:
; 🗒️ = N ≤ LIMIT
; 🟡 = N > LIMIT
; 🟠 = N ≥ 15
; 🔴 = N ≥ 20
;
; HOTKEYS:
; Enter          = Tag message + send (when BOND ON + Claude active)
; Ctrl+Enter     = Same as Enter (alternative send)
; XButton2       = Insert 🧠 limbic trigger
; XButton1       = Blocked (prevents back-nav in Claude)
; Ctrl+Shift+B   = Toggle BOND ON/OFF
; Ctrl+Shift+R   = Manual reset to 0
; Ctrl+Shift+T   = Show current status
; Ctrl+Shift+P   = Pin/unpin BOND Control Panel (always-on-top)
;
; ═══════════════════════════════════════════════════════

#Requires AutoHotkey v2.0
#SingleInstance Force

; ─── COUNTER CONFIG ───────────────────────────────────
global LIMIT := 10
global CounterFile := A_AppData . "\BOND\turn_counter.txt"
global TurnN := 0
global BondActive := true
global ResetPending := false



; ─── BRIDGE CONFIG ────────────────────────────────────
global POLL_URL := "http://localhost:3000/api/bridge/pending"
global POLL_INTERVAL := 500
global AUTO_SEND := false
global commandsTyped := 0
global lastError := ""
global bridgeActive := true

; ─── INIT ─────────────────────────────────────────────
InitCounter()
UpdateTray()
SetTimer(PollBridge, POLL_INTERVAL)

; ═══════════════════════════════════════════════════════
;   COUNTER
; ═══════════════════════════════════════════════════════

InitCounter() {
    global TurnN, CounterFile
    SplitPath(CounterFile, , &dir)
    if !DirExist(dir)
        DirCreate(dir)
    if FileExist(CounterFile) {
        try {
            TurnN := Integer(FileRead(CounterFile))
        } catch {
            TurnN := 0
        }
    }
}

GetEmoji() {
    global TurnN, LIMIT
    if (TurnN >= 20)
        return "🔴"
    if (TurnN >= 15)
        return "🟠"
    if (TurnN > LIMIT)
        return "🟡"
    return "🗒️"
}

SaveCounter() {
    global TurnN, CounterFile
    try FileDelete(CounterFile)
    try FileAppend(String(TurnN), CounterFile)
    UpdateTray()
}

ResetCounter() {
    global TurnN
    TurnN := 0
    SaveCounter()
    ToolTip("BOND Reset: N = 0")
    SetTimer(() => ToolTip(), -2000)
}

SetCounter() {
    global TurnN
    ib := InputBox("Set turn counter:", "BOND Counter", "w200 h100", TurnN)
    if (ib.Result = "OK") {
        try {
            TurnN := Integer(ib.Value)
            SaveCounter()
            ToolTip("Counter set to " . TurnN)
            SetTimer(() => ToolTip(), -2000)
        }
    }
}

ToggleBond() {
    global BondActive
    BondActive := !BondActive
    UpdateTray()
    ToolTip("BOND " . (BondActive ? "ON" : "OFF"))
    SetTimer(() => ToolTip(), -2000)
}

IsClaudeActive() {
    exe := ""
    try exe := WinGetProcessName("A")
    if (exe = "Claude.exe" || exe = "claude.exe")
        return true
    if (exe = "chrome.exe" || exe = "msedge.exe" || exe = "firefox.exe") {
        title := WinGetTitle("A")
        if InStr(title, "claude.ai")
            return true
    }
    return false
}

FlagReset() {
    global ResetPending
    ResetPending := true
    ToolTip("Reset flagged - next send will be «t1»")
    SetTimer(() => ToolTip(), -1500)
}


InjectTagAndSend() {
    global TurnN, ResetPending, LIMIT
    if ResetPending {
        TurnN := 0
        ResetPending := false
    }
    TurnN++
    SaveCounter()
    emoji := GetEmoji()
    tag := " «t" . TurnN . "/" . LIMIT . " " . emoji . "»"
    Send("{End}")
    Sleep(30)
    SendText(tag)
    Sleep(30)
    Send("{Enter}")
    ToolTip(emoji . " " . TurnN . "/" . LIMIT)
    SetTimer(() => ToolTip(), -1000)
}

; ═══════════════════════════════════════════════════════
;   BRIDGE
; ═══════════════════════════════════════════════════════

PollBridge() {
    global lastError, commandsTyped, bridgeActive
    if (!bridgeActive)
        return
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
        commands := ParseCommands(response)
        for cmd in commands {
            TypeInClaude(cmd)
            commandsTyped++
        }
    } catch as err {
        lastError := err.Message
    }
}

TypeInClaude(command) {
    global AUTO_SEND, TurnN, ResetPending

    ; If this is a reset command, reset counter directly
    if (command == "{Sync}" || command == "{Full Restore}") {
        TurnN := 0
        ResetPending := false
        SaveCounter()
        ToolTip("📡 " . command . " + counter reset")
        SetTimer(() => ToolTip(), -1500)
    }

    ; Find Claude window
    claudeWin := FindClaudeWindow()
    if (!claudeWin) {
        ToolTip("⚠ Claude window not found")
        SetTimer(() => ToolTip(), -2000)
        return
    }

    WinActivate(claudeWin)
    Sleep(150)
    SendText(command)

    if (AUTO_SEND) {
        Sleep(50)
        Send("{Enter}")
    }

    if (command != "{Sync}" && command != "{Full Restore}") {
        ToolTip("📡 Typed: " . command)
        SetTimer(() => ToolTip(), -1500)
    }
}

FindClaudeWindow() {
    if WinExist("Claude ahk_exe Claude.exe")
        return "Claude ahk_exe Claude.exe"
    if WinExist("Claude ahk_exe chrome.exe")
        return "Claude ahk_exe chrome.exe"
    if WinExist("Claude ahk_exe msedge.exe")
        return "Claude ahk_exe msedge.exe"
    if WinExist("Claude ahk_exe firefox.exe")
        return "Claude ahk_exe firefox.exe"
    if WinExist("Claude")
        return "Claude"
    return ""
}

ParseCommands(jsonText) {
    commands := []
    pos := 1
    while (pos := InStr(jsonText, '"command":"', , pos)) {
        pos += 11
        endPos := InStr(jsonText, '"', , pos)
        if (endPos > pos) {
            cmd := SubStr(jsonText, pos, endPos - pos)
            cmd := StrReplace(cmd, "\\", "\")
            cmd := StrReplace(cmd, '\"', '"')
            commands.Push(cmd)
            pos := endPos
        }
    }
    return commands
}

; ═══════════════════════════════════════════════════════
;   TRAY
; ═══════════════════════════════════════════════════════

UpdateTray() {
    global TurnN, BondActive, LIMIT, bridgeActive
    emoji := GetEmoji()
    if BondActive {
        TraySetIcon("shell32.dll", 278)
        A_IconTip := "BOND ON | " . emoji . " " . TurnN . "/" . LIMIT . (bridgeActive ? " | 📡 Bridge" : "")
    } else {
        TraySetIcon("shell32.dll", 132)
        A_IconTip := "BOND OFF | " . emoji . " " . TurnN . "/" . LIMIT
    }
    A_TrayMenu.Delete()
    A_TrayMenu.Add(BondActive ? "● BOND ON" : "○ BOND OFF", (*) => ToggleBond())
    A_TrayMenu.Add()
    A_TrayMenu.Add(emoji . " " . TurnN . "/" . LIMIT, (*) => "")
    A_TrayMenu.Disable(emoji . " " . TurnN . "/" . LIMIT)
    A_TrayMenu.Add()
    A_TrayMenu.Add("Set Counter...", (*) => SetCounter())
    A_TrayMenu.Add("Reset to 0", (*) => ResetCounter())
    A_TrayMenu.Add()
    A_TrayMenu.Add("Bridge: " . (bridgeActive ? "ON" : "OFF"), (*) => ToggleBridge())
    A_TrayMenu.Add("Auto-Send: " . (AUTO_SEND ? "ON" : "OFF"), (*) => ToggleAutoSend())
    A_TrayMenu.Add("Status...", ShowStatus)
    A_TrayMenu.Add()
    A_TrayMenu.Add("Exit", (*) => ExitApp())
}

ToggleBridge() {
    global bridgeActive
    bridgeActive := !bridgeActive
    UpdateTray()
    ToolTip("Bridge " . (bridgeActive ? "ON" : "OFF"))
    SetTimer(() => ToolTip(), -1500)
}

ToggleAutoSend(*) {
    global AUTO_SEND
    AUTO_SEND := !AUTO_SEND
    UpdateTray()
    ToolTip("Auto-send: " . (AUTO_SEND ? "ON" : "OFF"))
    SetTimer(() => ToolTip(), -1500)
}

ShowStatus(*) {
    global commandsTyped, lastError, AUTO_SEND, POLL_URL, TurnN, LIMIT, bridgeActive
    emoji := GetEmoji()
    status := "BOND v7 Status`n"
    status .= "═══════════════`n"
    status .= "`nCounter: " . emoji . " " . TurnN . "/" . LIMIT . "`n"
    status .= "`nBridge: " . (bridgeActive ? "ON" : "OFF") . "`n"
    status .= "Polling: " . POLL_URL . "`n"
    status .= "Commands typed: " . commandsTyped . "`n"
    status .= "Auto-send: " . (AUTO_SEND ? "ON" : "OFF") . "`n"
    status .= "Last error: " . (lastError ? lastError : "none") . "`n"
    MsgBox(status, "BOND v7", "Iconi")
}

; ═══════════════════════════════════════════════════════
;   HOTKEYS
; ═══════════════════════════════════════════════════════

; Global hotkeys
^+b:: ToggleBond()
^+r:: ResetCounter()
^+t:: {
    global TurnN, BondActive, LIMIT, bridgeActive
    emoji := GetEmoji()
    ToolTip("BOND " . (BondActive ? "ON" : "OFF") . " | " . emoji . " " . TurnN . "/" . LIMIT . (bridgeActive ? " | 📡" : ""))
    SetTimer(() => ToolTip(), -2000)
}
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

; Hotstrings: detect {Sync} and {Full Restore} typed by user
:*:{Sync}::{
    FlagReset()
    SendText("{Sync}")
}

:*:{Full Restore}::{
    FlagReset()
    SendText("{Full Restore}")
}

; Claude-only hotkeys
#HotIf IsClaudeActive() && BondActive
Enter:: InjectTagAndSend()
; Ctrl+Enter also sends with tag (alternative to Enter)
^Enter:: InjectTagAndSend()
XButton2:: {
    SendText("🧠")
    ToolTip("🧠 Limbic")
    SetTimer(() => ToolTip(), -1000)
}
XButton1:: return
#HotIf

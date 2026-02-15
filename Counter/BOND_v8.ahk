; ═══════════════════════════════════════════════════════
;   BOND v8 — Counter + Clipboard Bridge
;   Counter: tags messages with «tN/L emoji» on Enter
;   Bridge: clipboard-based (zero polling, event-driven)
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
; BRIDGE:
; Panel copies command to clipboard → AHK detects → types into Claude
; No HTTP polling. Event-driven via OnClipboardChange.
; Prefix: "BOND:" signals a bridge command (stripped before typing)
;
; HOTKEYS:
; Enter          = Tag message + send (when BOND ON + Claude active)
; Ctrl+Enter     = Same as Enter
; XButton2       = Insert 🧠 limbic trigger
; XButton1       = Blocked (prevents back-nav)
; Ctrl+Shift+B   = Toggle BOND ON/OFF
; Ctrl+Shift+R   = Manual reset to 0
; Ctrl+Shift+T   = Show current status
; Ctrl+Shift+P   = Pin/unpin BOND Control Panel
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
global BRIDGE_PREFIX := "BOND:"
global commandsTyped := 0
global bridgeActive := true
global lastClipboard := ""

; ─── STATUS FILE ───────────────────────────────────────
; Panel reads this to reflect AHK state in the UI
global StatusFile := A_ScriptDir . "\..\state\ahk_status.json"

; ─── INIT ─────────────────────────────────────────────
InitCounter()
UpdateTray()
WriteStatus()
OnClipboardChange(ClipboardBridge)

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
    WriteStatus()
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
    WriteStatus()
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
;   STATUS FILE (panel reads this)
; ═══════════════════════════════════════════════════════

WriteStatus() {
    global StatusFile, BondActive, bridgeActive, TurnN, LIMIT, commandsTyped
    json := '{'
    json .= '"bond_active":' . (BondActive ? 'true' : 'false') . ','
    json .= '"bridge_active":' . (bridgeActive ? 'true' : 'false') . ','
    json .= '"turn":' . TurnN . ','
    json .= '"limit":' . LIMIT . ','
    json .= '"commands_typed":' . commandsTyped
    json .= '}'
    try {
        tmpFile := StatusFile . ".tmp"
        if FileExist(tmpFile)
            FileDelete(tmpFile)
        FileAppend(json, tmpFile)
        FileMove(tmpFile, StatusFile, true)
    }
}

; ═══════════════════════════════════════════════════════
;   CLIPBOARD BRIDGE
; ═══════════════════════════════════════════════════════

ClipboardBridge(dataType) {
    global BRIDGE_PREFIX, commandsTyped, bridgeActive, lastClipboard, BondActive

    ; Only handle text
    if (dataType != 1)
        return

    clip := A_Clipboard
    
    ; Ignore empty or duplicate
    if (!clip || clip == lastClipboard)
        return

    ; Check for BOND prefix
    if !InStr(clip, BRIDGE_PREFIX, true, 1, 1)
        return
    
    ; Extract command (strip prefix)
    command := SubStr(clip, StrLen(BRIDGE_PREFIX) + 1)
    command := Trim(command)
    
    ; ─── Panel control commands (fire even when paused) ───
    if (command == "__BRIDGE_TOGGLE__") {
        ToggleBridge()
        A_Clipboard := ""
        lastClipboard := ""
        return
    }
    if (command == "__BOND_TOGGLE__") {
        ToggleBond()
        A_Clipboard := ""
        lastClipboard := ""
        return
    }
    if (command == "__STATUS__") {
        WriteStatus()
        A_Clipboard := ""
        lastClipboard := ""
        return
    }
    
    ; Check if bridge is active (after panel commands)
    if (!bridgeActive)
        return
    
    if (!command)
        return
    
    ; Escalate commands stay in clipboard for manual paste — don't auto-type
    if (SubStr(command, 1, 9) == "escalate:") {
        ; Strip BOND:escalate: prefix, leave clean text in clipboard for paste
        cleanText := SubStr(command, 10)
        lastClipboard := cleanText
        A_Clipboard := cleanText
        ToolTip("📋 Escalation ready — paste to Claude")
        SetTimer(() => ToolTip(), -2500)
        return
    }
    
    lastClipboard := clip
    
    ; If this is a reset command, flag the counter
    if (command == "{Sync}" || command == "{Full Restore}") {
        FlagReset()
    }
    
    ; Find and activate Claude, type command
    TypeInClaude(command)
    commandsTyped++
    
    ; Clear the BOND command from clipboard so normal copy/paste isn't affected
    A_Clipboard := ""
    lastClipboard := ""
}

TypeInClaude(command) {
    claudeWin := FindClaudeWindow()
    if (!claudeWin) {
        ToolTip("⚠ Claude window not found")
        SetTimer(() => ToolTip(), -2000)
        return
    }

    WinActivate(claudeWin)
    Sleep(150)
    SendText(command)
    ToolTip("📡 " . command)
    SetTimer(() => ToolTip(), -1500)
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

; ═══════════════════════════════════════════════════════
;   TRAY
; ═══════════════════════════════════════════════════════

UpdateTray() {
    global TurnN, BondActive, LIMIT, bridgeActive
    emoji := GetEmoji()
    if BondActive {
        TraySetIcon("shell32.dll", 278)
        A_IconTip := "BOND ON | " . emoji . " " . TurnN . "/" . LIMIT . (bridgeActive ? " | 📋 Bridge" : "")
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
    A_TrayMenu.Add("Bridge: " . (bridgeActive ? "ON 📋" : "OFF"), (*) => ToggleBridge())
    A_TrayMenu.Add("Status...", ShowStatus)
    A_TrayMenu.Add()
    A_TrayMenu.Add("Exit", (*) => ExitApp())
}

ToggleBridge() {
    global bridgeActive
    bridgeActive := !bridgeActive
    UpdateTray()
    WriteStatus()
    ToolTip("Bridge " . (bridgeActive ? "ON" : "OFF"))
    SetTimer(() => ToolTip(), -1500)
}

ShowStatus(*) {
    global commandsTyped, BondActive, TurnN, LIMIT, bridgeActive
    emoji := GetEmoji()
    status := "BOND v8 Status`n"
    status .= "═══════════════`n"
    status .= "`nCounter: " . emoji . " " . TurnN . "/" . LIMIT . "`n"
    status .= "`nBridge: " . (bridgeActive ? "ON (clipboard)" : "OFF") . "`n"
    status .= "Commands received: " . commandsTyped . "`n"
    MsgBox(status, "BOND v8", "Iconi")
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
    ToolTip("BOND " . (BondActive ? "ON" : "OFF") . " | " . emoji . " " . TurnN . "/" . LIMIT . (bridgeActive ? " | 📋" : ""))
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

; ═══════════════════════════════════════════════════════
;   SEND BUTTON INTERCEPT
; ═══════════════════════════════════════════════════════
; Detects click on Claude's amber send button by pixel color.
; Fast path: coordinate check first (cheap), pixel scan only if in zone.
; If send button detected → block click → inject tag → Enter.
; Otherwise → normal click passes through instantly.
;
; TUNING: Adjust IsSendButtonColor() if Claude changes theme.
; Current target: amber/gold #FFD04F / #FACC38 / #FFC337 range.

InSendButtonZone(x, y) {
    ; Cheap check: is cursor near the bottom-right of Claude window?
    ; Skips pixel scan for 99% of clicks.
    try {
        WinGetPos(&wx, &wy, &ww, &wh, "A")
        ; Send button lives in bottom ~80px, right half of window
        if (y > wy + wh - 80 && x > wx + (ww / 2))
            return true
    }
    return false
}

IsSendButtonColor(x, y) {
    ; Check a 3x3 area around cursor for the amber send button
    loop 3 {
        cx := x - 1 + A_Index - 1
        loop 3 {
            cy := y - 1 + A_Index - 1
            try {
                color := PixelGetColor(cx, cy)
                ; Color format: 0xBBGGRR in AHK
                b := (color >> 16) & 0xFF
                g := (color >> 8) & 0xFF
                r := color & 0xFF
                ; Amber/gold detection: high red, medium-high green, low blue
                if (r > 220 && g > 170 && g < 230 && b < 110)
                    return true
            }
        }
    }
    return false
}

; Claude-only hotkeys
#HotIf IsClaudeActive() && BondActive
Enter:: InjectTagAndSend()
^Enter:: InjectTagAndSend()
; LButton send intercept — DISABLED for now, revisit later
; LButton:: {
;     MouseGetPos(&mx, &my)
;     if (InSendButtonZone(mx, my) && IsSendButtonColor(mx, my)) {
;         InjectTagAndSend()
;     } else {
;         SendLevel(1)
;         Click(mx, my)
;         SendLevel(0)
;     }
; }
XButton2:: {
    SendText("🧠")
    ToolTip("🧠 Limbic")
    SetTimer(() => ToolTip(), -1000)
}
XButton1:: return
#HotIf

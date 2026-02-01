; ============================================
; BOND Turn Counter v5 for AutoHotkey v2
; User-side turn tracking for Claude conversations
; ============================================
;
; WHAT THIS DOES:
; - Appends «tN» tag to your messages when you press Enter
; - Claude reads this tag to know the turn number
; - Auto-resets when you type {Sync} or {Full Restore}
; - Works with Claude Desktop AND browser
;
; WHY THIS EXISTS:
; Claude's internal counter can fail due to context issues.
; User-side tracking makes YOU the source of truth.
; Claude just reads your tag — no internal counting needed.
;
; HOTKEYS:
; Enter          = Tag message + send (when BOND ON + Claude active)
; Ctrl+Shift+B   = Toggle BOND ON/OFF
; Ctrl+Shift+R   = Manual reset to 0
; Ctrl+Shift+T   = Show current N
;
; INSTALLATION:
; 1. Install AutoHotkey v2: https://www.autohotkey.com/
; 2. Save this file anywhere (e.g., Documents\BOND\)
; 3. Double-click to run
; 4. (Optional) Add to Startup folder for auto-run
;
; ============================================

#Requires AutoHotkey v2.0
#SingleInstance Force

global CounterFile := A_AppData . "\BOND\turn_counter.txt"
global TurnN := 0
global BondActive := true
global ResetPending := false

InitCounter()

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
    UpdateTray()
}

UpdateTray() {
    global TurnN, BondActive
    if BondActive {
        TraySetIcon("shell32.dll", 278)
        A_IconTip := "BOND ON | N=" . TurnN
    } else {
        TraySetIcon("shell32.dll", 132)
        A_IconTip := "BOND OFF | N=" . TurnN
    }
    A_TrayMenu.Delete()
    A_TrayMenu.Add(BondActive ? "● BOND ON" : "○ BOND OFF", (*) => ToggleBond())
    A_TrayMenu.Add()
    A_TrayMenu.Add("N = " . TurnN, (*) => "")
    A_TrayMenu.Disable("N = " . TurnN)
    A_TrayMenu.Add()
    A_TrayMenu.Add("Reset to 0", (*) => ResetCounter())
    A_TrayMenu.Add()
    A_TrayMenu.Add("Exit", (*) => ExitApp())
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

ToggleBond() {
    global BondActive
    BondActive := !BondActive
    UpdateTray()
    ToolTip("BOND " . (BondActive ? "ON" : "OFF"))
    SetTimer(() => ToolTip(), -2000)
}

IsClaudeActive() {
    title := WinGetTitle("A")
    exe := ""
    try exe := WinGetProcessName("A")
    if InStr(exe, "Claude") || InStr(exe, "claude")
        return true
    if InStr(title, "Claude") || InStr(title, "claude.ai")
        return true
    return false
}

FlagReset() {
    global ResetPending
    ResetPending := true
    ToolTip("Reset flagged - next send will be «t1»")
    SetTimer(() => ToolTip(), -1500)
}

InjectTagAndSend() {
    global TurnN, ResetPending
    
    if ResetPending {
        TurnN := 0
        ResetPending := false
    }
    
    TurnN++
    SaveCounter()
    
    tag := " «t" . TurnN . "»"
    Send("{End}")
    Sleep(30)
    SendText(tag)
    Sleep(30)
    Send("{Enter}")
    
    ToolTip("«t" . TurnN . "»")
    SetTimer(() => ToolTip(), -1000)
}

; --- Global Hotkeys ---
^+b:: ToggleBond()
^+r:: ResetCounter()
^+t:: {
    global TurnN, BondActive
    ToolTip("BOND " . (BondActive ? "ON" : "OFF") . " | N=" . TurnN)
    SetTimer(() => ToolTip(), -2000)
}

; --- Hotstrings: detect {Sync} and {Full Restore} as typed ---
:*:{Sync}::{
    FlagReset()
    SendText("{Sync}")
}

:*:{Full Restore}::{
    FlagReset()
    SendText("{Full Restore}")
}

; --- Claude-only: Enter tags and sends ---
#HotIf IsClaudeActive() && BondActive
Enter:: InjectTagAndSend()
#HotIf

; ============================================
; BOND Turn Counter v6 for AutoHotkey v2
; User-side turn tracking for Claude conversations
; ============================================
;
; TAG FORMAT: «tN/LIMIT emoji»
; Examples: «t3/10 🗒️»  «t12/10 🟡»  «t15/10 🟠»  «t20/10 🔴»
;
; COLOR SCHEME:
; 🗒️ = N ≤ LIMIT (green/normal)
; 🟡 = N > LIMIT (yellow - over limit)
; 🟠 = N ≥ 15 (orange - getting long)
; 🔴 = N ≥ 20 (red - very long)
;
; HOTKEYS:
; Enter          = Tag message + send (when BOND ON + Claude active)
; Orange Arrow   = Tag message + send (when BOND ON + Claude active + calibrated)
; XButton2       = Insert 🧠 limbic trigger (when BOND ON + Claude active)
; XButton1       = Blocked (prevents back-nav in Claude)
; Ctrl+Shift+B   = Toggle BOND ON/OFF
; Ctrl+Shift+R   = Manual reset to 0
; Ctrl+Shift+T   = Show current N
; Ctrl+F7        = Calibrate send button (hover over orange arrow first)
;
; INSTALLATION:
; 1. Install AutoHotkey v2: https://www.autohotkey.com/
; 2. Save this file anywhere
; 3. Double-click to run
;
; ============================================

#Requires AutoHotkey v2.0
#SingleInstance Force

; --- CONFIGURATION ---
global LIMIT := 10  ; Change this to your preferred limit
global SEND_BTN_RADIUS := 25  ; Pixel radius around calibrated send button

global CounterFile := A_AppData . "\BOND\turn_counter.txt"
global SendBtnFile := A_AppData . "\BOND\send_btn_pos.txt"
global TurnN := 0
global BondActive := true
global ResetPending := false
global SendBtnOffsetR := 0
global SendBtnOffsetB := 0
global SendBtnCalibrated := false
global LastSendTick := 0          ; Debounce: prevent double-fire
global DEBOUNCE_MS := 500          ; Minimum ms between sends

InitCounter()
InitSendBtn()

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

InitSendBtn() {
    global SendBtnOffsetR, SendBtnOffsetB, SendBtnCalibrated, SendBtnFile
    if FileExist(SendBtnFile) {
        try {
            coords := StrSplit(FileRead(SendBtnFile), ",")
            SendBtnOffsetR := Integer(coords[1])
            SendBtnOffsetB := Integer(coords[2])
            SendBtnCalibrated := true
        } catch {
            SendBtnCalibrated := false
        }
    }
}

CalibrateSendBtn() {
    global SendBtnOffsetR, SendBtnOffsetB, SendBtnCalibrated, SendBtnFile
    ToolTip("Calibrating...")
    Sleep(200)
    CoordMode("Mouse", "Window")
    MouseGetPos(&mx, &my)
    WinGetPos(, , &winW, &winH, "A")
    SendBtnOffsetR := winW - mx
    SendBtnOffsetB := winH - my
    SendBtnCalibrated := true
    try FileDelete(SendBtnFile)
    try FileAppend(String(SendBtnOffsetR) . "," . String(SendBtnOffsetB), SendBtnFile)
    ToolTip("Send button calibrated: " . SendBtnOffsetR . "px from right, " . SendBtnOffsetB . "px from bottom")
    SetTimer(() => ToolTip(), -2000)
}

IsNearSendBtn(mx, my) {
    global SendBtnOffsetR, SendBtnOffsetB, SendBtnCalibrated, SEND_BTN_RADIUS
    if !SendBtnCalibrated
        return false
    WinGetPos(, , &winW, &winH, "A")
    btnX := winW - SendBtnOffsetR
    btnY := winH - SendBtnOffsetB
    dx := mx - btnX
    dy := my - btnY
    return (dx * dx + dy * dy) <= (SEND_BTN_RADIUS * SEND_BTN_RADIUS)
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

UpdateTray() {
    global TurnN, BondActive, LIMIT
    emoji := GetEmoji()
    if BondActive {
        TraySetIcon("shell32.dll", 278)
        A_IconTip := "BOND ON | " . emoji . " " . TurnN . "/" . LIMIT
    } else {
        TraySetIcon("shell32.dll", 132)
        A_IconTip := "BOND OFF | " . emoji . " " . TurnN . "/" . LIMIT
    }
    A_TrayMenu.Delete()
    A_TrayMenu.Add(BondActive ? "● BOND ON" : "○ BOND OFF", (*) => ToggleBond())
    A_TrayMenu.Add()
    A_TrayMenu.Add(emoji . " " . TurnN . "/" . LIMIT . "  ✏️", (*) => SetCounter())
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

SetCounter() {
    global TurnN
    ib := InputBox("Set turn counter to:", "BOND Counter", "w200 h100", String(TurnN))
    if (ib.Result = "OK") {
        try {
            TurnN := Integer(ib.Value)
            SaveCounter()
            emoji := GetEmoji()
            ToolTip(emoji . " Set to " . TurnN)
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
    
    ; Claude Desktop - exact exe name
    if (exe = "Claude.exe" || exe = "claude.exe")
        return true
    
    ; Browser - must be browser AND title contains claude.ai
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
    global TurnN, ResetPending, LIMIT, LastSendTick, DEBOUNCE_MS
    
    ; Debounce: ignore if fired too recently (prevents double-fire on orange arrow)
    now := A_TickCount
    if (now - LastSendTick < DEBOUNCE_MS)
        return
    LastSendTick := now
    
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

; --- Global Hotkeys ---
^+b:: ToggleBond()
^+r:: ResetCounter()
^+t:: {
    global TurnN, BondActive, LIMIT
    emoji := GetEmoji()
    ToolTip("BOND " . (BondActive ? "ON" : "OFF") . " | " . emoji . " " . TurnN . "/" . LIMIT)
    SetTimer(() => ToolTip(), -2000)
}
F9:: CalibrateSendBtn()       ; F9 = calibrate send button position

; --- Hotstrings: detect {Sync} and {Full Restore} as typed ---
:*:{Sync}::{
    FlagReset()
    SendText("{Sync}")
}

:*:{Full Restore}::{
    FlagReset()
    SendText("{Full Restore}")
}

IsMouseNearSendBtn() {
    global SendBtnCalibrated
    if !SendBtnCalibrated
        return false
    CoordMode("Mouse", "Window")
    MouseGetPos(&mx, &my)
    return IsNearSendBtn(mx, my)
}

; --- Claude-only hotkeys at InputLevel 1 ---
; InputLevel 1 prevents Send("{Enter}") inside InjectTagAndSend from
; re-triggering the Enter hotkey (fixes double-fire from orange arrow)
#InputLevel 1

; Orange arrow hook (only when mouse is over send button)
#HotIf IsClaudeActive() && BondActive && IsMouseNearSendBtn()
LButton:: InjectTagAndSend()

; Enter and other hotkeys
#HotIf IsClaudeActive() && BondActive
Enter:: InjectTagAndSend()
XButton2:: {                  ; Forward thumb = limbic trigger
    SendText("🧠")
    ToolTip("🧠 Limbic")
    SetTimer(() => ToolTip(), -1000)
}
XButton1:: return             ; Back thumb = blocked (prevents nav)
#HotIf
#InputLevel 0

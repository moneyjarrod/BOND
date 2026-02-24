@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0installer\verify.ps1" %*

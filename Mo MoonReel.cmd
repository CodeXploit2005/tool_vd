@echo off
pwsh.exe -NoProfile -File "%~dp0Start-MoonReel.ps1"
if errorlevel 1 pause

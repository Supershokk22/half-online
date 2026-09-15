@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALAR-MOD-FASE-1.ps1"
if errorlevel 1 pause

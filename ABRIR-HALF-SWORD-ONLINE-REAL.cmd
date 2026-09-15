@echo off
"%~dp0..\production\.venv\Scripts\python.exe" "%~dp0real_launcher.py"
if errorlevel 1 pause

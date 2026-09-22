@echo off
setlocal
set "EDITOR=C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe"
set "PROJECT=%~dp0HalfOpenWorldV1.uproject"
if not exist "%EDITOR%" (
  echo Unreal Engine 5.4 nao encontrado em: %EDITOR%
  pause
  exit /b 1
)
if not exist "%PROJECT%" (
  echo Projeto nao encontrado em: %PROJECT%
  pause
  exit /b 1
)
start "Half Open World V1" "%EDITOR%" "%PROJECT%" -game -d3d11 -windowed -ResX=1280 -ResY=720 -nosplash -nop4
endlocal

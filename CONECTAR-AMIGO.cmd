@echo off
title Half Sword Online — CONECTAR
setlocal enabledelayedexpansion

echo ============================================
echo   HALF SWORD ONLINE — ENTRAR NA SALA
echo ============================================
echo.

set /p HOST_IP="Cole o IP Tailscale do host (100.x.x.x): "
if "%HOST_IP%"=="" (
    echo ERRO: IP obrigatorio!
    pause
    exit /b 1
)

echo.
echo IP do host: %HOST_IP%
echo.

echo [1/4] Matando processos antigos...
taskkill /F /IM "HalfSwordUE5-Win64-Shipping.exe" >nul 2>&1
taskkill /F /IM "python.exe" >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/4] Limpando ponte...
set BRIDGE=%LOCALAPPDATA%\HalfSwordUE5\Saved\HalfSwordOnlineReal
if not exist "%BRIDGE%" mkdir "%BRIDGE%"
echo. > "%BRIDGE%\mp_inbound.txt"
echo remote remove > "%BRIDGE%\mp_game_control.txt"

echo [3/4] Conectando ao host...
start "HS-Client" /B python "%~dp0peer_agent.py" --server "ws://%HOST_IP%:8790" --room duelo --name Amigo --role client
timeout /t 3 /nobreak >nul

echo [4/4] Abrindo Half Sword...
echo.
echo ============================================
echo   PRONTO! Abra o jogo pela Steam
echo   e entre em Spar/Training pra jogar.
echo ============================================
echo.
start steam://rungameid/2397300
pause

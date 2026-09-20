@echo off
title Half Sword Online — CONECTAR
setlocal enabledelayedexpansion

echo ============================================
echo   HALF SWORD ONLINE — MODO CLIENTE
echo   assinado: shokk
echo ============================================
echo.

REM Pega IP do host: argumento ou pede pro usuario
set HOST_IP=%~1
if "%HOST_IP%"=="" (
    set /p HOST_IP="Cole o IP Tailscale do host (100.x.x.x): "
)
if "%HOST_IP%"=="" (
    echo ERRO: IP obrigatorio!
    pause
    exit /b 1
)

echo IP do host: %HOST_IP%
echo.

echo [1/5] Matando processos antigos...
taskkill /F /IM "HalfSwordUE5-Win64-Shipping.exe" >nul 2>&1
taskkill /F /IM "HalfSwordUE5.exe" >nul 2>&1
taskkill /F /IM "python.exe" >nul 2>&1
taskkill /F /IM "pythonw.exe" >nul 2>&1
timeout /t 2 /nobreak >nul
echo       Processos antigos mortos.

echo.
echo [2/5] Limpando arquivos de ponte antigos...
set BRIDGE=%LOCALAPPDATA%\HalfSwordUE5\Saved\HalfSwordOnlineReal
if not exist "%BRIDGE%" mkdir "%BRIDGE%"
echo. > "%BRIDGE%\mp_inbound.txt"
echo remote remove > "%BRIDGE%\mp_game_control.txt"
echo       Ponte limpa.

echo.
echo [3/5] Conectando ao relay do host em %HOST_IP%:8790...
start "HalfSword-Agent" /B python "%~dp0peer_agent.py" --server "ws://%HOST_IP%:8790" --room duelo --name Amigo --role client
timeout /t 3 /nobreak >nul
echo       Peer agent conectado.

echo.
echo [4/5] Abrindo Half Sword via Steam...
echo.
echo ============================================
echo   PRONTO! O jogo vai abrir e o mod vai
echo   carregar automaticamente e conectar
echo   a sala do host.
echo ============================================
echo.
start steam://rungameid/2397300
pause

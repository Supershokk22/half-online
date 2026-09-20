@echo off
title Half Sword Online — HOST
echo ============================================
echo   HALF SWORD ONLINE — MODO HOST
echo   assinado: shokk
echo ============================================
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
echo [3/5] Iniciando relay server na porta 8790...
start "HalfSword-Relay" /B python "%~dp0relay_server.py" --host 0.0.0.0 --port 8790
timeout /t 2 /nobreak >nul
echo       Relay rodando.

echo.
echo [4/5] Iniciando peer agent (host)...
start "HalfSword-Agent" /B python "%~dp0peer_agent.py" --server "ws://127.0.0.1:8790" --room duelo --name Jogador --role host
timeout /t 2 /nobreak >nul
echo       Peer agent conectado ao relay.

echo.
echo [5/5] Abrindo Half Sword via Steam...
echo.
echo ============================================
echo   PRONTO! O jogo vai abrir e o mod vai
echo   carregar automaticamente.
echo.
echo   Envie seu IP Tailscale pro amigo:
for /f "tokens=*" %%i in ('"C:\Program Files\Tailscale\tailscale.exe" ip -4 2^>nul') do echo   %%i
echo.
echo   Nome da sala: duelo
echo ============================================
echo.
start steam://rungameid/2397300
pause

@echo off
title Half Sword Online — Entrar
color 0A
echo ============================================
echo   HALF SWORD ONLINE — ENTRAR NA SALA
echo ============================================
echo.
echo 1. Cole o LINK que o host enviou:
echo    (ex: https://xxx.trycloudflare.com)
echo.
set /p HOST_URL="Link do host: "
echo.
echo 2. Seu nome:
set /p MY_NAME="Nome: "
echo.
echo 3. Nome da sala (mesmo do host):
set /p MY_ROOM="Sala: "
echo.

if "%HOST_URL%"=="" (
    echo [ERRO] Link vazio!
    pause
    exit /b 1
)

echo Conectando ao relay via tunnel...
echo.

:: Matar processos antigos
taskkill /F /IM HalfSwordUE5-Win64-Shipping.exe >nul 2>&1
taskkill /F /IM HalfSwordUE5.exe >nul 2>&1
taskkill /F /IM peer_agent.exe >nul 2>&1

:: Converter https:// para wss://
set WS_URL=%HOST_URL:https://=wss://%
set WS_URL=%WS_URL:http://=ws://%

:: Se nao comeca com ws, adicionar wss://
echo %WS_URL% | findstr /B "ws://" >nul 2>&1
if errorlevel 1 set WS_URL=wss://%HOST_URL:https://=%

:: Iniciar peer agent
echo Iniciando peer agent...
start "PeerAgent" /min python peer_agent.py --server "%WS_URL%" --room "%MY_ROOM%" --name "%MY_NAME%" --role client

echo.
echo Peer agent rodando!
echo Agora abra o Half Sword via Steam e entre em Spar/Training.
echo.
echo Para fechar: feche esta janela.
pause

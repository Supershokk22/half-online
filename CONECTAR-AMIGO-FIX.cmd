@echo off
title Half Sword Online — Entrar (com OpenWorld)
color 0A
echo ============================================
echo   HALF SWORD ONLINE — ENTRAR NA SALA
echo   (versao FIX: entra direto no mapa L_World_V1)
echo ============================================
echo.
echo Uso: CONECTAR-AMIGO-FIX.cmd [url] [nome] [sala] [pasta_do_jogo]
echo   Sem argumentos, pergunta interativamente.
echo.

set HOST_URL=%~1
set MY_NAME=%~2
set MY_ROOM=%~3
set MY_GAME_DIR=%~4

if "%MY_GAME_DIR%"=="" set MY_GAME_DIR=C:\Program Files (x86)\Steam\steamapps\common\Half Sword

if "%HOST_URL%"=="" (
    echo 1. Cole o LINK que o host enviou:
    echo    (ex: https://xxx.trycloudflare.com)
    set /p HOST_URL="Link do host: "
)
if "%MY_NAME%"=="" (
    echo 2. Seu nome:
    set /p MY_NAME="Nome: "
)
if "%MY_ROOM%"=="" (
    echo 3. Nome da sala (mesmo do host):
    set /p MY_ROOM="Sala: "
)

if "%HOST_URL%"=="" (
    echo [ERRO] Link vazio!
    pause
    exit /b 1
)

echo Conectando ao relay via tunnel...
echo.

:: Matar processos antigos
taskkill /F /IM peer_agent.py >nul 2>&1
taskkill /F /IM HalfSwordUE5-Win64-Shipping.exe >nul 2>&1

:: Converter https:// para wss://
set WS_URL=%HOST_URL:https://=wss://%
set WS_URL=%WS_URL:http://=ws://%

:: Se nao comeca com ws, adicionar wss://
echo %WS_URL% | findstr /B "ws://" >nul 2>&1
if errorlevel 1 set WS_URL=wss://%HOST_URL:https://=%

:: Iniciar peer agent — --openworld eh OBRIGATORIO:
:: escreve "openworld start <session>" no mp_openworld_control.txt
:: e o HalfSwordBridge do jogo entra no L_World_V1 automaticamente.
:: --sync-dest + --game-dir: recebe TODOS os updates do host em tempo real
:: (mods, scripts, docs) e aplica no repo e no jogo sozinho. Nada de git.
echo Iniciando peer agent com --openworld + sync automatico...
start "PeerAgent" /min python peer_agent.py --server "%WS_URL%" --room "%MY_ROOM%" --name "%MY_NAME%" --role client --openworld --sync-dest "%~dp0" --game-dir "%MY_GAME_DIR%"

echo.
echo Peer agent rodando!
echo Abra o Half Sword via Steam e aguarde: o jogo deve abrir o L_World_V1 sozinho.
echo Confira no UE4SS.log: "Multiplayer lobby requested Open World start".
echo.
echo Para fechar: feche esta janela.
pause
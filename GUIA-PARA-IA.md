# Guia para outra IA — configurar o Half Online

Este arquivo descreve o procedimento completo para uma IA ajudar duas pessoas a
instalar, criar uma sala privada, conectar os dois jogos e verificar a
sincronização do Half Online.

O projeto é comunitário, não oficial e experimental. Cada pessoa deve usar seu
próprio PC, sua própria conta Steam e uma cópia legítima do Half Sword.

## O que o sistema faz atualmente

- Cria um relay WebSocket no PC do host, na porta local `8790`.
- Publica esse relay com um Quick Tunnel do Cloudflare.
- Conecta o host diretamente em `ws://127.0.0.1:8790`.
- Conecta o amigo pelo endereço público `wss://...trycloudflare.com`.
- Envia posição e rotação dos jogadores em snapshots de seis valores.
- Cria e movimenta um avatar remoto dentro da arena.
- Remove o avatar remoto quando o outro jogador sai.

O protótipo ainda não sincroniza de forma completa golpes, dano, física,
inventário, armas ou animações. Não apresentar essa camada como multiplayer
competitivo finalizado.

## Arquitetura

```text
Half Sword + UE4SS mod
        |
        | arquivos mp_outbound.txt / mp_inbound.txt
        v
peer_agent.py
        |
        | WebSocket
        v
relay_server.py no PC do host
        |
        | Cloudflare Quick Tunnel
        v
peer_agent.py no PC do amigo
        |
        v
Half Sword + UE4SS mod
```

## Pré-requisitos nos dois computadores

1. Half Sword instalado pela Steam.
2. UE4SS já instalado e carregando mods no Half Sword.
3. Python 3.10 ou superior.
4. Instalar a dependência com `python -m pip install "websockets>=15,<18"`.
5. Baixar ou clonar este repositório nos dois PCs.
6. Fechar o Half Sword antes de instalar o mod.
7. Executar `INSTALAR-MOD-FASE-1.ps1` em PowerShell.

O instalador espera a instalação padrão da Steam em:

```text
C:\Program Files (x86)\Steam\steamapps\common\Half Sword
```

Se o jogo estiver em outra biblioteca, a IA deve localizar
`HalfswordUE5\Binaries\Win64\ue4ss\Mods` e ajustar o caminho do instalador antes
de executá-lo.

## Requisito adicional do host

O host precisa do `cloudflared.exe`. O launcher procura na pasta do projeto, na
subpasta `bin`, na Área de Trabalho, em `%LOCALAPPDATA%` e no `PATH` do Windows.
Para outros usuários, prefira colocar `cloudflared.exe` ao lado de
`real_launcher.py`.

## Como o host cria a sala

1. Abrir `real_launcher.py` ou executar `HOSTEAR.cmd`.
2. Preencher `Seu nome` e `Nome da sala`.
3. Clicar em `CRIAR SALA`.
4. Aguardar a mensagem de link criado.
5. Confirmar que a arena aparece como `ATIVA` e mostra `1/2` jogadores.
6. Copiar o link `https://...trycloudflare.com` e enviá-lo ao amigo.
7. Abrir o Half Sword pelo launcher.
8. Entrar em `Train` ou `Spar` e carregar a arena.

O host não usa o endereço público para registrar a própria sala. Ele entra pelo
relay local para evitar a propagação inicial de DNS do Quick Tunnel.

## Como o amigo entra

1. Instalar a mesma versão do repositório e do mod.
2. Abrir `real_launcher.py` ou executar `CONECTAR-AMIGO.cmd`.
3. Preencher o próprio nome.
4. Usar exatamente o mesmo nome de sala informado pelo host.
5. Colar o link público no campo `Link do host`.
6. Clicar em `ENTRAR`.
7. Confirmar que o launcher mostra `2/2` jogadores.
8. Abrir o Half Sword pela própria Steam.
9. Entrar em `Train` ou `Spar` e carregar a mesma arena do host.

Os dois jogadores precisam usar o mesmo identificador de sala. O link sozinho
não substitui o nome da sala.

## Como verificar se está sincronizando

No PC de cada jogador, conferir:

```text
%LOCALAPPDATA%\HalfSwordUE5\Saved\HalfSwordOnlineReal
```

Sinais esperados:

- `mp_room_status.json` contém a sala e dois jogadores.
- `mp_outbound.txt` muda quando o jogador local se movimenta.
- `mp_inbound.txt` recebe os valores enviados pelo outro jogador.
- `logs\peer-host.log` contém `connected to room ... as host` no host.
- `logs\peer-client.log` contém `connected to room ... as client` no amigo.
- O log do UE4SS mostra o mod Half Online carregado.
- Um avatar remoto aparece e muda de posição na arena.

## Diagnóstico rápido

### O botão Criar sala não faz nada

1. Confirmar Python e `websockets`.
2. Abrir `logs\launcher-error.log`.
3. Confirmar que `cloudflared.exe` foi encontrado.
4. Confirmar que a porta local `8790` não está ocupada.
5. Reiniciar o launcher depois de atualizar o Git.

### O link é criado, mas o amigo não entra

1. Aguardar alguns segundos para o DNS do Quick Tunnel propagar.
2. Confirmar que o nome da sala é idêntico nos dois PCs.
3. Não fechar o launcher do host nem o processo do Cloudflare.
4. Conferir `peer-client.log`:
   - `room_not_found`: nome diferente ou host ainda não registrado.
   - `room_locked`: o host trancou a sala.
   - `room_full`: a sala já possui dois jogadores.
   - `getaddrinfo failed`: o endereço ainda não propagou ou está errado.

### Conecta, mas não aparece o outro jogador

1. Confirmar `2/2` em `mp_room_status.json`.
2. Confirmar que ambos entraram em uma arena, não apenas no menu.
3. Conferir se `mp_outbound.txt` está mudando nos dois PCs.
4. Confirmar que `HalfSwordOnlineRealMod` está ativado no `mods.txt` do UE4SS.
5. Comparar as versões do jogo, UE4SS e do repositório.

## Limitações importantes

- Não existe servidor-diretório global publicado. O host precisa enviar o link.
- O Quick Tunnel é temporário e cada sala pode gerar outro endereço.
- Fechar o launcher do host encerra a sala.
- A sincronização atual é de posição e rotação, não do estado completo da luta.
- Os dois jogadores devem usar versões compatíveis do jogo e do mod.

## Arquivos principais para uma IA inspecionar

- `real_launcher.py`: interface, criação e entrada na sala.
- `relay_server.py`: salas, limite e encaminhamento de snapshots.
- `peer_agent.py`: ponte entre arquivos locais e WebSocket.
- `HalfSwordOnlineRealMod/Scripts/main.lua`: integração com o jogo via UE4SS.
- `logs/`: diagnóstico de relay, túnel, host e cliente.

Assinado: shokk

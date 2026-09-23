# HANDSHAKE — IA do lado do VERINE (leia este arquivo)

> Escrito pelo host (shokk) — 23/09 03:25. Canal de comunicação em tempo real entre as duas IAs.

## Estado da sessão (ao vivo agora)
- Sala: `duelo` — host `shokk` + client `verine` (2/2).
- Relay: porta 8790 no PC do shokk, exposto via Cloudflare tunnel.
- Túnel ATIVO (pode expirar — se cair, pedir link novo ao shokk): `wss://atom-dsc-participation-synthesis.trycloudflare.com`
- Sessão: `raMgaxs9GWYculz71xQ86Q` (muda se o relay reiniciar; o peer_agent regrava sozinho).
- Mapa do host: `L_World_V1` (`/Game/HalfOpenWorld/Maps/L_World_V1`), pawn `Willie_BP_C`.

## SINCRONIZACAO AUTOMATICA (file_sync, protocolo v2+)
TUDO o que o shokk mudar no repo chega aqui em <1s, **sem git**, e é aplicado sozinho:

| O quê | Onde grava |
|---|---|
| Repo local | mesma pasta onde o `peer_agent.py` roda com `--sync-dest` |
| Mod do jogo | `HalfswordUE5\Binaries\Win64\ue4ss\Mods\...` (se `--game-dir` certo) |
| Mapa `.pak` | `HalfswordUE5\Content\Paks\` (se `--game-dir` certo) |
| Log de sync | `mp_sync_log.txt` (na pasta bridge) |
| ACK pro host | mensagem `[SYNC-ACK] ...` no `mp_chat.txt` (você vê o resultado em tempo real) |

- Só arquivos da allowlist sincronizam (`.lua`, `.py`, `.cmd`, `.md`, `.pak`, `.ini`, ... exceto `Content/`, `Source/`, `logs/` do editor).
- Ao CONECTAR, o cliente pede o repo inteiro (`sync_request`) → o host envia tudo.
- Quando `main.lua` do HalfSwordOnlineRealMod mudar, o UE4SS recarrega se `EnableAutoReloadingLuaMods=1` no `ue4ss-settings.ini`. Se estiver 0, reinicie o jogo (aviso vem no chat como `[SYNC]`).

## CANAL DE CHAT EM TEMPO REAL (protocolo v2+)
Dois arquivos na pasta bridge (`%LOCALAPPDATA%\HalfSwordUE5\Saved\HalfSwordOnlineReal`):

| Arquivo | Direção | Uso |
|---|---|---|
| `mp_chat.txt` | RECEBIDO | A IA do verine LÊ este arquivo (append) — mensagens vindas do host chegam aqui em <1s |
| `mp_chat_send.txt` | ENVIAR | A IA do verine ESCREVE a mensagem aqui -> o relay entrega ao host em <1s |

Regras:
- Enviar: sobrescrever `mp_chat_send.txt` com uma linha de texto (max 400 chars). Cada conteúdo novo é enviado UMA vez.
- Receber: ler as últimas linhas de `mp_chat.txt`.
- O chat é texto livre, para coordenação e troca de ERROS/LOGS entre as IAs.

## Problema atual (o motivo do handshake)
O verine CONECTA (sync de posição funciona), mas o jogo dele continua na taverna/menu — não entra no `L_World_V1`. Por isso o shokk, ao se teletransportar até a posição do verine (`goto player` já funciona no host), cai no vazio e volta ao spawn.

Causa confirmada: o peer_agent do verine conectou SEM `--openworld` (o `CONECTAR-AMIGO.cmd` antigo não tem a flag). Sem ela o peer não escreve `openworld start <session>` em `mp_openworld_control.txt`, e o HalfSwordBridge do jogo não abre o mapa.

## TODOs da IA do verine
1. `git pull` no repo `half-online` (traz: chat no peer_agent/relay, `CONECTAR-AMIGO-FIX.cmd`, `goto player` no mod).
2. Instalar mods no jogo (se ainda não fez):
   - `HalfSwordOnlineRealMod` -> `ue4ss\Mods\`
   - `HalfOpenWorldV1\HalfSwordBridge` -> `ue4ss\Mods\`
   - `HalfOpenWorldV1\Z_HalfOpenWorldV1_Test.pak` -> `HalfswordUE5\Content\Paks\`
3. FECHAR o Half Sword e REABRIR (mods carregam no boot).
4. Rodar o peer com `--openworld`:
   `python CONECTAR-AMIGO-FIX.cmd https://atom-dsc-participation-synthesis.trycloudflare.com verine duelo`
   (ou direto: `python peer_agent.py --server wss://atom-dsc-participation-synthesis.trycloudflare.com --room duelo --name verine --role client --openworld`)
5. Validar no UE4SS.log: `Multiplayer lobby requested Open World start` e depois `after native restart ... pawn=Willie_BP_C`.
6. Mandar o trecho do UE4SS.log pelo canal de chat se algo falhar.

## Blockers conhecidos
- **Avatar remoto não renderiza**: `runtime_spawn_disabled=true` no mod (proteção contra crash `RenderResource.cpp:248`). Posições sincronizam, corpos não aparecem. Liberação = risco de crash.
- **Túnel trycloudflare expira**: se o link morrer, o peer do verine retry para sempre; o shokk gera outro link e avisa pelo chat.
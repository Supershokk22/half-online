# HALF SWORD ONLINE — COMO CONECTAR
## Siga esses passos EXATAMENTE na ordem.

### O QUE VOCE PRECISA
1. Half Sword instalado na Steam
2. Python 3.10+ (com websockets: `pip install "websockets>=17,<18"`)
3. Mod HalfSwordOnlineRealMod instalado

### PASSO A PASSO

#### OPCAO A — Pelo Launcher (mais facil)
1. Abra `real_launcher.py`
2. Cole o **link** que o host enviou no campo "URL do host"
3. Coloque seu nome e o nome da sala
4. Clique **"Entrar na sala"**
5. Abra o Half Sword pela Steam → Spar/Training

#### OPCAO B — Pelo CMD
1. Execute `CONECTAR-AMIGO.cmd`
2. Cole o link do host
3. Digite seu nome e nome da sala
4. Abra o Half Sword pela Steam → Spar/Training

#### OPCAO C — Pelo terminal (manual)
1. Abra PowerShell ou CMD
2. Navegue ate a pasta do projeto:
   ```
   cd C:\Users\SEU_NOME\Desktop\HalfSwordOnlineGit
   ```
3. Execute (substitua o link):
   ```
   python peer_agent.py --server wss://xxx.trycloudflare.com --room duelo --name SEU_NOME --role client
   ```

### COMO FUNCIONA
- O host clica "Hospedar sala" no launcher
- O launcher cria um **link publico** via Cloudflare Tunnel
- O host envia o link para voce
- Voce cola o link no seu launcher e conecta
- O mod dentro do jogo detecta seu personagem
- A posicao e sincronizada entre os dois jogadores em tempo real

### TROUBLESHOOTING
- "connection refused": host nao esta com a sala aberta
- "room not_found": sala nao existe, confirme o nome
- "room_locked": sala esta trancada pelo host
- "room_full": sala ja tem 2 jogadores
- Jogo nao abre: Steam precisa estar aberta
- Avatar nao aparece: entre no Spar/Training e selecione um mapa
- Link nao funciona: pea ao host para criar a sala novamente

### ARQUITETURA
```
[Seu Jogo+Mod] <-> [peer_agent.py] <-> [Cloudflare Tunnel] <-> [relay_server.py (host)] <-> [Jogo Host+Mod]
```

# HALF SWORD ONLINE — COMO CONECTAR
## Siga esses passos EXATAMENTE na ordem.

### O QUE VOCE PRECISA
1. Half Sword instalado na Steam
2. Tailscale instalado e conectado (mesma rede do host)
3. Python 3.10+ (com websockets: `pip install "websockets>=17,<18"`)
4. Mod HalfSwordOnlineRealMod instalado (rode uma vez: `INSTALAR-MOD-FASE-1.ps1`)

### PASSO A PASSO
1. Peça o IP Tailscale do host (formato: 100.x.x.x)
2. Abra o terminal (PowerShell ou CMD)
3. Navegue até a pasta do projeto:
   ```
   cd C:\Users\SEU_NOME\Desktop\HalfSwordOnlineGit
   ```
4. Execute:
   ```
   python peer_agent.py --server ws://IP_DO_HOST:8790 --room duelo --name SEU_NOME --role client
   ```
   Exemplo:
   ```
   python peer_agent.py --server ws://100.79.236.57:8790 --room duelo --name Amigo --role client
   ```
5. Abra o Half Sword pela Steam
6. Navegue: Spar/Training → selecione um mapa → jogue

### O QUE ACONTECE
- O peer_agent conecta ao relay do host
- O mod dentro do jogo detecta seu personagem
- A posição é sincronizada entre os dois jogadores em tempo real
- Quando um sair da sala, o avatar do outro some

### TROUBLESHOOTING
- "connection refused": host não está rodando o relay
- "room not_found": sala não existe, confirme o nome
- "unsupported_protocol": versão do peer_agent desatualizada, atualize do GitHub
- Jogo não abre: Steam precisa estar aberta
- Avatar não aparece: entre no Spar/Training e selecione um mapa

### ARQUITETURA
```
[Seu Jogo+Mod] ↔ [peer_agent.py] ↔ [relay_server.py (host)] ↔ [peer_agent.py (host)] ↔ [Jogo Host+Mod]
```

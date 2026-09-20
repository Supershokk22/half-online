# HALF SWORD ONLINE — INSTRUCOES PARA O AMIGO
## Para IA assistente: siga estes passos exatamente.

### REQUISITOS
- Half Sword instalado na Steam (app ID 2397300)
- Tailscale instalado e conectado na mesma rede do host
- Python 3.10+ instalado (com websockets: `pip install "websockets>=17,<18"`)
- Mod HalfSwordOnlineRealMod instalado (rode INSTALAR-MOD-FASE-1.ps1 uma vez)

### COMO CONECTAR (CLIENTE)
1. Peca o IP Tailscale do host (formato: 100.x.x.x)
2. Execute `CONECTAR.cmd` passando o IP:
   ```
   CONECTAR.cmd 100.79.236.57
   ```
   Ou execute sem argumento e cole o IP quando pedido.
3. O script faz TUDO automaticamente:
   - Mata processos antigos (jogo, python, relay)
   - Conecta ao relay do host na sala "duelo"
   - Abre o jogo via Steam
4. O mod dentro do jogo vai:
   - Carregar o mapa automaticamente
   - Detectar seu pawn (personagem)
   - Conectar ao relay e sincronizar posicao

### COMO HOSTEAR
1. Execute `HOSTEAR.cmd`
2. O script faz TUDO:
   - Mata processos antigos
   - Inicia o relay server na porta 8790
   - Conecta o peer agent como host
   - Abre o jogo
3. Envie seu IP Tailscale pro amigo

### FLUXO DO JOGO
- Ambos vao cair no hub (taverna automaticamente)
- Navegue: Spar/Training -> selecione um mapa -> jogue
- O mod sincroniza posicao e rotacao entre os dois jogadores
- Quando um sair da sala, o avatar do outro some

### SOLUCAO DE PROBLEMAS
- Se "porta 8790 em uso": feche todos os python e relay antes
- Se "room not_found": o host nao esta conectado ainda, espere
- Se o jogo nao abre: verifique se a Steam esta aberta
- O relay roda em: ws://IP_HOST:8790
- A sala padrao se chama: "duelo"

### ARQUITETURA
```
[Seu Jogo + Mod] <-> [peer_agent.py] <-> [relay_server.py (no host)] <-> [peer_agent.py (host)] <-> [Jogo do Host + Mod]
```
- Mod UE4SS escreve posicao em: %LOCALAPPDATA%\HalfSwordUE5\Saved\HalfSwordOnlineReal\mp_outbound.txt
- Mod UE4SS le posicao remota de: mp_inbound.txt
- peer_agent.py faz a ponte entre arquivos e WebSocket
- relay_server.py encaminha snapshots entre os dois jogadores

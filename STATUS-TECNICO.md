# Estado técnico — Half Online v2.1

Assinado: shokk

## Validado localmente

- Relay: host e cliente compartilham uma sessão nova; snapshots são encaminhados;
  uma terceira conexão é recusada; saída do jogador é notificada.
- Launcher: o jogo não é aberto até que o peer tenha recebido `welcome` do relay.
- Segurança de estado: o lease `mp_session.txt` expira em poucos segundos e os
  arquivos de sessão são removidos ao desconectar.
- Jogo offline: o módulo não remove mais o inimigo nativo em loop quando não há
  uma sessão válida.

Execute `python test_fake_client.py` na raiz para repetir o teste do relay.

## Uso

1. Nos dois PCs, instale a mesma versão do projeto com o jogo fechado.
2. O host cria a sala no launcher e envia o link e o nome da sala.
3. O amigo cola o link, informa exatamente o mesmo nome e entra.
4. Ao aparecer “Sala confirmada”, o launcher abre o Half Sword e o bridge leva
   os dois ao Open World V1.

No lobby, `Ctrl+F7` mostra o painel de diagnóstico. `Ctrl+F8` abre o lobby
manualmente, `Ctrl+F11` volta à arena nativa e `Ctrl+F9` escreve diagnóstico no
log do UE4SS. O host possui os comandos de marcador de teste; eles não são
inimigos nem itens nativos.

## Limite honesto desta versão

O projeto ainda não é um multiplayer de combate completo. A versão atual não
replica golpes, armas, dano, ragdoll, inventário, IA ou física entre PCs. O
avatar remoto no lobby é uma representação de posição/rotação. Fazer combate
real exigirá integração de replicação própria do Unreal ou suporte oficial do
jogo; não é seguro fingir que um `SpawnActor` simples fornece física ou IA.

## Para continuidade por outra IA

Arquitetura: `real_launcher.py` inicia `relay_server.py` e `peer_agent.py`.
O peer troca snapshots pela sala WebSocket e publica uma sessão curta no
diretório `%LOCALAPPDATA%\\HalfSwordUE5\\Saved\\HalfSwordOnlineReal`.
`HalfSwordBridge` só abre o mapa se `mp_openworld_control.txt` e
`mp_session.txt` tiverem o mesmo token não expirado. `HalfSwordOnlineRealMod`
só atualiza o avatar remoto com a mesma sessão válida.

Antes de alterar classes nativas, reproduza em um modo original, capture o
log UE4SS e valide inicialização, animação, colisão e limpeza em uma sessão
isolada. Não reutilize o antigo comando `mp_game_control.txt` para autorizar
viagem de mapa: ele não tem lease e foi substituído pelo protocolo v2.

# Half Sword Online — Community Mod

> Assinado: **shokk**

> Projeto não oficial, sem afiliação com Half Sword ou Steam. Este repositório
> não distribui executáveis, arquivos ou conteúdo do jogo.

Esta é a fundação para duas cópias legítimas do Half Sword, uma em cada PC.
Ela não usa captura de tela, controle remoto ou split-screen: cada PC roda seu
próprio jogo, seu próprio mod e seu próprio processo de rede.

## O que está implementado

- Relay WebSocket privado para uma sala com host + um cliente.
- Agente local em cada PC que encaminha snapshots entre o mod e o relay.
- Protocolo compacto validado pelo relay, limitado a 2 KiB por mensagem.
- Ponte de arquivos a 20 Hz para compatibilidade com UE4SS Lua.
- Mod v2 que envia posição/rotação local e cria um avatar remoto sem controle
  local para aplicar o snapshot recebido.
- Controles de host no relay: estado da sala e trava de entrada.
- Painel do host: limpar bot nativo do Spar e adicionar/remover oponente de
  treino parado.
- Sala vazia remove o avatar remoto da sessão anterior.

## Launcher

Abra `ABRIR-HALF-SWORD-ONLINE-REAL.cmd` em cada PC. O host escolhe
**Hospedar sala**, copia o IP Tailscale e envia ao amigo. O amigo cola o IP,
usa o mesmo nome de sala e escolhe **Entrar na sala**. Depois, ambos abrem o
próprio Half Sword pela Steam.

## Estado desta fase

Movimento e rotação são a base validada. Armas, colisões, ragdoll, dano e
inventário ainda **não** são sincronizados. Valide primeiro no Free Mode, com
dois PCs e o mesmo build do jogo.

Também não há sincronização de ataques, IA nativa nem progresso. Não anuncie o
projeto como multiplayer completo antes de validar uma partida entre dois PCs.

## Arquitetura

```text
Half Sword + UE4SS mod <-> ponte de arquivos <-> peer_agent.py
                                                    |
                                             relay_server.py
                                                    |
                                            Tailscale privado
                                                    |
                                             peer_agent.py
                                                    |
Half Sword + UE4SS mod <-> ponte de arquivos <-> segundo PC
```

## Suporte da comunidade

Mod não oficial criado pela comunidade. Terá suporte da nossa equipe,
atualizações e correções conforme novos problemas forem encontrados.

## Rede entre Wi-Fis diferentes

Instalem Tailscale nos dois PCs e usem o IP `100.x.x.x` do host. Isto evita
port-forwarding e VPS para partidas ocasionais. O host executa:

```powershell
py .\relay_server.py
py .\peer_agent.py --server ws://IP-TAILSCALE-DO-HOST:8790 --room teste --name Host --role host
```

O amigo executa apenas o segundo comando com `--role client` e o mesmo `--room`.
Cada um executa o mod UE4SS correspondente dentro de sua instalação local do jogo.

## Painel do host

- **Trancar sala** impede uma nova entrada depois que o amigo conectar.
- **Limpar bot do Spar** remove apenas o oponente nativo não controlado do Spar
  enquanto a sala estiver vazia.
- **Adicionar/Remover oponente** controla um boneco estacionário de treino;
  ele não é IA de combate.

O avatar do amigo só é criado quando ele envia seu primeiro snapshot e é
removido quando ele sai da sala.

## Segurança e teste

- Use apenas uma rede privada controlada (Tailscale) durante o desenvolvimento.
- Não exponha a porta 8790 na internet pública nesta fase.
- A ponte lê no máximo um estado a cada 50 ms; o mod deve ser testado a 20 Hz
  antes de aumentar a frequência.
- Para desfazer, pare `relay_server.py` e `peer_agent.py` e remova o mod da
  pasta `Mods` de cada instalação.

## Publicação responsável

- Nunca publique chaves, logs, saves, IPs pessoais ou arquivos do jogo.
- Abra issues com a versão do jogo, UE4SS, papel host/cliente e passos para
  reproduzir, removendo dados pessoais do log.
- Código licenciado sob MIT; Half Sword e seus conteúdos pertencem aos seus
  respectivos detentores.

Projeto comunitário assinado por **shokk**. Suporte, correções e atualizações
serão publicados conforme os testes encontrarem problemas.

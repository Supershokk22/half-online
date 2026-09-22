# Half Online — plano de progresso

## Objetivo da versão 1

Entregar um lobby multiplayer privado, uma vila leve para exploração e combate, e uma integração estável com o Half Sword sem alterar os arquivos originais do jogo.

## Regras do projeto

- Testar uma mudança por vez e manter um backup funcional.
- Não usar `SpawnActor`/`DestroyActor` em runtime até existir uma classe nativa segura.
- Não ativar a GUI de debug do UE4SS no build estável.
- Não incluir assets proprietários extraídos no GitHub; o jogador precisa ter o Half Sword instalado.
- Cada etapa só é considerada concluída depois de um teste reproduzível.

## Etapas

### 0. Base estável — concluída

- [x] UE4SS configurado para evitar a GUI DX11 instável.
- [x] Mods antigos desativados.
- [x] Ponte e sincronização do lobby ativas.
- [x] Spawns dinâmicos bloqueados para evitar `FRenderResource`.
- [x] Relay testado com host, cliente, snapshot, limite e saída.

### 1. Mapa da vila — em andamento

- [ ] Praça central ampla para lutas.
- [ ] Ruas estreitas para combate próximo.
- [ ] Pátio de treino separado.
- [ ] Casas, cercas, madeira e pedra usando referências nativas do jogo.
- [ ] Iluminação simples e colisão estática; sem Lumen/Nanite.
- [ ] Testar carregamento no jogo e medir se não há crash.

### 2. Lobby conectado ao mapa

- [ ] Host cria a sessão no launcher.
- [ ] Cliente entra pela mesma sessão.
- [ ] Ambos carregam automaticamente o mapa da vila.
- [ ] Estado da sala aparece no launcher.
- [ ] Entrada/saída do cliente não deixa recursos órfãos.

### 3. Player remoto seguro

- [ ] Descobrir a classe nativa de personagem no build atual.
- [ ] Reutilizar um pawn nativo já criado pelo jogo.
- [ ] Sincronizar posição e rotação com interpolação.
- [ ] Validar colisão, animação e física nativas.
- [ ] Só então testar combate entre dois jogadores.

### 4. Painel administrativo

- [ ] Painel externo estável para host.
- [ ] Mostrar jogadores conectados e latência.
- [ ] Comandos seguros: limpar sala, voltar ao mapa, diagnóstico.
- [ ] Spawns só depois da etapa 3 e apenas por classes nativas validadas.

### 5. Empacotamento e distribuição

- [ ] Gerar `.pak` da vila.
- [ ] Script de instalação/remoção reversível.
- [ ] README com requisitos, atalhos e solução de problemas.
- [ ] Teste em uma segunda instalação limpa.
- [ ] Publicar código e scripts sem assets proprietários.

## Critério de versão jogável

A versão só será marcada como jogável quando duas instalações conectarem na mesma sala, carregarem a vila, permanecerem estáveis por 15 minutos e permitirem sair/entrar sem crash.

## Próximo passo desta sessão

Concluir a etapa 1 no Unreal Editor: salvar a vila em `L_World_V1`, cozinhar o `.pak` e testar o carregamento antes de reativar qualquer spawn.

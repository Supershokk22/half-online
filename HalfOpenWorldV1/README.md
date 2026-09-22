# Half Open World V1

Protótipo de autoria para uma expansão de Half Sword, assinado: shokk.

## Estado honesto

- Projeto editável no Unreal Engine 5.4.
- `L_Menu_V1`: cena de menu. O menu funcional é construído pelo módulo runtime `HalfOpenWorldV1`; `WBP_OpenWorldMenu` permanece como estudo visual, não é o menu executado.
- `L_World_V1`: mapa cinza editável com colisão, praça, taverna, estrada, casas, portões e pontos de interesse.
- Os mapas usam sol e claridade do céu dinâmicos para aparecerem sem compilar iluminação. A V1 ainda é um *graybox*: não há texturas finais.
- O fluxo de teste no projeto Unreal funciona: Novo Jogo abre `L_World_V1`; Esc pausa; Salvar e voltar ao menu grava posição local; Continuar restaura essa posição. Configurações oferece qualidade baixa/média e Sair fecha o teste. Há um personagem de câmera em primeira pessoa com colisão e movimento básico, não o personagem nem a física de combate do Half Sword.
- O mapa foi empacotado como teste removível e abriu no executável de Half Sword. No primeiro carregamento não havia personagem; o bridge UE4SS criou e possuiu `Willie_BP_C` via GameMode nativo após Ctrl+F10 (confirmado no log). Movimento, combate, inventário e estabilidade ainda não foram validados. O respawn automático após Ctrl+F8 foi preparado, mas ainda não testado após reiniciar o jogo.
- O menu principal de Half Sword **continua original**. O menu Slate deste projeto depende do módulo C++ do protótipo e não foi integrado ao jogo. `WBP_OpenWorldMenu` é apenas estudo visual, sem botões funcionais no executável do jogo.
- Nenhum arquivo do jogo base é incluído neste projeto. O mod multiplayer permanece separado e pausado.

## Abrir

Abra `HalfOpenWorldV1.uproject` no Unreal 5.4. No Content Browser, abra `Content/HalfOpenWorld/Maps/L_World_V1` para editar o mundo. O projeto abre inicialmente em `L_Menu_V1`.

Para testar o fluxo completo fora do Editor, execute `JOGAR-V1.cmd` (é um teste pelo Unreal, não pelo Half Sword). A primeira abertura pode demorar alguns minutos enquanto o Engine compila shaders. No menu, use mouse ou Tab/Enter. No mapa: WASD mover, mouse olhar, Espaço pular, Shift correr e Esc pausar. O progresso fica em `Saved/SaveGames/HalfOpenWorldV1_Player.sav` dentro deste projeto.

Para reconstruir os mapas faltantes, execute `Scripts/build_v1.py` no Editor (PythonScriptPlugin). Para gerar o menu UMG, compile o target `HalfOpenWorldV1Editor` e execute o commandlet `-run=GenerateOpenWorldMenu`. Ambos preservam assets já existentes para não apagar edições futuras.

Se um mapa anterior abrir preto, feche o Editor e execute `Scripts/repair_v1_lighting.py` com `UnrealEditor-Cmd.exe -run=pythonscript -script=...` para atualizar apenas as luzes, preservando a geometria.

## Teste experimental no Half Sword

O pacote `Z_HalfOpenWorldV1_Test.pak` está instalado em `HalfswordUE5/Content/Paks/` e o script em `HalfswordUE5/Binaries/Win64/ue4ss/Mods/HalfSwordBridge/`. Entre em Free Mode e use Ctrl+F8 para abrir o mapa. Ctrl+F9 registra o estado; Ctrl+F10 é fallback manual de respawn. O script atualmente instalado tem tentativa de respawn automático, mas essa versão ainda precisa de um teste com o jogo reiniciado. Não divulgar como versão pronta.

## Plano de integração no Half Sword

1. Confirmar a versão de Engine, plataforma, nomes de mapa, regras de montagem e `GameMode` do build instalado. A evidência local está em `CONTINUAR-IA.md`.
2. Usar o fluxo de menu e mapa já testado no projeto de autoria como referência. Adaptar a entrada para um menu/tecla opcional no jogo base, sem substituir o menu principal original.
3. Criar fluxo de viagem seguro para `L_World_V1` no jogo real. O primeiro teste deve ser reversível e isolado.
4. Cozinhar e empacotar somente assets próprios para Win64 com UE 5.4, montar em namespace próprio, verificar referências e testar entrada/saída. Não embutir assets originais de Half Sword.
5. Validar que a classe de pawn/controlador, física, combate e inventário do jogo são criados no novo mapa. Se não forem, parar e integrar via interfaces/Blueprints compatíveis; nunca declarar suporte de física antes do teste no executável.

## Performance

- Protótipo de aproximadamente 30 atores simples, sem Tick de Blueprint, IA, foliage, partículas ou pós-processamento próprio.
- Geometria estática simples; não gerar centenas de componentes individuais nem sombras móveis extras.
- Antes de adicionar decoração, registrar FPS, frame time CPU/GPU, memória e log em `L_World_V1` com e sem o mod. Alvo inicial: custo adicional de até 2 ms por frame em 1080p no PC de teste.
- Para expansão: HLOD/instancing/streaming por região e limites de spawn; nunca ativar todos os NPCs simultaneamente.

## Reverter

Com o jogo fechado, para desativar o teste, retire **somente** `Z_HalfOpenWorldV1_Test.pak` de `HalfswordUE5/Content/Paks/` e a pasta `HalfSwordBridge` de `ue4ss/Mods/`. Não remova mods de terceiros. A pasta do projeto pode ser guardada sem afetar saves. Nenhum `pakchunk0-Windows.pak`, save nativo ou `mods.txt` foi alterado por este teste.

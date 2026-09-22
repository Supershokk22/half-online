# Estado da tarefa — 21/09/2026 (histórico + atualização)

ESTADO ATUAL: mapa próprio instalado e aberto no Half Sword por Ctrl+F8. Ctrl+F10 manual criou/possuiu `Willie_BP_C` segundo o log. O respawn automático foi copiado ao bridge, mas ainda não foi testado após reiniciar. O menu principal do jogo continua original. Leia `GUIA-PARA-OUTRA-IA.md` para procedimento completo e evidências. O texto abaixo registra a fase anterior do protótipo, não o estado atual.

O usuário pediu uma V1 de menu e mapa editável, com baixo custo de desempenho. O multiplayer está pausado. Nesta fase inicial o projeto era apenas de autoria, antes da integração experimental descrita acima.

- Projeto, configurações, `Scripts/build_v1.py`, `README.md` e `CONTINUAR-IA.md` criados.
- `python -m py_compile Scripts/build_v1.py` passou.
- `L_Menu_V1.umap` e `L_World_V1.umap` foram gerados e salvos. A primeira tentativa de criar UMG via Python falhou porque o `WidgetBlueprint.widget_tree` não é exposto nessa versão.
- Foi criado e compilado `HalfOpenWorldV1Editor` com `UGenerateOpenWorldMenuCommandlet`. O comando `-run=GenerateOpenWorldMenu` salvou `WBP_OpenWorldMenu.uasset` com 0 erros.
- A rotação do sol estava com eixos trocados e causava o mapa preto. Corrigido em `build_v1.py` e nos mapas existentes por `repair_v1_lighting.py`; o usuário confirmou que o mapa ficou visível.
- O módulo runtime `HalfOpenWorldV1` foi compilado sem erro. Teste em `UnrealEditor.exe -game -d3d11`: menu aparece; Tab/Enter em Novo Jogo abriu `L_World_V1`; Esc abriu pausa; Salvar e voltar criou `Saved/SaveGames/HalfOpenWorldV1_Player.sav`; Continuar restaurou o mapa e a posição (`Save restored` no log). O usuário confirmou que o último teste abriu após carregamento lento.
- `WBP_OpenWorldMenu.uasset` é apenas estudo visual. O menu funcional é Slate/C++ no `AOWPlayerController`, com `AOWGameMode`, `AOWExplorerCharacter`, `UOWGameInstance` e `UOWSaveGame` próprios deste projeto. Controles básicos são definidos, mas movimento manual e qualidade ainda devem ser validados pelo usuário.

Ao retomar: não substituir o menu funcional pelo `WBP_OpenWorldMenu` sem necessidade. Confirmar opções de qualidade e controles manualmente. Para integrar ao Half Sword, o módulo C++ deste projeto não pode simplesmente ser colocado em `.pak` do jogo; criar uma interface asset-only ou UE4SS compatível, cozinhar assets em namespace próprio, verificar versão da Engine/mount point e testar entrada reversível no executável real. Não marcar integração nem física nativa como testadas antes de evidência reproduzível.

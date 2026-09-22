# Handoff para outra IA — Half Open World V1

Leia também `GUIA-PARA-OUTRA-IA.md`: contém a sequência reproduzível, fontes, comandos, testes e próximos passos atualizados.

Objetivo: total conversion gradual, mas o primeiro marco é menu próprio e mapa editável DENTRO do Half Sword. Não confundir o projeto de autoria com um jogo separado e não prometer integração que ainda não foi testada.

## Estado atual para retomar rápido (21/09/2026)

- Projeto local em `C:\Users\shokk123\Documents\Codex\2026-09-14\vam\outputs\HalfOpenWorldV1`. Este diretório **não é um repositório Git**; nada foi publicado nesta etapa.
- Mapa próprio empacotado e instalado como `Z_HalfOpenWorldV1_Test.pak`. Bridge instalado em `ue4ss/Mods/HalfSwordBridge/Scripts/main.lua`; a cópia instalada e o arquivo do projeto têm SHA-256 idêntico.
- Teste real confirmou: Ctrl+F8 abriu `L_World_V1`; o primeiro GameMode tinha `DefaultPawnClass=none` e `pawn=none`. Ctrl+F10 atribuiu `Willie_BP_C` e `RestartPlayer` resultou em `pawn=Willie_BP_C`. Usuário disse que “foi”, mas não confirmou ainda movimento/câmera/combate.
- O bridge salvo agora tenta esse respawn automaticamente até 10 segundos após Ctrl+F8. **Ainda não foi reiniciado/testado desde essa alteração.** Não confundir confirmação do Ctrl+F10 manual com validação do automático.
- Menu principal de Half Sword ainda é o original. O menu Slate do projeto de autoria não roda no executável shipping; `WBP_OpenWorldMenu` é só asset visual, não menu funcional. Próximo marco: interface UMG própria acionada pelo bridge, com entrada funcional no mapa e retorno, mantendo o menu original intacto. Não empacotar ou anunciar esse menu antes de teste real.
- Captura remota da janela falhou com `SetIsBorderRequired ... 0x80004002`; pedir screenshot ao usuário, não afirmar inspeção visual do jogo.

## Ambiente observado em 21/09/2026

- Jogo instalado em `C:\Program Files (x86)\Steam\steamapps\common\Half Sword`.
- Executável `HalfswordUE5\Binaries\Win64\HalfSwordUE5-Win64-Shipping.exe`, SHA-256 `367DFCCF1AACA3BBF6824C9BB616F2F31BC30E7AC70C5FA8657E212DBB2C2E03`.
- Editor em `C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe`.
- O UE4SS está em `HalfswordUE5\Binaries\Win64\ue4ss`. Não tocar `HalfSwordOnlineRealMod` nem mods de terceiros.
- `OpenWorldExpansion DISABLED` é legado, tem lógica de RPG simulada por Lua/JSON e documentação que exagera o estado real. Não reativar automaticamente. Não reutilizar seu `main.lua` sem corrigir boot, limites de spawn e keybinds conflitantes.

## Estrutura da V1

- `HalfOpenWorldV1.uproject`: projeto de autoria UE 5.4.
- `Scripts/build_v1.py`: gerador idempotente, não sobrescreve assets já existentes.
- `Content/HalfOpenWorld/Maps/L_Menu_V1.umap`: cena do menu.
- `Content/HalfOpenWorld/Maps/L_World_V1.umap`: mundo cinza com colisão e PlayerStart.
- `Source/HalfOpenWorldV1`: módulo runtime C++ com `AOWGameMode`, `AOWPlayerController`, `AOWExplorerCharacter`, `UOWSaveGame` e `UOWGameInstance`. Menu Slate funcional; `WBP_OpenWorldMenu.uasset` é só estudo visual não usado em execução.
- `README.md`: estado, performance, instalação e rollback.

## Próximos passos na ordem

### Integração experimental em 21/09/2026

- `Scripts/prepare_game_assets.py` criou e salvou malha e materiais próprios, sem substituir assets do jogo. O mapa não tem GameMode override do projeto.
- Cook Windows de `L_World_V1` terminou com 0 erros e 0 avisos. `half_sword_map_pak.txt` empacotou 14 arquivos em `Z_HalfOpenWorldV1_Test.pak` (Pak v11, 98.351 bytes, sem criptografia).
- Cópia reversível instalada em `HalfswordUE5/Content/Paks/Z_HalfOpenWorldV1_Test.pak`; bridge UE4SS em `ue4ss/Mods/HalfSwordBridge` com `enabled.txt`. Ctrl+F8 tenta abrir o mapa somente após ação explícita do jogador.
- Half Sword iniciou pela Steam e o log UE4SS confirmou `HalfOpenWorldV1 Bridge loaded`. Esta foi a situação inicial; ver o estado atual no topo para os testes posteriores. A captura da janela pelo controle remoto falhou com `SetIsBorderRequired ... 0x80004002`.
- Se houver erro, coletar linhas `[HalfOpenWorldV1]` do `ue4ss/UE4SS.log` e relatório em `AppData/Local/HalfSwordUE5/Saved/Crashes`. Não afirmar que a integração está pronta. Para desativar, mover apenas o `.pak` e a pasta `HalfSwordBridge` para fora da instalação, com o jogo fechado; não tocar outros mods.
- O primeiro teste de Ctrl+F8 foi observado no log às 13:55: atalho disparou, mas `controller:ConsoleCommand` falhou (`attempt to call a TrivialObject value`). Bridge alterado para `UEHelpers.GetGameplayStatics():OpenLevel(controller, UEHelpers.AddFName(map), true, "")`, reiniciado e depois confirmado funcional.
- Teste posterior: Ctrl+F8 abriu `L_World_V1`. Ctrl+F9 confirmou `BP_HalfSwordGameMode_C` e `PlayerController`, mas `pawn=none`. `DefaultPawnClass=none` explicava o respawn sem efeito. Em 14:42, Ctrl+F10 definiu `Willie_BP_C` apenas no GameMode do mapa customizado e `RestartPlayer` criou/possuiu `Willie_BP_C` (confirmado no log; usuário disse “foi”). Ainda confirmar movimento, câmera, combate e estabilidade.
- Bridge agora agenda esse respawn automaticamente após Ctrl+F8, com checagem restrita ao mapa e até 10 tentativas. Arquivo foi instalado, **mas o automático ainda não foi testado em uma nova abertura do jogo**; Ctrl+F10 continua como fallback. Não interromper a sessão atual sem combinar com o usuário.

1. Abrir UE 5.4 e verificar os três assets. `L_World_V1` passou Map Check com 0 erros e 0 avisos; a rotação errada do sol foi corrigida. Os geradores preservam assets existentes.
2. O fluxo de autoria compilou e foi testado em `-game`: menu visível; Tab/Enter em Novo Jogo abriu `L_World_V1`; Esc mostrou pausa; Salvar e voltar gerou `Saved/SaveGames/HalfOpenWorldV1_Player.sav`; Continuar reabriu o mapa e registrou `Save restored`. Ainda testar controles de movimento manualmente e qualidade no hardware-alvo.
3. O `AOWExplorerCharacter` é um placeholder de primeira pessoa. Somente o teste no executável de Half Sword comprova integração de física, combate, inventário e pawn nativos.
4. Conferir o mount point do `.pak` nativo com `UnrealPak -List` (somente inspeção); cozinhar apenas `/Game/HalfOpenWorld`, empacotar, instalar de forma reversível e validar carga de asset via UE4SS. Não extrair nem distribuir conteúdo proprietário.
   Em 21/09, `UnrealPak.exe` 5.4 não conseguiu listar `pakchunk0-Windows.pak`: o índice exige chave de criptografia. Não tentar contornar isso. Um pacote de mod já instalado (`chrome334's pistol mod.pak`) é legível, Pak v8, índice sem criptografia; isso não comprova que nossos assets cozinharão ou montarão no jogo.
5. No mod runtime, adicionar entrada opcional por tecla/menu, guardar mapa anterior, viajar com confirmação e fallback ao menu nativo. Só habilitar por padrão depois de testar spawn do pawn e `GameMode` nativos.
6. Medir `stat unit`, `stat gpu`, `stat memory` e comparar com mapa nativo. Meta adicional <=2 ms/frame em 1080p. Introduzir instancing, streaming e orçamento de NPCs antes de decorar.

## Regras

- Não publicar como multiplayer nem alterar o projeto `half-online` por causa deste trabalho.
- Não declarar que o mapa roda dentro do Half Sword até existir teste reproduzível no executável com logs e screenshot.
- Não substituir `pakchunk0-Windows.pak`, saves ou menu nativo. A instalação deve ser removível.
- Preservar alterações do usuário; não deletar pastas `Content`, `Saved` ou `Intermediate` sem validar alvo e obter autorização específica.
- Atualizações do Half Sword exigem revalidar hash, UE version e asset paths.

Assinado: shokk.

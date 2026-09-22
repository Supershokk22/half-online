# Continuação técnica — Half Open World V1

Assinado: shokk. Atualizado em 21/09/2026. Leia este arquivo e `CONTINUAR-IA.md` antes de alterar o jogo. O projeto **não** é o repositório público `half-online`; não publicar nem misturar o multiplayer sem pedido explícito.

## Objetivo e situação real

O usuário quer expandir Half Sword com mapa e menu próprios, mantendo mecânicas/controles do jogo. O projeto de autoria UE 5.4.4 já contém um menu Slate funcional **somente no protótipo** e o mapa `L_World_V1`. No jogo Steam, foi instalado um `.pak` removível com o mapa e uma ponte Lua UE4SS. O mapa abriu. Um teste manual com Ctrl+F10 criou e possuiu o Willie nativo; ainda **não** foi comprovado movimento, câmera, física de combate, inventário ou estabilidade. O menu principal Steam segue original. Não chamar o mod de completo.

## Caminhos e artefatos

- Projeto: `C:\Users\shokk123\Documents\Codex\2026-09-14\vam\outputs\HalfOpenWorldV1`.
- Projeto UE: `HalfOpenWorldV1.uproject`; UE instalado em `C:\Program Files\Epic Games\UE_5.4`.
- Jogo: `C:\Program Files (x86)\Steam\steamapps\common\Half Sword`; Steam app ID `2397300`.
- Pak instalado: `HalfswordUE5\Content\Paks\Z_HalfOpenWorldV1_Test.pak`.
- Ponte instalada: `HalfswordUE5\Binaries\Win64\ue4ss\Mods\HalfSwordBridge\Scripts\main.lua`, habilitada por `enabled.txt`. Fonte idêntica dentro deste projeto em `HalfSwordBridge\Scripts\main.lua`.
- Log runtime: `HalfswordUE5\Binaries\Win64\ue4ss\UE4SS.log`; filtrar `[HalfOpenWorldV1]`.
- Assets fonte: `Content\HalfOpenWorld\Maps`, `Geometry`, `Materials`, `UI`.
- Receita do pacote: `half_sword_map_pak.txt` (14 entradas, só mapa, malha e materiais próprios). Saída gerada `Z_HalfOpenWorldV1_Test.pak` (98.351 bytes, Pak v11).
- Arquivos fundamentais: `Scripts\build_v1.py`, `repair_v1_lighting.py`, `prepare_game_assets.py`, `Source\HalfOpenWorldV1`, `Source\HalfOpenWorldV1Editor`, `Config`.
- Não há `.git` na pasta de trabalho `vam`. Nenhum commit/push desta etapa.

## Como foi feito — sequência reproduzível

1. Conferi o executável instalado e o log UE4SS: jogo usa Unreal 5.4. O projeto usa UE 5.4.4. `UnrealPak -List` no `pakchunk0-Windows.pak` original falhou porque o índice exige chave; **não** tentar decifrar ou contornar. Inspecionei apenas pak de mod não criptografado como comparação.
2. Criei `L_Menu_V1` e `L_World_V1` com `Scripts/build_v1.py`; depois corrigi a rotação do sol em `repair_v1_lighting.py`. O usuário confirmou visualmente que o mapa deixou de estar preto. O mapa tem `PlayerStart` e geometria simples.
3. Testei o projeto de autoria com `JOGAR-V1.cmd`: o menu Slate do módulo C++ abriu o mapa, pausa/salvamento/continuar funcionaram no protótipo. **Esse módulo C++ não é carregado pelo executável shipping de Half Sword** e seu menu não deve ser anunciado como integrado.
4. Executei `Scripts/prepare_game_assets.py` pelo `UnrealEditor-Cmd.exe -run=pythonscript -script=<caminho>` para criar/salvar `SM_Block` e cinco materiais próprios e reatribuir somente atores `OWV1_`. Um primeiro cook avisou malha ausente porque ela não fora salva; interrompi, salvei a malha no script e repeti. O cook final terminou com 0 erros e 0 avisos.
5. Cook: `UnrealEditor-Cmd.exe <uproject> -run=cook -targetplatform=Windows -map=/Game/HalfOpenWorld/Maps/L_World_V1 -unattended -nop4 -nosplash`. Nesta máquina a saída ficou em `Saved\Cooked\Windows\HalfOpenWorldV1\Content`. O cook levou ~53 s e usou memória considerável; feche o Editor/jogo antes de refazer.
6. Empacotei com `UnrealPak.exe <projeto>\Z_HalfOpenWorldV1_Test.pak -Create=<projeto>\half_sword_map_pak.txt -NoP4`. O mount point das entradas é `../../../HalfswordUE5/Content/HalfOpenWorld/...`. Instalei **cópia** com nome único em `Paks`; nenhum pak original foi sobrescrito. A ponte Lua está em pasta própria, sem editar `mods.txt`.
7. Inicialmente Ctrl+F8 chegava ao script, mas `controller:ConsoleCommand` deu erro `attempt to call a TrivialObject value`. Troquei para `UEHelpers.GetGameplayStatics():OpenLevel(controller, UEHelpers.AddFName(map), true, "")`; Ctrl+F8 passou a abrir nosso mapa.
8. Ctrl+F9 revelou `BP_HalfSwordGameMode_C` e `PlayerController`, mas `pawn=none`; Ctrl+F10 chamando apenas `RestartPlayer` não resolveu, pois `DefaultPawnClass=none`. A versão seguinte carregou `/Game/Character/Blueprints/Willie_BP.Willie_BP_C`, atribuiu `mode.DefaultPawnClass` **somente na instância do nosso mapa**, e chamou `mode:RestartPlayer(controller)`. Log de 14:42:39 confirmou `pawn=Willie_BP_C`. Usuário disse que “foi”.
9. A versão atual de `HalfSwordBridge/Scripts/main.lua` agenda esse respawn após Ctrl+F8, com limite de dez checagens de 1 s e guarda para não agir fora do nosso mapa. **Este automático foi copiado ao jogo, mas a sessão ainda executa a versão Lua anterior; reiniciar e validar antes de tratar como aprovado.** Ctrl+F9 diagnostica; Ctrl+F10 permanece fallback manual.

## Próximas ações prioritárias

1. Sem fechar a partida atual sem necessidade, confirmar com o usuário se após Ctrl+F10 consegue mover câmera/WASD, pular, lutar e usar inventário. Captura automática da janela falhou (`SetIsBorderRequired ... 0x80004002`); pedir print se precisar de evidência visual.
2. Na próxima reinicialização, testar o respawn **automático**: entrar em Free Mode, Ctrl+F8 uma vez, verificar no log `after native restart ... pawn=Willie_BP_C` sem Ctrl+F10; testar controles. Se falhar, conferir erros Lua e corrigir o agendamento sem alterar mods de terceiros.
3. Menu: o menu original ainda não mudou. `WBP_OpenWorldMenu.uasset` é apenas layout sem lógica de botões; o menu Slate C++ do protótipo não roda no shipping. Criar uma interface UMG **nova e funcional**, cozinhar/empacotar em namespace `/Game/HalfOpenWorld/UI`, apresentá-la por ponte UE4SS de forma aditiva (não substituir assets originais), ligar entrada no mapa/voltar e testar mouse, teclado, foco e saída. Não instalar painel visual com botões falsos. Primeiro validar em sandbox e depois no jogo.
4. Depois medir FPS/memória e validar física/combate. Não retomar multiplayer neste projeto. Não publicar no Git sem pedido específico.

## Fontes — separar documentação de observação

- [UE4SS: estrutura e ativação de mods Lua, hot reload, `RegisterKeyBind`, `ExecuteInGameThread`](https://docs.ue4ss.com/guides/creating-a-lua-mod.html). O `enabled.txt` foi confirmado pelo **log local** do UE4SS, não inferido dessa página.
- [Epic: cozinhar conteúdo por commandlet](https://dev.epicgames.com/documentation/unreal-engine/cooking-content-in-unreal-engine). O caminho `Saved/Cooked/Windows` foi **observado nesta máquina**, embora a documentação geral mostre variantes.
- [Epic: `UGameplayStatics::OpenLevel`](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/Kismet/UGameplayStatics/OpenLevel?application_version=5.5).
- [Epic: `AGameModeBase::RestartPlayer` e `DefaultPawnClass`](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/AGameModeBase).
- [Epic: criar/exibir UMG no viewport](https://dev.epicgames.com/documentation/unreal-engine/creating-widgets-in-unreal-engine).
- Caminho de `Willie_BP_C`, presença do `BP_HalfSwordGameMode_C`, `DefaultPawnClass=none` e resultado `pawn=Willie_BP_C` vieram de **arquivos locais e logs do jogo**, principalmente `UE4SS.log`, não das páginas oficiais. São específicos deste build. Não presumir após atualização do Half Sword.

## Segurança, rollback e limites

Trabalhar apenas no jogo instalado pelo usuário e nos nossos assets. Não tocar paks originais, não tentar obter chave de criptografia, não mexer em anticheat, não incluir conteúdo proprietário no projeto. Outros mods UE4SS do usuário estão ativos; preservar todos. Para desativar nosso teste, fechar o jogo e mover para fora da instalação **somente** `Z_HalfOpenWorldV1_Test.pak` e a pasta `HalfSwordBridge`. Não apagar saves, `mods.txt`, projeto ou caches amplos. A instalação já pode ter sessão em andamento com versão Lua anterior à fonte salva.

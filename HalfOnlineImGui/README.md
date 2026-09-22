# HalfOnlineImGui

Plugin C++ opcional para UE4SS, assinado: shokk.

Ele usa o ImGui já embutido no UE4SS e registra a aba `Half Online` com:

- estado da última ação;
- spawn de marcador de bot;
- spawn de marcador de item;
- limpeza dos marcadores.

O plugin escreve apenas `mp_openworld_control.txt`. A execução continua no
bridge Lua, no game thread, para evitar chamadas de engine no callback de UI.

## Compilação

Compile contra os headers/libs da mesma build do UE4SS instalada no jogo
(UE4SS 3.x/RE-UE4SS compatível). O guia oficial exige `UE4SS_ENABLE_IMGUI()`
antes de `register_tab`; omitir isso pode causar crash ao renderizar.

Depois copie a DLL para `ue4ss/Mods/HalfOnlineImGui/dlls/` e crie
`ue4ss/Mods/HalfOnlineImGui/enabled.txt`. Não use uma DLL compilada para outra
versão do UE4SS.

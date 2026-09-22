@echo off
setlocal
where cl >nul 2>nul
if errorlevel 1 (
  echo Visual C++ nao encontrado.
  echo Instale Visual Studio Build Tools com o workload Desktop development with C++.
  echo Depois abra o Developer Command Prompt e execute este arquivo novamente.
  exit /b 1
)
if not exist include\Mod\CppUserModBase.hpp (
  echo SDK do UE4SS nao encontrado em HalfOnlineImGui\include.
  echo Copie os headers da mesma build do UE4SS para esta pasta antes de compilar.
  exit /b 2
)
cl /std:c++20 /EHsc /LD HalfOnlineImGui.cpp /I include /Fe:HalfOnlineImGui.dll
if errorlevel 1 exit /b 3
echo DLL criada. Copie para ue4ss\Mods\HalfOnlineImGui\dlls\

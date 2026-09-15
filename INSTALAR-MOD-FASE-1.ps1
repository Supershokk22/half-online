$ErrorActionPreference = 'Stop'

$source = Join-Path $PSScriptRoot 'HalfSwordOnlineRealMod'
$mods = 'C:\Program Files (x86)\Steam\steamapps\common\Half Sword\HalfswordUE5\Binaries\Win64\ue4ss\Mods'
$destination = Join-Path $mods 'HalfSwordOnlineRealMod'
$modsList = Join-Path $mods 'mods.txt'

if (-not (Test-Path $source)) { throw "Mod de fase 1 nao encontrado: $source" }
if (-not (Test-Path $mods)) { throw "Pasta UE4SS Mods nao encontrada: $mods" }
if (-not (Test-Path $modsList)) { throw "mods.txt nao encontrado: $modsList" }

Copy-Item $modsList "$modsList.bak" -Force
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item (Join-Path $source '*') $destination -Recurse -Force

$entry = 'HalfSwordOnlineRealMod : 1'
$content = Get-Content $modsList
if ($content -match '^HalfSwordOnlineRealMod\s*:\s*[01]\s*$') {
    $content = $content -replace '^HalfSwordOnlineRealMod\s*:\s*[01]\s*$', $entry
} else {
    $content += $entry
}

# This replaces the older screen-streaming prototype during the controlled
# real-multiplayer test; the original mods.txt is retained as .bak.
$content = $content -replace '^HalfSwordOnlineMod\s*:\s*1\s*$', 'HalfSwordOnlineMod : 0'
$content | Set-Content -Path $modsList

Write-Host ''
Write-Host 'Mod de movimento multiplayer instalado.' -ForegroundColor Green
Write-Host "Backup criado: $modsList.bak"
Write-Host 'Abra o launcher, hospede/entre na sala e depois abra o Half Sword.'

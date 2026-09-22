-- Half Open World V1: opt-in map test inside Half Sword.
-- Ctrl+F8 opens the custom map; nothing changes until the key is pressed.
local map = "/Game/HalfOpenWorld/Maps/L_World_V1"
local fallback_map = "/Game/Maps/Arenas/Map_Arena_Yard"
local willie_class_path = "/Game/Character/Blueprints/Willie_BP.Willie_BP_C"
local UEHelpers = require("UEHelpers")
local attempted_world = nil
local travel_pending = false
local admin_enabled = false
local base = os.getenv("LOCALAPPDATA")
local online_bridge = (base or ".") .. "\\HalfSwordUE5\\Saved\\HalfSwordOnlineReal"
local last_control_command = ""
local control_retry_count = 0
local admin_spawns = {}

local function describe(object)
    if not object or not object:IsValid() then return "none" end
    return object:GetFullName()
end

local function report_state(stage)
    local controller = UEHelpers.GetPlayerController()
    local world = UEHelpers.GetWorld()
    local mode = UEHelpers.GetGameModeBase()
    local pawn = controller:IsValid() and controller.Pawn or nil
    print("[HalfOpenWorldV1] " .. stage .. " world=" .. describe(world)
        .. " mode=" .. describe(mode) .. " controller=" .. describe(controller)
        .. " pawn=" .. describe(pawn) .. "\n")
end

local function is_custom_world(world)
    return world and world:IsValid() and world:GetFullName():find(map, 1, true) ~= nil
end

local function admin_log(message)
    print("[HalfOpenWorldV1][ADMIN] " .. message .. "\n")
    local controller = UEHelpers.GetPlayerController()
    if controller and controller:IsValid() then
        pcall(function() controller:ClientMessage("[OW ADMIN] " .. message) end)
    end
end

local function admin_help()
    admin_log("Painel admin V0 - assinado: shokk")
    admin_log("Ctrl+Num1 spawn bot proxy | Ctrl+Num2 spawn item proxy | Ctrl+Num3 limpar spawns")
    admin_log("Ctrl+F8 entrar lobby | Ctrl+F11 voltar | Ctrl+F12 descobrir classes nativas")
    admin_log("Spawn de bot/item fica bloqueado ate uma classe nativa valida ser confirmada para evitar T-pose/trava.")
end

local function local_role()
    local file = io.open(online_bridge .. "\\mp_role.txt", "r")
    if not file then return "" end
    local role = (file:read("*l") or ""):lower()
    file:close()
    return role
end

local function is_room_admin()
    return local_role() == "host"
end

local function get_player_location(offset_x, offset_y, offset_z)
    local controller = UEHelpers.GetPlayerController()
    local pawn = controller and controller:IsValid() and controller.Pawn or nil
    if pawn and pawn:IsValid() then
        local loc = pawn:K2_GetActorLocation()
        return { X = loc.X + offset_x, Y = loc.Y + offset_y, Z = loc.Z + offset_z }
    end
    return { X = offset_x, Y = offset_y, Z = offset_z + 180 }
end

local function setup_proxy_mesh(actor, scale)
    local mesh = StaticFindObject("/Game/HalfOpenWorld/Geometry/SM_Block.SM_Block")
    if not mesh or not mesh:IsValid() then
        LoadAsset("/Game/HalfOpenWorld/Geometry/SM_Block.SM_Block")
        mesh = StaticFindObject("/Game/HalfOpenWorld/Geometry/SM_Block.SM_Block")
    end
    local component_class = StaticFindObject("/Script/Engine.StaticMeshComponent")
    local component = component_class and actor:GetComponentByClass(component_class) or nil
    if component and component:IsValid() and mesh and mesh:IsValid() then
        component:SetStaticMesh(mesh)
    end
    actor:SetActorScale3D(scale)
    actor:SetActorEnableCollision(true)
end

local function spawn_admin_proxy(kind)
    if not is_room_admin() then
        admin_log("Apenas o host/admin da sala pode spawnar.")
        return
    end
    local world = UEHelpers.GetWorld()
    if not is_custom_world(world) then
        admin_log("Spawn recusado: entre no lobby Open World primeiro.")
        return
    end
    local class = StaticFindObject("/Script/Engine.StaticMeshActor")
    if not class or not class:IsValid() then
        admin_log("StaticMeshActor indisponivel.")
        return
    end
    local offset = kind == "item" and { 160, 80, 80 } or { 260, 0, 160 }
    local transform = {
        Translation = get_player_location(offset[1], offset[2], offset[3]),
        Rotation = { Pitch = 0, Yaw = 0, Roll = 0 },
        Scale3D = { X = 1, Y = 1, Z = 1 }
    }
    local ok, actor = pcall(function() return world:SpawnActor(class, transform, {}) end)
    if ok and actor and actor:IsValid() then
        if kind == "item" then
            setup_proxy_mesh(actor, { X = 0.45, Y = 0.45, Z = 0.45 })
            admin_log("Item proxy spawnado.")
        else
            setup_proxy_mesh(actor, { X = 0.8, Y = 0.8, Z = 1.8 })
            admin_log("Bot proxy spawnado.")
        end
        table.insert(admin_spawns, actor)
    else
        admin_log("Spawn falhou: " .. tostring(actor))
    end
end

local function clear_admin_spawns()
    if not is_room_admin() then
        admin_log("Apenas o host/admin da sala pode limpar spawns.")
        return
    end
    local removed = 0
    for _, actor in ipairs(admin_spawns) do
        if actor and actor:IsValid() then
            pcall(function() actor:K2_DestroyActor() end)
            removed = removed + 1
        end
    end
    admin_spawns = {}
    admin_log("Spawns removidos: " .. tostring(removed))
end

local function discover_loaded_classes()
    local keywords = {
        "ai", "bot", "enemy", "npc", "willie", "weapon", "sword", "axe", "shield", "item"
    }
    local seen = {}
    local printed = 0
    local ok, actors = pcall(FindAllOf, "Actor")
    if not ok or not actors then
        admin_log("FindAllOf('Actor') indisponivel; entre no mapa ou reinicie com UE4SS ativo.")
        return
    end
    admin_log("Discovery iniciado. Atores carregados: " .. tostring(#actors))
    for _, actor in ipairs(actors) do
        local ok_name, class_name = pcall(function() return actor:GetClass():GetName() end)
        if ok_name and class_name and not seen[class_name] then
            local lower = string.lower(class_name)
            for _, keyword in ipairs(keywords) do
                if lower:find(keyword, 1, true) then
                    seen[class_name] = true
                    printed = printed + 1
                    admin_log("Classe candidata: " .. class_name .. " | " .. describe(actor))
                    break
                end
            end
        end
        if printed >= 40 then break end
    end
    if printed == 0 then
        admin_log("Nenhuma classe candidata encontrada nesta cena. Abra arena/treino/luta e rode Ctrl+F12 de novo.")
    else
        admin_log("Discovery completo. Envie as linhas [HalfOpenWorldV1][ADMIN] para escolhermos spawns reais.")
    end
end

local function open_level(level_path, label)
    local controller = UEHelpers.GetPlayerController()
    if not controller or not controller:IsValid() then
        if control_retry_count == 0 or control_retry_count % 10 == 0 then
            print("[HalfOpenWorldV1] No player controller yet; waiting for game lobby/free mode.\n")
        end
        return false
    end
    print("[HalfOpenWorldV1] Opening " .. label .. " (" .. level_path .. ")\n")
    UEHelpers.GetGameplayStatics():OpenLevel(controller, UEHelpers.AddFName(level_path), true, "")
    return true
end

local function enter_openworld()
    local world = UEHelpers.GetWorld()
    if travel_pending or is_custom_world(world) then
        print("[HalfOpenWorldV1] Already opening or inside custom map.\n")
        return true
    end
    travel_pending = true
    report_state("before travel")
    if open_level(map, "Half Open World V1") then
        wait_for_map(1)
        return true
    else
        travel_pending = false
        return false
    end
end

local function handle_external_control(command)
    if command == "" or command == last_control_command then return end
    if command == "openworld start" then
        if control_retry_count == 0 then
            print("[HalfOpenWorldV1] Multiplayer lobby requested Open World start.\n")
        end
        control_retry_count = control_retry_count + 1
        if enter_openworld() then
            last_control_command = command
            control_retry_count = 0
        end
    elseif command:find("openworld return", 1, true) == 1 then
        last_control_command = command
        control_retry_count = 0
        print("[HalfOpenWorldV1] Multiplayer lobby requested native return.\n")
        attempted_world = nil
        travel_pending = false
        report_state("before return")
        open_level(fallback_map, "Half Sword training yard")
    elseif command:find("game spawn_bot", 1, true) == 1 then
        last_control_command = command
        spawn_admin_proxy("bot")
    elseif command:find("game spawn_item", 1, true) == 1 then
        last_control_command = command
        spawn_admin_proxy("item")
    elseif command:find("game clear_spawns", 1, true) == 1 then
        last_control_command = command
        clear_admin_spawns()
    end
end

local function poll_external_control()
    ExecuteWithDelay(500, function()
        ExecuteInGameThread(function()
            local ok, err = pcall(function()
                local file = io.open(online_bridge .. "\\mp_game_control.txt", "r")
                if file then
                    local command = (file:read("*l") or ""):lower()
                    file:close()
                    handle_external_control(command)
                end
            end)
            if not ok then print("[HalfOpenWorldV1] Control poll failed: " .. tostring(err) .. "\n") end
            poll_external_control()
        end)
    end)
end

local function try_native_respawn()
    local ok, err = pcall(function()
            local world = UEHelpers.GetWorld()
            if not is_custom_world(world) then
                print("[HalfOpenWorldV1] Respawn refused outside custom map.\n")
                return
            end
            local controller = UEHelpers.GetPlayerController()
            local mode = UEHelpers.GetGameModeBase()
            if not controller:IsValid() or not mode:IsValid() then
                print("[HalfOpenWorldV1] Respawn unavailable: controller or mode missing.\n")
                return
            end
            if controller.Pawn and controller.Pawn:IsValid() then
                print("[HalfOpenWorldV1] Respawn skipped: pawn already exists.\n")
                return
            end
            local mode_instance = mode:GetFullName()
            if attempted_world == mode_instance then
                print("[HalfOpenWorldV1] Respawn already attempted in this map instance.\n")
                return
            end
            attempted_world = mode_instance
            local native_class = StaticFindObject(willie_class_path)
            if not native_class or not native_class:IsValid() then
                LoadAsset(willie_class_path)
                native_class = StaticFindObject(willie_class_path)
            end
            if not native_class or not native_class:IsValid() then
                print("[HalfOpenWorldV1] Willie native class unavailable.\n")
                return
            end
            mode.DefaultPawnClass = native_class
            print("[HalfOpenWorldV1] DefaultPawnClass set to " .. describe(mode.DefaultPawnClass) .. "\n")
            mode:RestartPlayer(controller)
            report_state("after native restart")
    end)
    if not ok then print("[HalfOpenWorldV1] Native restart failed: " .. tostring(err) .. "\n") end
end

local function wait_for_map(attempt)
    ExecuteWithDelay(1000, function()
        ExecuteInGameThread(function()
            local world = UEHelpers.GetWorld()
            if is_custom_world(world) then
                travel_pending = false
                try_native_respawn()
            elseif attempt < 10 then
                wait_for_map(attempt + 1)
            else
                travel_pending = false
                print("[HalfOpenWorldV1] Map did not load within 10 seconds.\n")
            end
        end)
    end)
end

RegisterKeyBind(Key.F8, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        local ok, err = pcall(function()
            enter_openworld()
        end)
        if not ok then
            travel_pending = false
            print("[HalfOpenWorldV1] Map launch failed: " .. tostring(err) .. "\n")
        end
    end)
end)

RegisterKeyBind(Key.F9, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        local ok, err = pcall(function() report_state("manual diagnostic") end)
        if not ok then print("[HalfOpenWorldV1] Diagnostic failed: " .. tostring(err) .. "\n") end
    end)
end)

RegisterKeyBind(Key.F7, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        admin_enabled = not admin_enabled
        admin_log("Painel admin " .. (admin_enabled and "ON" or "OFF"))
        if admin_enabled then admin_help() end
    end)
end)

RegisterKeyBind(Key.Num1, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        local ok, err = pcall(function() spawn_admin_proxy("bot") end)
        if not ok then admin_log("Spawn bot falhou: " .. tostring(err)) end
    end)
end)

RegisterKeyBind(Key.Num2, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        local ok, err = pcall(function() spawn_admin_proxy("item") end)
        if not ok then admin_log("Spawn item falhou: " .. tostring(err)) end
    end)
end)

RegisterKeyBind(Key.Num3, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        local ok, err = pcall(clear_admin_spawns)
        if not ok then admin_log("Limpar spawns falhou: " .. tostring(err)) end
    end)
end)

RegisterKeyBind(Key.F12, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        local ok, err = pcall(discover_loaded_classes)
        if not ok then admin_log("Discovery falhou: " .. tostring(err)) end
    end)
end)

-- Safe exit back to the native training/yard arena observed in this build.
RegisterKeyBind(Key.F11, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        local ok, err = pcall(function()
            attempted_world = nil
            travel_pending = false
            report_state("before return")
            open_level(fallback_map, "Half Sword training yard")
        end)
        if not ok then print("[HalfOpenWorldV1] Return failed: " .. tostring(err) .. "\n") end
    end)
end)

-- Manual fallback: never runs outside our map.
RegisterKeyBind(Key.F10, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(try_native_respawn)
end)

poll_external_control()
print("[HalfOpenWorldV1] Bridge loaded. Ctrl+F7 admin, Ctrl+F8 opens map, Ctrl+F9 diagnoses, Ctrl+F10 respawns, Ctrl+F11 returns, Ctrl+F12 discovers spawn classes. Multiplayer launcher can request Open World lobby.\n")

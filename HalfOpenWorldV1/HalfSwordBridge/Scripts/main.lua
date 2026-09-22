-- Half Open World V1: opt-in map test inside Half Sword.
-- Ctrl+F8 opens the custom map; nothing changes until the key is pressed.
local map = "/Game/HalfOpenWorld/Maps/L_World_V1"
local fallback_map = "/Game/Maps/Arenas/Map_Arena_Yard"
local willie_class_path = "/Game/Character/Blueprints/Willie_BP.Willie_BP_C"
local UEHelpers = require("UEHelpers")
local attempted_world = nil
local travel_pending = false
local admin_enabled = false
local last_panel_toggle = 0
local base = os.getenv("LOCALAPPDATA")
local online_bridge = (base or ".") .. "\\HalfSwordUE5\\Saved\\HalfSwordOnlineReal"
local last_control_command = ""
local consumed_openworld_session = ""
local control_retry_count = 0
local admin_spawns = {}
local current_session
-- Keep file-bridge polling light.  A 500 ms callback queue can survive map
-- teardown and leave stale game-thread callbacks during UE5 renderer shutdown.
local control_poll_interval_ms = 2000
-- Forward declaration: Lua only closes over locals that already exist.
-- `enter_openworld` calls this after travel, so it must be declared first.
local wait_for_map

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

local function screen_notice(message, duration, key_name)
    local world = UEHelpers.GetWorld()
    if not world or not world:IsValid() then return end
    local kismet = UEHelpers.GetKismetSystemLibrary()
    if not kismet or not kismet:IsValid() then return end
    local ok, err = pcall(function()
        -- PrintString requires all seven UE parameters.  A stable FName lets
        -- the panel replace itself instead of filling the screen with lines.
        kismet:PrintString(
            world,
            "[HALF ONLINE] " .. message,
            true,
            true,
            { R = 1.0, G = 0.72, B = 0.15, A = 1.0 },
            duration or 5.0,
            UEHelpers.AddFName(key_name or "HalfOnlineNotice")
        )
    end)
    if not ok then
        print("[HalfOpenWorldV1][HUD] PrintString failed: " .. tostring(err) .. "\n")
    end
end

local function admin_log(message)
    print("[HalfOpenWorldV1][ADMIN] " .. message .. "\n")
    screen_notice(message, 5.0, "HalfOnlineNotice")
    local controller = UEHelpers.GetPlayerController()
    if controller and controller:IsValid() then
        pcall(function() controller:ClientMessage("[OW ADMIN] " .. message) end)
    end
end

local function session_label()
    local session = current_session()
    if not session then return "SEM SALA CONFIRMADA" end
    return string.upper(session.role) .. " | jogadores " .. tostring(session.players)
end

local function show_admin_panel()
    screen_notice(
        "PAINEL ADMIN  |  " .. session_label() .. "\n"
        .. "Ctrl+1 bot marcador  |  Ctrl+2 item marcador  |  Ctrl+3 limpar\n"
        .. "Ctrl+Space salto  |  Ctrl+X esquiva  |  Ctrl+C salto acrobatico\n"
        .. "Ctrl+F9 diagnostico  |  Ctrl+F10 restaurar  |  Ctrl+F11 arena\n"
        .. "Ctrl+F7 fechar painel",
        120.0,
        "HalfOnlineAdminPanel"
    )
    local controller = UEHelpers.GetPlayerController()
    if controller and controller:IsValid() then
        pcall(function() controller:ClientMessage("[HALF ONLINE] Painel admin ativo — " .. session_label()) end)
    end
end

local function hide_admin_panel()
    screen_notice(" ", 0.01, "HalfOnlineAdminPanel")
end

local function admin_help()
    print("[HalfOpenWorldV1][ADMIN] Painel admin V0 - assinado: shokk\n")
    print("[HalfOpenWorldV1][ADMIN] Ctrl+1 bot | Ctrl+2 item | Ctrl+3 limpar | Ctrl+F10 jogador | Ctrl+F11 arena\n")
end

current_session = function()
    local file = io.open(online_bridge .. "\\mp_session.txt", "r")
    if not file then return nil end
    local line = file:read("*l") or ""
    file:close()
    -- v2 <session> <role> <room> <expires> <players> openworld-v1
    local version, session, role, room, expires, players, world_tag = line:match("^(%S+)%s+(%S+)%s+(%S+)%s+(%S+)%s+(%S+)%s+(%S+)%s+(%S+)$")
    expires = tonumber(expires)
    if version ~= "v2" or not session or (role ~= "host" and role ~= "client")
        or not expires or expires < os.time() or world_tag ~= "openworld-v1" then
        return nil
    end
    return { id = session, role = role, room = room, players = tonumber(players) or 0 }
end

local function is_room_admin()
    local session = current_session()
    if session then return session.role == "host" end
    -- Local map testing has no relay lease. Keep the admin tools available in
    -- that controlled offline map, while online clients still require a host
    -- lease and therefore cannot spawn anything by stale files.
    return is_custom_world(UEHelpers.GetWorld())
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

local function movement_action(kind)
    ExecuteInGameThread(function()
        local ok, err = pcall(function()
            local world = UEHelpers.GetWorld()
            local controller = UEHelpers.GetPlayerController()
            local pawn = controller and controller:IsValid() and controller.Pawn or nil
            if not is_custom_world(world) or not pawn or not pawn:IsValid() then
                admin_log("Movimento especial disponivel apenas no lobby com jogador carregado.")
                return
            end
            local forward = pawn:GetActorForwardVector()
            local velocity, label
            if kind == "jump" then
                velocity, label = { X = 0, Y = 0, Z = 520 }, "Salto"
            elseif kind == "dodge" then
                velocity, label = { X = forward.X * 650, Y = forward.Y * 650, Z = 90 }, "Esquiva para frente"
            else
                velocity, label = { X = forward.X * 380, Y = forward.Y * 380, Z = 360 }, "Salto acrobatico (sem montage)"
            end
            pawn:LaunchCharacter(velocity, true, true)
            admin_log(label .. " aplicado.")
        end)
        if not ok then admin_log("Movimento falhou: " .. tostring(err)) end
    end)
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
    else
        return false, "StaticMeshComponent ou SM_Block indisponivel"
    end
    actor:SetActorScale3D(scale)
    actor:SetActorEnableCollision(true)
    return true, "ok"
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
        local mesh_ok, mesh_reason
        if kind == "item" then
            mesh_ok, mesh_reason = setup_proxy_mesh(actor, { X = 0.45, Y = 0.45, Z = 0.45 })
            admin_log(mesh_ok and "Item proxy spawnado." or "Item criado, mas sem malha: " .. tostring(mesh_reason))
        else
            mesh_ok, mesh_reason = setup_proxy_mesh(actor, { X = 0.8, Y = 0.8, Z = 1.8 })
            admin_log(mesh_ok and "Bot proxy spawnado." or "Bot criado, mas sem malha: " .. tostring(mesh_reason))
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
    admin_log("Abrindo " .. label .. "...")
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
    local action, session_id = command:match("^(openworld%s+start)%s+(%S+)$")
    if action and session_id then
        local session = current_session()
        if not session or session.id ~= session_id then
            return
        end
        if consumed_openworld_session == session_id then
            last_control_command = command
            return
        end
        if control_retry_count == 0 then
            print("[HalfOpenWorldV1] Multiplayer lobby requested Open World start.\n")
        end
        control_retry_count = control_retry_count + 1
        if enter_openworld() then
            last_control_command = command
            consumed_openworld_session = session_id
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
    ExecuteWithDelay(control_poll_interval_ms, function()
        ExecuteInGameThread(function()
            local ok, err = pcall(function()
                local controller = UEHelpers.GetPlayerController()
                if not controller or not controller:IsValid() then
                    return
                end
                local file = io.open(online_bridge .. "\\mp_openworld_control.txt", "r")
                if file then
                    -- Session ids are case-sensitive URL-safe tokens; do not
                    -- lowercase the whole control line.
                    local command = file:read("*l") or ""
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

wait_for_map = function(attempt)
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
                admin_log("Mapa nao carregou em 10 segundos. Use Ctrl+F8 novamente.")
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
        local ok, err = pcall(function()
            report_state("manual diagnostic")
            admin_log("Diagnostico enviado ao log.")
        end)
        if not ok then print("[HalfOpenWorldV1] Diagnostic failed: " .. tostring(err) .. "\n") end
    end)
end)

RegisterKeyBind(Key.F7, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        local now = os.clock()
        if now - last_panel_toggle < 0.45 then return end
        last_panel_toggle = now
        admin_enabled = not admin_enabled
        admin_log("Painel admin " .. (admin_enabled and "ON" or "OFF"))
        if admin_enabled then
            show_admin_panel()
            admin_help()
        else
            hide_admin_panel()
        end
    end)
end)

local function bind_movement(key, action)
    if key then RegisterKeyBind(key, {ModifierKey.CONTROL}, action) end
end
-- Disabled by default while validating this shipping build. The functions
-- remain available for a confirmed key enum; registering unknown key objects
-- can crash UE4SS before the game reaches its first map.
-- bind_movement(Key.SPACE, function() movement_action("jump") end)
-- bind_movement(Key.X, function() movement_action("dodge") end)
-- bind_movement(Key.C, function() movement_action("acro") end)

local function admin_spawn_bot()
    ExecuteInGameThread(function()
        local ok, err = pcall(function() spawn_admin_proxy("bot") end)
        if not ok then admin_log("Spawn bot falhou: " .. tostring(err)) end
    end)
end

local function admin_spawn_item()
    ExecuteInGameThread(function()
        local ok, err = pcall(function() spawn_admin_proxy("item") end)
        if not ok then admin_log("Spawn item falhou: " .. tostring(err)) end
    end)
end

local function admin_clear_spawns()
    ExecuteInGameThread(function()
        local ok, err = pcall(clear_admin_spawns)
        if not ok then admin_log("Limpar spawns falhou: " .. tostring(err)) end
    end)
end

-- NUM_ONE/TWO/THREE are UE4SS's actual numpad names.  Bind the number row as
-- well, so the panel works on compact keyboards without a numeric keypad.
-- Spawn commands are exposed by the external launcher. Avoid registering
-- duplicate number bindings in this shipping build: UE4SS versions differ in
-- how they handle the same key with and without a modifier and can crash at
-- startup. The launcher writes the same bridge commands safely.

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
            admin_log("Voltando para a arena de treino...")
            report_state("before return")
            open_level(fallback_map, "Half Sword training yard")
        end)
        if not ok then print("[HalfOpenWorldV1] Return failed: " .. tostring(err) .. "\n") end
    end)
end)

-- Manual fallback: never runs outside our map.
RegisterKeyBind(Key.F10, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(function()
        admin_log("Tentando restaurar o jogador no lobby...")
        try_native_respawn()
    end)
end)

poll_external_control()
print("[HalfOpenWorldV1] Bridge loaded. Ctrl+F7 admin, Ctrl+F8 opens map, Ctrl+F9 diagnoses, Ctrl+F10 respawns, Ctrl+F11 returns, Ctrl+F12 discovers spawn classes. Admin spawn shortcuts: Ctrl+1/2/3 or Ctrl+Numpad 1/2/3. Multiplayer launcher can request Open World lobby.\n")

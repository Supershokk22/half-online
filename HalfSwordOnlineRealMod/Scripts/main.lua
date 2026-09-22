-- Half Online — v9 clean — assinado: shokk
-- Multiplayer bridge: pawn detection + position sync. No spam.

local MOD = "HalfOnline"
local REMOTE_CLASS_PATH = "/Game/Character/Blueprints/Willie_BP.Willie_BP_C"
local ALT_REMOTE_CLASS = "/Game/Maps/Map_Hub_Tavern_Frank.NewBlueprint_C"
local ARENA_MAP = "/Game/Maps/Arenas/Map_Arena_Cellar"
local OPENWORLD_MAP = "/Game/HalfOpenWorld/Maps/L_World_V1"
local OPENWORLD_PROXY_MESH = "/Game/HalfOpenWorld/Geometry/SM_Block.SM_Block"
-- Safe mode: runtime SpawnActor/DestroyActor is not stable in this Shipping build.
-- Keep networking alive, but wait for a native replicated pawn implementation.
local runtime_spawn_disabled = true
local base = os.getenv("LOCALAPPDATA")
local BRIDGE = (base or ".") .. "\\HalfSwordUE5\\Saved\\HalfSwordOnlineReal"
local state = { running = false, session = "", remotePawn = nil, botPawn = nil, spawnRequested = false, lastInbound = "", lastGameControl = "", lastStatus = 0, loadAttempts = 0, pawnStableCount = 0, lastRemotePosition = nil, lastRemoteTime = nil, last_cleanup = 0 }

local function log(message) print("[" .. MOD .. "] " .. message) end

local function valid(object)
    if not object then return false end
    local ok, value = pcall(function() return object:IsValid() end)
    return ok and value == true
end

local function getPlayerPawn()
    local controllers = FindAllOf("PlayerController")
    if not controllers then controllers = FindAllOf("Controller") end
    if not controllers then return nil, nil end
    for _, controller in ipairs(controllers) do
        if valid(controller) and controller.Pawn and valid(controller.Pawn) then
            local ok, controlled = pcall(function() return controller.Pawn:IsPlayerControlled() end)
            local okName, pawnName = pcall(function() return controller.Pawn:GetFullName() end)
            if ok and controlled then
                if okName and pawnName and not pawnName:find("Camera") and not pawnName:find("FreeCamera") then
                    return controller, controller.Pawn
                end
            end
        end
    end
    return nil, nil
end

local function writeOutbound(pawn)
    local ok, location, rotation = pcall(function() return pawn:K2_GetActorLocation(), pawn:K2_GetActorRotation() end)
    if not ok or not location or not rotation then return end
    local file = io.open(BRIDGE .. "\\mp_outbound.txt", "w")
    if not file then return end
    file:write(string.format("state %.4f %.4f %.4f %.4f %.4f %.4f\n", location.X, location.Y, location.Z, rotation.Pitch, rotation.Yaw, rotation.Roll))
    file:close()
end

local function parseInbound()
    local file = io.open(BRIDGE .. "\\mp_inbound.txt", "r")
    if not file then return nil end
    local line = file:read("*l") or ""
    file:close()
    if line == "" or line == state.lastInbound then return nil end
    local x, y, z, pitch, yaw, roll = line:match("^state%s+([%-%d%.]+)%s+([%-%d%.]+)%s+([%-%d%.]+)%s+([%-%d%.]+)%s+([%-%d%.]+)%s+([%-%d%.]+)$")
    if not x then return nil end
    state.lastInbound = line
    return { tonumber(x), tonumber(y), tonumber(z), tonumber(pitch), tonumber(yaw), tonumber(roll) }
end

local function getRemoteClass()
    local cls = StaticFindObject(REMOTE_CLASS_PATH)
    if valid(cls) then return cls end
    cls = StaticFindObject(ALT_REMOTE_CLASS)
    if valid(cls) then return cls end
    return nil
end

local function findInitializedOpponent(localPawn)
    local candidates = FindAllOf("Willie_BP_C") or {}
    local alt = FindAllOf("NewBlueprint_C")
    if alt then for _, actor in ipairs(alt) do table.insert(candidates, actor) end end
    for _, actor in ipairs(candidates) do
        if valid(actor) and actor ~= localPawn and actor ~= state.botPawn then
            local playerControlled = false
            pcall(function() playerControlled = actor:IsPlayerControlled() end)
            if not playerControlled then return actor end
        end
    end
    return nil
end

local function activeSession()
    local file = io.open(BRIDGE .. "\\mp_session.txt", "r")
    if not file then return nil end
    local line = file:read("*l") or ""
    file:close()
    local version, session, role, room, expires, players, tag = line:match("^(%S+)%s+(%S+)%s+(%S+)%s+(%S+)%s+(%S+)%s+(%S+)%s+(%S+)$")
    if version ~= "v2" or not session or (role ~= "host" and role ~= "client")
        or not tonumber(expires) or tonumber(expires) < os.time() or tag ~= "openworld-v1" then
        return nil
    end
    return session
end

local function isOpenWorld()
    local ok, world = pcall(function()
        local helpers = require("UEHelpers")
        return helpers.GetWorld()
    end)
    if not ok or not valid(world) then return false end
    local okName, name = pcall(function() return world:GetFullName() end)
    return okName and name and name:find(OPENWORLD_MAP, 1, true) ~= nil
end

local function getOpenWorldProxyClass()
    local cls = StaticFindObject("/Script/Engine.StaticMeshActor")
    return valid(cls) and cls or nil
end

local function setupOpenWorldProxy(actor)
    pcall(function()
        local mesh = StaticFindObject(OPENWORLD_PROXY_MESH)
        if not valid(mesh) then
            LoadAsset(OPENWORLD_PROXY_MESH)
            mesh = StaticFindObject(OPENWORLD_PROXY_MESH)
        end
        local component = actor:GetComponentByClass(StaticFindObject("/Script/Engine.StaticMeshComponent"))
        if valid(component) and valid(mesh) then
            component:SetStaticMesh(mesh)
        end
        actor:SetActorScale3D({ X = 0.9, Y = 0.9, Z = 2.0 })
        actor:SetActorEnableCollision(false)
    end)
end

local function claimRemoteAvatar(localPawn)
    if valid(state.remotePawn) or not valid(localPawn) then return valid(state.remotePawn) end
    if isOpenWorld() then
        if runtime_spawn_disabled then
            log("Avatar remoto adiado: SpawnActor desativado no modo seguro")
            return false
        end
        local world, class = localPawn:GetWorld(), getOpenWorldProxyClass()
        if not valid(world) or not valid(class) then return false end
        local here = localPawn:K2_GetActorLocation()
        local rotation = localPawn:K2_GetActorRotation()
        local transform = { Translation = { X = here.X + 260, Y = here.Y, Z = here.Z }, Rotation = rotation, Scale3D = { X = 1, Y = 1, Z = 1 } }
        local ok, actor = pcall(function() return world:SpawnActor(class, transform, {}) end)
        if ok and valid(actor) then
            state.remotePawn = actor
            setupOpenWorldProxy(actor)
            state.lastRemotePosition = nil
            state.lastRemoteTime = nil
            log("Avatar remoto Open World criado como proxy leve de lobby")
            return true
        end
        return false
    end
    local actor = findInitializedOpponent(localPawn)
    if not valid(actor) then return false end

    -- Reuse the opponent created by Spar. Its skeletal mesh, animation blueprint,
    -- collision and physics have already passed through the game's normal setup.
    -- A raw SpawnActor here is what produced the frozen T-pose proxy.
    pcall(function()
        local controller = actor.Controller
        if valid(controller) then
            pcall(function() controller:StopMovement() end)
            pcall(function() controller:UnPossess() end)
        end
        actor:SetActorEnableCollision(true)
    end)
    state.remotePawn = actor
    state.lastRemotePosition = nil
    state.lastRemoteTime = nil
    log("Adversario conectado com animacao e fisica nativas!")
    return true
end

local function destroyActor(actor)
    if not valid(actor) then return end
    -- Static lobby proxies must not be destroyed from a Lua callback: UE5 can
    -- release their render resource on the wrong thread (RenderResource.cpp).
    if isOpenWorld() then
        pcall(function() actor:SetActorHiddenInGame(true) end)
        pcall(function() actor:SetActorEnableCollision(false) end)
    else
        pcall(function() actor:K2_DestroyActor() end)
    end
end

local function spawnPracticeOpponent(localPawn)
    if runtime_spawn_disabled then
        log("Bot de pratica nao criado: SpawnActor desativado no modo seguro")
        return
    end
    if valid(state.botPawn) or not valid(localPawn) then return end
    ExecuteInGameThread(function()
        local world, class = localPawn:GetWorld(), getRemoteClass()
        if not valid(world) or not valid(class) then return end
        local here = localPawn:K2_GetActorLocation()
        local rotation = localPawn:K2_GetActorRotation()
        local transform = { Translation = { X = here.X + 260, Y = here.Y, Z = here.Z }, Rotation = rotation, Scale3D = { X = 1, Y = 1, Z = 1 } }
        local ok, actor = pcall(function() return world:SpawnActor(class, transform, {}) end)
        if ok and valid(actor) then state.botPawn = actor end
    end)
end

local function clearNativeSparOpponents(localPawn)
    local candidates = FindAllOf("Willie_BP_C")
    if not candidates then candidates = {} end
    local alt = FindAllOf("NewBlueprint_C")
    if alt then for _, a in ipairs(alt) do table.insert(candidates, a) end end
    local removed = 0
    for _, actor in ipairs(candidates) do
        if valid(actor) and actor ~= localPawn and actor ~= state.remotePawn and actor ~= state.botPawn then
            local playerControlled = false
            pcall(function() playerControlled = actor:IsPlayerControlled() end)
            if not playerControlled then destroyActor(actor); removed = removed + 1 end
        end
    end
    if removed > 0 then log("Bots removidos: " .. removed) end
end

local function applyGameControl(localPawn)
    local file = io.open(BRIDGE .. "\\mp_game_control.txt", "r")
    if not file then return end
    local command = (file:read("*l") or ""):lower()
    file:close()
    if command == "" or command == state.lastGameControl then return end
    state.lastGameControl = command
    if command == "remote remove" then
        destroyActor(state.remotePawn); state.remotePawn = nil; state.spawnRequested = false; state.lastInbound = ""
        log("Adversario saiu da sala")
    elseif command == "spar clear" then
        clearNativeSparOpponents(localPawn)
    end
end

local function applyInbound(localPawn)
    local packet = parseInbound()
    if not packet then return end
    if not valid(state.remotePawn) and not claimRemoteAvatar(localPawn) then
        -- Keep the packet eligible for a retry while the Spar pawn finishes loading.
        state.lastInbound = ""
        return
    end
    local now = os.clock()
    if state.lastRemotePosition and state.lastRemoteTime then
        local dt = now - state.lastRemoteTime
        if dt > 0.001 then
            local velocity = {
                X = (packet[1] - state.lastRemotePosition[1]) / dt,
                Y = (packet[2] - state.lastRemotePosition[2]) / dt,
                Z = (packet[3] - state.lastRemotePosition[3]) / dt,
            }
            pcall(function()
                if state.remotePawn.CharacterMovement then
                    state.remotePawn.CharacterMovement.Velocity = velocity
                end
            end)
        end
    end
    pcall(function()
        state.remotePawn:K2_SetActorLocationAndRotation({ X = packet[1], Y = packet[2], Z = packet[3] }, { Pitch = packet[4], Yaw = packet[5], Roll = packet[6] }, true, {}, false)
    end)
    state.lastRemotePosition = { packet[1], packet[2], packet[3] }
    state.lastRemoteTime = now
end

local function stopRound(reason)
    if not state.running then return end
    destroyActor(state.remotePawn)
    state.running, state.session, state.remotePawn = false, "", nil
    state.lastInbound, state.lastRemotePosition, state.lastRemoteTime = "", nil, nil
    log(reason or "Sessao multiplayer encerrada")
end

local function updateLoop()
    local session = activeSession()
    if not session then
        stopRound("Sessao multiplayer encerrada")
        ExecuteWithDelay(500, updateLoop)
        return
    end
    if not state.running or state.session ~= session then
        if state.running then stopRound("Sessao trocada") end
        state.running, state.session = true, session
        state.remotePawn, state.botPawn, state.spawnRequested, state.lastInbound, state.lastGameControl = nil, nil, false, "", ""
        state.lastRemotePosition, state.lastRemoteTime = nil, nil
        log("Sala confirmada. Aguardando jogador remoto...")
    end
    local controller, pawn = getPlayerPawn()
    if controller and pawn then
        writeOutbound(pawn)
        applyGameControl(pawn)
        applyInbound(pawn)
        -- Preserve the game's normal AI in Free Mode, Train and Arena.  The
        -- previous unconditional cleanup destroyed the only enemy every
        -- 100 ms, even when nobody was connected.  Only remove an initialized
        -- native spar bot after a real remote avatar has been claimed.
        if valid(state.remotePawn) and not isOpenWorld() and os.clock() - state.last_cleanup > 1.0 then
            clearNativeSparOpponents(pawn)
            state.last_cleanup = os.clock()
        end
    end
    -- 5 Hz is sufficient for the file bridge and avoids a full actor scan on
    -- every frame; rendering and native game physics remain untouched.
    ExecuteWithDelay(200, updateLoop)
end

ExecuteWithDelay(1000, updateLoop)
log("Mod carregado — aguardando sala confirmada pelo launcher")

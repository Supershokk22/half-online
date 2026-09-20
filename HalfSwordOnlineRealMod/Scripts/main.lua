-- Half Online — rebuild v8 — assinado: shokk
-- Auto-enter arena + multiplayer bridge (no menu needed).
-- Fix: detect NewBlueprint_C (hub/tavern) OR Willie_BP_C (arena/spar)

local MOD = "HalfSwordOnlineReal"
local REMOTE_CLASS_PATH = "/Game/Character/Blueprints/Willie_BP.Willie_BP_C"
local ALT_REMOTE_CLASS = "/Game/Maps/Map_Hub_Tavern_Frank.NewBlueprint_C"
local ARENA_MAP = "/Game/Maps/Arenas/Map_Arena_Cellar"
local base = os.getenv("LOCALAPPDATA")
local BRIDGE = (base or ".") .. "\\HalfSwordUE5\\Saved\\HalfSwordOnlineReal"
local state = { running = false, remotePawn = nil, botPawn = nil, spawnRequested = false, lastInbound = "", lastGameControl = "", lastStatus = 0, loadAttempts = 0, pawnStableCount = 0 }

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

local function spawnRemoteAvatar(localPawn, packet)
    if state.spawnRequested or not valid(localPawn) then return end
    state.spawnRequested = true
    ExecuteInGameThread(function()
        local world = localPawn:GetWorld()
        local class = getRemoteClass()
        if not valid(world) or not valid(class) then
            state.spawnRequested = false
            log("Remote avatar class or world unavailable")
            return
        end
        local transform = {
            Translation = { X = packet[1], Y = packet[2], Z = packet[3] },
            Rotation = { Pitch = packet[4], Yaw = packet[5], Roll = packet[6] },
            Scale3D = { X = 1, Y = 1, Z = 1 },
        }
        local ok, actor = pcall(function() return world:SpawnActor(class, transform, {}) end)
        if ok and valid(actor) then
            state.remotePawn = actor
            state.spawnRequested = false
            log("Remote avatar spawned - room connected")
        else
            state.spawnRequested = false
            log("Remote avatar spawn failed")
        end
    end)
end

local function destroyActor(actor)
    if valid(actor) then pcall(function() actor:K2_DestroyActor() end) end
end

local function spawnPracticeOpponent(localPawn)
    if valid(state.botPawn) or not valid(localPawn) then return end
    ExecuteInGameThread(function()
        local world, class = localPawn:GetWorld(), getRemoteClass()
        if not valid(world) or not valid(class) then log("Practice opponent class unavailable"); return end
        local here = localPawn:K2_GetActorLocation()
        local rotation = localPawn:K2_GetActorRotation()
        local transform = { Translation = { X = here.X + 260, Y = here.Y, Z = here.Z }, Rotation = rotation, Scale3D = { X = 1, Y = 1, Z = 1 } }
        local ok, actor = pcall(function() return world:SpawnActor(class, transform, {}) end)
        if ok and valid(actor) then state.botPawn = actor; log("Practice opponent added by host") end
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
    log("Native opponents removed: " .. tostring(removed))
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
        log("Remote avatar removed - room is empty")
    elseif command == "bot spawn" then
        spawnPracticeOpponent(localPawn)
    elseif command == "bot remove" then
        destroyActor(state.botPawn); state.botPawn = nil; log("Practice opponent removed by host")
    elseif command == "spar clear" then
        clearNativeSparOpponents(localPawn)
    end
end

local function applyInbound(localPawn)
    local packet = parseInbound()
    if not packet then return end
    if not valid(state.remotePawn) then spawnRemoteAvatar(localPawn, packet); return end
    pcall(function()
        state.remotePawn:K2_SetActorLocationAndRotation({ X = packet[1], Y = packet[2], Z = packet[3] }, { Pitch = packet[4], Yaw = packet[5], Roll = packet[6] }, false, {}, true)
    end)
end

local function updateLoop()
    if not state.running then return end
    local controller, pawn = getPlayerPawn()
    if controller and pawn then
        writeOutbound(pawn)
        applyGameControl(pawn)
        applyInbound(pawn)
        local now = os.clock()
        if now - state.lastStatus > 5 then state.lastStatus = now; log("Room bridge active - assinado: shokk") end
    end
    ExecuteWithDelay(100, updateLoop)
end

local function beginRound()
    if state.running then return end
    state.running = true
    state.remotePawn, state.botPawn, state.spawnRequested, state.lastInbound, state.lastGameControl = nil, nil, false, "", ""
    log("Player pawn detected — arena loaded, starting multiplayer bridge")
    ExecuteWithDelay(1200, function() log("Arena ready; multiplayer bridge starting"); updateLoop() end)
end

local function tryLoadArena()
    if state.running then return end
    local controller, pawn = getPlayerPawn()
    if pawn then
        state.pawnStableCount = state.pawnStableCount + 1
        if state.pawnStableCount >= 2 then
            log("Pawn stable — starting round (attempt " .. state.loadAttempts .. ")")
            beginRound()
            return
        end
    else
        state.pawnStableCount = 0
    end

    state.loadAttempts = state.loadAttempts + 1
    if state.loadAttempts > 60 then
        log("GAVE UP after 60 attempts — player must navigate menu manually")
        return
    end

    if state.loadAttempts % 10 == 1 then
        log("Attempt " .. state.loadAttempts .. " — no player pawn yet, sending console commands to load arena")
    end

    ExecuteInGameThread(function()
        pcall(function() ExecuteConsoleCommand("open " .. ARENA_MAP) end)
    end)
end

RegisterHook("/Script/Engine.PlayerController:ClientRestart", function() ExecuteInGameThread(function()
    local controller, pawn = getPlayerPawn()
    if pawn and not state.running then
        state.pawnStableCount = state.pawnStableCount + 1
        if state.pawnStableCount >= 2 then
            beginRound()
        end
    end
end) end)

ExecuteWithDelay(3000, function()
    log("Auto-load started — trying open command + pawn detection every 2s")
    local function autoLoadLoop()
        if state.running then return end
        tryLoadArena()
        if not state.running then ExecuteWithDelay(2000, autoLoadLoop) end
    end
    autoLoadLoop()
end)

log("Rebuild v8 loaded — auto-entering arena (no menu). assinado: shokk")

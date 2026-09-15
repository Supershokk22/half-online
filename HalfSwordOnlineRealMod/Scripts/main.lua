-- Half Sword Online Real Multiplayer — rebuild v2
-- Uses the ClientRestart + 100 ms lifecycle validated by BodyDamageHUD.

local MOD = "HalfSwordOnlineReal"
local REMOTE_CLASS_PATH = "/Game/Character/Blueprints/Willie_BP.Willie_BP_C"
local base = os.getenv("LOCALAPPDATA")
local BRIDGE = (base or ".") .. "\\HalfSwordUE5\\Saved\\HalfSwordOnlineReal"
local state = { running = false, remotePawn = nil, botPawn = nil, spawnRequested = false, lastInbound = "", lastGameControl = "", lastStatus = 0 }

local function log(message) print("[" .. MOD .. "] " .. message) end

local function valid(object)
    if not object then return false end
    local ok, value = pcall(function() return object:IsValid() end)
    return ok and value == true
end

local function getLocalPlayer()
    local controllers = FindAllOf("PlayerController")
    if not controllers then return nil, nil end
    for _, controller in ipairs(controllers) do
        if valid(controller) and controller.Player and controller.Player.ControllerId == 0 then
            local pawn = controller.Pawn
            if valid(pawn) then
                local ok, controlled = pcall(function() return pawn:IsPlayerControlled() end)
                if ok and controlled then return controller, pawn end
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

local function spawnRemoteAvatar(localPawn, packet)
    if state.spawnRequested or not valid(localPawn) then return end
    state.spawnRequested = true
    ExecuteInGameThread(function()
        local world = localPawn:GetWorld()
        local class = StaticFindObject(REMOTE_CLASS_PATH)
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
            log("Remote avatar spawned — room connected")
        else
            state.spawnRequested = false
            log("Remote avatar spawn failed")
        end
    end)
end

local function destroyActor(actor)
    if valid(actor) then pcall(function() actor:K2_DestroyActor() end) end
end

-- This is deliberately a stationary practice opponent.  It is not attached to
-- the game's unknown AI controller, so it cannot interfere with the host while
-- the room is empty or destabilize the round.
local function spawnPracticeOpponent(localPawn)
    if valid(state.botPawn) or not valid(localPawn) then return end
    ExecuteInGameThread(function()
        local world, class = localPawn:GetWorld(), StaticFindObject(REMOTE_CLASS_PATH)
        if not valid(world) or not valid(class) then log("Practice opponent class unavailable"); return end
        local here = localPawn:K2_GetActorLocation()
        local rotation = localPawn:K2_GetActorRotation()
        local transform = { Translation = { X = here.X + 260, Y = here.Y, Z = here.Z }, Rotation = rotation, Scale3D = { X = 1, Y = 1, Z = 1 } }
        local ok, actor = pcall(function() return world:SpawnActor(class, transform, {}) end)
        if ok and valid(actor) then state.botPawn = actor; log("Practice opponent added by host") end
    end)
end

-- Spar creates an unowned Willie pawn before a network peer exists.  The host
-- can explicitly remove only those unowned pawns; the local player, our
-- tracked practice pawn, and the tracked remote player are always preserved.
local function clearNativeSparOpponents(localPawn)
    local candidates = FindAllOf("Willie_BP_C")
    local removed = 0
    if candidates then
        for _, actor in ipairs(candidates) do
            if valid(actor) and actor ~= localPawn and actor ~= state.remotePawn and actor ~= state.botPawn then
                local playerControlled = false
                pcall(function() playerControlled = actor:IsPlayerControlled() end)
                if not playerControlled then destroyActor(actor); removed = removed + 1 end
            end
        end
    end
    log("Native Spar opponents removed: " .. tostring(removed))
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
        log("Remote avatar removed — room is empty")
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
    local controller, pawn = getLocalPlayer()
    if controller and pawn then
        writeOutbound(pawn)
        applyGameControl(pawn)
        applyInbound(pawn)
        local now = os.clock()
        if now - state.lastStatus > 5 then state.lastStatus = now; log("Room bridge active — assinado: shokk") end
    end
    ExecuteWithDelay(100, updateLoop)
end

local function beginRound()
    if state.running then return end
    state.running = true
    state.remotePawn, state.botPawn, state.spawnRequested, state.lastInbound, state.lastGameControl = nil, nil, false, "", ""
    ExecuteWithDelay(1200, function() log("Arena ready; multiplayer bridge starting"); updateLoop() end)
end

RegisterHook("/Script/Engine.PlayerController:ClientRestart", function() ExecuteInGameThread(beginRound) end)
log("Rebuild v2 loaded. Enter Free Mode to start the private room bridge.")

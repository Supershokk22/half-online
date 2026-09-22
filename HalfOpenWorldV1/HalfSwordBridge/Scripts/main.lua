-- Half Open World V1: opt-in map test inside Half Sword.
-- Ctrl+F8 opens the custom map; nothing changes until the key is pressed.
local map = "/Game/HalfOpenWorld/Maps/L_World_V1"
local willie_class_path = "/Game/Character/Blueprints/Willie_BP.Willie_BP_C"
local UEHelpers = require("UEHelpers")
local attempted_world = nil
local travel_pending = false

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

local function try_native_respawn()
    local ok, err = pcall(function()
            local world = UEHelpers.GetWorld()
            if not world:IsValid() or not world:GetFullName():find(map, 1, true) then
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
            if world:IsValid() and world:GetFullName():find(map, 1, true) then
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
            local controller = UEHelpers.GetPlayerController()
            local world = UEHelpers.GetWorld()
            if not controller or not controller:IsValid() then
                print("[HalfOpenWorldV1] No player controller; enter Free Mode first.\n")
                return
            end
            if travel_pending or (world:IsValid() and world:GetFullName():find(map, 1, true)) then
                print("[HalfOpenWorldV1] Already opening or inside custom map.\n")
                return
            end
            travel_pending = true
            report_state("before travel")
            print("[HalfOpenWorldV1] Opening " .. map .. "\n")
            UEHelpers.GetGameplayStatics():OpenLevel(controller, UEHelpers.AddFName(map), true, "")
            wait_for_map(1)
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

-- Manual fallback: never runs outside our map.
RegisterKeyBind(Key.F10, {ModifierKey.CONTROL}, function()
    ExecuteInGameThread(try_native_respawn)
end)

print("[HalfOpenWorldV1] Bridge loaded. Ctrl+F8 opens the test map.\n")

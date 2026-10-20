-- GameFrame MAME 0.289 local command bridge.
-- Fixed non-destructive whitelist. Never evaluates external Lua code.
local root = assert(os.getenv("GAMEFRAME_BRIDGE_DIR"), "GAMEFRAME_BRIDGE_DIR missing")
local sep = package.config:sub(1, 1)
if root:sub(-1) ~= sep then root = root .. sep end
local json = require("json")
local lfs = require("lfs")
local processed = {}
local pending_step = nil
local completed_frames = 0
emu.register_frame_done(function() completed_frames = completed_frames + 1 end, "frame")

local function frame_counter()
    local frames = {}
    local ok, err = pcall(function()
        for tag, screen in pairs(manager.machine.screens) do
            -- MAME versions may expose frame_number as a property or method.
            local success, n = pcall(function()
                local value = screen.frame_number
                if type(value) == "function" then return screen:frame_number() end
                return value
            end)
            if success and type(n) == "number" then
                frames[tostring(tag)] = n
            end
        end
    end)
    return frames, ok and nil or tostring(err)
end

local function input_catalog()
    local ports = {}
    local count = 0
    local ok, allports = pcall(function() return manager.machine.ioport.ports end)
    if not ok or not allports then return ports end
    pcall(function()
        for tag, port in pairs(allports) do
            local fields = {}
            pcall(function()
                for name, field in pairs(port.fields) do
                    fields[#fields + 1] = {name = tostring(name)}
                end
            end)
            ports[#ports + 1] = {tag = tostring(tag), fields = fields}
            count = count + 1
            if count >= 64 then break end
        end
    end)
    return ports
end

local function input_capabilities()
    local result = {}
    local ok, ports = pcall(function() return manager.machine.ioport.ports end)
    if not ok or not ports then return result end
    pcall(function()
        for tag, port in pairs(ports) do
            local fields = {}
            pcall(function()
                for name, field in pairs(port.fields) do
                    local entry = {name = tostring(name)}
                    for _, property in ipairs({"type", "player", "mask", "minvalue", "maxvalue", "defvalue", "value"}) do
                        local success, value = pcall(function() return field[property] end)
                        if success and (type(value) == "number" or type(value) == "string" or type(value) == "boolean") then
                            entry[property] = value
                        end
                    end
                    for _, method in ipairs({"set_value", "set_user_settings"}) do
                        local success, value = pcall(function() return field[method] end)
                        entry[method .. "_available"] = success and type(value) == "function"
                    end
                    fields[#fields + 1] = entry
                end
            end)
            result[#result + 1] = {tag = tostring(tag), fields = fields}
        end
    end)
    return result
end

local function respond(id, ok, info, err)
    local response = {id = id, ok = ok}
    if ok then response.info = info else response.error = tostring(err or "Unknown error") end
    local temporary = root .. "response_" .. id .. ".tmp"
    local final = root .. "response_" .. id .. ".json"
    local file = assert(io.open(temporary, "w"))
    file:write(json.stringify(response))
    file:close()
    local moved, why = os.rename(temporary, final)
    assert(moved, "Cannot publish MAME response: " .. tostring(why))
end

local function execute(action)
    if action == "status" then
        local frames, frame_error = frame_counter()
        if pending_step and manager.machine.paused then
            local moved = false
            for tag, previous in pairs(pending_step.before) do
                if type(frames[tag]) == "number" and frames[tag] > previous then moved = true end
            end
            if moved then pending_step = nil end
        end
        return {system = manager.machine.system.name,
                paused = manager.machine.paused,
                recording = manager.machine.video.is_recording,
                single_step_available = type(manager.ui.single_step) == "boolean",
                screen_frames = frames, screen_frame_error = frame_error,
                completed_frames = completed_frames,
                single_step_flag = manager.ui.single_step,
                step_pending = pending_step ~= nil}
    elseif action == "input_capabilities" then
        return {ports = input_capabilities()}
    elseif action == "list_inputs" then
        return {ports = input_catalog()}
    elseif action == "pause" then
        emu.pause()
        return {paused = true}
    elseif action == "resume" then
        emu.unpause()
        return {paused = false}
    elseif action == "step_once" then
        -- MAME 0.289 documented single_step flag pauses after next drawn frame.
        -- Verify actual frame delta against system-specific screen counters.
        if type(manager.ui.single_step) ~= "boolean" then
            error("UI single_step is not available in this MAME build")
        end
        if pending_step ~= nil then error("Previous step not yet observed; do not overlap step commands") end
        local baseline = frame_counter()
        pending_step = {before = baseline}
        if type(emu.step) == "function" then
            emu.step()
        else
            manager.ui.single_step = true
            emu.unpause()
        end
        return {step_requested = true, frame_advance_confirmed = false}
    elseif action == "reset_step_tracking" then
        -- Clears only the pending handshake; does not advance or resume MAME.
        pending_step = nil
        return {step_pending = false}
    elseif action == "snapshot" then
        manager.machine.video:snapshot()
        return {snapshot = "Saved to configured MAME snap directory"}
    elseif action == "record_start" then
        manager.machine.video:begin_recording(nil, "avi")
        return {recording = manager.machine.video.is_recording}
    elseif action == "record_stop" then
        manager.machine.video:end_recording()
        return {recording = manager.machine.video.is_recording}
    end
    error("Unsupported action")
end

local function poll()
    for name in lfs.dir(root) do
        local id = name:match("^request_([a-f0-9]+)%.json$")
        if id and #id == 32 and not processed[id] then
            processed[id] = true
            local f = io.open(root .. name, "r")
            if f then
                local payload = f:read("*a")
                f:close()
                local valid, request = pcall(json.parse, payload)
                if valid and type(request) == "table" and request.id == id
                   and type(request.action) == "string" then
                    local success, result = pcall(execute, request.action)
                    if success then
                        respond(id, true, result, nil)
                    else
                        respond(id, false, nil, result)
                    end
                else
                    respond(id, false, nil, "Invalid command format")
                end
                os.remove(root .. name)
            end
        end
    end
end

emu.register_periodic(poll)
print("GameFrame MAME bridge ready: " .. root)

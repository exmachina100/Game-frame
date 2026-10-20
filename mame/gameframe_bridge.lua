-- GameFrame MAME 0.289 local command bridge.
-- Fixed non-destructive whitelist. Never evaluates external Lua code.
local root = assert(os.getenv("GAMEFRAME_BRIDGE_DIR"), "GAMEFRAME_BRIDGE_DIR missing")
local sep = package.config:sub(1, 1)
if root:sub(-1) ~= sep then root = root .. sep end
local json = require("json")
local lfs = require("lfs")
local processed = {}

local function frame_counter()
    local frames = {}
    for tag, screen in pairs(manager.machine.screens) do
        frames[tostring(tag)] = screen.frame_number
    end
    return frames
end

local function input_catalog()
    local ports = {}
    local count = 0
    for tag, port in pairs(manager.machine.ioport.ports) do
        local fields = {}
        for name, field in pairs(port.fields) do
            fields[#fields + 1] = {name = tostring(name), player = field.player,
                mask = field.mask, analog = field.minvalue ~= nil}
        end
        ports[#ports + 1] = {tag = tostring(tag), fields = fields}
        count = count + 1
        if count >= 64 then break end
    end
    return ports
end

local function respond(id, ok, info, err)
    local response = {id = id, ok = ok}
    if ok then response.info = info else response.error = tostring(err or "Unknown error") end
    local file = assert(io.open(root .. "response_" .. id .. ".json", "w"))
    file:write(json.stringify(response))
    file:close()
end

local function execute(action)
    if action == "status" then
        return {system = manager.machine.system.name,
                paused = manager.machine.paused,
                recording = manager.machine.video.is_recording,
                single_step_available = type(manager.ui.single_step) == "boolean",
                screen_frames = frame_counter()}
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
        manager.ui.single_step = true
        emu.unpause()
        return {step_requested = true, frame_advance_confirmed = false}
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

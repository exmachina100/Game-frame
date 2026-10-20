-- GameFrame bridge for MAME Lua. Requires GAMEFRAME_BRIDGE_DIR env var.
-- Start with: mame <system> -autoboot_script mame/gameframe_bridge.lua
-- Only a fixed, non-destructive command whitelist is accepted.
-- No arbitrary Lua evaluation, shell execution, game-memory writes or ROM access.
local root = os.getenv("GAMEFRAME_BRIDGE_DIR")
assert(root and #root > 0, "Set GAMEFRAME_BRIDGE_DIR to an existing writable directory")
local sep = package.config:sub(1, 1)
if root:sub(-1) ~= sep then root = root .. sep end
local json = require("json")
local processed = {}

local function respond(id, ok, info, err)
    local f = assert(io.open(root .. "response_" .. id .. ".json", "w"))
    f:write(json.stringify({id = id, ok = ok, info = info, error = err}))
    f:close()
end

local function execute(action)
    if action == "status" then
        local system = "unknown"
        if manager.machine.system and manager.machine.system.name then
            system = manager.machine.system.name
        end
        return {system = system, paused = manager.machine.paused,
                recording = manager.machine.video.is_recording}
    elseif action == "pause" then
        emu.pause()
        return {paused = true}
    elseif action == "resume" then
        emu.unpause()
        return {paused = false}
    elseif action == "snapshot" then
        manager.machine.video:snapshot()
        return {snapshot = "Saved to MAME configured snap directory"}
    elseif action == "record_start" then
        manager.machine.video:begin_recording(nil, "avi")
        return {recording = true}
    elseif action == "record_stop" then
        manager.machine.video:end_recording()
        return {recording = false}
    end
    error("Unsupported command")
end

-- A basic command scanner. Script intentionally avoids external Lua libraries.
-- The directory listing is performed through MAME's lfs module when present.
local ok_lfs, lfs = pcall(require, "lfs")
assert(ok_lfs, "This bridge requires LuaFileSystem (lfs) in MAME's Lua environment")
local function poll()
    for name in lfs.dir(root) do
        local id = name:match("^request_([a-f0-9]+)%.json$")
        if id and #id == 32 and not processed[id] then
            processed[id] = true
            local path = root .. name
            local f = io.open(path, "r")
            if f then
                local body = f:read("*a")
                f:close()
                local decoded, request = pcall(json.parse, body)
                if decoded and request and request.id == id then
                    local success, data = pcall(execute, request.action)
                    respond(id, success, success and data or nil, success and nil or tostring(data))
                else
                    respond(id, false, nil, "Malformed command")
                end
                os.remove(path)
            end
        end
    end
end

emu.register_periodic(poll)
print("GameFrame MAME bridge active: " .. root)

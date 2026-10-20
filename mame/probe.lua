-- GameFrame independent MAME Lua API probe (no external Lua packages/ROMs).
-- Launched via -autoboot_script. Produces a status file for Windows runner.
local output = os.getenv("GAMEFRAME_PROBE_FILE")
if not output or output == "" then error("GAMEFRAME_PROBE_FILE not defined") end
local function safe(f)
    local ok, value = pcall(f)
    return ok and tostring(value) or ("ERROR: " .. tostring(value))
end
local f = assert(io.open(output, "w"))
f:write("gameframe_probe=1\n")
f:write("version=" .. safe(function() return emu.app_version() end) .. "\n")
f:write("system=" .. safe(function() return manager.machine.system.name end) .. "\n")
f:write("register_periodic=" .. tostring(type(emu.register_periodic)) .. "\n")
f:write("video_snapshot=" .. safe(function() return type(manager.machine.video.snapshot) end) .. "\n")
f:write("video_record=" .. safe(function() return type(manager.machine.video.begin_recording) end) .. "\n")
f:write("json_module=" .. safe(function() return type(require("json")) end) .. "\n")
f:write("lfs_module=" .. safe(function() return type(require("lfs")) end) .. "\n")
f:close()
print("GameFrame Lua probe saved: " .. output)

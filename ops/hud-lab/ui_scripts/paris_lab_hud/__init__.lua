-- Original diagnostic HUD. One LuaFile, no engine/global event overrides.
local PANEL_ID = "ParisLabHud_011"
local remaining = 480

local function attach()
    remaining = remaining - 1
    if Engine.InFrontend() then
        if remaining > 0 then scheduler.once(attach, 500) end
        return
    end
    local root = Engine.GetLuiRoot()
    if not root then
        if remaining > 0 then scheduler.once(attach, 500) end
        return
    end
    if root:getFirstDescendentById(PANEL_ID) then return end

    local font = CoD.TextSettings.ButtonHelperFont
    local panel = LUI.UIElement.new({
        topAnchor = true, bottomAnchor = false,
        leftAnchor = true, rightAnchor = false,
        top = 96, bottom = 168, left = 42, right = 382, alpha = 1
    })
    panel.id = PANEL_ID
    local function line(id, text, top, color)
        local label = LUI.UIText.new({
            topAnchor = true, bottomAnchor = false,
            leftAnchor = true, rightAnchor = true,
            top = top, bottom = top + font.Height,
            left = 0, right = 0, font = font.Font, alpha = 1, color = color
        })
        label.id = id
        label:setText(text)
        panel:addElement(label)
    end
    line("ParisLabHud_Title", "PRIVATE TEST LAB", 0, {r = 0.35, g = 0.9, b = 0.85})
    line("ParisLabHud_Version", "HUD MODULE / 0.1.1", font.Height + 4, {r = 1, g = 1, b = 1})
    root:addElement(panel)
    print("[PARIS_HUD] attached version=0.1.1; render witness pending")
end

print("[PARIS_HUD] loaded version=0.1.1; attach pending")
scheduler.once(attach, 500)

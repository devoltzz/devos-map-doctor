# Lets a click on a skill slot of the LoLHUD interface of M16 maps press the key of that slot.
import re


MARK = '// [Devo\'s Map Doctor, issue 31] the click on the skills of the LoLHUD interface (hud_lol.py)'

FUNCTIONS = MARK + '''
function KKHUD_tecla takes integer s returns string
    if s==SLOT_A then
        return "A"
    elseif s==SLOT_F then
        return "F"
    elseif s==SLOT_G then
        return "G"
    elseif s==SLOT_Z then
        return "Z"
    elseif s==SLOT_Q then
        return "Q"
    elseif s==SLOT_W then
        return "W"
    elseif s==SLOT_E then
        return "E"
    elseif s==SLOT_R then
        return "R"
    elseif s==SLOT_D then
        return "D"
    endif
    return ""
endfunction

function KKHUD_clique takes nothing returns nothing
    local integer s
    local string k
    if GetTriggerPlayer()!=GetLocalPlayer() or BlzGetTriggerPlayerMouseButton()!=MOUSE_BUTTON_TYPE_LEFT then
        return
    endif
    if AltDown or LoLHUD_Hero==null then
        return
    endif
    set s=LoLHUD_LastHover
    if s<0 or s>8 then
        return
    endif
    if LoLHUD_SlotAbil[s]==0 then
        return
    endif
    set k=KKHUD_tecla(s)
    if k!="" then
        call ForceUIKey(k)
    endif
endfunction

function KKHUD_init takes nothing returns nothing
    local trigger t=CreateTrigger()
    local integer i=0
    loop
        exitwhen i>=bj_MAX_PLAYERS
        call TriggerRegisterPlayerEvent(t, Player(i), EVENT_PLAYER_MOUSE_UP)
        set i=i+1
    endloop
    call TriggerAddAction(t, function KKHUD_clique)
    set t=null
endfunction
'''

RX_MAIN = re.compile(r'(?m)^function main takes nothing returns nothing[ \t]*\r?$')


def applies(body_text):
    info = {'failures': [], 'done': False}
    if MARK in body_text:
        return body_text, info
    nl = '\r\n' if '\r\n' in body_text[:20000] else '\n'
    m = list(RX_MAIN.finditer(body_text))
    if len(m) != 1:
        info['failures'].append('hud_lol: %d function main, expected 1' % len(m))
        return body_text, info
    begin = m[0].start()
    end_pos = body_text.find(nl + 'endfunction', m[0].end())
    if end_pos < 0:
        info['failures'].append('hud_lol: main without endfunction')
        return body_text, info
    new = (
        body_text[:begin]
        + FUNCTIONS.replace('\n', nl)
        + nl
        + body_text[begin:end_pos]
        + nl
        + '    call KKHUD_init()'
        + body_text[end_pos:]
    )
    info['done'] = True
    return new, info


def report_data(info):
    if info.get('done'):
        print('hud_lol: the click on the LoLHUD skills (the key of the slot) before main, the registration at its end')

function KK_chat takes nothing returns string
    local string s=GetEventPlayerChatString()
    local integer n
    local integer i=1
    if s==null or SubString(s, 0, 1)!="-" then
        return s
    endif
    set n=StringLength(s)
    loop
        exitwhen i>=n or SubString(s, i, i+1)==" "
        set i=i+1
    endloop
    return StringCase(SubString(s, 0, i), false)+SubString(s, i, n)
endfunction

function KK_chat_arg takes nothing returns string
    local string s=GetEventPlayerChatString()
    local integer n
    local integer i=0
    if s==null then
        return ""
    endif
    set n=StringLength(s)
    loop
        exitwhen i>=n or SubString(s, i, i+1)==" "
        set i=i+1
    endloop
    if i>=n then
        return ""
    endif
    return SubString(s, i+1, n)
endfunction

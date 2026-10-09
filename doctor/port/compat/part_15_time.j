function DB_GetPlayerTeam takes player p returns integer
    local integer t
    if p == null then
        return -1
    endif
    set t = GetPlayerTeam(p)
    if t == 0 and GetPlayerId(p) >= bj_MAX_PLAYERS then
        return 1
    endif
    return t
endfunction

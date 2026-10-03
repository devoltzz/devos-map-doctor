// ==============================================================================================
// ==============================================================================================

function KK_tmr_destroi takes timer t returns nothing
    if t!=null then
        call PauseTimer(t)
        call DestroyTimer(t)
    endif
endfunction

function KK_unid_morta takes unit u returns boolean
    return IsUnitType(u, UNIT_TYPE_DEAD) or GetUnitTypeId(u)==0
endfunction

integer KK_dano_prof=0

function KK_dano_alvo takes unit u, widget alvo, real valor, boolean ataque, boolean distancia, attacktype ta, damagetype td, weapontype tw returns boolean
    local integer p=KK_dano_prof
    local boolean r
    set KK_dano_prof=p+1
    set r=UnitDamageTarget(u, alvo, valor, ataque, distancia, ta, td, tw)
    set KK_dano_prof=p
    return r
endfunction

function KK_dano_alvo_bj takes unit u, unit alvo, real valor, attacktype ta, damagetype td returns boolean
    local integer p=KK_dano_prof
    local boolean r
    set KK_dano_prof=p+1
    set r=UnitDamageTargetBJ(u, alvo, valor, ta, td)
    set KK_dano_prof=p
    return r
endfunction

function KK_dano_dado takes integer edd returns integer
    if edd==1 and KK_dano_prof>0 then
        return 0
    endif
    return EXGetEventDamageData(edd)
endfunction

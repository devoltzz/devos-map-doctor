//@GLOBALS
constant integer RPGA_MAXC=24
constant integer RPGA_MAXE=24
real RPGA_tique=0.25
real RPGA_troca_perto=1.10
real RPGA_troca_longe=1.30
real RPGA_corpo=300.0
real RPGA_alcance=3000.0
real RPGA_taunt_frac=1.10
real RPGA_cura_frac=0.5
real RPGA_post_mult=4.0
real RPGA_post_dano=0.75
real RPGA_post_red=0.15
real RPGA_post_cd=5.0
real RPGA_calma=8.0
hashtable RPGA_ht=null
timer RPGA_tm=null
real RPGA_agora=0.0
unit array RPGA_c_u
unit array RPGA_c_alvo
real array RPGA_c_trava
real array RPGA_c_sem
integer array RPGA_c_n
unit array RPGA_e_u
real array RPGA_e_v
//@ENDGLOBALS

function RPGA_viva takes unit u returns boolean
    return u!=null and GetUnitTypeId(u)!=0 and not IsUnitType(u, UNIT_TYPE_DEAD)
endfunction

function RPGA_slot takes unit boss returns integer
    if boss==null then
        return -1
    endif
    return LoadInteger(RPGA_ht, GetHandleId(boss), 0)-1
endfunction

function RPGA_registra takes unit boss returns integer
    local integer c=RPGA_slot(boss)
    if c>=0 then
        return c
    endif
    set c=0
    loop
        exitwhen c>=RPGA_MAXC
        if RPGA_c_u[c]==null then
            set RPGA_c_u[c]=boss
            set RPGA_c_alvo[c]=null
            set RPGA_c_trava[c]=0.0
            set RPGA_c_sem[c]=0.0
            set RPGA_c_n[c]=0
            call SaveInteger(RPGA_ht, GetHandleId(boss), 0, c+1)
            return c
        endif
        set c=c+1
    endloop
    return -1
endfunction

function RPGA_limpa_slot takes integer c returns nothing
    local integer i=0
    loop
        exitwhen i>=RPGA_MAXE
        set RPGA_e_u[c*RPGA_MAXE+i]=null
        set RPGA_e_v[c*RPGA_MAXE+i]=0.0
        set i=i+1
    endloop
    set RPGA_c_n[c]=0
    set RPGA_c_alvo[c]=null
    set RPGA_c_trava[c]=0.0
    set RPGA_c_sem[c]=0.0
endfunction

function RPGA_solta takes unit boss returns nothing
    local integer c=RPGA_slot(boss)
    if c<0 then
        return
    endif
    call RPGA_limpa_slot(c)
    set RPGA_c_u[c]=null
    call RemoveSavedInteger(RPGA_ht, GetHandleId(boss), 0)
endfunction

function RPGA_entrada takes integer c, unit u, boolean cria returns integer
    local integer i=0
    local integer b=c*RPGA_MAXE
    loop
        exitwhen i>=RPGA_c_n[c]
        if RPGA_e_u[b+i]==u then
            return i
        endif
        set i=i+1
    endloop
    if not cria or RPGA_c_n[c]>=RPGA_MAXE then
        return -1
    endif
    set i=RPGA_c_n[c]
    set RPGA_e_u[b+i]=u
    set RPGA_e_v[b+i]=0.0
    set RPGA_c_n[c]=i+1
    return i
endfunction

function RPGA_mult_de takes unit u returns real
    local integer h=GetHandleId(u)
    local real m=1.0
    if HaveSavedReal(RPGA_ht, h, 1) then
        set m=LoadReal(RPGA_ht, h, 1)
    endif
    if LoadBoolean(RPGA_ht, h, 2) then
        set m=m*RPGA_post_mult
    endif
    return m
endfunction

function RPGA_mult takes unit u, real m returns nothing
    call SaveReal(RPGA_ht, GetHandleId(u), 1, m)
endfunction

function RPGA_em_postura takes unit u returns boolean
    return u!=null and LoadBoolean(RPGA_ht, GetHandleId(u), 2)
endfunction

function RPGA_postura takes unit u returns boolean
    local integer h=GetHandleId(u)
    local boolean liga
    if HaveSavedReal(RPGA_ht, h, 3) and RPGA_agora<LoadReal(RPGA_ht, h, 3)+RPGA_post_cd then
        return false
    endif
    set liga=not LoadBoolean(RPGA_ht, h, 2)
    call SaveBoolean(RPGA_ht, h, 2, liga)
    call SaveReal(RPGA_ht, h, 3, RPGA_agora)
    if liga then
        call RPGD_soma(u, RPGD_S_RED, RPGA_post_red)
    else
        call RPGD_soma(u, RPGD_S_RED, -RPGA_post_red)
    endif
    return true
endfunction

function RPGA_soma takes unit boss, unit u, real v returns nothing
    local integer c=RPGA_slot(boss)
    local integer i
    if c<0 or u==null then
        return
    endif
    set i=RPGA_entrada(c, u, true)
    if i>=0 then
        set RPGA_e_v[c*RPGA_MAXE+i]=RPGA_e_v[c*RPGA_MAXE+i]+v
    endif
endfunction

function RPGA_valor takes unit boss, unit u returns real
    local integer c=RPGA_slot(boss)
    local integer i
    if c<0 then
        return 0.0
    endif
    set i=RPGA_entrada(c, u, false)
    if i<0 then
        return 0.0
    endif
    return RPGA_e_v[c*RPGA_MAXE+i]
endfunction

function RPGA_corta takes unit u, real frac returns nothing
    local integer c=0
    local integer i
    loop
        exitwhen c>=RPGA_MAXC
        if RPGA_c_u[c]!=null then
            set i=RPGA_entrada(c, u, false)
            if i>=0 then
                set RPGA_e_v[c*RPGA_MAXE+i]=RPGA_e_v[c*RPGA_MAXE+i]*(1.0-frac)
            endif
        endif
        set c=c+1
    endloop
endfunction

function RPGA_valido takes integer c, unit u returns boolean
    local real dx
    local real dy
    if u==null or not RPGA_viva(u) then
        return false
    endif
    set dx=GetUnitX(u)-GetUnitX(RPGA_c_u[c])
    set dy=GetUnitY(u)-GetUnitY(RPGA_c_u[c])
    return dx*dx+dy*dy<=RPGA_alcance*RPGA_alcance
endfunction

function RPGA_perto takes integer c, unit u returns boolean
    local real dx=GetUnitX(u)-GetUnitX(RPGA_c_u[c])
    local real dy=GetUnitY(u)-GetUnitY(RPGA_c_u[c])
    return dx*dx+dy*dy<=RPGA_corpo*RPGA_corpo
endfunction

function RPGA_maior takes integer c returns integer
    local integer i=0
    local integer m=-1
    local integer b=c*RPGA_MAXE
    loop
        exitwhen i>=RPGA_c_n[c]
        if RPGA_valido(c, RPGA_e_u[b+i]) and (m<0 or RPGA_e_v[b+i]>RPGA_e_v[b+m]) then
            set m=i
        endif
        set i=i+1
    endloop
    return m
endfunction

function RPGA_taunt takes unit boss, unit u, real dur returns nothing
    local integer c=RPGA_slot(boss)
    local integer m
    local integer i
    local real alvo
    if c<0 or u==null then
        return
    endif
    set m=RPGA_maior(c)
    set i=RPGA_entrada(c, u, true)
    if i<0 then
        return
    endif
    set alvo=0.0
    if m>=0 then
        set alvo=RPGA_e_v[c*RPGA_MAXE+m]*RPGA_taunt_frac
    endif
    if RPGA_e_v[c*RPGA_MAXE+i]<alvo then
        set RPGA_e_v[c*RPGA_MAXE+i]=alvo
    endif
    set RPGA_c_alvo[c]=u
    set RPGA_c_trava[c]=RPGA_agora+dur
    call IssueTargetOrder(boss, "attack", u)
endfunction

function RPGA_alvo takes unit boss returns unit
    local integer c=RPGA_slot(boss)
    if c<0 then
        return null
    endif
    return RPGA_c_alvo[c]
endfunction

function RPGA_outro takes unit boss returns unit
    local integer c=RPGA_slot(boss)
    local integer i=0
    local integer n=0
    local integer k
    local integer b
    if c<0 then
        return null
    endif
    set b=c*RPGA_MAXE
    loop
        exitwhen i>=RPGA_c_n[c]
        if RPGA_e_u[b+i]!=RPGA_c_alvo[c] and RPGA_valido(c, RPGA_e_u[b+i]) then
            set n=n+1
        endif
        set i=i+1
    endloop
    if n==0 then
        return null
    endif
    set k=GetRandomInt(1, n)
    set i=0
    loop
        exitwhen i>=RPGA_c_n[c]
        if RPGA_e_u[b+i]!=RPGA_c_alvo[c] and RPGA_valido(c, RPGA_e_u[b+i]) then
            set k=k-1
            if k==0 then
                return RPGA_e_u[b+i]
            endif
        endif
        set i=i+1
    endloop
    return null
endfunction

function RPGA_gancho_dano takes nothing returns boolean
    local unit src=RPGD_ev_src
    local unit tgt=RPGD_ev_tgt
    local integer c
    local integer n
    local real v
    if RPGD_ev_tipo==RPGD_T_CURA then
        set n=0
        set c=0
        loop
            exitwhen c>=RPGA_MAXC
            if RPGA_c_u[c]!=null and (RPGA_entrada(c, src, false)>=0 or RPGA_entrada(c, tgt, false)>=0) then
                set n=n+1
            endif
            set c=c+1
        endloop
        if n>0 then
            set v=RPGD_ev_valor*RPGA_cura_frac*RPGA_mult_de(src)/I2R(n)
            set c=0
            loop
                exitwhen c>=RPGA_MAXC
                if RPGA_c_u[c]!=null and (RPGA_entrada(c, src, false)>=0 or RPGA_entrada(c, tgt, false)>=0) then
                    call RPGA_soma(RPGA_c_u[c], src, v)
                endif
                set c=c+1
            endloop
        endif
    else
        if src!=null and RPGA_em_postura(src) then
            set RPGD_ev_valor=RPGD_ev_valor*RPGA_post_dano
        endif
        if RPGA_slot(tgt)>=0 and src!=null then
            call RPGA_soma(tgt, src, RPGD_ev_valor*RPGA_mult_de(src))
        endif
        if RPGA_slot(src)>=0 and tgt!=null then
            call RPGA_soma(src, tgt, 0.0)
        endif
    endif
    set src=null
    set tgt=null
    return false
endfunction

function RPGA_escolhe takes integer c returns nothing
    local unit boss=RPGA_c_u[c]
    local unit atual=RPGA_c_alvo[c]
    local integer m
    local integer ia
    local real va
    local unit novo=null
    if not RPGA_viva(boss) then
        call RPGA_limpa_slot(c)
        set boss=null
        set atual=null
        return
    endif
    set m=RPGA_maior(c)
    if m<0 then
        set RPGA_c_sem[c]=RPGA_c_sem[c]+RPGA_tique
        if RPGA_c_sem[c]>=RPGA_calma and RPGA_c_n[c]>0 then
            call RPGA_limpa_slot(c)
        endif
        set boss=null
        set atual=null
        return
    endif
    set RPGA_c_sem[c]=0.0
    if atual!=null and RPGA_valido(c, atual) and RPGA_agora<RPGA_c_trava[c] then
        set boss=null
        set atual=null
        return
    endif
    set novo=RPGA_e_u[c*RPGA_MAXE+m]
    if atual!=null and RPGA_valido(c, atual) and novo!=atual then
        set ia=RPGA_entrada(c, atual, false)
        set va=RPGA_e_v[c*RPGA_MAXE+ia]
        if RPGA_perto(c, novo) then
            if RPGA_e_v[c*RPGA_MAXE+m]<=va*RPGA_troca_perto then
                set novo=atual
            endif
        elseif RPGA_e_v[c*RPGA_MAXE+m]<=va*RPGA_troca_longe then
            set novo=atual
        endif
    endif
    if novo!=atual or GetUnitCurrentOrder(boss)==0 then
        set RPGA_c_alvo[c]=novo
        call IssueTargetOrder(boss, "attack", novo)
    endif
    set boss=null
    set atual=null
    set novo=null
endfunction

function RPGA_tiq takes nothing returns nothing
    local integer c=0
    set RPGA_agora=RPGA_agora+RPGA_tique
    loop
        exitwhen c>=RPGA_MAXC
        if RPGA_c_u[c]!=null then
            call RPGA_escolhe(c)
        endif
        set c=c+1
    endloop
endfunction

function RPGA_init takes nothing returns nothing
    if RPGA_ht!=null then
        return
    endif
    set RPGA_ht=InitHashtable()
    call RPGD_gancho(function RPGA_gancho_dano)
    set RPGA_tm=CreateTimer()
    call TimerStart(RPGA_tm, RPGA_tique, true, function RPGA_tiq)
endfunction

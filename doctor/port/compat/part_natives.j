function EXSetEffectSize takes effect e,real size returns nothing
    local integer i=DB_ef(e)
    if i>=0 then
        set DB_ef_size[i]=size
        if DB_ef_uni[i]!=null then
            call SetUnitScale(DB_ef_uni[i], size, size, size)
            return
        endif
        if DB_ef_car[i]!=null then
            if DB_ef_vis[i]!=null and not DB_ef_oculto[i] then
                call BlzSetSpecialEffectScale(DB_ef_vis[i], size)
            endif
            return
        endif
    endif
    if e!=null then
        call BlzSetSpecialEffectScale(e, size)
    endif
endfunction

function EXGetEffectSize takes effect e returns real
    local integer i=DB_ef_idx(e)
    if i>=0 then
        return DB_ef_size[i]
    endif
    if e==null then
        return 1.0
    endif
    return BlzGetSpecialEffectScale(e)
endfunction

function EXSetEffectSpeed takes effect e,real speed returns nothing
    local integer i=DB_ef_idx(e)
    if e==null then
        return
    endif
    if i>=0 then
        set DB_ef_vel[i]=speed
        if DB_ef_car[i]!=null then
            if DB_ef_vis[i]!=null then
                call BlzSetSpecialEffectTimeScale(DB_ef_vis[i], speed)
            endif
            return
        endif
    endif
    call BlzSetSpecialEffectTimeScale(e, speed)
endfunction

function EXSetEffectXY takes effect e,real x,real y returns nothing
    local integer i
    if e==null then
        return
    endif
    set i=DB_ef(e)
    if i<0 then
        call BlzSetSpecialEffectPosition(e, x, y, BlzGetLocalSpecialEffectZ(e))
        return
    endif
    set DB_ef_x[i]=x
    set DB_ef_y[i]=y
    set DB_ef_segue[i]=null
    if DB_ef_uni[i]!=null then
        call KK_leque_poe(DB_ef_uni[i], x, y)
        return
    endif
    if DB_ef_car[i]!=null then
        call KK_leque_poe(DB_ef_car[i], x, y)
        call DB_car_altura(i)
        return
    endif
    call BlzSetSpecialEffectPosition(e, DB_ef_x[i], DB_ef_y[i], DB_ef_z[i])
endfunction

function EXSetEffectZ takes effect e,real z returns nothing
    local integer i
    if e==null then
        return
    endif
    set i=DB_ef(e)
    if i<0 then
        call BlzSetSpecialEffectZ(e, z)
        return
    endif
    set DB_ef_z[i]=z
    if DB_ef_segue[i]!=null then
        set DB_ef_x[i]=GetWidgetX(DB_ef_segue[i])
        set DB_ef_y[i]=GetWidgetY(DB_ef_segue[i])
        set DB_ef_segue[i]=null
    endif
    if DB_ef_uni[i]!=null then
        return
    endif
    if DB_ef_car[i]!=null then
        call DB_car_altura(i)
        return
    endif
    call BlzSetSpecialEffectPosition(e, DB_ef_x[i], DB_ef_y[i], DB_ef_z[i])
endfunction

function EXGetEffectX takes effect e returns real
    local integer i=DB_ef_idx(e)
    if i<0 then
        if e==null then
            return 0.0
        endif
        return BlzGetLocalSpecialEffectX(e)
    endif
    if DB_ef_segue[i]!=null then
        return GetWidgetX(DB_ef_segue[i])
    endif
    return DB_ef_x[i]
endfunction

function EXGetEffectY takes effect e returns real
    local integer i=DB_ef_idx(e)
    if i<0 then
        if e==null then
            return 0.0
        endif
        return BlzGetLocalSpecialEffectY(e)
    endif
    if DB_ef_segue[i]!=null then
        return GetWidgetY(DB_ef_segue[i])
    endif
    return DB_ef_y[i]
endfunction

function EXGetEffectZ takes effect e returns real
    local integer i=DB_ef_idx(e)
    if i<0 then
        if e==null then
            return 0.0
        endif
        return BlzGetLocalSpecialEffectZ(e)
    endif
    return DB_ef_z[i]
endfunction

function EXEffectMatRotateX takes effect e,real deg returns nothing
    local integer i=DB_ef(e)
    if i<0 then
        return
    endif
    set DB_ef_rx[i]=DB_ef_rx[i]+deg*3.14159265358979/180.0
    set DB_ef_pend[i]=false
    if DB_ef_uni[i]!=null then
        return
    endif
    if DB_ef_car[i]!=null and DB_ef_rx[i]!=0.0 then
        call DB_ef_solta(i, e)
    endif
    if DB_ef_car[i]!=null then
        return
    endif
    call BlzSetSpecialEffectOrientation(e, DB_ef_rz[i], DB_ef_ry[i], DB_ef_rx[i])
endfunction

function EXEffectMatRotateY takes effect e,real deg returns nothing
    local integer i=DB_ef(e)
    if i<0 then
        return
    endif
    set DB_ef_ry[i]=DB_ef_ry[i]+deg*3.14159265358979/180.0
    set DB_ef_pend[i]=false
    if DB_ef_uni[i]!=null then
        return
    endif
    if DB_ef_car[i]!=null and DB_ef_ry[i]!=0.0 then
        call DB_ef_solta(i, e)
    endif
    if DB_ef_car[i]!=null then
        return
    endif
    call BlzSetSpecialEffectOrientation(e, DB_ef_rz[i], DB_ef_ry[i], DB_ef_rx[i])
endfunction

function EXEffectMatRotateZ takes effect e,real deg returns nothing
    local integer i=DB_ef(e)
    if i<0 then
        return
    endif
    set DB_ef_rz[i]=DB_ef_rz[i]+deg*3.14159265358979/180.0
    set DB_ef_pend[i]=false
    if DB_ef_uni[i]!=null then
        call BlzSetUnitFacingEx(DB_ef_uni[i], DB_ef_rz[i]*180.0/3.14159265358979)
        return
    endif
    if DB_ef_car[i]==null and DB_CAR_LIGADO and DB_ef_sinc[i] and not DB_ef_solto[i] and DB_ef_rx[i]==0.0 and DB_ef_ry[i]==0.0 then
        call DB_ef_porta(i, e)
    endif
    if DB_ef_car[i]!=null then
        call BlzSetUnitFacingEx(DB_ef_car[i], DB_ef_rz[i]*180.0/3.14159265358979)
        return
    endif
    call BlzSetSpecialEffectOrientation(e, DB_ef_rz[i], DB_ef_ry[i], DB_ef_rx[i])
endfunction

function EXEffectMatScale takes effect e,real x,real y,real z returns nothing
    local integer i
    if e==null then
        return
    endif
    set i=DB_ef_idx(e)
    if i>=0 then
        set DB_ef_msc[i]=true
        set DB_ef_mx[i]=x
        set DB_ef_my[i]=y
        set DB_ef_mz[i]=z
        if DB_ef_uni[i]!=null then
            return
        endif
        if DB_ef_car[i]!=null then
            if DB_ef_vis[i]!=null and not DB_ef_oculto[i] then
                call BlzSetSpecialEffectMatrixScale(DB_ef_vis[i], x, y, z)
            endif
            return
        endif
    endif
    call BlzSetSpecialEffectMatrixScale(e, x, y, z)
endfunction

function DB_efp_aplica takes nothing returns nothing
    local integer k=0
    local integer i
    local effect e
    loop
        exitwhen k>=DB_efp_n
        set e=DB_efp_e[k]
        set i=DB_efp_i[k]
        if e!=null and DB_ef_pend[i] and DB_ef_vivo[i] and DB_ef_id[i]==GetHandleId(e) then
            set DB_ef_pend[i]=false
            if DB_ef_car[i]!=null then
                call BlzSetUnitFacingEx(DB_ef_car[i], DB_ef_rz[i]*180.0/3.14159265358979)
            else
                call BlzSetSpecialEffectOrientation(e, DB_ef_rz[i], DB_ef_ry[i], DB_ef_rx[i])
            endif
        endif
        set DB_efp_e[k]=null
        set k=k+1
    endloop
    set DB_efp_n=0
    set e=null
endfunction

function EXEffectMatReset takes effect e returns nothing
    local integer i=DB_ef_idx(e)
    if i>=0 then
        set DB_ef_rx[i]=0.0
        set DB_ef_ry[i]=0.0
        set DB_ef_rz[i]=0.0
        if DB_ef_uni[i]!=null then
            return
        endif
        if DB_ef_car[i]!=null then
            if DB_ef_msc[i] and DB_ef_vis[i]!=null then
                call BlzResetSpecialEffectMatrix(DB_ef_vis[i])
            endif
            set DB_ef_msc[i]=false
            set DB_ef_mx[i]=1.0
            set DB_ef_my[i]=1.0
            set DB_ef_mz[i]=1.0
        endif
    endif
    if e==null then
        return
    endif
    if i>=0 and (DB_ef_car[i]!=null or not DB_ef_msc[i]) and DB_efp_n<DB_EFP_MAX then
        if not DB_ef_pend[i] then
            set DB_ef_pend[i]=true
            set DB_efp_e[DB_efp_n]=e
            set DB_efp_i[DB_efp_n]=i
            set DB_efp_n=DB_efp_n+1
            if DB_efp_n==1 then
                if DB_efp_tmr==null then
                    set DB_efp_tmr=CreateTimer()
                endif
                call TimerStart(DB_efp_tmr, 0.0, false, function DB_efp_aplica)
            endif
        endif
        return
    endif
    if i>=0 then
        set DB_ef_msc[i]=false
        set DB_ef_pend[i]=false
        set DB_ef_mx[i]=1.0
        set DB_ef_my[i]=1.0
        set DB_ef_mz[i]=1.0
        if DB_ef_car[i]!=null then
            call BlzSetUnitFacingEx(DB_ef_car[i], 0.0)
            return
        endif
    endif
    call BlzResetSpecialEffectMatrix(e)
    call BlzSetSpecialEffectOrientation(e, 0.0, 0.0, 0.0)
endfunction

function DB_ef_uni_cor takes integer i returns nothing
    local integer r=255
    local integer g=255
    local integer b=255
    local integer a=255
    if DB_ef_cor[i]>=0 then
        set r=DB_ef_cor[i]/65536
        set g=ModuloInteger(DB_ef_cor[i]/256, 256)
        set b=ModuloInteger(DB_ef_cor[i], 256)
    endif
    if DB_ef_oculto[i] then
        set a=0
    endif
    call SetUnitVertexColor(DB_ef_uni[i], r, g, b, a)
endfunction

function DzSetEffectVisible takes effect whichEffect,boolean enable returns nothing
    local integer i
    if whichEffect==null then
        return
    endif
    set i=DB_ef(whichEffect)
    if i>=0 then
        set DB_ef_oculto[i]=not enable
    endif
    if i>=0 and DB_ef_uni[i]!=null then
        call DB_ef_uni_cor(i)
        return
    endif
    if i>=0 and DB_ef_car[i]!=null then
        if DB_ef_vis[i]!=null then
            if enable then
                call BlzSetSpecialEffectAlpha(DB_ef_vis[i], DB_ef_alfa[i])
                call BlzSetSpecialEffectScale(DB_ef_vis[i], DB_ef_size[i])
                if DB_ef_msc[i] and not DB_ef_assado[i] then
                    call BlzSetSpecialEffectMatrixScale(DB_ef_vis[i], DB_ef_mx[i], DB_ef_my[i], DB_ef_mz[i])
                endif
            else
                call BlzSetSpecialEffectAlpha(DB_ef_vis[i], 0)
                call BlzSetSpecialEffectScale(DB_ef_vis[i], 0.0)
            endif
        endif
        return
    endif
    if enable then
        call BlzSetSpecialEffectAlpha(whichEffect, 255)
        if i>=0 then
            call BlzSetSpecialEffectScale(whichEffect, DB_ef_size[i])
        else
            call BlzSetSpecialEffectScale(whichEffect, 1.0)
        endif
        call BlzResetSpecialEffectMatrix(whichEffect)
    else
        call BlzSetSpecialEffectAlpha(whichEffect, 0)
        call BlzSetSpecialEffectScale(whichEffect, 0.0)
        call BlzSetSpecialEffectMatrixScale(whichEffect, 0.0, 0.0, 0.0)
    endif
endfunction

function DzSetEffectVertexColor takes effect whichEffect,integer color returns nothing
    local integer c=color
    local integer i
    local integer r
    local integer g
    local integer b
    if whichEffect==null then
        return
    endif
    if c<0 then
        set c=c+0x7FFFFFFF+1
    endif
    set r=ModuloInteger(c/65536, 256)
    set g=ModuloInteger(c/256, 256)
    set b=ModuloInteger(c, 256)
    set i=DB_ef_idx(whichEffect)
    if i>=0 then
        set DB_ef_cor[i]=r*65536+g*256+b
        if DB_ef_uni[i]!=null then
            call DB_ef_uni_cor(i)
            return
        endif
        if DB_ef_car[i]!=null then
            if DB_ef_vis[i]!=null then
                call BlzSetSpecialEffectColor(DB_ef_vis[i], r, g, b)
            endif
            return
        endif
    endif
    call BlzSetSpecialEffectColor(whichEffect, r, g, b)
endfunction

function DzSetEffectVertexAlpha takes effect whichEffect,integer alpha returns nothing
    local integer i=DB_ef_idx(whichEffect)
    if whichEffect==null then
        return
    endif
    if i>=0 then
        set DB_ef_alfa[i]=alpha
        if DB_ef_car[i]!=null then
            if DB_ef_vis[i]!=null and not DB_ef_oculto[i] then
                call BlzSetSpecialEffectAlpha(DB_ef_vis[i], alpha)
            endif
            return
        endif
    endif
    call BlzSetSpecialEffectAlpha(whichEffect, alpha)
endfunction

function DzSetEffectPos takes effect whichEffect,real x,real y,real z returns nothing
    local integer i
    if whichEffect==null then
        return
    endif
    call DB_efeito_anota(whichEffect, x, y, z)
    set i=DB_ef_idx(whichEffect)
    if i>=0 and DB_ef_uni[i]!=null then
        call KK_leque_poe(DB_ef_uni[i], x, y)
        return
    endif
    if i>=0 and DB_ef_car[i]!=null then
        call KK_leque_poe(DB_ef_car[i], x, y)
        call DB_car_altura(i)
        return
    endif
    call BlzSetSpecialEffectPosition(whichEffect, x, y, z)
endfunction

function DzSetEffectModel takes effect whichEffect,string model returns nothing
endfunction

function DB_seq_chave takes string m returns integer
    local string s=StringCase(m, false)
    local integer n=StringLength(s)
    if n>4 then
        if SubString(s, n-4, n)==".mdx" or SubString(s, n-4, n)==".mdl" then
            set s=SubString(s, 0, n-4)
        endif
    endif
    return StringHash(s)
endfunction

function DB_seq_tipo takes string m,integer index returns integer
    local integer t=0
    if m!=null and m!="" then
        if DB_seq_ht==null then
            call DB_seq_init()
        endif
        set t=LoadInteger(DB_seq_ht, DB_seq_chave(m), index)
    endif
    if t==0 then
        if index==1 then
            set t=2
        elseif index==2 then
            set t=1
        elseif index==3 then
            set t=7
        elseif index==4 then
            set t=6
        else
            set t=5
        endif
    endif
    return t
endfunction

function DzSetEffectAnimation takes effect whichEffect,integer index,integer flag returns nothing
    local string m=null
    local integer t=0
    local integer i
    if whichEffect==null then
        return
    endif
    set i=DB_ef_idx(whichEffect)
    if i>=0 then
        set DB_ef_anim[i]=index
        if DB_ef_car[i]!=null then
            if DB_ef_vis[i]!=null and DB_ef_ht!=null then
                call BlzPlaySpecialEffect(DB_ef_vis[i], ConvertAnimType(DB_seq_tipo(LoadStr(DB_ef_ht, GetHandleId(whichEffect), 1), index)-1))
            endif
            return
        endif
    endif
    if DB_ef_ht!=null then
        set m=LoadStr(DB_ef_ht, GetHandleId(whichEffect), 1)
    endif
    if m!=null and m!="" then
        if DB_seq_ht==null then
            call DB_seq_init()
        endif
        set t=LoadInteger(DB_seq_ht, DB_seq_chave(m), index)
    endif
    if t==0 then
        if index==1 then
            set t=2
        elseif index==2 then
            set t=1
        elseif index==3 then
            set t=7
        elseif index==4 then
            set t=6
        else
            set t=5
        endif
    endif
    call BlzPlaySpecialEffect(whichEffect, ConvertAnimType(t-1))
endfunction

function DzPlayEffectAnimation takes effect whichEffect,string anim,string link returns nothing
    local integer i=DB_ef_idx(whichEffect)
    if whichEffect==null or anim==null then
        return
    endif
    if i>=0 and DB_ef_car[i]!=null then
        if DB_ef_vis[i]!=null then
            call BlzSetSpecialEffectAnimation(DB_ef_vis[i], anim)
        endif
        return
    endif
    call BlzSetSpecialEffectAnimation(whichEffect, anim)
endfunction

//{{KK_SE:KK_UI_ANCORA}}
constant integer DB_ANCORA_BASE=0x7E000000
originframetype array DB_ancora_tipo
integer array DB_ancora_ix
boolean array DB_ancora_ok
integer DB_ancora_n=0
integer DB_ancora_tentativas=0
timer DB_ancora_timer=null
integer array DB_ancora_fila_f
integer array DB_ancora_fila_p
integer array DB_ancora_fila_r
integer array DB_ancora_fila_rp
real array DB_ancora_fila_x
real array DB_ancora_fila_y
integer DB_ancora_fila_n=0

function DB_ancora_tique takes nothing returns nothing
    local integer i=0
    local integer k=0
    local integer pend=0
    local framehandle f
    set DB_ancora_tentativas=DB_ancora_tentativas+1
    loop
        exitwhen i>=DB_ancora_n
        if not DB_ancora_ok[i] then
            set f=BlzGetOriginFrame(DB_ancora_tipo[i], DB_ancora_ix[i])
            if f!=null then
                if DB_frame_ht==null then
                    set DB_frame_ht=InitHashtable()
                endif
                call SaveFrameHandle(DB_frame_ht, DB_ANCORA_BASE+i, 0, f)
                set DB_ancora_ok[i]=true
            else
                set pend=pend+1
            endif
        endif
        set i=i+1
    endloop
    set i=0
    loop
        exitwhen i>=DB_ancora_fila_n
        if DB_ancora_ok[DB_ancora_fila_r[i]-DB_ANCORA_BASE] or DB_ancora_tentativas>=80 then
            set f=DB_fh(DB_ancora_fila_f[i])
            if f!=null and DB_fh(DB_ancora_fila_r[i])!=null then
                call BlzFrameSetPoint(f, DB_p(DB_ancora_fila_p[i]), DB_fh(DB_ancora_fila_r[i]), DB_p(DB_ancora_fila_rp[i]), DB_ancora_fila_x[i], DB_ancora_fila_y[i])
            elseif f!=null then
                call BlzFrameSetAbsPoint(f, DB_p(DB_ancora_fila_p[i]), DB_ancora_fila_x[i], DB_ancora_fila_y[i])
            endif
        else
            set DB_ancora_fila_f[k]=DB_ancora_fila_f[i]
            set DB_ancora_fila_p[k]=DB_ancora_fila_p[i]
            set DB_ancora_fila_r[k]=DB_ancora_fila_r[i]
            set DB_ancora_fila_rp[k]=DB_ancora_fila_rp[i]
            set DB_ancora_fila_x[k]=DB_ancora_fila_x[i]
            set DB_ancora_fila_y[k]=DB_ancora_fila_y[i]
            set k=k+1
        endif
        set i=i+1
    endloop
    set DB_ancora_fila_n=k
    if (pend==0 and k==0) or DB_ancora_tentativas>=80 then
        call PauseTimer(DB_ancora_timer)
    endif
    set f=null
endfunction

function DB_ancora_reserva takes originframetype tipo,integer index,integer chave returns integer
    local integer id
    if DB_ancora_n>=256 then
        return 0
    endif
    set id=DB_ANCORA_BASE+DB_ancora_n
    set DB_ancora_tipo[DB_ancora_n]=tipo
    set DB_ancora_ix[DB_ancora_n]=index
    set DB_ancora_ok[DB_ancora_n]=false
    set DB_ancora_n=DB_ancora_n+1
    if DB_origem_n<DB_MAX then
        set DB_origem[DB_origem_n]=id
        set DB_origem_chave[DB_origem_n]=chave
        set DB_origem_n=DB_origem_n+1
    endif
    if DB_ancora_timer==null then
        set DB_ancora_timer=CreateTimer()
    endif
    set DB_ancora_tentativas=0
    call TimerStart(DB_ancora_timer, 0.25, true, function DB_ancora_tique)
    return id
endfunction
//{{KK_FIMSE:KK_UI_ANCORA}}

function DB_origin takes originframetype tipo,integer index returns integer
    local integer i=0
    local integer chave
    local framehandle f
    set chave=GetHandleId(tipo)*64+index
    loop
        exitwhen i>=DB_origem_n
        if DB_origem_chave[i]==chave then
            return DB_origem[i]
        endif
        set i=i+1
    endloop
    set f=BlzGetOriginFrame(tipo, index)
    if f==null then
        //{{KK_SE:KK_UI_ANCORA}}
        return DB_ancora_reserva(tipo, index, chave)
        //{{KK_FIMSE:KK_UI_ANCORA}}
        return 0
    endif
    set i=DB_fid(f)
    if i==0 then
        return 0
    endif
    if DB_origem_n<DB_MAX then
        set DB_origem[DB_origem_n]=i
        set DB_origem_chave[DB_origem_n]=chave
        set DB_origem_n=DB_origem_n+1
    endif
    return i
endfunction

//{{KK_SE:KK_UI_MSG}}
integer array DB_msg_id
integer DB_msg_n=0

function DB_msg_marca takes integer id returns integer
    local integer i=0
    if id==0 then
        return 0
    endif
    loop
        exitwhen i>=DB_msg_n
        if DB_msg_id[i]==id then
            return id
        endif
        set i=i+1
    endloop
    if DB_msg_n<8 then
        set DB_msg_id[DB_msg_n]=id
        set DB_msg_n=DB_msg_n+1
    endif
    return id
endfunction

function DB_eh_msg takes integer id returns boolean
    local integer i=0
    if id==0 then
        return false
    endif
    loop
        exitwhen i>=DB_msg_n
        if DB_msg_id[i]==id then
            return true
        endif
        set i=i+1
    endloop
    return false
endfunction

//{{KK_FIMSE:KK_UI_MSG}}
function DzGetGameUI takes nothing returns integer
    return DB_origin(ORIGIN_FRAME_GAME_UI, 0)
endfunction

function DzFrameGetPortrait takes nothing returns integer
    return DB_origin(ORIGIN_FRAME_PORTRAIT, 0)
endfunction

function DzFrameGetTooltip takes nothing returns integer
    return DB_origin(ORIGIN_FRAME_TOOLTIP, 0)
endfunction

function DzFrameGetCommandBarButton takes integer row,integer column returns integer
    return DB_origin(ORIGIN_FRAME_COMMAND_BUTTON, row*4+column)
endfunction

function DzFrameGetHeroBarButton takes integer buttonId returns integer
    return DB_origin(ORIGIN_FRAME_HERO_BUTTON, buttonId)
endfunction

function DzFrameGetHeroManaBar takes integer buttonId returns integer
    return DB_origin(ORIGIN_FRAME_HERO_MANA_BAR, buttonId)
endfunction

function DzFrameGetItemBarButton takes integer buttonId returns integer
    return DB_origin(ORIGIN_FRAME_ITEM_BUTTON, buttonId)
endfunction

function DzFrameShow takes integer frame,boolean enable returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        if DB_ui_ht!=null and HaveSavedHandle(DB_ui_ht, frame, DB_MUNDO_TT) then
            call SetTextTagVisibility(LoadTextTagHandle(DB_ui_ht, frame, DB_MUNDO_TT), enable)
            return
        endif
        call BlzFrameSetVisible(f, enable)
    endif
endfunction

function DzFrameSetEnable takes integer name,boolean enable returns nothing
    local framehandle f=DB_fh(name)
    if f!=null then
        call BlzFrameSetEnable(f, enable)
    endif
endfunction

//{{KK_SE:KK_UI_ALFA}}
function DB_ui_alfa takes string s returns string
    local integer i=0
    local integer n=StringLength(s)
    local string r=""
    local string c
    if s==null or n<4 then
        return s
    endif
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+4)
        if c=="|c00" or c=="|C00" then
            set r=r+"|cff"
            set i=i+4
        else
            set r=r+SubString(s, i, i+1)
            set i=i+1
        endif
    endloop
    return r
endfunction
//{{KK_FIMSE:KK_UI_ALFA}}

function DzFrameSetText takes integer frame,string text returns nothing
    local framehandle f=DB_fh(frame)
    local integer pai
    if f!=null then
        //{{KK_SE:KK_UI_ALFA}}
        set text=DB_ui_alfa(text)
        //{{KK_FIMSE:KK_UI_ALFA}}
        if text==null then
            call BlzFrameSetText(f, "")
        else
            call BlzFrameSetText(f, text)
        endif
        if DB_ui_ht!=null then
            set pai=LoadInteger(DB_ui_ht, frame, DB_MUNDO_PAI)
            if pai!=0 and HaveSavedHandle(DB_ui_ht, pai, DB_MUNDO_TT) then
                call DB_mundo_texto(pai, text)
            endif
        endif
    endif
endfunction

function DzFrameAddText takes integer frame,string text returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        if text==null then
            call BlzFrameAddText(f, "")
        else
            call BlzFrameAddText(f, text)
        endif
    endif
endfunction

function DzFrameSetSize takes integer frame,real w,real h returns nothing
    local framehandle f=DB_fh(frame)
    //{{KK_SE:KK_UI_MSG}}
    if DB_eh_msg(frame) then
        return
    endif
    //{{KK_FIMSE:KK_UI_MSG}}
    if f!=null then
        call BlzFrameSetSize(f, w, h)
    endif
endfunction

function DzFrameGetHeight takes integer frame returns real
    local framehandle f=DB_fh(frame)
    if f!=null then
        return BlzFrameGetHeight(f)
    endif
    return 0.0
endfunction

function DzFrameSetTexture takes integer frame,string texture,integer flag returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        if texture==null then
            call BlzFrameSetTexture(f, "", flag, true)
        else
            call BlzFrameSetTexture(f, texture, flag, true)
        endif
    endif
endfunction

function DzFrameSetFont takes integer frame,string fileName,real height,integer flag returns nothing
    local framehandle f=DB_fh(frame)
    //{{KK_SE:KK_UI_MSG}}
    if DB_eh_msg(frame) then
        return
    endif
    //{{KK_FIMSE:KK_UI_MSG}}
    if f!=null then
        if fileName==null then
            call BlzFrameSetFont(f, "", height, flag)
        else
            call BlzFrameSetFont(f, fileName, height, flag)
        endif
    endif
endfunction

//{{KK_SE:KK_DZ_REAL}}
hashtable DB_alinha_ht=InitHashtable()

//{{KK_FIMSE:KK_DZ_REAL}}
function DzFrameSetTextAlignment takes integer frame,integer align returns nothing
    local framehandle f=DB_fh(frame)
    local textaligntype v=TEXT_JUSTIFY_MIDDLE
    local textaligntype h=TEXT_JUSTIFY_CENTER
    local integer dh
    local integer dv
    if f==null then
        return
    endif
    //{{KK_SE:KK_DZ_REAL}}
    set dv=LoadInteger(DB_alinha_ht, frame, 0)
    set dh=LoadInteger(DB_alinha_ht, frame, 1)
    if ModuloInteger(align, 2)==1 then
        set dv=1
    elseif ModuloInteger(align/2, 2)==1 then
        set dv=2
    elseif ModuloInteger(align/4, 2)==1 then
        set dv=3
    endif
    if ModuloInteger(align/8, 2)==1 then
        set dh=1
    elseif ModuloInteger(align/16, 2)==1 then
        set dh=2
    elseif ModuloInteger(align/32, 2)==1 then
        set dh=3
    endif
    call SaveInteger(DB_alinha_ht, frame, 0, dv)
    call SaveInteger(DB_alinha_ht, frame, 1, dh)
    if dv==1 then
        set v=TEXT_JUSTIFY_TOP
    elseif dv==3 then
        set v=TEXT_JUSTIFY_BOTTOM
    endif
    if dh==1 then
        set h=TEXT_JUSTIFY_LEFT
    elseif dh==3 then
        set h=TEXT_JUSTIFY_RIGHT
    endif
    call BlzFrameSetTextAlignment(f, v, h)
    return
    //{{KK_FIMSE:KK_DZ_REAL}}
    if align>=11 then
        set dh=align/10-(align/100)*10
        set dv=align-(align/10)*10
        if dh==1 then
            set h=TEXT_JUSTIFY_LEFT
        elseif dh==3 then
            set h=TEXT_JUSTIFY_RIGHT
        endif
        if dv==1 then
            set v=TEXT_JUSTIFY_TOP
        elseif dv==3 then
            set v=TEXT_JUSTIFY_BOTTOM
        endif
    elseif align==0 then
        set v=TEXT_JUSTIFY_TOP
    elseif align==2 then
        set v=TEXT_JUSTIFY_BOTTOM
    elseif align==3 then
        set h=TEXT_JUSTIFY_LEFT
    elseif align==5 then
        set h=TEXT_JUSTIFY_RIGHT
    endif
    call BlzFrameSetTextAlignment(f, v, h)
endfunction

function DB_borda_direita takes nothing returns real
    local integer w
    local integer h
    local real prop
    if DB_pad_dir>=0.0 then
        return DB_pad_dir
    endif
    set w=BlzGetLocalClientWidth()
    set h=BlzGetLocalClientHeight()
    if h<=0 or w<=0 then
        return 0.0
    endif
    set DB_pad_dir=0.0
    set prop=I2R(w)/I2R(h)
    if prop>4.0/3.0 then
        set DB_pad_dir=0.4*(prop/(4.0/3.0)-1.0)
    endif
    if DB_pad_dir>0.30 then
        set DB_pad_dir=0.30
    endif
    return DB_pad_dir
endfunction

//{{KK_SE:KK_UI_CICLO}}
hashtable DB_anc_ht=null
integer DB_anc_marca=0
integer DB_anc_desfeitos=0

function DB_anc_grava takes integer f,integer p,integer r,integer rp,real x,real y returns nothing
    if DB_anc_ht==null then
        set DB_anc_ht=InitHashtable()
    endif
    call SaveBoolean(DB_anc_ht, f, 340+p, true)
    call SaveInteger(DB_anc_ht, f, 300+p, r)
    call SaveInteger(DB_anc_ht, f, 310+p, rp)
    call SaveReal(DB_anc_ht, f, 320+p, x)
    call SaveReal(DB_anc_ht, f, 330+p, y)
endfunction

function DB_anc_limpa takes integer f returns nothing
    local integer p=0
    if DB_anc_ht==null then
        return
    endif
    loop
        exitwhen p>8
        call RemoveSavedBoolean(DB_anc_ht, f, 340+p)
        set p=p+1
    endloop
endfunction

function DB_anc_alcanca takes integer de,integer alvo,integer prof returns boolean
    local integer p=0
    if de==alvo then
        return true
    endif
    if de==0 or prof>24 or DB_anc_ht==null then
        return false
    endif
    if LoadInteger(DB_anc_ht, de, 399)==DB_anc_marca then
        return false
    endif
    call SaveInteger(DB_anc_ht, de, 399, DB_anc_marca)
    loop
        exitwhen p>8
        if LoadBoolean(DB_anc_ht, de, 340+p) then
            if DB_anc_alcanca(LoadInteger(DB_anc_ht, de, 300+p), alvo, prof+1) then
                return true
            endif
        endif
        set p=p+1
    endloop
    return false
endfunction

function DB_anc_desfaz takes integer f,integer r returns nothing
    local integer p=0
    local integer q
    local integer rr
    local integer rq
    local real x2
    local real y2
    local framehandle h=DB_fh(r)
    loop
        exitwhen p>8
        if LoadBoolean(DB_anc_ht, r, 340+p) and LoadInteger(DB_anc_ht, r, 300+p)==f then
            set q=LoadInteger(DB_anc_ht, r, 310+p)
            if LoadBoolean(DB_anc_ht, f, 340+q) and LoadInteger(DB_anc_ht, f, 300+q)!=r and h!=null then
                set rr=LoadInteger(DB_anc_ht, f, 300+q)
                set rq=LoadInteger(DB_anc_ht, f, 310+q)
                set x2=LoadReal(DB_anc_ht, r, 320+p)+LoadReal(DB_anc_ht, f, 320+q)
                set y2=LoadReal(DB_anc_ht, r, 330+p)+LoadReal(DB_anc_ht, f, 330+q)
                if rr==0 then
                    call BlzFrameSetAbsPoint(h, DB_p(p), x2, y2)
                elseif DB_fh(rr)!=null then
                    call BlzFrameSetPoint(h, DB_p(p), DB_fh(rr), DB_p(rq), x2, y2)
                endif
                call DB_anc_grava(r, p, rr, rq, x2, y2)
                set DB_anc_desfeitos=DB_anc_desfeitos+1
            endif
        endif
        set p=p+1
    endloop
    set h=null
endfunction

function DB_anc_pode takes integer frame,integer relativeFrame returns boolean
    if relativeFrame==0 or DB_anc_ht==null then
        return true
    endif
    set DB_anc_marca=DB_anc_marca+1
    if not DB_anc_alcanca(relativeFrame, frame, 0) then
        return true
    endif
    call DB_anc_desfaz(frame, relativeFrame)
    set DB_anc_marca=DB_anc_marca+1
    return not DB_anc_alcanca(relativeFrame, frame, 0)
endfunction
//{{KK_FIMSE:KK_UI_CICLO}}

function DzFrameSetPoint takes integer frame,integer point,integer relativeFrame,integer relativePoint,real x,real y returns nothing
    local framehandle f=DB_fh(frame)
    local framehandle r=DB_fh(relativeFrame)
    local real pad
    if f==null then
        return
    endif
    //{{KK_SE:KK_UI_MSG}}
    if DB_eh_msg(frame) then
        return
    endif
    //{{KK_FIMSE:KK_UI_MSG}}
    //{{KK_SE:KK_UI_ANCORA}}
    if r==null and relativeFrame>=DB_ANCORA_BASE and relativeFrame<DB_ANCORA_BASE+DB_ancora_n and DB_ancora_tentativas<80 and DB_ancora_fila_n<256 then
        set DB_ancora_fila_f[DB_ancora_fila_n]=frame
        set DB_ancora_fila_p[DB_ancora_fila_n]=point
        set DB_ancora_fila_r[DB_ancora_fila_n]=relativeFrame
        set DB_ancora_fila_rp[DB_ancora_fila_n]=relativePoint
        set DB_ancora_fila_x[DB_ancora_fila_n]=x
        set DB_ancora_fila_y[DB_ancora_fila_n]=y
        set DB_ancora_fila_n=DB_ancora_fila_n+1
        return
    endif
    //{{KK_FIMSE:KK_UI_ANCORA}}
    if (relativePoint==2 or relativePoint==5 or relativePoint==8) and relativeFrame!=0 and relativeFrame==DzGetGameUI() then
        set pad=DB_borda_direita()
        if pad>0.0 and DB_fundo_tela!=null and not LoadBoolean(DB_ui_ht, frame, 3) then
            call BlzFrameSetParent(f, DB_fundo_tela)
            call SaveBoolean(DB_ui_ht, frame, 3, true)
        endif
        if LoadBoolean(DB_ui_ht, frame, 3) then
            set x=x+pad
        endif
    endif
    //{{KK_SE:KK_UI_CICLO}}
    if r!=null and not DB_anc_pode(frame, relativeFrame) then
        return
    endif
    if r!=null then
        call DB_anc_grava(frame, point, relativeFrame, relativePoint, x, y)
    else
        call DB_anc_grava(frame, point, 0, point, x, y)
    endif
    //{{KK_FIMSE:KK_UI_CICLO}}
    if r!=null then
        call BlzFrameSetPoint(f, DB_p(point), r, DB_p(relativePoint), x, y)
    else
        call BlzFrameSetAbsPoint(f, DB_p(point), x, y)
    endif
endfunction

function DzFrameSetAbsolutePoint takes integer frame,integer point,real x,real y returns nothing
    local framehandle f=DB_fh(frame)
    //{{KK_SE:KK_UI_MSG}}
    if DB_eh_msg(frame) then
        return
    endif
    //{{KK_FIMSE:KK_UI_MSG}}
    if f!=null then
        //{{KK_SE:KK_UI_CICLO}}
        call DB_anc_grava(frame, point, 0, point, x, y)
        //{{KK_FIMSE:KK_UI_CICLO}}
        call BlzFrameSetAbsPoint(f, DB_p(point), x, y)
    endif
endfunction

function DzFrameClearAllPoints takes integer frame returns nothing
    local framehandle f=DB_fh(frame)
    //{{KK_SE:KK_UI_MSG}}
    if DB_eh_msg(frame) then
        return
    endif
    //{{KK_FIMSE:KK_UI_MSG}}
    if f!=null then
        //{{KK_SE:KK_UI_CICLO}}
        call DB_anc_limpa(frame)
        //{{KK_FIMSE:KK_UI_CICLO}}
        call BlzFrameClearAllPoints(f)
        //{{KK_SE:KK_UI_RETRATO}}
        if frame==DzFrameGetPortrait() then
            call BlzFrameSetAbsPoint(f, FRAMEPOINT_CENTER, -1.0, -1.0)
            call BlzFrameSetSize(f, 0.0001, 0.0001)
        endif
        //{{KK_FIMSE:KK_UI_RETRATO}}
    endif
endfunction

function DzFrameSetAllPoints takes integer frame,integer relativeFrame returns boolean
    local framehandle f=DB_fh(frame)
    local framehandle r=DB_fh(relativeFrame)
    if f==null or r==null then
        return false
    endif
    //{{KK_SE:KK_UI_MSG}}
    if DB_eh_msg(frame) then
        return false
    endif
    //{{KK_FIMSE:KK_UI_MSG}}
    //{{KK_SE:KK_UI_CICLO}}
    if not DB_anc_pode(frame, relativeFrame) then
        return false
    endif
    call DB_anc_grava(frame, 0, relativeFrame, 0, 0.0, 0.0)
    call DB_anc_grava(frame, 8, relativeFrame, 8, 0.0, 0.0)
    //{{KK_FIMSE:KK_UI_CICLO}}
    call BlzFrameSetAllPoints(f, r)
    return true
endfunction

function DzFrameSetModel takes integer frame,string modelFile,integer modelType,integer flag returns nothing
    local framehandle f=DB_fh(frame)
    if f==null then
        return
    endif
    if modelFile==null then
        call BlzFrameSetModel(f, "", modelType)
    else
        call BlzFrameSetModel(f, modelFile, modelType)
    endif
endfunction

function DzFrameGetParent takes integer frame returns integer
    local framehandle f=DB_fh(frame)
    if f==null then
        return 0
    endif
    return DB_fid(BlzFrameGetParent(f))
endfunction

function DzFrameGetEnable takes integer frame returns boolean
    local framehandle f=DB_fh(frame)
    if f!=null then
        return BlzFrameGetEnable(f)
    endif
    return false
endfunction

function DzCreateFrameByTagName takes string frameType,string name,integer parent,string template,integer id returns integer
    local framehandle p=DB_fh(parent)
    local framehandle f
    local integer nid
    if p==null then
        return 0
    endif
    if name==null then
        set name=""
    endif
    if template==null then
        set template=""
    endif
    set f=BlzCreateFrameByType(frameType, name, p, template, id)
    if f==null then
        return 0
    endif
    set nid=DB_fid(f)
    if frameType=="TEXT" then
        call DB_ui_ht_ok()
        call SaveInteger(DB_ui_ht, nid, DB_MUNDO_PAI, parent)
        call SaveInteger(DB_ui_ht, parent, DB_MUNDO_FILHO, nid)
    endif
    if frameType=="BUTTON" or frameType=="GLUEBUTTON" or frameType=="GLUETEXTBUTTON" then
        call SaveBoolean(DB_ui_ht, nid, 2, true)
        call DB_ui_foco(f, nid)
        call DB_ui_roda_registra(f, nid)
    elseif frameType=="SIMPLEBUTTON" then
        call DB_ui_ht_ok()
        call SaveBoolean(DB_ui_ht, nid, 2, true)
    elseif frameType=="BACKDROP" then
        call DB_ui_foco(f, nid)
    endif
    return nid
endfunction

function DB_cova_passa takes nothing returns nothing
    set DB_cova_agora=DB_cova_agora+1
    loop
        exitwhen DB_cova_ini==DB_cova_fim
        exitwhen DB_cova_agora-DB_cova_tique[DB_cova_ini]<DB_COVA_TIQUES
        if DB_cova[DB_cova_ini]!=null then
            call BlzDestroyFrame(DB_cova[DB_cova_ini])
            set DB_cova[DB_cova_ini]=null
        endif
        set DB_cova_ini=ModuloInteger(DB_cova_ini+1, DB_COVA_TAM)
    endloop
endfunction

function DB_cova_poe takes framehandle f returns nothing
    local integer prox
    if DB_cova_relogio==null then
        call BlzDestroyFrame(f)
        return
    endif
    call BlzFrameSetVisible(f, false)
    set prox=ModuloInteger(DB_cova_fim+1, DB_COVA_TAM)
    if prox==DB_cova_ini then
        if DB_cova[DB_cova_ini]!=null then
            call BlzDestroyFrame(DB_cova[DB_cova_ini])
            set DB_cova[DB_cova_ini]=null
        endif
        set DB_cova_ini=ModuloInteger(DB_cova_ini+1, DB_COVA_TAM)
    endif
    set DB_cova[DB_cova_fim]=f
    set DB_cova_tique[DB_cova_fim]=DB_cova_agora
    set DB_cova_fim=prox
endfunction

function DzDestroyFrame takes integer frame returns nothing
    local framehandle f=DB_fh(frame)
    local integer ev=1
    local trigger t
    if f==null then
        return
    endif
    loop
        exitwhen ev>17
        set t=LoadTriggerHandle(DB_ui_ht, frame, 100+ev)
        if t!=null then
            call FlushChildHashtable(DB_ui_ht, GetHandleId(t))
            call DestroyTrigger(t)
        endif
        set ev=ev+1
    endloop
    set ev=0
    loop
        exitwhen ev>2
        set t=LoadTriggerHandle(DB_ui_ht, frame, 200+ev)
        if t!=null then
            call FlushChildHashtable(DB_ui_ht, GetHandleId(t))
            call DestroyTrigger(t)
        endif
        set ev=ev+1
    endloop
    call DB_mundo_solta(frame)
    call FlushChildHashtable(DB_ui_ht, frame)
    if DB_mouse_focus==frame then
        set DB_mouse_focus=0
    endif
    call RemoveSavedHandle(DB_frame_ht, frame, 0)
    call DB_cova_poe(f)
    set t=null
endfunction

function DzLoadToc takes string fileName returns nothing
    if fileName==null or fileName=="" then
        return
    endif
    set DB_toc_ok=BlzLoadTOCFile(fileName)
endfunction

location DB_mundo_loc=null
constant integer DB_MUNDO_TT=300
constant integer DB_MUNDO_PAI=301
constant integer DB_MUNDO_FILHO=302
constant real DB_MUNDO_ALTURA=0.022
constant real DB_MUNDO_CAR=14.0

function DB_mundo_largura takes string s returns integer
    local integer n=StringLength(s)
    local integer i=0
    local integer linha=0
    local integer maior=0
    local string c
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+1)
        if c=="|" and i+1<n then
            set c=SubString(s, i+1, i+2)
            if c=="c" or c=="C" then
                set i=i+10
            elseif c=="r" or c=="R" then
                set i=i+2
            elseif c=="n" or c=="N" then
                set linha=0
                set i=i+2
            else
                set linha=linha+1
                set i=i+1
            endif
        elseif c=="\n" then
            set linha=0
            set i=i+1
        else
            set linha=linha+1
            set i=i+1
        endif
        if linha>maior then
            set maior=linha
        endif
    endloop
    return maior
endfunction

function DB_mundo_texto takes integer frame,string s returns nothing
    local texttag tt
    if DB_ui_ht==null then
        return
    endif
    set tt=LoadTextTagHandle(DB_ui_ht, frame, DB_MUNDO_TT)
    if tt==null then
        return
    endif
    if s==null then
        set s=""
    endif
    call SetTextTagText(tt, s, DB_MUNDO_ALTURA)
    call SetTextTagPos(tt, LoadReal(DB_ui_ht, frame, DB_MUNDO_TT+3)-DB_MUNDO_CAR*0.5*I2R(DB_mundo_largura(s)), LoadReal(DB_ui_ht, frame, DB_MUNDO_TT+4), LoadReal(DB_ui_ht, frame, DB_MUNDO_TT+5))
    set tt=null
endfunction

function DB_mundo_prende takes integer frame,real x,real y,real z returns nothing
    local framehandle f=DB_fh(frame)
    local framehandle t
    local texttag tt
    local string s=""
    if f==null then
        return
    endif
    call DB_ui_ht_ok()
    set tt=LoadTextTagHandle(DB_ui_ht, frame, DB_MUNDO_TT)
    if tt==null then
        set tt=CreateTextTag()
        call SaveTextTagHandle(DB_ui_ht, frame, DB_MUNDO_TT, tt)
        call SetTextTagPermanent(tt, true)
        call SetTextTagColor(tt, 255, 255, 255, 255)
        call SetTextTagVisibility(tt, BlzFrameIsVisible(f))
    endif
    if DB_mundo_loc==null then
        set DB_mundo_loc=Location(x, y)
    else
        call MoveLocation(DB_mundo_loc, x, y)
    endif
    call SaveReal(DB_ui_ht, frame, DB_MUNDO_TT+3, x)
    call SaveReal(DB_ui_ht, frame, DB_MUNDO_TT+4, y)
    call SaveReal(DB_ui_ht, frame, DB_MUNDO_TT+5, z-GetLocationZ(DB_mundo_loc))
    set t=DB_fh(LoadInteger(DB_ui_ht, frame, DB_MUNDO_FILHO))
    if t!=null then
        set s=BlzFrameGetText(t)
    endif
    call DB_mundo_texto(frame, s)
    call BlzFrameSetVisible(f, false)
    set tt=null
    set t=null
    set f=null
endfunction

function DB_mundo_solta takes integer frame returns nothing
    local texttag tt
    if DB_ui_ht==null then
        return
    endif
    set tt=LoadTextTagHandle(DB_ui_ht, frame, DB_MUNDO_TT)
    if tt!=null then
        call DestroyTextTag(tt)
        call RemoveSavedHandle(DB_ui_ht, frame, DB_MUNDO_TT)
    endif
    set tt=null
endfunction

function DB_ui_ht_ok takes nothing returns nothing
    if DB_ui_ht==null then
        set DB_ui_ht=InitHashtable()
    endif
endfunction

function DB_ui_entra takes nothing returns nothing
    if GetLocalPlayer()==GetTriggerPlayer() then
        set DB_mouse_focus=LoadInteger(DB_ui_ht, GetHandleId(GetTriggeringTrigger()), 0)
    endif
endfunction

function DB_ui_sai takes nothing returns nothing
    if GetLocalPlayer()==GetTriggerPlayer() and DB_mouse_focus==LoadInteger(DB_ui_ht, GetHandleId(GetTriggeringTrigger()), 0) then
        set DB_mouse_focus=0
    endif
endfunction

function DB_ui_foco takes framehandle f,integer id returns nothing
    local trigger t
    if f==null or id==0 then
        return
    endif
    call DB_ui_ht_ok()
    if LoadBoolean(DB_ui_ht, id, 1) then
        return
    endif
    call SaveBoolean(DB_ui_ht, id, 1, true)
    set t=CreateTrigger()
    call BlzTriggerRegisterFrameEvent(t, f, FRAMEEVENT_MOUSE_ENTER)
    call TriggerAddAction(t, function DB_ui_entra)
    call SaveInteger(DB_ui_ht, GetHandleId(t), 0, id)
    call SaveTriggerHandle(DB_ui_ht, id, 200, t)
    set t=CreateTrigger()
    call BlzTriggerRegisterFrameEvent(t, f, FRAMEEVENT_MOUSE_LEAVE)
    call TriggerAddAction(t, function DB_ui_sai)
    call SaveInteger(DB_ui_ht, GetHandleId(t), 0, id)
    call SaveTriggerHandle(DB_ui_ht, id, 201, t)
    set t=null
endfunction

function DB_ui_roda takes nothing returns nothing
    set DB_wheel_delta=R2I(BlzGetTriggerFrameValue())
    if DB_roda_trig!=null then
        call TriggerExecute(DB_roda_trig)
    endif
endfunction

function DB_ui_roda_registra takes framehandle f,integer id returns nothing
    local trigger t
    if f==null or id==0 then
        return
    endif
    call DB_ui_ht_ok()
    if HaveSavedHandle(DB_ui_ht, id, 202) then
        return
    endif
    set t=CreateTrigger()
    call BlzTriggerRegisterFrameEvent(t, f, FRAMEEVENT_MOUSE_WHEEL)
    call TriggerAddAction(t, function DB_ui_roda)
    call SaveInteger(DB_ui_ht, GetHandleId(t), 0, id)
    call SaveTriggerHandle(DB_ui_ht, id, 202, t)
    set t=null
endfunction

function DB_ui_solta_foco takes nothing returns nothing
    local framehandle f
    if GetLocalPlayer()==GetTriggerPlayer() then
        set f=DB_fh(LoadInteger(DB_ui_ht, GetHandleId(GetTriggeringTrigger()), 0))
        if f!=null then
            call BlzFrameSetEnable(f, false)
            call BlzFrameSetEnable(f, true)
        endif
        set f=null
    endif
endfunction

constant real DB_DUPLO_JANELA=0.45
constant integer DB_UI_DUPLO=400
timer DB_ui_relogio=null

function DB_ui_duplo takes nothing returns boolean
    local integer q=LoadInteger(DB_ui_ht, GetHandleId(GetTriggeringTrigger()), 0)
    local integer k=DB_UI_DUPLO+GetPlayerId(GetTriggerPlayer())
    local real agora=TimerGetElapsed(DB_ui_relogio)
    if HaveSavedReal(DB_ui_ht, q, k) and agora-LoadReal(DB_ui_ht, q, k)<=DB_DUPLO_JANELA then
        call RemoveSavedReal(DB_ui_ht, q, k)
        return true
    endif
    call SaveReal(DB_ui_ht, q, k, agora)
    return false
endfunction

function DzFrameSetScriptByCode takes integer frame,integer eventId,code funcHandle,boolean sync returns nothing
    local framehandle f=DB_fh(frame)
    local frameeventtype ev=DB_ev(eventId)
    local trigger t
    if f==null or ev==null then
        return
    endif
    call DB_ui_ht_ok()
    call DB_ui_foco(f, frame)
    set t=LoadTriggerHandle(DB_ui_ht, frame, 100+eventId)
    if t!=null then
        call FlushChildHashtable(DB_ui_ht, GetHandleId(t))
        call DestroyTrigger(t)
        call RemoveSavedHandle(DB_ui_ht, frame, 100+eventId)
    endif
    if funcHandle==null then
        set t=null
        return
    endif
    //{{KK_INCLUI:quadro_evento}}
    if eventId==12 or (eventId==4 and LoadBoolean(DB_ui_ht, frame, 2)) then
        set t=CreateTrigger()
        if LoadBoolean(DB_ui_ht, frame, 2) then
            call BlzTriggerRegisterFrameEvent(t, f, FRAMEEVENT_CONTROL_CLICK)
        else
            call BlzTriggerRegisterFrameEvent(t, f, FRAMEEVENT_MOUSE_UP)
        endif
        call SaveInteger(DB_ui_ht, GetHandleId(t), 0, frame)
        if eventId==12 then
            if DB_ui_relogio==null then
                set DB_ui_relogio=CreateTimer()
                call TimerStart(DB_ui_relogio, 1000000.0, false, null)
            endif
            call TriggerAddCondition(t, Condition(function DB_ui_duplo))
        endif
        if LoadBoolean(DB_ui_ht, frame, 2) then
            call TriggerAddAction(t, function DB_ui_solta_foco)
        endif
        call TriggerAddAction(t, funcHandle)
        call SaveTriggerHandle(DB_ui_ht, frame, 100+eventId, t)
        set t=null
        return
    endif
    set t=CreateTrigger()
    call BlzTriggerRegisterFrameEvent(t, f, ev)
    call SaveInteger(DB_ui_ht, GetHandleId(t), 0, frame)
    if eventId==1 and LoadBoolean(DB_ui_ht, frame, 2) then
        call TriggerAddAction(t, function DB_ui_solta_foco)
    endif
    call TriggerAddAction(t, funcHandle)
    call SaveTriggerHandle(DB_ui_ht, frame, 100+eventId, t)
    set t=null
endfunction

function DB_quadro_tique takes nothing returns nothing
    if DB_quadro_trig!=null then
        call TriggerExecute(DB_quadro_trig)
    endif
endfunction

function DzFrameSetUpdateCallbackByCode takes code funcHandle returns nothing
    if funcHandle==null then
        return
    endif
    if DB_quadro_trig==null then
        set DB_quadro_trig=CreateTrigger()
    endif
    call TriggerAddAction(DB_quadro_trig, funcHandle)
    if DB_quadro_timer==null then
        set DB_quadro_timer=CreateTimer()
        call TimerStart(DB_quadro_timer, 0.03, true, function DB_quadro_tique)
    endif
endfunction

function DB_quadro_registra takes code funcHandle,integer chave returns nothing
    call DB_ui_ht_ok()
    if LoadBoolean(DB_ui_ht, -7, chave) then
        return
    endif
    call SaveBoolean(DB_ui_ht, -7, chave, true)
    call DzFrameSetUpdateCallbackByCode(funcHandle)
endfunction

function DB_mov_registra takes trigger trig returns nothing
    local integer i=0
    loop
        exitwhen i>=bj_MAX_PLAYERS
        call TriggerRegisterPlayerEvent(trig, Player(i), EVENT_PLAYER_MOUSE_MOVE)
        set i=i+1
    endloop
endfunction

//{{KK_SE:KK_UI_BORDAS}}
boolean DB_bordas_zero=false

function DB_bordas_aplica takes nothing returns nothing
    if DB_bordas_zero and DB_fundo_tela!=null then
        call BlzFrameSetSize(DB_fundo_tela, 0.0, 0.0001)
    endif
endfunction

//{{KK_FIMSE:KK_UI_BORDAS}}
function DB_ui_pos_init takes nothing returns nothing
    local integer i=0
    set DB_pos_init=true
    call DzGetGameUI()
    call DzFrameGetPortrait()
    call DzFrameGetTooltip()
    loop
        exitwhen i>11
        call DB_origin(ORIGIN_FRAME_COMMAND_BUTTON, i)
        set i=i+1
    endloop
    set i=0
    loop
        exitwhen i>6
        call DB_origin(ORIGIN_FRAME_HERO_BUTTON, i)
        set i=i+1
    endloop
    set i=0
    loop
        exitwhen i>5
        call DB_origin(ORIGIN_FRAME_ITEM_BUTTON, i)
        set i=i+1
    endloop
    set DB_fundo_tela=BlzGetFrameByName("ConsoleUIBackdrop", 0)
    //{{KK_SE:KK_UI_BORDAS}}
    call DB_bordas_aplica()
    //{{KK_FIMSE:KK_UI_BORDAS}}
    //{{KK_SE:KK_TECLAS}}
    call DB_teclas_registra()
    //{{KK_FIMSE:KK_TECLAS}}
    call DB_mov_registra(DB_mundo_trig)
    set i=0
    loop
        exitwhen i>=DB_mov_n
        call DB_mov_registra(DB_mov_fila[i])
        set DB_mov_fila[i]=null
        set i=i+1
    endloop
    set DB_mov_n=0
    call DestroyTimer(GetExpiredTimer())
endfunction

function DB_ui_boot takes nothing returns nothing
    local trigger t=CreateTrigger()
    set DB_sel_g=CreateGroup()
    call DB_ui_ht_ok()
    call DB_init_pontos()
    call DB_init_eventos()
    call TriggerAddAction(t, function DB_sv_prepara)
    call TriggerExecute(t)
    call DestroyTrigger(t)
    set t=null
    set DB_mundo_trig=CreateTrigger()
    call TriggerAddAction(DB_mundo_trig, function DB_mouse_mundo)
    call TimerStart(CreateTimer(), 0.00, false, function DB_ui_pos_init)
    set DB_cova_relogio=CreateTimer()
    call TimerStart(DB_cova_relogio, 0.25, true, function DB_cova_passa)
    //{{KK_SE:KK_CMD_ATAQUE}}
    call DB_cmd_atk_boot()
    //{{KK_FIMSE:KK_CMD_ATAQUE}}
endfunction

function DB_i32 takes integer n returns integer
    return n
endfunction

function DB_bit takes integer i,integer indice returns integer
    local integer k=0
    if indice<0 or indice>31 then
        return 0
    endif
    if indice==31 then
        if i<0 then
            return 1
        endif
        return 0
    endif
    if i<0 then
        set i=i+2147483647+1
    endif
    loop
        exitwhen k>=indice
        set i=i/2
        set k=k+1
    endloop
    return i-(i/2)*2
endfunction

function DB_bit_op takes integer a,integer b,integer op returns integer
    local integer r=0
    local integer p=1
    local integer k=0
    local integer ba
    local integer bb
    local boolean sa=a<0
    local boolean sb=b<0
    local boolean s
    if sa then
        set a=a+2147483647+1
    endif
    if sb then
        set b=b+2147483647+1
    endif
    loop
        exitwhen k>=31
        set ba=a-(a/2)*2
        set bb=b-(b/2)*2
        if (op==1 and ba==1 and bb==1) or (op==2 and (ba==1 or bb==1)) or (op==3 and ba!=bb) then
            set r=r+p
        endif
        set a=a/2
        set b=b/2
        if k<30 then
            set p=p*2
        endif
        set k=k+1
    endloop
    if op==1 then
        set s=sa and sb
    elseif op==2 then
        set s=sa or sb
    else
        set s=sa!=sb
    endif
    if s then
        set r=r-2147483647-1
    endif
    return r
endfunction

function DzBitAnd takes integer a,integer b returns integer
    return DB_bit_op(a, b, 1)
endfunction

function DzBitOr takes integer a,integer b returns integer
    return DB_bit_op(a, b, 2)
endfunction

function DzBitShiftLeft takes integer i,integer bitsToShift returns integer
    local integer resto
    local integer k=0
    set resto=bitsToShift-bitsToShift/32*32
    if resto<0 then
        set resto=resto+32
    endif
    loop
        exitwhen k>=resto
        set i=i*2
        set k=k+1
    endloop
    return i
endfunction

function DzBitGet takes integer i,integer byteIndex returns integer
    return DB_bit(i, byteIndex)
endfunction

function DzGetWindowWidth takes nothing returns integer
    return BlzGetLocalClientWidth()
endfunction

function DzGetWindowHeight takes nothing returns integer
    return BlzGetLocalClientHeight()
endfunction

function DzGetWindowX takes nothing returns integer
    return 0
endfunction

function DzGetWindowY takes nothing returns integer
    return 0
endfunction

//{{KK_SE:KK_UI_MOUSE_POS}}
boolean DB_mouse_virt=false
integer DB_mouse_vx=0
integer DB_mouse_vy=0

function DB_mouse_rx takes nothing returns integer
    local integer w=BlzGetLocalClientWidth()
    if w<=0 then
        return 0
    endif
    return R2I(BlzPixelToFrameX(BlzGetMouseScreenPosX())/0.8*w+0.5)
endfunction

function DB_mouse_ry takes nothing returns integer
    local integer h=BlzGetLocalClientHeight()
    if h<=0 then
        return 0
    endif
    return R2I((1.0-BlzPixelToFrameY(BlzGetMouseScreenPosY())/0.6)*h+0.5)
endfunction

//{{KK_FIMSE:KK_UI_MOUSE_POS}}
function DzGetMouseXRelative takes nothing returns integer
    local integer w=BlzGetLocalClientWidth()
    local real fx=BlzPixelToFrameX(BlzGetMouseScreenPosX())
    //{{KK_SE:KK_UI_MOUSE_POS}}
    if DB_mouse_virt then
        return DB_mouse_vx
    endif
    //{{KK_FIMSE:KK_UI_MOUSE_POS}}
    if w<=0 then
        return 0
    endif
    return R2I(fx/0.8*w+0.5)
endfunction

function DzGetMouseYRelative takes nothing returns integer
    local integer h=BlzGetLocalClientHeight()
    local real fy=BlzPixelToFrameY(BlzGetMouseScreenPosY())
    //{{KK_SE:KK_UI_MOUSE_POS}}
    if DB_mouse_virt then
        return DB_mouse_vy
    endif
    //{{KK_FIMSE:KK_UI_MOUSE_POS}}
    if h<=0 then
        return 0
    endif
    return R2I((1.0-fy/0.6)*h+0.5)
endfunction

function DzGetMouseX takes nothing returns integer
    return DzGetMouseXRelative()
endfunction

function DzGetMouseY takes nothing returns integer
    return DzGetMouseYRelative()
endfunction

function DzGetMouseTerrainX takes nothing returns real
    return DB_mouse_wx[GetPlayerId(GetLocalPlayer())]
endfunction

function DzGetMouseTerrainY takes nothing returns real
    return DB_mouse_wy[GetPlayerId(GetLocalPlayer())]
endfunction

function DB_mouse_mundo takes nothing returns nothing
    local integer i=GetPlayerId(GetTriggerPlayer())
    set DB_mouse_wx[i]=BlzGetTriggerPlayerMouseX()
    set DB_mouse_wy[i]=BlzGetTriggerPlayerMouseY()
    //{{KK_SE:KK_UI_MOUSE_POS}}
    if GetLocalPlayer()==GetTriggerPlayer() then
        set DB_mouse_virt=false
    endif
    //{{KK_FIMSE:KK_UI_MOUSE_POS}}
endfunction

function DzGetWheelDelta takes nothing returns integer
    return DB_wheel_delta
endfunction

function DzGetMouseFocus takes nothing returns integer
    return DB_mouse_focus
endfunction

function DzGetUnitUnderMouse takes nothing returns unit
    return BlzGetMouseFocusUnit()
endfunction

function DzIsWindowActive takes nothing returns boolean
    return BlzIsLocalClientActive()
endfunction

function DzSetMousePos takes integer x,integer y returns nothing
    //{{KK_SE:KK_UI_MOUSE_POS}}
    set x=x-DzGetWindowX()
    set y=y-DzGetWindowY()
    if x==DB_mouse_rx() and y==DB_mouse_ry() then
        set DB_mouse_virt=false
    else
        set DB_mouse_virt=true
        set DB_mouse_vx=x
        set DB_mouse_vy=y
    endif
    //{{KK_FIMSE:KK_UI_MOUSE_POS}}
endfunction

function DzEnableWideScreen takes boolean enable returns nothing
endfunction

function DzSetCustomFovFix takes real value returns nothing
endfunction

function DzTriggerRegisterKeyEventByCode takes trigger trig,integer key,integer status,boolean sync,code funcHandle returns nothing
    local integer i=0
    local oskeytype k=ConvertOsKeyType(key)
    if trig==null then
        set trig=CreateTrigger()
    endif
    loop
        exitwhen i>=bj_MAX_PLAYERS
        call BlzTriggerRegisterPlayerKeyEvent(trig, Player(i), k, 0, status==1)
        set i=i+1
    endloop
    if funcHandle!=null then
        call TriggerAddAction(trig, funcHandle)
    elseif not sync then
        call TriggerAddCondition(trig, Condition(function DB_cond_local))
    endif
endfunction

function DzTriggerRegisterKeyEvent takes trigger trig,integer key,integer status,boolean sync,string func returns nothing
    call DzTriggerRegisterKeyEventByCode(trig, key, status, sync, null)
endfunction

function DB_ui_cond_botao takes nothing returns boolean
    local integer b=LoadInteger(DB_ui_ht, GetHandleId(GetTriggeringTrigger()), 2)
    if b==1 then
        return BlzGetTriggerPlayerMouseButton()==MOUSE_BUTTON_TYPE_LEFT
    elseif b==2 then
        return BlzGetTriggerPlayerMouseButton()==MOUSE_BUTTON_TYPE_RIGHT
    elseif b==3 then
        return BlzGetTriggerPlayerMouseButton()==MOUSE_BUTTON_TYPE_MIDDLE
    endif
    return true
endfunction

function DzTriggerRegisterMouseEventByCode takes trigger trig,integer btn,integer status,boolean sync,code funcHandle returns nothing
    local playerevent ev=EVENT_PLAYER_MOUSE_UP
    local integer i=0
    if trig==null then
        set trig=CreateTrigger()
    endif
    call DB_ui_ht_ok()
    if status==1 then
        set ev=EVENT_PLAYER_MOUSE_DOWN
    endif
    loop
        exitwhen i>=bj_MAX_PLAYERS
        call TriggerRegisterPlayerEvent(trig, Player(i), ev)
        set i=i+1
    endloop
    call SaveInteger(DB_ui_ht, GetHandleId(trig), 2, btn)
    call TriggerAddCondition(trig, Condition(function DB_ui_cond_botao))
    if funcHandle!=null then
        call TriggerAddAction(trig, funcHandle)
    elseif not sync then
        call TriggerAddCondition(trig, Condition(function DB_cond_local))
    endif
endfunction

function DzTriggerRegisterMouseEvent takes trigger trig,integer btn,integer status,boolean sync,string func returns nothing
    call DzTriggerRegisterMouseEventByCode(trig, btn, status, sync, null)
endfunction

function DzTriggerRegisterMouseMoveEventByCode takes trigger trig,boolean sync,code funcHandle returns nothing
    if trig==null then
        set trig=CreateTrigger()
    endif
    if funcHandle!=null then
        call TriggerAddAction(trig, funcHandle)
    elseif not sync then
        call TriggerAddCondition(trig, Condition(function DB_cond_local))
    endif
    if DB_pos_init then
        call DB_mov_registra(trig)
    else
        set DB_mov_fila[DB_mov_n]=trig
        set DB_mov_n=DB_mov_n+1
    endif
endfunction

function DzTriggerRegisterMouseMoveEvent takes trigger trig,boolean sync,string func returns nothing
    call DzTriggerRegisterMouseMoveEventByCode(trig, sync, null)
endfunction

function DzTriggerRegisterMouseWheelEventByCode takes trigger trig,boolean sync,code funcHandle returns nothing
    if funcHandle==null then
        return
    endif
    if DB_roda_trig==null then
        set DB_roda_trig=CreateTrigger()
    endif
    call TriggerAddAction(DB_roda_trig, funcHandle)
endfunction

function DzTriggerRegisterMouseWheelEvent takes trigger trig,boolean sync,string func returns nothing
    call DzTriggerRegisterMouseWheelEventByCode(trig, sync, null)
endfunction

function DzTriggerRegisterWindowResizeEvent takes trigger trig,boolean sync,string func returns nothing
endfunction

function DzTriggerRegisterWindowResizeEventByCode takes trigger trig,boolean sync,code funcHandle returns nothing
endfunction

function DzIsKeyDown takes integer iKey returns boolean
    if BlzGetTriggerPlayerKey()!=null and GetHandleId(BlzGetTriggerPlayerKey())==iKey then
        return BlzGetTriggerPlayerIsKeyDown()
    endif
    if iKey<0 or iKey>255 then
        return false
    endif
    return DB_key_down[GetPlayerId(GetLocalPlayer())*256+iKey]
endfunction

//{{KK_SE:KK_TECLAS}}
constant string DB_teclas_lista="{{KK_TECLAS_LISTA}}"

function DB_tecla_muda takes nothing returns nothing
    local integer k=GetHandleId(BlzGetTriggerPlayerKey())
    if k>=0 and k<256 then
        set DB_key_down[GetPlayerId(GetTriggerPlayer())*256+k]=BlzGetTriggerPlayerIsKeyDown()
    endif
endfunction

function DB_botao_muda takes nothing returns nothing
    local integer k=1
    if BlzGetTriggerPlayerMouseButton()==MOUSE_BUTTON_TYPE_RIGHT then
        set k=2
    elseif BlzGetTriggerPlayerMouseButton()==MOUSE_BUTTON_TYPE_MIDDLE then
        set k=4
    endif
    set DB_key_down[GetPlayerId(GetTriggerPlayer())*256+k]=GetTriggerEventId()==EVENT_PLAYER_MOUSE_DOWN
endfunction

function DB_teclas_registra takes nothing returns nothing
    local trigger t=CreateTrigger()
    local trigger tb=null
    local integer i=0
    local integer j
    local integer p
    local integer m
    local integer n=StringLength(DB_teclas_lista)
    local integer k
    call TriggerAddAction(t, function DB_tecla_muda)
    loop
        exitwhen i>=n
        set j=i
        loop
            exitwhen j>=n or SubString(DB_teclas_lista, j, j+1)==","
            set j=j+1
        endloop
        set k=S2I(SubString(DB_teclas_lista, i, j))
        set p=0
        loop
            exitwhen p>=bj_MAX_PLAYERS
            if GetPlayerController(Player(p))==MAP_CONTROL_USER and GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING then
                if k==1 or k==2 or k==4 then
                    if tb==null then
                        set tb=CreateTrigger()
                        call TriggerAddAction(tb, function DB_botao_muda)
                    endif
                    call TriggerRegisterPlayerEvent(tb, Player(p), EVENT_PLAYER_MOUSE_DOWN)
                    call TriggerRegisterPlayerEvent(tb, Player(p), EVENT_PLAYER_MOUSE_UP)
                elseif k>0 and k<256 then
                    set m=0
                    loop
                        exitwhen m>15
                        call BlzTriggerRegisterPlayerKeyEvent(t, Player(p), ConvertOsKeyType(k), m, true)
                        call BlzTriggerRegisterPlayerKeyEvent(t, Player(p), ConvertOsKeyType(k), m, false)
                        set m=m+1
                    endloop
                endif
            endif
            set p=p+1
        endloop
        set i=j+1
    endloop
    set t=null
    set tb=null
endfunction

//{{KK_FIMSE:KK_TECLAS}}

function DzGetTriggerKey takes nothing returns integer
    return GetHandleId(BlzGetTriggerPlayerKey())
endfunction

function DzGetTriggerKeyPlayer takes nothing returns player
    return GetTriggerPlayer()
endfunction

function DzGetTriggerUIEventPlayer takes nothing returns player
    return GetTriggerPlayer()
endfunction

function DzGetTriggerUIEventFrame takes nothing returns integer
    local integer id=LoadInteger(DB_ui_ht, GetHandleId(GetTriggeringTrigger()), 0)
    if id!=0 then
        return id
    endif
    return DB_fid(BlzGetTriggerFrame())
endfunction

//{{KK_SE:KK_SYNC_FATIA}}
constant string DB_SF_PREFIXO="kkSF"
hashtable DB_sf_ht=null
trigger DB_sf_trig=null
boolean DB_sf_desp=false
string DB_sf_dado=""
player DB_sf_jog=null
string array DB_sf_resto
integer array DB_sf_prox

function DB_sf_barra takes string s,integer ini returns integer
    local integer n=StringLength(s)
    local integer i=ini
    loop
        exitwhen i>=n
        if SubString(s, i, i+1)=="|" then
            return i
        endif
        set i=i+1
    endloop
    return -1
endfunction

function DB_sf_despacha takes player p,string prefix,string dado returns nothing
    local integer k=StringHash(prefix)
    local integer n=LoadInteger(DB_sf_ht, k, -1)
    local integer i=0
    local trigger t
    local boolean desp0=DB_sf_desp
    local string dado0=DB_sf_dado
    local player jog0=DB_sf_jog
    set DB_sf_desp=true
    set DB_sf_dado=dado
    set DB_sf_jog=p
    loop
        exitwhen i>=n
        if LoadStr(DB_sf_ht, k, -2-i)==prefix then
            set t=LoadTriggerHandle(DB_sf_ht, k, i)
            if t!=null and IsTriggerEnabled(t) then
                if TriggerEvaluate(t) then
                    call TriggerExecute(t)
                endif
            endif
        endif
        set i=i+1
    endloop
    set DB_sf_desp=desp0
    set DB_sf_dado=dado0
    set DB_sf_jog=jog0
    set t=null
    set jog0=null
endfunction

function DB_sf_recebe takes nothing returns nothing
    local string s=BlzGetTriggerSyncData()
    local player p=GetTriggerPlayer()
    local integer id=GetPlayerId(p)
    local integer a
    local integer b=-1
    local integer c=-1
    local integer i
    local integer n
    local integer tam
    local string prefix
    if s==null then
        set p=null
        return
    endif
    set a=DB_sf_barra(s, 0)
    if a>0 then
        set b=DB_sf_barra(s, a+1)
    endif
    if b>a+1 then
        set c=DB_sf_barra(s, b+1)
    endif
    if c<=b+1 then
        set p=null
        return
    endif
    set i=S2I(SubString(s, 0, a))
    set n=S2I(SubString(s, a+1, b))
    set tam=S2I(SubString(s, b+1, c))
    set prefix=SubString(s, c+1, c+1+tam)
    if i==0 then
        set DB_sf_resto[id]=""
        set DB_sf_prox[id]=0
    endif
    if i!=DB_sf_prox[id] or n<1 then
        set DB_sf_resto[id]=""
        set DB_sf_prox[id]=-1
        set p=null
        return
    endif
    set DB_sf_resto[id]=DB_sf_resto[id]+SubString(s, c+1+tam, StringLength(s))
    set DB_sf_prox[id]=i+1
    if i>=n-1 then
        set s=DB_sf_resto[id]
        set DB_sf_resto[id]=""
        set DB_sf_prox[id]=0
        call DB_sf_despacha(p, prefix, s)
    endif
    set p=null
endfunction

function DB_sf_guarda takes trigger trig,string prefix returns nothing
    local integer k=StringHash(prefix)
    local integer n
    local integer i=0
    if DB_sf_ht==null then
        set DB_sf_ht=InitHashtable()
        set DB_sf_trig=CreateTrigger()
        loop
            exitwhen i>=bj_MAX_PLAYERS
            call BlzTriggerRegisterPlayerSyncEvent(DB_sf_trig, Player(i), DB_SF_PREFIXO, false)
            set i=i+1
        endloop
        call TriggerAddAction(DB_sf_trig, function DB_sf_recebe)
    endif
    set n=LoadInteger(DB_sf_ht, k, -1)
    call SaveTriggerHandle(DB_sf_ht, k, n, trig)
    call SaveStr(DB_sf_ht, k, -2-n, prefix)
    call SaveInteger(DB_sf_ht, k, -1, n+1)
endfunction

function DB_sf_envia takes string prefix,string data returns nothing
    local integer n=StringLength(data)
    local integer tam=StringLength(prefix)
    local integer pedaco=DB_SYNC_TRECHO
    local integer partes
    local integer i=0
    local string cab
    if 12+tam+pedaco>DB_SYNC_DIRETO then
        set pedaco=DB_SYNC_DIRETO-12-tam
        if pedaco<16 then
            set pedaco=16
        endif
    endif
    set partes=(n+pedaco-1)/pedaco
    set cab="|"+I2S(partes)+"|"+I2S(tam)+"|"+prefix
    loop
        exitwhen i>=partes
        call BlzSendSyncData(DB_SF_PREFIXO, I2S(i)+cab+SubString(data, i*pedaco, (i+1)*pedaco))
        set i=i+1
    endloop
endfunction

//{{KK_FIMSE:KK_SYNC_FATIA}}
function DzTriggerRegisterSyncData takes trigger trig,string prefix,boolean server returns nothing
    local integer i=0
    if trig==null or prefix==null then
        return
    endif
    loop
        exitwhen i>=bj_MAX_PLAYERS
        call BlzTriggerRegisterPlayerSyncEvent(trig, Player(i), prefix, false)
        set i=i+1
    endloop
    //{{KK_SE:KK_SYNC_FATIA}}
    call DB_sf_guarda(trig, prefix)
    //{{KK_FIMSE:KK_SYNC_FATIA}}
endfunction

function DzSyncData takes string prefix,string data returns nothing
    if prefix==null then
        return
    endif
    if data==null then
        set data=""
    endif
    //{{KK_SE:KK_SYNC_FATIA}}
    if StringLength(data)>DB_SYNC_DIRETO then
        call DB_sf_envia(prefix, data)
        return
    endif
    //{{KK_FIMSE:KK_SYNC_FATIA}}
    //{{KK_SE:KK_SYNC_VAZIO}}
    if data=="" then
        set data="~KKvazio~"
    endif
    //{{KK_FIMSE:KK_SYNC_VAZIO}}
    call BlzSendSyncData(prefix, data)
endfunction

function DzSyncDataImmediately takes string prefix,string data returns nothing
    call DzSyncData(prefix, data)
endfunction

function DzGetTriggerSyncData takes nothing returns string
    local string r=BlzGetTriggerSyncData()
    //{{KK_SE:KK_SYNC_FATIA}}
    if DB_sf_desp then
        return DB_sf_dado
    endif
    //{{KK_FIMSE:KK_SYNC_FATIA}}
    if r==null then
        return ""
    endif
    //{{KK_SE:KK_SYNC_VAZIO}}
    if r=="~KKvazio~" then
        return ""
    endif
    //{{KK_FIMSE:KK_SYNC_VAZIO}}
    return r
endfunction

function DzGetTriggerSyncPlayer takes nothing returns player
    //{{KK_SE:KK_SYNC_FATIA}}
    if DB_sf_desp then
        return DB_sf_jog
    endif
    //{{KK_FIMSE:KK_SYNC_FATIA}}
    return GetTriggerPlayer()
endfunction

function EXSetEventDamage takes real amount returns boolean
    call BlzSetEventDamage(amount)
    return true
endfunction

function EXSetUnitFacing takes unit u,real angle returns nothing
    if u==null then
        return
    endif
    call BlzSetUnitFacingEx(u, angle)
endfunction

function EXGetUnitAbility takes unit u,integer abilcode returns ability
    local ability a
    if u==null then
        return null
    endif
    set a=BlzGetUnitAbility(u, abilcode)
    if a!=null then
        call DB_exab_garante()
        call SaveUnitHandle(DB_exab_ht,GetHandleId(a),0,u)
        call SaveInteger(DB_exab_ht,GetHandleId(a),1,abilcode)
    endif
    return a
endfunction

hashtable DB_pausa_ht=null

function EXPauseUnit takes unit u,boolean flag returns nothing
    local integer h
    local integer t
    if u==null then
        return
    endif
    if DB_pausa_ht==null then
        set DB_pausa_ht=InitHashtable()
    endif
    set h=GetHandleId(u)
    set t=GetUnitTypeId(u)
    if flag then
        if HaveSavedInteger(DB_pausa_ht,h,0) and LoadInteger(DB_pausa_ht,h,0)==t then
            return
        endif
        call SaveInteger(DB_pausa_ht,h,0,t)
        call BlzPauseUnitEx(u, true)
    else
        if HaveSavedInteger(DB_pausa_ht,h,0) then
            if LoadInteger(DB_pausa_ht,h,0)==t then
                call BlzPauseUnitEx(u, false)
            endif
            call RemoveSavedInteger(DB_pausa_ht,h,0)
        endif
    endif
endfunction

function EXSetUnitCollisionType takes boolean enable,unit u,integer t returns nothing
    if u==null then
        return
    endif
    call SetUnitPathing(u, enable)
endfunction

function DB_movetype_indice takes integer t returns integer
    if t==0x02 then
        return 0
    elseif t==0x08 then
        return 1
    elseif t==0x04 then
        return 2
    elseif t==0x10 then
        return 3
    elseif t==0x20 then
        return 4
    elseif t==0x40 then
        return 5
    endif
    return -1
endfunction

function EXSetUnitMoveType takes unit u,integer t returns nothing
    local integer i
    if u==null then
        return
    endif
    set i=DB_movetype_indice(t)
    if i>=0 then
        call BlzSetUnitIntegerField(u, UNIT_IF_MOVE_TYPE, i)
    endif
endfunction

hashtable DB_exab_ht=null
hashtable DB_exit_ht=null

function DB_exab_garante takes nothing returns nothing
    if DB_exab_ht==null then
        set DB_exab_ht=InitHashtable()
    endif
endfunction

function DB_exit_garante takes nothing returns nothing
    if DB_exit_ht==null then
        set DB_exit_ht=InitHashtable()
    endif
endfunction

function DB_ex_abil_id takes ability abil returns integer
    local integer id
    if abil==null then
        return 0
    endif
    call DB_exab_garante()
    if HaveSavedInteger(DB_exab_ht,GetHandleId(abil),1) then
        set id=LoadInteger(DB_exab_ht,GetHandleId(abil),1)
        if id!=0 then
            return id
        endif
    endif
    return BlzGetAbilityId(abil)
endfunction

function DB_ex_abil_dono takes ability abil returns unit
    if abil==null then
        return null
    endif
    call DB_exab_garante()
    if not HaveSavedHandle(DB_exab_ht,GetHandleId(abil),0) then
        return null
    endif
    return LoadUnitHandle(DB_exab_ht,GetHandleId(abil),0)
endfunction

function DB_ex_dano_int takes damagetype t returns integer
    if t==DAMAGE_TYPE_UNKNOWN then
        return 0
    elseif t==DAMAGE_TYPE_NORMAL then
        return 4
    elseif t==DAMAGE_TYPE_ENHANCED then
        return 5
    elseif t==DAMAGE_TYPE_FIRE then
        return 8
    elseif t==DAMAGE_TYPE_COLD then
        return 9
    elseif t==DAMAGE_TYPE_LIGHTNING then
        return 10
    elseif t==DAMAGE_TYPE_POISON then
        return 11
    elseif t==DAMAGE_TYPE_DISEASE then
        return 12
    elseif t==DAMAGE_TYPE_DIVINE then
        return 13
    elseif t==DAMAGE_TYPE_MAGIC then
        return 14
    elseif t==DAMAGE_TYPE_SONIC then
        return 15
    elseif t==DAMAGE_TYPE_ACID then
        return 16
    elseif t==DAMAGE_TYPE_FORCE then
        return 17
    elseif t==DAMAGE_TYPE_DEATH then
        return 18
    elseif t==DAMAGE_TYPE_MIND then
        return 19
    elseif t==DAMAGE_TYPE_PLANT then
        return 20
    elseif t==DAMAGE_TYPE_DEFENSIVE then
        return 21
    elseif t==DAMAGE_TYPE_DEMOLITION then
        return 22
    elseif t==DAMAGE_TYPE_SLOW_POISON then
        return 23
    elseif t==DAMAGE_TYPE_SPIRIT_LINK then
        return 24
    elseif t==DAMAGE_TYPE_SHADOW_STRIKE then
        return 25
    elseif t==DAMAGE_TYPE_UNIVERSAL then
        return 26
    endif
    return -1
endfunction

function DB_ex_arma_int takes weapontype t returns integer
    if t==WEAPON_TYPE_WHOKNOWS then
        return 0
    elseif t==WEAPON_TYPE_METAL_LIGHT_CHOP then
        return 1
    elseif t==WEAPON_TYPE_METAL_MEDIUM_CHOP then
        return 2
    elseif t==WEAPON_TYPE_METAL_HEAVY_CHOP then
        return 3
    elseif t==WEAPON_TYPE_METAL_LIGHT_SLICE then
        return 4
    elseif t==WEAPON_TYPE_METAL_MEDIUM_SLICE then
        return 5
    elseif t==WEAPON_TYPE_METAL_HEAVY_SLICE then
        return 6
    elseif t==WEAPON_TYPE_METAL_MEDIUM_BASH then
        return 7
    elseif t==WEAPON_TYPE_METAL_HEAVY_BASH then
        return 8
    elseif t==WEAPON_TYPE_METAL_MEDIUM_STAB then
        return 9
    elseif t==WEAPON_TYPE_METAL_HEAVY_STAB then
        return 10
    elseif t==WEAPON_TYPE_WOOD_LIGHT_SLICE then
        return 11
    elseif t==WEAPON_TYPE_WOOD_MEDIUM_SLICE then
        return 12
    elseif t==WEAPON_TYPE_WOOD_HEAVY_SLICE then
        return 13
    elseif t==WEAPON_TYPE_WOOD_LIGHT_BASH then
        return 14
    elseif t==WEAPON_TYPE_WOOD_MEDIUM_BASH then
        return 15
    elseif t==WEAPON_TYPE_WOOD_HEAVY_BASH then
        return 16
    elseif t==WEAPON_TYPE_WOOD_LIGHT_STAB then
        return 17
    elseif t==WEAPON_TYPE_WOOD_MEDIUM_STAB then
        return 18
    elseif t==WEAPON_TYPE_CLAW_LIGHT_SLICE then
        return 19
    elseif t==WEAPON_TYPE_CLAW_MEDIUM_SLICE then
        return 20
    elseif t==WEAPON_TYPE_CLAW_HEAVY_SLICE then
        return 21
    elseif t==WEAPON_TYPE_AXE_MEDIUM_CHOP then
        return 22
    elseif t==WEAPON_TYPE_ROCK_HEAVY_BASH then
        return 23
    endif
    return -1
endfunction

function DB_ex_ataque_int takes attacktype t returns integer
    if t==ATTACK_TYPE_NORMAL then
        return 0
    elseif t==ATTACK_TYPE_MELEE then
        return 1
    elseif t==ATTACK_TYPE_PIERCE then
        return 2
    elseif t==ATTACK_TYPE_SIEGE then
        return 3
    elseif t==ATTACK_TYPE_MAGIC then
        return 4
    elseif t==ATTACK_TYPE_CHAOS then
        return 5
    elseif t==ATTACK_TYPE_HERO then
        return 6
    endif
    return -1
endfunction

function EXGetEventDamageData takes integer edd_type returns integer
    if edd_type==0 then
        return 1
    elseif edd_type==1 then
        if BlzGetEventDamageType()==DAMAGE_TYPE_NORMAL then
            return 1
        endif
        return 0
    elseif edd_type==2 then
        if BlzGetEventIsAttack() then
            return 1
        endif
        return 0
    elseif edd_type==3 then
        if BlzGetEventIsAttack() and IsUnitType(GetEventDamageSource(),UNIT_TYPE_RANGED_ATTACKER) then
            return 1
        endif
        return 0
    elseif edd_type==4 then
        return DB_ex_dano_int(BlzGetEventDamageType())
    elseif edd_type==5 then
        return DB_ex_arma_int(BlzGetEventWeaponType())
    elseif edd_type==6 then
        return DB_ex_ataque_int(BlzGetEventAttackType())
    endif
    return 0
endfunction

function EXGetItemDataString takes integer itemcode,integer data_type returns string
    local string s
    if DB_exit_ht!=null and HaveSavedString(DB_exit_ht,itemcode,data_type) then
        return LoadStr(DB_exit_ht,itemcode,data_type)
    endif
    if itemcode==0 then
        return ""
    endif
    if data_type==4 then
        set s=DB_slk_get(DB_TAB_ITEM,itemcode,DB_C_ITEM_NAME)
        if s==null or s=="" then
            set s=GetObjectName(itemcode)
        endif
        return s
    elseif data_type==1 then
        set s=DB_slk_get(DB_TAB_ITEM,itemcode,DB_C_ITEM_ART)
        if s==null or s=="" then
            set s=BlzGetAbilityIcon(itemcode)
        endif
        return s
    elseif data_type==3 then
        set s=DB_slk_get(DB_TAB_ITEM,itemcode,DB_C_ITEM_UBERTIP)
        if s==null or s=="" then
            set s=BlzGetAbilityExtendedTooltip(itemcode,0)
        endif
        return s
    elseif data_type==2 then
        return BlzGetAbilityTooltip(itemcode,0)
    endif
    return ""
endfunction

function EXSetItemDataString takes integer itemcode,integer data_type,string value returns boolean
    call DB_exit_garante()
    call SaveStr(DB_exit_ht,itemcode,data_type,value)
    return true
endfunction

function DB_ex_dado_bonus takes ability abil,integer lv,integer data_type,integer v returns boolean
    if data_type==108 then
        if BlzSetAbilityIntegerLevelField(abil,ABILITY_ILF_ATTACK_BONUS,lv,v) then
            return true
        elseif BlzSetAbilityIntegerLevelField(abil,ABILITY_ILF_DEFENSE_BONUS_IDEF,lv,v) then
            return true
        endif
        return BlzSetAbilityIntegerLevelField(abil,ABILITY_ILF_AGILITY_BONUS,lv,v)
    elseif data_type==109 then
        return BlzSetAbilityIntegerLevelField(abil,ABILITY_ILF_INTELLIGENCE_BONUS,lv,v)
    elseif data_type==110 then
        return BlzSetAbilityIntegerLevelField(abil,ABILITY_ILF_STRENGTH_BONUS_ISTR,lv,v)
    endif
    return false
endfunction

function EXGetAbilityDataReal takes ability abil,integer level,integer data_type returns real
    local integer lv=level-1
    if abil==null then
        return 0.0
    endif
    if lv<0 then
        set lv=0
    endif
    if data_type==102 then
        return BlzGetAbilityRealLevelField(abil,ABILITY_RLF_DURATION_NORMAL,lv)
    elseif data_type==103 then
        return BlzGetAbilityRealLevelField(abil,ABILITY_RLF_DURATION_HERO,lv)
    elseif data_type==105 then
        return BlzGetAbilityRealLevelField(abil,ABILITY_RLF_COOLDOWN,lv)
    elseif data_type==106 then
        return BlzGetAbilityRealLevelField(abil,ABILITY_RLF_AREA_OF_EFFECT,lv)
    elseif data_type==107 then
        return BlzGetAbilityRealLevelField(abil,ABILITY_RLF_CAST_RANGE,lv)
    endif
    call DB_exab_garante()
    return LoadReal(DB_exab_ht,GetHandleId(abil),data_type*100+level)
endfunction

function EXSetAbilityDataReal takes ability abil,integer level,integer data_type,real value returns boolean
    local integer lv=level-1
    if abil==null then
        return false
    endif
    if lv<0 then
        set lv=0
    endif
    if data_type==102 then
        return BlzSetAbilityRealLevelField(abil,ABILITY_RLF_DURATION_NORMAL,lv,value)
    elseif data_type==103 then
        return BlzSetAbilityRealLevelField(abil,ABILITY_RLF_DURATION_HERO,lv,value)
    elseif data_type==105 then
        return BlzSetAbilityRealLevelField(abil,ABILITY_RLF_COOLDOWN,lv,value)
    elseif data_type==106 then
        return BlzSetAbilityRealLevelField(abil,ABILITY_RLF_AREA_OF_EFFECT,lv,value)
    elseif data_type==107 then
        return BlzSetAbilityRealLevelField(abil,ABILITY_RLF_CAST_RANGE,lv,value)
    elseif data_type>=108 and data_type<=110 then
        call DB_ex_dado_bonus(abil,lv,data_type,DB_est_piso(value))
    endif
    call DB_exab_garante()
    call SaveReal(DB_exab_ht,GetHandleId(abil),data_type*100+level,value)
    return true
endfunction

function EXGetAbilityDataInteger takes ability abil,integer level,integer data_type returns integer
    local integer lv=level-1
    if abil==null then
        return 0
    endif
    if lv<0 then
        set lv=0
    endif
    if data_type==104 then
        return BlzGetAbilityIntegerLevelField(abil,ABILITY_ILF_MANA_COST,lv)
    endif
    call DB_exab_garante()
    //{{KK_INCLUI:ex_ab_inteiro}}
    return LoadInteger(DB_exab_ht,GetHandleId(abil),data_type*100+level)
endfunction

function EXSetAbilityDataInteger takes ability abil,integer level,integer data_type,integer value returns boolean
    local integer lv=level-1
    if abil==null then
        return false
    endif
    if lv<0 then
        set lv=0
    endif
    if data_type==104 then
        return BlzSetAbilityIntegerLevelField(abil,ABILITY_ILF_MANA_COST,lv,value)
    elseif data_type>=108 and data_type<=110 then
        call DB_ex_dado_bonus(abil,lv,data_type,value)
    endif
    call DB_exab_garante()
    call SaveInteger(DB_exab_ht,GetHandleId(abil),data_type*100+level,value)
    return true
endfunction

function EXGetAbilityDataString takes ability abil,integer level,integer data_type returns string
    local integer lv=level-1
    local integer id
    if abil==null then
        return ""
    endif
    if lv<0 then
        set lv=0
    endif
    call DB_exab_garante()
    if HaveSavedString(DB_exab_ht,GetHandleId(abil),data_type*100+level) then
        return LoadStr(DB_exab_ht,GetHandleId(abil),data_type*100+level)
    endif
    set id=DB_ex_abil_id(abil)
    if id==0 then
        return ""
    endif
    if data_type==203 then
        return GetObjectName(id)
    elseif data_type==204 then
        return BlzGetAbilityIcon(id)
    elseif data_type==215 then
        return BlzGetAbilityTooltip(id,lv)
    elseif data_type==218 then
        return BlzGetAbilityExtendedTooltip(id,lv)
    elseif data_type==214 then
        return BlzGetAbilityResearchTooltip(id,lv)
    elseif data_type==217 then
        return BlzGetAbilityResearchExtendedTooltip(id,lv)
    elseif data_type==216 then
        return BlzGetAbilityActivatedTooltip(id,lv)
    elseif data_type==219 then
        return BlzGetAbilityActivatedExtendedTooltip(id,lv)
    elseif data_type==220 then
        return BlzGetAbilityActivatedIcon(id)
    endif
    return ""
endfunction

function EXSetAbilityDataString takes ability abil,integer level,integer data_type,string value returns boolean
    local integer lv=level-1
    local integer id
    if abil==null then
        return false
    endif
    if lv<0 then
        set lv=0
    endif
    set id=DB_ex_abil_id(abil)
    if id!=0 then
        if data_type==204 then
            call BlzSetAbilityIcon(id,value)
            return true
        elseif data_type==215 then
            call BlzSetAbilityTooltip(id,value,lv)
            return true
        elseif data_type==218 then
            call BlzSetAbilityExtendedTooltip(id,value,lv)
            return true
        elseif data_type==214 then
            call BlzSetAbilityResearchTooltip(id,value,lv)
            return true
        elseif data_type==217 then
            call BlzSetAbilityResearchExtendedTooltip(id,value,lv)
            return true
        elseif data_type==216 then
            call BlzSetAbilityActivatedTooltip(id,value,lv)
            return true
        elseif data_type==219 then
            call BlzSetAbilityActivatedExtendedTooltip(id,value,lv)
            return true
        elseif data_type==220 then
            call BlzSetAbilityActivatedIcon(id,value)
            return true
        endif
    endif
    call DB_exab_garante()
    call SaveStr(DB_exab_ht,GetHandleId(abil),data_type*100+level,value)
    return true
endfunction

function EXGetAbilityState takes ability abil,integer state_type returns real
    local unit dono
    local integer id
    local real r=0.0
    if state_type!=1 then
        return 0.0
    endif
    set dono=DB_ex_abil_dono(abil)
    if dono!=null then
        set id=DB_ex_abil_id(abil)
        if id!=0 then
            set r=BlzGetUnitAbilityCooldownRemaining(dono,id)
        endif
    endif
    set dono=null
    return r
endfunction

function EXSetAbilityState takes ability abil,integer state_type,real value returns boolean
    local unit dono
    local integer id
    local boolean ok=false
    if state_type!=1 then
        return false
    endif
    set dono=DB_ex_abil_dono(abil)
    if dono!=null then
        set id=DB_ex_abil_id(abil)
        if id!=0 then
            if value>0.0 then
                if BlzGetUnitAbilityCooldownRemaining(dono,id)>0.0 then
                    call BlzSetUnitAbilityCooldownRemaining(dono,id,value)
                else
                    call BlzStartUnitAbilityCooldown(dono,id,value)
                endif
            else
                call BlzEndUnitAbilityCooldown(dono,id)
            endif
            set ok=true
        endif
    endif
    set dono=null
    return ok
endfunction

function DB_morph_chaos takes integer alvo returns integer
    //{{KK_INCLUI:morph_chaos}}
    return 0
endfunction

function DB_morph_skin takes unit u,integer alvo returns nothing
    local string art=null
    local real vel=0.0
    local real arco=0.0
    local boolean dist=IsUnitType(u,UNIT_TYPE_HERO) and IsUnitType(u,UNIT_TYPE_RANGED_ATTACKER)
    //{{KK_SE:KK_MORFO_ESTADO}}
    local boolean heroi=IsUnitType(u,UNIT_TYPE_HERO)
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
    if dist then
        set art=BlzGetUnitWeaponStringField(u,UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART,0)
        set vel=BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_PROJECTILE_SPEED,0)
        set arco=BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_PROJECTILE_ARC,0)
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    if heroi then
        call DB_morfo_anuncia(u)
    endif
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
    call BlzSetUnitSkin(u,alvo)
    if dist then
        if art!=null and art!="" then
            call BlzSetUnitWeaponStringField(u,UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART,0,art)
        endif
        if vel>0.0 then
            call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_PROJECTILE_SPEED,0,vel)
        endif
        if arco>0.0 then
            call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_PROJECTILE_ARC,0,arco)
        endif
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    if heroi then
        call DB_morfo_skin_volta(u)
    endif
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
    set art=null
endfunction

function DB_morph takes unit u,integer alvo returns nothing
    local integer chaos
    local real vida
    local real mana
    local real m
    if u==null or alvo==0 then
        return
    endif
    if GetUnitTypeId(u)==alvo then
        if BlzGetUnitSkin(u)!=alvo then
            call BlzSetUnitSkin(u,alvo)
        endif
        return
    endif
    set chaos=DB_morph_chaos(alvo)
    if chaos!=0 then
        set vida=GetUnitState(u,UNIT_STATE_LIFE)
        set mana=GetUnitState(u,UNIT_STATE_MANA)
        //{{KK_SE:KK_MORFO_ESTADO}}
        if IsUnitType(u,UNIT_TYPE_HERO) then
            call DB_morfo_anuncia(u)
        endif
        //{{KK_FIMSE:KK_MORFO_ESTADO}}
        call UnitAddAbility(u,chaos)
        if GetUnitTypeId(u)==alvo then
            call UnitRemoveAbility(u,chaos)
            if GetUnitTypeId(u)!=alvo then
                call UnitAddAbility(u,chaos)
            endif
            //{{KK_SE:KK_MORFO_ESTADO}}
            call DB_morfo_confere(u)
            //{{KK_FIMSE:KK_MORFO_ESTADO}}
            set m=GetUnitState(u,UNIT_STATE_MAX_LIFE)
            if vida>0.405 then
                if vida<m then
                    call SetUnitState(u,UNIT_STATE_LIFE,vida)
                else
                    call SetUnitState(u,UNIT_STATE_LIFE,m)
                endif
            endif
            set m=GetUnitState(u,UNIT_STATE_MAX_MANA)
            if mana>0.0 then
                if mana<m then
                    call SetUnitState(u,UNIT_STATE_MANA,mana)
                else
                    call SetUnitState(u,UNIT_STATE_MANA,m)
                endif
            endif
            return
        endif
        call UnitRemoveAbility(u,chaos)
    endif
    call DB_morph_skin(u,alvo)
endfunction

function EXSetAbilityAEmeDataA takes ability abil,integer unitid returns boolean
    local unit dono
    if abil==null then
        return false
    endif
    call DB_exab_garante()
    call SaveInteger(DB_exab_ht,GetHandleId(abil),2,unitid)
    set dono=DB_ex_abil_dono(abil)
    if dono!=null then
        call DB_morph(dono,unitid)
        set dono=null
    endif
    return true
endfunction

function DzSetUnitName takes unit whichUnit,string name returns nothing
    if whichUnit==null then
        return
    endif
    if name==null or name=="" then
        return
    endif
    call BlzSetUnitName(whichUnit, name)
endfunction

function DzSetUnitProperName takes unit whichUnit,string name returns nothing
    if whichUnit==null then
        return
    endif
    if name==null or name=="" then
        return
    endif
    call BlzSetHeroProperName(whichUnit, name)
endfunction

function DzUnitFindAbility takes unit whichUnit,integer abilcode returns ability
    local ability a
    if whichUnit==null then
        return null
    endif
    set a=BlzGetUnitAbility(whichUnit, abilcode)
    if a!=null then
        call DB_exab_garante()
        call SaveUnitHandle(DB_exab_ht,GetHandleId(a),0,whichUnit)
        call SaveInteger(DB_exab_ht,GetHandleId(a),1,abilcode)
    endif
    return a
endfunction

// @bug) nao acumula.
function DzAbilitySetEnable takes ability whichAbility,boolean enable,boolean hideUI returns nothing
    local unit u
    local integer id
    if whichAbility==null then
        return
    endif
    call DB_exab_garante()
    set u=LoadUnitHandle(DB_exab_ht,GetHandleId(whichAbility),0)
    set id=LoadInteger(DB_exab_ht,GetHandleId(whichAbility),1)
    if u!=null and id!=0 then
        call BlzUnitDisableAbility(u,id,not enable,hideUI)
    endif
    set u=null
endfunction

function DzGetSelectedLeaderUnit takes nothing returns unit
    if DB_sel_g==null then
        return null
    endif
    call GroupClear(DB_sel_g)
    call GroupEnumUnitsSelected(DB_sel_g, GetLocalPlayer(), null)
    set DB_sel_u=FirstOfGroup(DB_sel_g)
    call GroupClear(DB_sel_g)
    return DB_sel_u
endfunction

hashtable DB_mod_ht=null
boolean DB_mod_ok=false
unit array DB_mod_u
effect array DB_mod_e
integer DB_mod_n=0
timer DB_mod_tmr=null
constant integer DB_MOD_MAX=8000

function DB_mod_sem_ext takes string f returns string
    local integer n=StringLength(f)
    local string ext
    if n>4 then
        set ext=StringCase(SubString(f,n-4,n),false)
        if ext==".mdx" or ext==".mdl" then
            return SubString(f,0,n-4)
        endif
    endif
    return f
endfunction

function DB_mod_indexa takes nothing returns nothing
    local integer i=0
    local string f
    local integer k
    set DB_mod_ok=true
    if DB_mod_ht==null then
        set DB_mod_ht=InitHashtable()
    endif
    call SLK_U_FILE(0)
    loop
        exitwhen i>=SLK_U_FILE_N
        set f=DB_mod_sem_ext(SLK_U_FILE_v[i])
        if f!=null and f!="" then
            set k=StringHash(f)
            if not HaveSavedInteger(DB_mod_ht,0,k) or (SLK_U_FILE_k[i]>=0x7A000000 and SLK_U_FILE_k[i]<0x7A610000) then
                call SaveInteger(DB_mod_ht,0,k,SLK_U_FILE_k[i])
            endif
        endif
        set i=i+1
    endloop
endfunction

function DB_mod_tipo takes string path returns integer
    local integer k
    if not DB_mod_ok then
        call DB_mod_indexa()
    endif
    set k=StringHash(DB_mod_sem_ext(path))
    if HaveSavedInteger(DB_mod_ht,0,k) then
        return LoadInteger(DB_mod_ht,0,k)
    endif
    return 0
endfunction

function DB_mod_tira takes integer i returns nothing
    call RemoveSavedInteger(DB_mod_ht,1,GetHandleId(DB_mod_u[i]))
    set DB_mod_n=DB_mod_n-1
    if i<DB_mod_n then
        set DB_mod_u[i]=DB_mod_u[DB_mod_n]
        set DB_mod_e[i]=DB_mod_e[DB_mod_n]
        call SaveInteger(DB_mod_ht,1,GetHandleId(DB_mod_u[i]),i+1)
    endif
    set DB_mod_u[DB_mod_n]=null
    set DB_mod_e[DB_mod_n]=null
endfunction

function DB_mod_solta takes unit u returns nothing
    local integer i
    if DB_mod_ht==null or DB_mod_n==0 then
        return
    endif
    if not HaveSavedInteger(DB_mod_ht,1,GetHandleId(u)) then
        return
    endif
    set i=LoadInteger(DB_mod_ht,1,GetHandleId(u))-1
    call DestroyEffect(DB_mod_e[i])
    call DB_mod_tira(i)
endfunction

function DB_mod_varre takes nothing returns nothing
    local integer i=DB_mod_n-1
    loop
        exitwhen i<0
        if GetUnitTypeId(DB_mod_u[i])==0 or GetWidgetLife(DB_mod_u[i])<=0.405 then
            call DestroyEffect(DB_mod_e[i])
            call DB_mod_tira(i)
        endif
        set i=i-1
    endloop
    if DB_mod_n==0 then
        call PauseTimer(DB_mod_tmr)
    endif
endfunction

function DB_mod_pendura takes unit u,string path returns nothing
    local effect e
    if DB_mod_n>=DB_MOD_MAX then
        return
    endif
    //{{KK_SE:KK_FX_LOCAL}}
    set path=KK_fx_m(path)
    //{{KK_FIMSE:KK_FX_LOCAL}}
    set e=AddSpecialEffectTarget(path,u,"origin")
    if e==null then
        return
    endif
    set DB_mod_u[DB_mod_n]=u
    set DB_mod_e[DB_mod_n]=e
    set DB_mod_n=DB_mod_n+1
    call SaveInteger(DB_mod_ht,1,GetHandleId(u),DB_mod_n)
    if DB_mod_tmr==null then
        set DB_mod_tmr=CreateTimer()
    endif
    if DB_mod_n==1 then
        call TimerStart(DB_mod_tmr,0.10,true,function DB_mod_varre)
    endif
    set e=null
endfunction

//{{KK_SE:KK_MOD_ESCONDE_BASE}}
function DB_mod_esconde_base takes unit u returns nothing
    local real s
    if BlzGetUnitSkin(u)=={{KK_MOD_TIPO_VAZIO}} then
        return
    endif
    set s=BlzGetUnitRealField(u,UNIT_RF_SCALING_VALUE)
    call BlzSetUnitSkin(u,{{KK_MOD_TIPO_VAZIO}})
    call SetUnitScale(u,s,s,s)
endfunction

//{{KK_FIMSE:KK_MOD_ESCONDE_BASE}}
function DzSetUnitModel takes unit whichUnit,string path returns nothing
    local integer t
    if whichUnit==null or path==null then
        return
    endif
    if not DB_mod_ok then
        call DB_mod_indexa()
    endif
    call DB_mod_solta(whichUnit)
    if path=="" then
        return
    endif
    set t=DB_mod_tipo(path)
    if t!=0 and t!=GetUnitTypeId(whichUnit) and StringHash(DB_mod_sem_ext(SLK_U_FILE(GetUnitTypeId(whichUnit))))==StringHash(DB_mod_sem_ext(path)) then
        set t=GetUnitTypeId(whichUnit)
    endif
    if t!=0 then
        call BlzSetUnitSkin(whichUnit,t)
        //{{KK_SE:KK_FX_LOCAL}}
        call KK_fx_unidade(whichUnit)
        //{{KK_FIMSE:KK_FX_LOCAL}}
        return
    endif
    if GetUnitAbilityLevel(whichUnit,'Aloc')<=0 then
        return
    endif
    //{{KK_SE:KK_MOD_ESCONDE_BASE}}
    call DB_mod_esconde_base(whichUnit)
    //{{KK_FIMSE:KK_MOD_ESCONDE_BASE}}
    call DB_mod_pendura(whichUnit,path)
endfunction

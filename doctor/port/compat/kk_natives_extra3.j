//{{KK_SE:KK_UI_BOTOES}}
//@GLOBALS
hashtable DB_ui_botoes=null
//@ENDGLOBALS

function DB_ui_e_botao takes string nome returns boolean
    local string lista="{{KK_UI_BOTOES_1}}"+"{{KK_UI_BOTOES_2}}"+"{{KK_UI_BOTOES_3}}"+"{{KK_UI_BOTOES_4}}"+"{{KK_UI_BOTOES_5}}"+"{{KK_UI_BOTOES_6}}"+"{{KK_UI_BOTOES_7}}"+"{{KK_UI_BOTOES_8}}"
    local integer i=0
    local integer n
    local integer ini=0
    if DB_ui_botoes==null then
        set DB_ui_botoes=InitHashtable()
        set n=StringLength(lista)
        loop
            exitwhen i>n
            if i==n or SubString(lista, i, i+1)=="|" then
                if i>ini then
                    call SaveBoolean(DB_ui_botoes, 0, StringHash(SubString(lista, ini, i)), true)
                endif
                set ini=i+1
            endif
            set i=i+1
        endloop
    endif
    return LoadBoolean(DB_ui_botoes, 0, StringHash(nome))
endfunction
//{{KK_FIMSE:KK_UI_BOTOES}}

function DzCreateFrame takes string frame,integer parent,integer id returns integer
    local framehandle p=DB_fh(parent)
    local framehandle f
    //{{KK_SE:KK_UI_BOTOES}}
    local integer nid
    //{{KK_FIMSE:KK_UI_BOTOES}}
    if p==null then
        set p=DB_fh(DzGetGameUI())
    endif
    if frame==null or p==null then
        return 0
    endif
    set f=BlzCreateFrame(frame, p, 0, id)
    if f==null then
        return 0
    endif
    //{{KK_SE:KK_UI_BOTOES}}
    if DB_ui_e_botao(frame) then
        set nid=DB_fid(f)
        call DB_ui_ht_ok()
        call SaveBoolean(DB_ui_ht, nid, 2, true)
        call DB_ui_foco(f, nid)
        call DB_ui_roda_registra(f, nid)
        return nid
    endif
    //{{KK_FIMSE:KK_UI_BOTOES}}
    return DB_fid(f)
endfunction

function DzCreateSimpleFrame takes string frame,integer parent,integer id returns integer
    local framehandle p=DB_fh(parent)
    local framehandle f
    if p==null then
        set p=DB_fh(DzGetGameUI())
    endif
    if frame==null or p==null then
        return 0
    endif
    set f=BlzCreateSimpleFrame(frame, p, id)
    if f==null then
        set f=BlzCreateFrame(frame, p, 0, id)
    endif
    if f==null then
        return 0
    endif
    return DB_fid(f)
endfunction

function DzFrameFindByName takes string name,integer id returns integer
    if name==null or name=="" then
        return 0
    endif
    return DB_fid(BlzGetFrameByName(name, id))
endfunction

function DzSimpleFrameFindByName takes string name,integer id returns integer
    return DzFrameFindByName(name, id)
endfunction

function DzSimpleFontStringFindByName takes string name,integer id returns integer
    return DzFrameFindByName(name, id)
endfunction

function DzSimpleTextureFindByName takes string name,integer id returns integer
    return DzFrameFindByName(name, id)
endfunction

function DzFrameGetHeroHPBar takes integer buttonId returns integer
    return DB_origin(ORIGIN_FRAME_HERO_HP_BAR, buttonId)
endfunction

function DzFrameGetUpperButtonBarButton takes integer buttonId returns integer
    //{{KK_SE:KK_UI_SISTEMA}}
    if buttonId==0 then
        return DB_origin(ORIGIN_FRAME_SYSTEM_BUTTON, 3)
    elseif buttonId>=1 and buttonId<=3 then
        return DB_origin(ORIGIN_FRAME_SYSTEM_BUTTON, buttonId-1)
    endif
    //{{KK_FIMSE:KK_UI_SISTEMA}}
    return DB_origin(ORIGIN_FRAME_SYSTEM_BUTTON, buttonId)
endfunction

function DzFrameGetChatMessage takes nothing returns integer
    //{{KK_SE:KK_UI_MSG}}
    return DB_msg_marca(DB_origin(ORIGIN_FRAME_CHAT_MSG, 0))
    //{{KK_FIMSE:KK_UI_MSG}}
    return DB_origin(ORIGIN_FRAME_CHAT_MSG, 0)
endfunction

function DzFrameGetUnitMessage takes nothing returns integer
    //{{KK_SE:KK_UI_MSG}}
    return DB_msg_marca(DB_origin(ORIGIN_FRAME_UNIT_MSG, 0))
    //{{KK_FIMSE:KK_UI_MSG}}
    return DB_origin(ORIGIN_FRAME_UNIT_MSG, 0)
endfunction

function DzFrameGetTopMessage takes nothing returns integer
    //{{KK_SE:KK_UI_MSG}}
    return DB_msg_marca(DB_origin(ORIGIN_FRAME_TOP_MSG, 0))
    //{{KK_FIMSE:KK_UI_MSG}}
    return DB_origin(ORIGIN_FRAME_TOP_MSG, 0)
endfunction

function DzFrameHideInterface takes nothing returns nothing
    call BlzHideOriginFrames(true)
endfunction

function DzFrameEditBlackBorders takes real upperHeight,real bottomHeight returns nothing
    //{{KK_SE:KK_UI_BORDAS}}
    if bottomHeight<=0.0 then
        set DB_bordas_zero=true
        call DB_bordas_aplica()
    endif
    //{{KK_FIMSE:KK_UI_BORDAS}}
endfunction

function DzClickFrame takes integer frame returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameClick(f)
    endif
endfunction

function DzFrameCageMouse takes integer frame,boolean enable returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameCageMouse(f, enable)
    endif
endfunction

function DzFrameSetFocus takes integer frame,boolean enable returns boolean
    local framehandle f=DB_fh(frame)
    if f==null then
        return false
    endif
    call BlzFrameSetFocus(f, enable)
    return true
endfunction

function DzFrameGetAlpha takes integer frame returns integer
    local framehandle f=DB_fh(frame)
    if f==null then
        return 0
    endif
    return BlzFrameGetAlpha(f)
endfunction

function DzFrameGetName takes integer frame returns string
    local framehandle f=DB_fh(frame)
    if f==null then
        return ""
    endif
    return BlzFrameGetName(f)
endfunction

function DzFrameGetText takes integer frame returns string
    local framehandle f=DB_fh(frame)
    if f==null then
        return ""
    endif
    return BlzFrameGetText(f)
endfunction

function DzFrameGetTextSizeLimit takes integer frame returns integer
    local framehandle f=DB_fh(frame)
    if f==null then
        return 0
    endif
    return BlzFrameGetTextSizeLimit(f)
endfunction

function DzFrameGetValue takes integer frame returns real
    local framehandle f=DB_fh(frame)
    if f==null then
        return 0.0
    endif
    return BlzFrameGetValue(f)
endfunction

function DzFrameSetMinMaxValue takes integer frame,real minValue,real maxValue returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameSetMinMaxValue(f, minValue, maxValue)
    endif
endfunction

function DzFrameSetParent takes integer frame,integer parent returns nothing
    local framehandle f=DB_fh(frame)
    local framehandle p=DB_fh(parent)
    if f!=null and p!=null then
        call BlzFrameSetParent(f, p)
    endif
endfunction

function DzFrameSetPriority takes integer frame,integer priority returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameSetLevel(f, priority)
    endif
endfunction

function DzFrameSetStepValue takes integer frame,real step returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameSetStepSize(f, step)
    endif
endfunction

function DzFrameSetTextColor takes integer frame,integer color returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameSetTextColor(f, color)
    endif
endfunction

function DzFrameSetTextSizeLimit takes integer frame,integer size returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameSetTextSizeLimit(f, size)
    endif
endfunction

function DzFrameSetTooltip takes integer frame,integer tooltip returns nothing
    local framehandle f=DB_fh(frame)
    local framehandle t=DB_fh(tooltip)
    if f!=null and t!=null then
        call BlzFrameSetTooltip(f, t)
    endif
endfunction

function DzFrameSetValue takes integer frame,real value returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameSetValue(f, value)
    endif
endfunction

function DzFrameSetVertexColor takes integer frame,integer color returns nothing
    local framehandle f=DB_fh(frame)
    if f!=null then
        call BlzFrameSetVertexColor(f, color)
    endif
endfunction

function BitAnd takes integer x,integer y returns integer
    return DB_bit_op(x, y, 1)
endfunction

function BitOr takes integer x,integer y returns integer
    return DB_bit_op(x, y, 2)
endfunction

function BitXor takes integer x,integer y returns integer
    return DB_bit_op(x, y, 3)
endfunction

function BitShiftL takes integer x,integer y returns integer
    return DzBitShiftLeft(x, y)
endfunction

function BitShiftR takes integer x,integer y returns integer
    local integer resto=y-y/32*32
    local integer k=0
    if resto<0 then
        set resto=resto+32
    endif
    loop
        exitwhen k>=resto
        if x>=0 then
            set x=x/2
        else
            set x=(x-1)/2
        endif
        set k=k+1
    endloop
    return x
endfunction

function EXSetAbilityString takes integer abilcode,integer level,integer data_type,string value returns boolean
    local integer lv=level-1
    if value==null then
        set value=""
    endif
    if lv<0 then
        set lv=0
    endif
    if data_type==204 then
        call BlzSetAbilityIcon(abilcode, value)
    elseif data_type==215 then
        call BlzSetAbilityTooltip(abilcode, value, lv)
    elseif data_type==218 then
        call BlzSetAbilityExtendedTooltip(abilcode, value, lv)
    elseif data_type==214 then
        call BlzSetAbilityResearchTooltip(abilcode, value, lv)
    elseif data_type==217 then
        call BlzSetAbilityResearchExtendedTooltip(abilcode, value, lv)
    elseif data_type==216 then
        call BlzSetAbilityActivatedTooltip(abilcode, value, lv)
    elseif data_type==219 then
        call BlzSetAbilityActivatedExtendedTooltip(abilcode, value, lv)
    elseif data_type==220 then
        call BlzSetAbilityActivatedIcon(abilcode, value)
    else
        return false
    endif
    return true
endfunction

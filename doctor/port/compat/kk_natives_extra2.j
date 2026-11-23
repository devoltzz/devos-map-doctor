function DzSetUnitID takes unit whichUnit,integer id returns nothing
    set DB_morph_mantem=true
    call DB_morph(whichUnit, id)
    set DB_morph_mantem=false
endfunction

function DzSetUnitPosition takes unit whichUnit,real x,real y returns nothing
    if whichUnit==null then
        return
    endif
    call SetUnitX(whichUnit, x)
    call SetUnitY(whichUnit, y)
endfunction

function DzFrameSetScale takes integer frame,real scale returns nothing
    local framehandle f=DB_fh(frame)
    if DB_simples_tipo(frame)!=0 then
        set f=null
        return
    endif
    if f!=null then
        //{{KK_SE:KK_UI_IGUAL}}
        if DB_ui_ht!=null and LoadBoolean(DB_ui_ht, frame, DB_UI_NOSSO) then
            if HaveSavedReal(DB_ui_ht, frame, DB_UI_IG_ESC) and DB_ui_ig_igual(LoadReal(DB_ui_ht, frame, DB_UI_IG_ESC), scale) then
                set f=null
                return
            endif
            call SaveReal(DB_ui_ht, frame, DB_UI_IG_ESC, scale)
            call RemoveSavedString(DB_ui_ht, frame, DB_UI_IG_FNT)
        endif
        //{{KK_FIMSE:KK_UI_IGUAL}}
        call BlzFrameSetScale(f, scale)
    endif
    set f=null
endfunction

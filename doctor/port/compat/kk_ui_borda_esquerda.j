function KK_FrameAbsBordaEsquerda takes integer frame,integer point,real x,real y returns nothing
    local framehandle f=DB_fh(frame)
    local real pad
    if f==null then
        return
    endif
    if DB_fundo_tela==null then
        set DB_fundo_tela=BlzGetFrameByName("ConsoleUIBackdrop", 0)
    endif
    set pad=DB_borda_direita()
    if pad>0.0 and DB_fundo_tela!=null then
        if not LoadBoolean(DB_ui_ht, frame, 3) then
            call BlzFrameSetParent(f, DB_fundo_tela)
            call SaveBoolean(DB_ui_ht, frame, 3, true)
        endif
        set x=x-pad
    endif
    set f=null
    call DzFrameSetAbsolutePoint(frame, point, x, y)
endfunction

function DzSetUnitID takes unit whichUnit,integer id returns nothing
    call DB_morph(whichUnit, id)
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
    if f!=null then
        call BlzFrameSetScale(f, scale)
    endif
    set f=null
endfunction

hashtable DB_ord_ht=null
boolean DB_ord_on=false
unit DB_gtu_u=null
integer DB_gtu_n=0
constant string DB_B36="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

function DB_ord_init takes nothing returns nothing
    local integer k=32
    if DB_ord_on then
        return
    endif
    set DB_ord_on=true
    set DB_ord_ht=InitHashtable()
    call DB_chr_init()
    loop
        exitwhen k>126
        if (k<97 or k>122) and k!=47 then
            call SaveInteger(DB_ord_ht,0,StringHash(DB_CHR[k]),k)
        endif
        set k=k+1
    endloop
endfunction

function DB_ord takes string c returns integer
    local integer v
    local integer h
    if c==null or c=="" then
        return -1
    endif
    if c=="/" then
        return 47
    endif
    call DB_ord_init()
    set h=StringHash(c)
    if not HaveSavedInteger(DB_ord_ht,0,h) then
        return -1
    endif
    set v=LoadInteger(DB_ord_ht,0,h)
    if v>=65 and v<=90 and c!=StringCase(c,true) then
        return v+32
    endif
    return v
endfunction

function DB_chr takes integer b returns string
    if b<32 or b>126 then
        return ""
    endif
    call DB_chr_init()
    return DB_CHR[b]
endfunction

function DB_id2s takes integer a returns string
    local integer x
    local integer b3
    local integer b2
    local integer b1
    local integer b0
    if a==0 then
        return ""
    endif
    if a<0 then
        set x=a+2147483647+1
        set b3=x/16777216+128
        set x=x-(x/16777216)*16777216
    else
        set b3=a/16777216
        set x=a-b3*16777216
    endif
    set b2=x/65536
    set x=x-b2*65536
    set b1=x/256
    set b0=x-b1*256
    if b3>0 then
        return DB_chr(b3)+DB_chr(b2)+DB_chr(b1)+DB_chr(b0)
    elseif b2>0 then
        return DB_chr(b2)+DB_chr(b1)+DB_chr(b0)
    elseif b1>0 then
        return DB_chr(b1)+DB_chr(b0)
    endif
    return DB_chr(b0)
endfunction

function DB_s2id takes string s returns integer
    local integer n
    local integer i=0
    local integer r=0
    local integer v
    if s==null then
        return 0
    endif
    set n=StringLength(s)
    if n<1 or n>4 then
        return 0
    endif
    loop
        exitwhen i>=n
        set v=DB_ord(SubString(s,i,i+1))
        if v<0 then
            return 0
        endif
        set r=r*256+v
        set i=i+1
    endloop
    return r
endfunction

function DB_gtu takes nothing returns unit
    if DB_gtu_n>0 then
        return DB_gtu_u
    endif
    return GetTriggerUnit()
endfunction

function DB_timer_decorrido takes timer t returns real
    return TimerGetTimeout(t)-TimerGetRemaining(t)
endfunction

function DB_lh_hotkey takes string s returns integer
    local integer t=0
    local integer i=0
    local integer k
    local string c
    if s==null or StringLength(s)!=3 then
        return GetLocalizedHotkey(s)
    endif
    loop
        exitwhen i>=3
        set c=SubString(s,i,i+1)
        set k=0
        loop
            exitwhen k>=36
            if SubString(DB_B36,k,k+1)==c then
                exitwhen true
            endif
            set k=k+1
        endloop
        if k>=36 then
            set k=0
        endif
        set t=t*36+k
        set i=i+1
    endloop
    if t>=23328 then
        set t=t-46656
    endif
    return t
endfunction

function DB_lh_string takes string s returns string
    local integer n
    local integer i=0
    local integer k
    local string t=""
    if s==null or I2S(S2I(s))!=s then
        return GetLocalizedString(s)
    endif
    set n=S2I(s)
    set n=n-(n/46656)*46656
    if n<0 then
        set n=n+46656
    endif
    loop
        exitwhen i>=3
        set k=n/36
        set t=SubString(DB_B36,n-k*36,n-k*36+1)+t
        set n=k
        set i=i+1
    endloop
    return t
endfunction

hashtable DB_sh_ht=null
hashtable DB_sh_memo=null
integer DB_sh_memo_n=0
constant integer DB_SH_MEMO_MAX=200000
constant integer DB_SH_MAX_BYTES=8000
integer array DB_shb
integer DB_sh_x=0
integer DB_sh_y=0
integer DB_sh_z=0

function DB_sh_srl takes integer x,integer k returns integer
    if x<0 then
        return (x+2147483647+1)/DB_POT2[k]+DB_POT2[31-k]
    endif
    return x/DB_POT2[k]
endfunction

function DB_sh_mix takes integer a,integer b,integer c returns nothing
    set a=a-b
    set a=a-c
    set a=BlzBitXor(a, DB_sh_srl(c, 13))
    set b=b-c
    set b=b-a
    set b=BlzBitXor(b, a*256)
    set c=c-a
    set c=c-b
    set c=BlzBitXor(c, DB_sh_srl(b, 13))
    set a=a-b
    set a=a-c
    set a=BlzBitXor(a, DB_sh_srl(c, 12))
    set b=b-c
    set b=b-a
    set b=BlzBitXor(b, a*65536)
    set c=c-a
    set c=c-b
    set c=BlzBitXor(c, DB_sh_srl(b, 5))
    set a=a-b
    set a=a-c
    set a=BlzBitXor(a, DB_sh_srl(c, 3))
    set b=b-c
    set b=b-a
    set b=BlzBitXor(b, a*1024)
    set c=c-a
    set c=c-b
    set c=BlzBitXor(c, DB_sh_srl(b, 15))
    set DB_sh_x=a
    set DB_sh_y=b
    set DB_sh_z=c
endfunction

function DB_sh_ascii takes string c,integer v,integer cru,boolean baixa returns nothing
    local integer h=StringHash(c)
    if baixa then
        call SaveStr(DB_sh_ht, 2, h, c)
        call SaveInteger(DB_sh_ht, 3, h, v)
        call SaveInteger(DB_sh_ht, 11, h, cru)
    else
        call SaveStr(DB_sh_ht, 0, h, c)
        call SaveInteger(DB_sh_ht, 1, h, v)
        call SaveInteger(DB_sh_ht, 10, h, cru)
    endif
endfunction

function DB_sh_chave takes integer n,integer b0,integer b1,integer b2,integer b3 returns integer
    if n==2 then
        return b0*256+b1
    elseif n==3 then
        return (b0*256+b1)*256+b2
    endif
    return ((b0*256+b1)*256+b2)*256+b3
endfunction

function DB_sh_car takes string c,integer n,integer b0,integer b1,integer b2,integer b3 returns nothing
    local integer h=StringHash(c)
    call SaveStr(DB_sh_ht, 12, DB_sh_chave(n, b0, b1, b2, b3), c)
    if HaveSavedString(DB_sh_ht, 4, h) then
        return
    endif
    call SaveStr(DB_sh_ht, 4, h, c)
    call SaveInteger(DB_sh_ht, 5, h, n)
    call SaveInteger(DB_sh_ht, 6, h, b0)
    call SaveInteger(DB_sh_ht, 7, h, b1)
    call SaveInteger(DB_sh_ht, 8, h, b2)
    call SaveInteger(DB_sh_ht, 9, h, b3)
endfunction

function DB_sh_ini takes nothing returns nothing
    local integer k=32
    if DB_sh_ht!=null then
        return
    endif
    set DB_sh_ht=InitHashtable()
    set DB_sh_memo=InitHashtable()
    call DB_pot_init()
    call DB_chr_init()
    loop
        exitwhen k>126
        if k>=97 and k<=122 then
            call DB_sh_ascii(DB_CHR[k], k-32, k, true)
        elseif k==47 then
            call DB_sh_ascii(DB_CHR[k], 92, 47, true)
        else
            call DB_sh_ascii(DB_CHR[k], k, k, false)
        endif
        set k=k+1
    endloop
    call DB_sh_ascii("\n", 10, 10, false)
    call DB_sh_ascii("\r", 13, 13, false)
    call DB_sh_ascii("\t", 9, 9, false)
    call DB_sh_chars()
endfunction

function DB_sh_byte_cru takes string c returns integer
    local integer h=StringHash(c)
    if HaveSavedString(DB_sh_ht, 0, h) and LoadStr(DB_sh_ht, 0, h)==c then
        return LoadInteger(DB_sh_ht, 10, h)
    endif
    if HaveSavedString(DB_sh_ht, 2, h) and LoadStr(DB_sh_ht, 2, h)==c then
        return LoadInteger(DB_sh_ht, 11, h)
    endif
    return -1
endfunction

function DB_sh_byte takes string c returns integer
    local integer h=StringHash(c)
    if HaveSavedString(DB_sh_ht, 0, h) and LoadStr(DB_sh_ht, 0, h)==c then
        return LoadInteger(DB_sh_ht, 1, h)
    endif
    if HaveSavedString(DB_sh_ht, 2, h) and LoadStr(DB_sh_ht, 2, h)==c then
        return LoadInteger(DB_sh_ht, 3, h)
    endif
    return -1
endfunction

function DB_sh_multi takes string c returns integer
    local integer h=StringHash(c)
    if HaveSavedString(DB_sh_ht, 4, h) and LoadStr(DB_sh_ht, 4, h)==c then
        return LoadInteger(DB_sh_ht, 5, h)
    endif
    return 0
endfunction

function DB_sh_poe takes string c,integer m returns integer
    local integer h=StringHash(c)
    local integer n=LoadInteger(DB_sh_ht, 5, h)
    set DB_shb[m]=LoadInteger(DB_sh_ht, 6, h)
    if n>=2 then
        set DB_shb[m+1]=LoadInteger(DB_sh_ht, 7, h)
    endif
    if n>=3 then
        set DB_shb[m+2]=LoadInteger(DB_sh_ht, 8, h)
    endif
    if n>=4 then
        set DB_shb[m+3]=LoadInteger(DB_sh_ht, 9, h)
    endif
    return m+n
endfunction

function DB_SH takes string s returns integer
    local integer h0
    local integer n
    local integer i=0
    local integer m=0
    local integer k
    local integer v
    local integer a
    local integer b
    local integer c
    local integer j
    local integer t
    local string ch
    if s==null then
        set s=""
    endif
    if DB_sh_ht==null then
        call DB_sh_ini()
    endif
    set h0=StringHash(s)
    if HaveSavedString(DB_sh_memo, 0, h0) and LoadStr(DB_sh_memo, 0, h0)==s then
        return LoadInteger(DB_sh_memo, 1, h0)
    endif
    set n=StringLength(s)
    loop
        exitwhen i>=n or m>=DB_SH_MAX_BYTES
        set ch=SubString(s, i, i+1)
        set v=DB_sh_byte(ch)
        if v>=0 then
            set DB_shb[m]=v
            set m=m+1
            set i=i+1
        else
            set k=DB_sh_multi(SubString(s, i, i+3))
            if k==3 then
                set m=DB_sh_poe(SubString(s, i, i+3), m)
            else
                set k=DB_sh_multi(SubString(s, i, i+2))
                if k==2 then
                    set m=DB_sh_poe(SubString(s, i, i+2), m)
                else
                    set k=DB_sh_multi(SubString(s, i, i+4))
                    if k==4 then
                        set m=DB_sh_poe(SubString(s, i, i+4), m)
                    else
                        set t=StringHash(ch)
                        if t<0 then
                            set t=-(t+1)
                        endif
                        set DB_shb[m]=128+t-(t/128)*128
                        set m=m+1
                        set k=1
                    endif
                endif
            endif
            set i=i+k
        endif
    endloop
    set a=0x9E3779B9
    set b=0x9E3779B9
    set c=0
    set i=0
    loop
        exitwhen m-i<12
        set a=a+DB_shb[i]+DB_shb[i+1]*256+DB_shb[i+2]*65536+DB_shb[i+3]*16777216
        set b=b+DB_shb[i+4]+DB_shb[i+5]*256+DB_shb[i+6]*65536+DB_shb[i+7]*16777216
        set c=c+DB_shb[i+8]+DB_shb[i+9]*256+DB_shb[i+10]*65536+DB_shb[i+11]*16777216
        call DB_sh_mix(a, b, c)
        set a=DB_sh_x
        set b=DB_sh_y
        set c=DB_sh_z
        set i=i+12
    endloop
    set c=c+m
    set j=0
    loop
        exitwhen i+j>=m
        if j<4 then
            set a=a+DB_shb[i+j]*DB_POT2[j*8]
        elseif j<8 then
            set b=b+DB_shb[i+j]*DB_POT2[(j-4)*8]
        else
            set c=c+DB_shb[i+j]*DB_POT2[(j-7)*8]
        endif
        set j=j+1
    endloop
    call DB_sh_mix(a, b, c)
    set c=DB_sh_z
    if DB_sh_memo_n<DB_SH_MEMO_MAX then
        call SaveStr(DB_sh_memo, 0, h0, s)
        call SaveInteger(DB_sh_memo, 1, h0, c)
        set DB_sh_memo_n=DB_sh_memo_n+1
    endif
    return c
endfunction

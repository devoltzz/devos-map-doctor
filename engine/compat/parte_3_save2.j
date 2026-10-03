// ==============================================================================================
// ==============================================================================================

string array DB_ALFA
integer array DB_LV
boolean DB_c2_on=false

function DB_c2_init takes nothing returns nothing
    local integer i
    if DB_c2_on then
        return
    endif
    set DB_c2_on=true
    set i=0
    loop
        exitwhen i>255
        set DB_LV[i]=-1
        set i=i+1
    endloop
    set DB_ALFA[0]="0"
    set DB_ALFA[1]="1"
    set DB_ALFA[2]="2"
    set DB_ALFA[3]="3"
    set DB_ALFA[4]="4"
    set DB_ALFA[5]="5"
    set DB_ALFA[6]="6"
    set DB_ALFA[7]="7"
    set DB_ALFA[8]="8"
    set DB_ALFA[9]="9"
    set DB_LV[48]=0
    set DB_LV[49]=1
    set DB_LV[50]=2
    set DB_LV[51]=3
    set DB_LV[52]=4
    set DB_LV[53]=5
    set DB_LV[54]=6
    set DB_LV[55]=7
    set DB_LV[56]=8
    set DB_LV[57]=9
    set DB_ALFA[10]="A"
    set DB_ALFA[11]="B"
    set DB_ALFA[12]="C"
    set DB_ALFA[13]="D"
    set DB_ALFA[14]="E"
    set DB_ALFA[15]="F"
    set DB_ALFA[16]="G"
    set DB_ALFA[17]="H"
    set DB_ALFA[18]="I"
    set DB_ALFA[19]="J"
    set DB_ALFA[20]="K"
    set DB_ALFA[21]="L"
    set DB_ALFA[22]="M"
    set DB_ALFA[23]="N"
    set DB_ALFA[24]="O"
    set DB_ALFA[25]="P"
    set DB_ALFA[26]="Q"
    set DB_ALFA[27]="R"
    set DB_ALFA[28]="S"
    set DB_ALFA[29]="T"
    set DB_ALFA[30]="U"
    set DB_ALFA[31]="V"
    set DB_ALFA[32]="W"
    set DB_ALFA[33]="X"
    set DB_ALFA[34]="Y"
    set DB_ALFA[35]="Z"
    set DB_LV[65]=10
    set DB_LV[66]=11
    set DB_LV[67]=12
    set DB_LV[68]=13
    set DB_LV[69]=14
    set DB_LV[70]=15
    set DB_LV[71]=16
    set DB_LV[72]=17
    set DB_LV[73]=18
    set DB_LV[74]=19
    set DB_LV[75]=20
    set DB_LV[76]=21
    set DB_LV[77]=22
    set DB_LV[78]=23
    set DB_LV[79]=24
    set DB_LV[80]=25
    set DB_LV[81]=26
    set DB_LV[82]=27
    set DB_LV[83]=28
    set DB_LV[84]=29
    set DB_LV[85]=30
    set DB_LV[86]=31
    set DB_LV[87]=32
    set DB_LV[88]=33
    set DB_LV[89]=34
    set DB_LV[90]=35
    set DB_ALFA[36]="a"
    set DB_ALFA[37]="b"
    set DB_ALFA[38]="c"
    set DB_ALFA[39]="d"
    set DB_ALFA[40]="e"
    set DB_ALFA[41]="f"
    set DB_ALFA[42]="g"
    set DB_ALFA[43]="h"
    set DB_ALFA[44]="i"
    set DB_ALFA[45]="j"
    set DB_ALFA[46]="k"
    set DB_ALFA[47]="l"
    set DB_ALFA[48]="m"
    set DB_ALFA[49]="n"
    set DB_ALFA[50]="o"
    set DB_ALFA[51]="p"
    set DB_ALFA[52]="q"
    set DB_ALFA[53]="r"
    set DB_ALFA[54]="s"
    set DB_ALFA[55]="t"
    set DB_ALFA[56]="u"
    set DB_ALFA[57]="v"
    set DB_ALFA[58]="w"
    set DB_ALFA[59]="x"
    set DB_ALFA[60]="y"
    set DB_ALFA[61]="z"
    set DB_LV[97]=36
    set DB_LV[98]=37
    set DB_LV[99]=38
    set DB_LV[100]=39
    set DB_LV[101]=40
    set DB_LV[102]=41
    set DB_LV[103]=42
    set DB_LV[104]=43
    set DB_LV[105]=44
    set DB_LV[106]=45
    set DB_LV[107]=46
    set DB_LV[108]=47
    set DB_LV[109]=48
    set DB_LV[110]=49
    set DB_LV[111]=50
    set DB_LV[112]=51
    set DB_LV[113]=52
    set DB_LV[114]=53
    set DB_LV[115]=54
    set DB_LV[116]=55
    set DB_LV[117]=56
    set DB_LV[118]=57
    set DB_LV[119]=58
    set DB_LV[120]=59
    set DB_LV[121]=60
    set DB_LV[122]=61
    set DB_ALFA[62]="+"
    set DB_ALFA[63]="-"
    set DB_LV[43]=62
    set DB_LV[45]=63
endfunction

integer array DB_NORM
boolean DB_norm_on=false
integer array DB_TAIL

function DB_norm_init takes nothing returns nothing
    local integer i
    if DB_norm_on then
        return
    endif
    set DB_norm_on=true
    set i=0
    loop
        exitwhen i>255
        set DB_NORM[i]=i
        set i=i+1
    endloop
    set i=97
    loop
        exitwhen i>122
        set DB_NORM[i]=i-32
        set i=i+1
    endloop
    set DB_NORM[47]=92
    set DB_TAIL[0]=0
    set DB_TAIL[1]=0
    set DB_TAIL[2]=8
    set DB_TAIL[3]=16
    set DB_TAIL[4]=24
    set DB_TAIL[5]=0
    set DB_TAIL[6]=8
    set DB_TAIL[7]=16
    set DB_TAIL[8]=24
    set DB_TAIL[9]=8
    set DB_TAIL[10]=16
    set DB_TAIL[11]=24
endfunction

integer array DB_CC
integer DB_cc_on=0

function DB_code_init takes nothing returns nothing
    local integer i=0
    if DB_cc_on==1 then
        return
    endif
    set DB_cc_on=1
    loop
        exitwhen i>255
        set DB_CC[i]=-1
        set i=i+1
    endloop
    set DB_CC[48]=48
    set DB_CC[49]=49
    set DB_CC[50]=50
    set DB_CC[51]=51
    set DB_CC[52]=52
    set DB_CC[53]=53
    set DB_CC[54]=54
    set DB_CC[55]=55
    set DB_CC[56]=56
    set DB_CC[57]=57
    set DB_CC[65]=65
    set DB_CC[66]=66
    set DB_CC[67]=67
    set DB_CC[68]=68
    set DB_CC[69]=69
    set DB_CC[70]=70
    set DB_CC[71]=71
    set DB_CC[72]=72
    set DB_CC[73]=73
    set DB_CC[74]=74
    set DB_CC[75]=75
    set DB_CC[76]=76
    set DB_CC[77]=77
    set DB_CC[78]=78
    set DB_CC[79]=79
    set DB_CC[80]=80
    set DB_CC[81]=81
    set DB_CC[82]=82
    set DB_CC[83]=83
    set DB_CC[84]=84
    set DB_CC[85]=85
    set DB_CC[86]=86
    set DB_CC[87]=87
    set DB_CC[88]=88
    set DB_CC[89]=89
    set DB_CC[90]=90
    set DB_CC[97]=97
    set DB_CC[98]=98
    set DB_CC[99]=99
    set DB_CC[100]=100
    set DB_CC[101]=101
    set DB_CC[102]=102
    set DB_CC[103]=103
    set DB_CC[104]=104
    set DB_CC[105]=105
    set DB_CC[106]=106
    set DB_CC[107]=107
    set DB_CC[108]=108
    set DB_CC[109]=109
    set DB_CC[110]=110
    set DB_CC[111]=111
    set DB_CC[112]=112
    set DB_CC[113]=113
    set DB_CC[114]=114
    set DB_CC[115]=115
    set DB_CC[116]=116
    set DB_CC[117]=117
    set DB_CC[118]=118
    set DB_CC[119]=119
    set DB_CC[120]=120
    set DB_CC[121]=121
    set DB_CC[122]=122
    set DB_CC[43]=43
    set DB_CC[45]=45
    set DB_CC[61]=61
    set DB_CC[46]=46
    set DB_CC[124]=124
    set DB_CC[92]=92
    set DB_CC[95]=95
    set DB_CC[58]=58
    set DB_CC[59]=59
    set DB_CC[64]=64
    set DB_CC[35]=35
    set DB_CC[37]=37
    set DB_CC[32]=32
endfunction

function DB_u32 takes integer n returns integer
    if n<0 then
        return n+2147483647+1
    endif
    return n
endfunction

function DB_shl takes integer a,integer k returns integer
    return a*DB_POT2[k]
endfunction

function DB_shr takes integer a,integer k returns integer
    if k<=0 then
        return a
    endif
    if k>31 then
        return 0
    endif
    if a<0 then
        return DB_u32(a)/DB_POT2[k]+DB_POT2[31-k]
    endif
    return a/DB_POT2[k]
endfunction

integer array DB_POT2
boolean DB_pot_on=false

function DB_pot_init takes nothing returns nothing
    if DB_pot_on then
        return
    endif
    set DB_pot_on=true
    set DB_POT2[0]=1
    set DB_POT2[1]=2
    set DB_POT2[2]=4
    set DB_POT2[3]=8
    set DB_POT2[4]=16
    set DB_POT2[5]=32
    set DB_POT2[6]=64
    set DB_POT2[7]=128
    set DB_POT2[8]=256
    set DB_POT2[9]=512
    set DB_POT2[10]=1024
    set DB_POT2[11]=2048
    set DB_POT2[12]=4096
    set DB_POT2[13]=8192
    set DB_POT2[14]=16384
    set DB_POT2[15]=32768
    set DB_POT2[16]=65536
    set DB_POT2[17]=131072
    set DB_POT2[18]=262144
    set DB_POT2[19]=524288
    set DB_POT2[20]=1048576
    set DB_POT2[21]=2097152
    set DB_POT2[22]=4194304
    set DB_POT2[23]=8388608
    set DB_POT2[24]=16777216
    set DB_POT2[25]=33554432
    set DB_POT2[26]=67108864
    set DB_POT2[27]=134217728
    set DB_POT2[28]=268435456
    set DB_POT2[29]=536870912
    set DB_POT2[30]=1073741824
endfunction

integer array DB_XN
boolean DB_xn_on=false

function DB_xor_init takes nothing returns nothing
    local integer i=0
    local integer x
    local integer y
    local integer v
    local integer k
    if DB_xn_on then
        return
    endif
    set DB_xn_on=true
    loop
        exitwhen i>255
        set x=i-i/16*16
        set y=i/16
        set v=0
        set k=0
        loop
            exitwhen k>3
            if (x/DB_POT2[k]-x/DB_POT2[k+1]*2)!= (y/DB_POT2[k]-y/DB_POT2[k+1]*2) then
                set v=v+DB_POT2[k]
            endif
            set k=k+1
        endloop
        set DB_XN[i]=v
        set i=i+1
    endloop
endfunction

function DB_bxor takes integer a,integer b returns integer
    local integer r=0
    local integer k=0
    local integer ta
    local integer tb
    local integer v
    call DB_xor_init()
    if a==b then
        return 0
    endif
    set ta=DB_u32(a)
    set tb=DB_u32(b)
    loop
        exitwhen k>6
        set r=r+DB_XN[(tb-tb/16*16)*16+(ta-ta/16*16)]*DB_POT2[k*4]
        set ta=ta/16
        set tb=tb/16
        set k=k+1
    endloop
    if a<0 then
        set ta=ta+8
    endif
    if b<0 then
        set tb=tb+8
    endif
    set v=DB_XN[tb*16+ta]
    if v>=8 then
        return r+(v-8)*268435456-2147483647-1
    endif
    return r+v*268435456
endfunction

constant string DB_C2_SEGREDO="{{KK_SAVE_SEGREDO}}"
constant string DB_C2_ENV="{{KK_SAVE_ENV}}"
constant integer DB_C2_GEN=2
constant string DB_C2_CH_BLOB="{{KK_SAVE_CH_BLOB}}"
constant string DB_C2_CH_ENV="{{KK_SAVE_CH_ENV}}"
constant string DB_C2_CH_IV="{{KK_SAVE_CH_IV}}"
constant string DB_C2_CH_LEN="{{KK_SAVE_CH_LEN}}"
constant string DB_C2_CH_N="{{KK_SAVE_CH_N}}"
constant string DB_C2_CH_SIG="{{KK_SAVE_CH_SIG}}"
constant string DB_C2_CH_GEN="{{KK_SAVE_CH_GEN}}"

integer DB_j_a=0
integer DB_j_b=0
integer DB_j_c=0
integer DB_mx_a=0
integer DB_mx_b=0
integer DB_mx_c=0

function DB_jmix3 takes integer a,integer b,integer c returns nothing
    set a=DB_bxor(a-b-c, DB_shr(c, 13))
    set b=DB_bxor(b-c-a, DB_shl(a, 8))
    set c=DB_bxor(c-a-b, DB_shr(b, 13))
    set a=DB_bxor(a-b-c, DB_shr(c, 12))
    set b=DB_bxor(b-c-a, DB_shl(a, 16))
    set c=DB_bxor(c-a-b, DB_shr(b, 5))
    set a=DB_bxor(a-b-c, DB_shr(c, 3))
    set b=DB_bxor(b-c-a, DB_shl(a, 10))
    set c=DB_bxor(c-a-b, DB_shr(b, 15))
    set DB_mx_a=a
    set DB_mx_b=b
    set DB_mx_c=c
endfunction

function DB_sh takes string s returns integer
    local integer n
    local integer i=0
    local integer left
    local integer a=0x9E3779B9
    local integer b=0x9E3779B9
    local integer c=0
    local integer v
    local integer j
    call DB_norm_init()
    call DB_code_init()
    call DB_pot_init()
    if s==null then
        set s=""
    endif
    set n=StringLength(s)
    set left=n
    loop
        exitwhen left<12
        set a=a+DB_NORM[DB_byte_at(s, i)]+DB_NORM[DB_byte_at(s, i+1)]*256+DB_NORM[DB_byte_at(s, i+2)]*65536+DB_NORM[DB_byte_at(s, i+3)]*16777216
        set b=b+DB_NORM[DB_byte_at(s, i+4)]+DB_NORM[DB_byte_at(s, i+5)]*256+DB_NORM[DB_byte_at(s, i+6)]*65536+DB_NORM[DB_byte_at(s, i+7)]*16777216
        set c=c+DB_NORM[DB_byte_at(s, i+8)]+DB_NORM[DB_byte_at(s, i+9)]*256+DB_NORM[DB_byte_at(s, i+10)]*65536+DB_NORM[DB_byte_at(s, i+11)]*16777216
        call DB_jmix3(a, b, c)
        set a=DB_mx_a
        set b=DB_mx_b
        set c=DB_mx_c
        set i=i+12
        set left=left-12
    endloop
    set c=c+n
    set j=1
    loop
        exitwhen j>left
        set v=DB_NORM[DB_byte_at(s, i+j-1)]*DB_POT2[DB_TAIL[j]]
        if j<=4 then
            set a=a+v
        elseif j<=8 then
            set b=b+v
        else
            set c=c+v
        endif
        set j=j+1
    endloop
    call DB_jmix3(a, b, c)
    return DB_mx_c
endfunction

string array DB_HEXL
boolean DB_hexl_on=false

function DB_hexl_init takes nothing returns nothing
    if DB_hexl_on then
        return
    endif
    set DB_hexl_on=true
    set DB_HEXL[0]="0"
    set DB_HEXL[1]="1"
    set DB_HEXL[2]="2"
    set DB_HEXL[3]="3"
    set DB_HEXL[4]="4"
    set DB_HEXL[5]="5"
    set DB_HEXL[6]="6"
    set DB_HEXL[7]="7"
    set DB_HEXL[8]="8"
    set DB_HEXL[9]="9"
    set DB_HEXL[10]="a"
    set DB_HEXL[11]="b"
    set DB_HEXL[12]="c"
    set DB_HEXL[13]="d"
    set DB_HEXL[14]="e"
    set DB_HEXL[15]="f"
endfunction

function DB_hex32 takes integer n returns string
    local string out=""
    local integer k=7
    local integer d
    local boolean neg=n<0
    call DB_hexl_init()
    call DB_pot_init()
    set n=DB_u32(n)
    loop
        exitwhen k<0
        set d=n/DB_POT2[k*4]
        set d=d-d/16*16
        if k==7 and neg then
            set d=d+8
        endif
        set out=out+DB_HEXL[d]
        set k=k-1
    endloop
    return out
endfunction

function DB_hex_val takes string c returns integer
    local integer i=0
    call DB_hexl_init()
    loop
        exitwhen i>15
        if DB_HEXL[i]==c then
            return i
        endif
        set i=i+1
    endloop
    return -1
endfunction

function DB_hex8_int takes string s returns integer
    local integer i=0
    local integer v
    local integer r=0
    if s==null or StringLength(s)!=8 then
        return -1
    endif
    loop
        exitwhen i>7
        set v=DB_hex_val(SubString(s, i, i+1))
        if v<0 then
            return -1
        endif
        set r=DB_i32(r*16+v)
        set i=i+1
    endloop
    return r
endfunction

integer DB_k1
integer DB_k2

function DB_chaves takes string pasta,string env8 returns nothing
    local string base=DB_C2_SEGREDO+"|"+pasta+"|"+env8
    set DB_k1=DB_SH(base+"|k1")
    set DB_k2=DB_SH(base+"|k2")
endfunction

function DB_absorve takes integer k1,integer k2,string cab returns nothing
    set DB_j_a=BlzBitXor(k1, DB_SH("h1|"+cab))
    set DB_j_b=k2+DB_SH("h2|"+cab)
endfunction

function DB_byte_at takes string s,integer i returns integer
    local integer k=32
    local string c
    if i<0 or i>=StringLength(s) then
        return 0
    endif
    set c=SubString(s, i, i+1)
    call DB_chr_init()
    loop
        exitwhen k>126
        if DB_CHR[k]==c then
            return k
        endif
        set k=k+1
    endloop
    return 0
endfunction

// ==============================================================================================
// ==============================================================================================
integer array DB_U
integer DB_z

function DB_fluxo takes integer x,integer y returns nothing
    set x=DB_bxor(x, DB_shl(x, 13))
    set x=DB_bxor(x, DB_shr(x, 17))
    set x=DB_bxor(x, DB_shl(x, 5))
    set y=DB_bxor(y, DB_shl(y, 13))
    set y=DB_bxor(y, DB_shr(y, 17))
    set y=DB_bxor(y, DB_shl(y, 5))
    set DB_j_a=x
    set DB_j_b=y
endfunction

function DB_mac_par takes integer h1,integer h2 returns nothing
    set h1=DB_i32(h1+DB_U[0]+DB_shl(DB_U[1], 12))
    set h1=DB_bxor(h1, DB_shr(h1, 13))
    set h1=DB_i32(h1+DB_shl(h1, 9))
    set h2=DB_bxor(h2, DB_i32(DB_U[2]+DB_shl(DB_U[3], 12)))
    set h2=DB_i32(h2+DB_shl(h2, 7))
    set h2=DB_bxor(h2, DB_shr(h2, 11))
    set h1=DB_bxor(h1, DB_i32(DB_U[4]+DB_shl(DB_U[5], 12)))
    set h2=DB_i32(h2+DB_i32(DB_U[6]+DB_shl(DB_U[7], 12))+h1)
    set DB_j_a=h1
    set DB_j_b=h2
endfunction

function DB_bloco takes string p,integer i,integer n returns nothing
    local integer b1=0
    local integer b2=0
    local integer b3=0
    local integer b4=0
    local integer b5=0
    local integer b6=0
    local integer b7=0
    local integer b8=0
    local integer b9=0
    local integer b10=0
    local integer b11=0
    local integer b12=0
    if i<n then
        set b1=DB_byte_at(p, i)
    endif
    if i+1<n then
        set b2=DB_byte_at(p, i+1)
    endif
    if i+2<n then
        set b3=DB_byte_at(p, i+2)
    endif
    if i+3<n then
        set b4=DB_byte_at(p, i+3)
    endif
    if i+4<n then
        set b5=DB_byte_at(p, i+4)
    endif
    if i+5<n then
        set b6=DB_byte_at(p, i+5)
    endif
    if i+6<n then
        set b7=DB_byte_at(p, i+6)
    endif
    if i+7<n then
        set b8=DB_byte_at(p, i+7)
    endif
    if i+8<n then
        set b9=DB_byte_at(p, i+8)
    endif
    if i+9<n then
        set b10=DB_byte_at(p, i+9)
    endif
    if i+10<n then
        set b11=DB_byte_at(p, i+10)
    endif
    if i+11<n then
        set b12=DB_byte_at(p, i+11)
    endif
    set DB_U[0]=b1*16+b2/16
    set DB_U[1]=(b2-b2/16*16)*256+b3
    set DB_U[2]=b4*16+b5/16
    set DB_U[3]=(b5-b5/16*16)*256+b6
    set DB_U[4]=b7*16+b8/16
    set DB_U[5]=(b8-b8/16*16)*256+b9
    set DB_U[6]=b10*16+b11/16
    set DB_U[7]=(b11-b11/16*16)*256+b12
endfunction

function DB_cifra takes string p,integer k1,integer k2,integer iv,integer h1,integer h2 returns string
    local integer n=StringLength(p)
    local integer pad
    local integer m
    local integer x
    local integer y
    local integer i=0
    local string out=""
    set pad=12-(n-n/12*12)
    if pad==12 then
        set pad=0
    endif
    set m=n+pad
    set x=DB_bxor(k1, iv)
    set y=DB_i32(k2+iv)
    if x==0 then
        set x=455954835
    endif
    if y==0 then
        set y=1812535653
    endif
    loop
        exitwhen i>=m
        call DB_bloco(p, i, n)
        call DB_fluxo(x, y)
        set x=DB_j_a
        set y=DB_j_b
        set DB_z=DB_i32(x+y)
        set DB_U[0]=DB_bxor(DB_U[0], DB_shr(x, 20))
        set DB_U[1]=DB_bxor(DB_U[1], DB_shr(x, 8))
        set DB_U[2]=DB_bxor(DB_U[2], DB_shr(y, 20))
        set DB_U[3]=DB_bxor(DB_U[3], DB_shr(y, 8))
        set DB_U[4]=DB_bxor(DB_U[4], DB_shr(DB_z, 20))
        set DB_U[5]=DB_bxor(DB_U[5], DB_shr(DB_z, 8))
        set DB_U[6]=DB_bxor(DB_U[6], DB_shr(DB_bxor(x, y), 14))
        set DB_U[7]=DB_bxor(DB_U[7], DB_shr(DB_bxor(x, y), 2))
        set out=out+DB_ALFA[DB_U[0]/64]+DB_ALFA[DB_U[0]-DB_U[0]/64*64]
        set out=out+DB_ALFA[DB_U[1]/64]+DB_ALFA[DB_U[1]-DB_U[1]/64*64]
        set out=out+DB_ALFA[DB_U[2]/64]+DB_ALFA[DB_U[2]-DB_U[2]/64*64]
        set out=out+DB_ALFA[DB_U[3]/64]+DB_ALFA[DB_U[3]-DB_U[3]/64*64]
        set out=out+DB_ALFA[DB_U[4]/64]+DB_ALFA[DB_U[4]-DB_U[4]/64*64]
        set out=out+DB_ALFA[DB_U[5]/64]+DB_ALFA[DB_U[5]-DB_U[5]/64*64]
        set out=out+DB_ALFA[DB_U[6]/64]+DB_ALFA[DB_U[6]-DB_U[6]/64*64]
        set out=out+DB_ALFA[DB_U[7]/64]+DB_ALFA[DB_U[7]-DB_U[7]/64*64]
        call DB_mac_par(h1, h2)
        set h1=DB_j_a
        set h2=DB_j_b
        set x=DB_bxor(x, DB_U[7])
        set y=DB_i32(y+DB_U[0])
        set i=i+12
    endloop
    set DB_j_a=h1
    set DB_j_b=h2
    return out
endfunction

function DB_decifra takes string t,integer k1,integer k2,integer iv,integer h1,integer h2 returns string
    local integer m=StringLength(t)
    local integer x
    local integer y
    local integer i=0
    local integer k
    local integer a
    local integer v1
    local integer v2
    local integer v3
    local integer v4
    local integer v5
    local integer v6
    local integer v7
    local integer v8
    local string out=""
    if m-m/16*16!=0 then
        return null
    endif
    set x=DB_bxor(k1, iv)
    set y=DB_i32(k2+iv)
    if x==0 then
        set x=455954835
    endif
    if y==0 then
        set y=1812535653
    endif
    call DB_c2_init()
    call DB_chr_init()
    loop
        exitwhen i>=m
        set k=0
        loop
            exitwhen k>7
            set a=DB_LV[DB_byte_at(t, i+k*2)]
            if a<0 then
                return null
            endif
            set DB_U[k]=a*64
            set a=DB_LV[DB_byte_at(t, i+k*2+1)]
            if a<0 then
                return null
            endif
            set DB_U[k]=DB_U[k]+a
            set k=k+1
        endloop
        call DB_fluxo(x, y)
        set x=DB_j_a
        set y=DB_j_b
        set DB_z=DB_i32(x+y)
        call DB_mac_par(h1, h2)
        set h1=DB_j_a
        set h2=DB_j_b
        set v1=DB_bxor(DB_U[0], DB_shr(x, 20))
        set v2=DB_bxor(DB_U[1], DB_shr(x, 8))
        set v3=DB_bxor(DB_U[2], DB_shr(y, 20))
        set v4=DB_bxor(DB_U[3], DB_shr(y, 8))
        set v5=DB_bxor(DB_U[4], DB_shr(DB_z, 20))
        set v6=DB_bxor(DB_U[5], DB_shr(DB_z, 8))
        set v7=DB_bxor(DB_U[6], DB_shr(DB_bxor(x, y), 14))
        set v8=DB_bxor(DB_U[7], DB_shr(DB_bxor(x, y), 2))
        set out=out+DB_CHR[v1/16]+DB_CHR[(v1-v1/16*16)*16+v2/256]+DB_CHR[v2-v2/256*256]
        set out=out+DB_CHR[v3/16]+DB_CHR[(v3-v3/16*16)*16+v4/256]+DB_CHR[v4-v4/256*256]
        set out=out+DB_CHR[v5/16]+DB_CHR[(v5-v5/16*16)*16+v6/256]+DB_CHR[v6-v6/256*256]
        set out=out+DB_CHR[v7/16]+DB_CHR[(v7-v7/16*16)*16+v8/256]+DB_CHR[v8-v8/256*256]
        set x=DB_bxor(x, DB_U[7])
        set y=DB_i32(y+DB_U[0])
        set i=i+16
    endloop
    set DB_j_a=h1
    set DB_j_b=h2
    return out
endfunction
// ==============================================================================================
// ==============================================================================================
function DB_max takes integer a,integer b returns integer
    if a>b then
        return a
    endif
    return b
endfunction

// ==============================================================================================
// ==============================================================================================
group DB_foto_g=null

function DB_foto takes nothing returns string
    local integer i=0
    local integer n
    local string out=""
    local player p
    loop
        exitwhen i>15
        set p=Player(i)
        if p!=null then
            set out=out+I2S(GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD))+","+I2S(GetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER))+","+I2S(GetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_USED))+","+I2S(GetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_CAP))+","+I2S(GetPlayerState(p, PLAYER_STATE_GOLD_GATHERED))+","+I2S(GetPlayerState(p, PLAYER_STATE_LUMBER_GATHERED))+","
            if GetPlayerController(p)==MAP_CONTROL_USER then
                set out=out+"U"
            else
                set out=out+"C"
            endif
            set out=out+I2S(GetPlayerState(p, PLAYER_STATE_GOLD_UPKEEP_RATE))
            set n=0
            call GroupEnumUnitsOfPlayer(DB_foto_g, p, null)
            set n=BlzGroupGetSize(DB_foto_g)
            call GroupClear(DB_foto_g)
            set out=out+";"+I2S(n)
        endif
        set i=i+1
    endloop
    set out=out+";t"+I2S(R2I(TimerGetElapsed(bj_gameStartedTimer)*10.0))
    return out
endfunction

function DB_foto_antes takes nothing returns string
    if DB_foto_g==null then
        set DB_foto_g=CreateGroup()
    endif
    return DB_foto()
endfunction

function DB_foto_confere takes string antes returns string
    local string agora
    local string a
    local string b
    local integer pa=0
    local integer pb=0
    local integer campo=1
    if antes==null or antes=="" then
        return ""
    endif
    set agora=DB_foto_antes()
    if agora==antes then
        return ""
    endif
    loop
        exitwhen campo>64
        set a=DB_ate(antes, ";", pa)
        set b=DB_ate(agora, ";", pb)
        if a==null and b==null then
            return "tamanho diferente"
        endif
        if a!=b then
            return "campo"+I2S(campo)+" ["+DB_corta(a)+"] -> ["+DB_corta(b)+"]"
        endif
        set pa=DB_pos(antes, ";", pa)
        set pb=DB_pos(agora, ";", pb)
        if pa<0 or pb<0 then
            return ""
        endif
        set pa=pa+1
        set pb=pb+1
        set campo=campo+1
    endloop
    return "mudou"
endfunction

function DB_ate takes string s,string sep,integer de returns string
    local integer p
    if s==null or de<0 or de>=StringLength(s) then
        return null
    endif
    set p=DB_pos(s, sep, de)
    if p<0 then
        return SubString(s, de, StringLength(s))
    endif
    return SubString(s, de, p)
endfunction

function DB_corta takes string s returns string
    if s==null then
        return "(vazio)"
    endif
    if StringLength(s)>40 then
        return SubString(s, 0, 40)+"..."
    endif
    return s
endfunction

boolean DB_cheatpld=false
string DB_cheatpld_oque=""

function DB_save2_recusa_gravacao takes nothing returns boolean
    return DB_cheatpld
endfunction

function DB_save2_cheatpld takes string arquivo,string oque returns nothing
    set DB_cheatpld=true
    set DB_cheatpld_oque=arquivo+": "+oque
    call DB_perfil_diag("CHEATPLD "+I2S(GetPlayerId(GetLocalPlayer()))+" "+DB_cheatpld_oque)
endfunction

function DB_eh_digitos takes string s returns boolean
    local integer i=0
    if s==null or s=="" then
        return false
    endif
    loop
        exitwhen i>=StringLength(s)
        if DB_byte_at(s, i)<48 or DB_byte_at(s, i)>57 then
            return false
        endif
        set i=i+1
    endloop
    return true
endfunction

function DB_env_campo takes string env,string chave returns string
    local integer p
    local integer e
    set p=DB_pos(env, chave+"=", 0)
    if p<0 then
        return ""
    endif
    set p=p+StringLength(chave)+1
    set e=DB_pos(env, "|", p)
    if e<0 then
        return SubString(env, p, StringLength(env))
    endif
    return SubString(env, p, e)
endfunction

string DB_s2_motivo=""
integer DB_s2_n_lida=-1
integer DB_s2_gen_lida=-1

function DB_save2_abre takes string blob,string pasta returns string
    local integer p
    local string t
    local string env
    local string env8
    local string iv8
    local string sig
    local string gen
    local string nn
    local string len_s
    local integer ln
    local integer cont
    local integer iv
    local integer h1
    local integer h2
    local string cab
    local string claro
    local string calc
    set DB_s2_motivo="formato"
    set DB_s2_n_lida=-1
    set DB_s2_gen_lida=-1
    if blob==null then
        return null
    endif
    if SubString(blob, 0, 11)!=DB_C2_CH_BLOB+"=" then
        return null
    endif
    set p=DB_pos(blob, "|", 11)
    if p<0 then
        return null
    endif
    set t=SubString(blob, 11, p)
    set env=SubString(blob, p+1, StringLength(blob))
    set env8=DB_env_campo(env, DB_C2_CH_ENV)
    set iv8=DB_env_campo(env, DB_C2_CH_IV)
    set sig=DB_env_campo(env, DB_C2_CH_SIG)
    set gen=DB_env_campo(env, DB_C2_CH_GEN)
    set nn=DB_env_campo(env, DB_C2_CH_N)
    set len_s=DB_env_campo(env, DB_C2_CH_LEN)
    if env8=="" or iv8=="" or sig=="" or gen=="" or nn=="" or len_s=="" then
        return null
    endif
    if not DB_eh_digitos(nn) or not DB_eh_digitos(len_s) then
        return null
    endif
    set ln=S2I(len_s)
    set cont=S2I(nn)
    if ln<0 or ln>StringLength(t)/16*12 then
        return null
    endif
    set iv=DB_hex8_int(iv8)
    if iv<0 then
        return null
    endif
    set DB_s2_gen_lida=S2I(gen)
    set DB_s2_n_lida=cont
    call DB_chaves(pasta, DB_C2_ENV)
    set h1=DB_k1
    set h2=DB_k2
    set cab=gen+"|"+env8+"|"+iv8+"|"+len_s+"|"+nn+"|"+pasta
    call DB_absorve(h1, h2, cab)
    set h1=DB_j_a
    set h2=DB_j_b
    set claro=DB_decifra(t, DB_k1, DB_k2, iv, h1, h2)
    if claro==null then
        set DB_s2_motivo="assinatura"
        set DB_s2_n_lida=-1
        return null
    endif
    set calc=DB_hex32(DB_j_a)+DB_hex32(DB_j_b)
    if calc!=sig then
        set DB_s2_motivo="assinatura"
        set DB_s2_n_lida=-1
        return null
    endif
    set DB_s2_motivo=""
    if ln==0 then
        return ""
    endif
    return SubString(claro, 0, ln)
endfunction

integer DB_s2_cont=0

function DB_save2_embrulha takes string claro,string pasta returns string
    local integer k1
    local integer k2
    local integer iv
    local integer h1
    local integer h2
    local integer n
    local string cifrado
    local string sig
    local string cab
    local string env
    local integer ln
    if claro==null then
        return null
    endif
    set ln=StringLength(claro)
    call DB_chaves(pasta, DB_C2_ENV)
    set k1=DB_k1
    set k2=DB_k2
    set iv=DB_sh(I2S(ln)+"|"+SubString(claro, 0, 48)+"|"+SubString(claro, DB_max(0, ln-47), StringLength(claro))+"|"+DB_hex32(k1))
    set DB_s2_cont=DB_s2_cont+1
    if DB_s2_cont<1 or DB_s2_cont>1073741823 then
        set DB_s2_cont=1
    endif
    set n=DB_s2_cont
    set cab=I2S(DB_C2_GEN)+"|"+DB_C2_ENV+"|"+DB_hex32(iv)+"|"+I2S(ln)+"|"+I2S(n)+"|"+pasta
    call DB_absorve(k1, k2, cab)
    set h1=DB_j_a
    set h2=DB_j_b
    set cifrado=DB_cifra(claro, k1, k2, iv, h1, h2)
    set sig=DB_hex32(DB_j_a)+DB_hex32(DB_j_b)
    set env=DB_C2_CH_ENV+"="+DB_C2_ENV+"|"+DB_C2_CH_GEN+"="+I2S(DB_C2_GEN)+"|"+DB_C2_CH_IV+"="+DB_hex32(iv)+"|"+DB_C2_CH_LEN+"="+I2S(ln)+"|"+DB_C2_CH_N+"="+I2S(n)+"|"+DB_C2_CH_SIG+"="+sig
    return DB_C2_CH_BLOB+"="+cifrado+"|"+env
endfunction

// ==============================================================================================
// ==============================================================================================
string array DB_CHR
boolean DB_chr_on=false

function DB_chr_init takes nothing returns nothing
    if DB_chr_on then
        return
    endif
    set DB_chr_on=true
    set DB_CHR[32]=" "
    set DB_CHR[33]="!"
    set DB_CHR[34]="\""
    set DB_CHR[35]="#"
    set DB_CHR[36]="$"
    set DB_CHR[37]="%"
    set DB_CHR[38]="&"
    set DB_CHR[39]="'"
    set DB_CHR[40]="("
    set DB_CHR[41]=")"
    set DB_CHR[42]="*"
    set DB_CHR[43]="+"
    set DB_CHR[44]=","
    set DB_CHR[45]="-"
    set DB_CHR[46]="."
    set DB_CHR[47]="/"
    set DB_CHR[48]="0"
    set DB_CHR[49]="1"
    set DB_CHR[50]="2"
    set DB_CHR[51]="3"
    set DB_CHR[52]="4"
    set DB_CHR[53]="5"
    set DB_CHR[54]="6"
    set DB_CHR[55]="7"
    set DB_CHR[56]="8"
    set DB_CHR[57]="9"
    set DB_CHR[58]=":"
    set DB_CHR[59]=";"
    set DB_CHR[60]="<"
    set DB_CHR[61]="="
    set DB_CHR[62]=">"
    set DB_CHR[63]="?"
    set DB_CHR[64]="@"
    set DB_CHR[65]="A"
    set DB_CHR[66]="B"
    set DB_CHR[67]="C"
    set DB_CHR[68]="D"
    set DB_CHR[69]="E"
    set DB_CHR[70]="F"
    set DB_CHR[71]="G"
    set DB_CHR[72]="H"
    set DB_CHR[73]="I"
    set DB_CHR[74]="J"
    set DB_CHR[75]="K"
    set DB_CHR[76]="L"
    set DB_CHR[77]="M"
    set DB_CHR[78]="N"
    set DB_CHR[79]="O"
    set DB_CHR[80]="P"
    set DB_CHR[81]="Q"
    set DB_CHR[82]="R"
    set DB_CHR[83]="S"
    set DB_CHR[84]="T"
    set DB_CHR[85]="U"
    set DB_CHR[86]="V"
    set DB_CHR[87]="W"
    set DB_CHR[88]="X"
    set DB_CHR[89]="Y"
    set DB_CHR[90]="Z"
    set DB_CHR[91]="["
    set DB_CHR[92]="\\"
    set DB_CHR[93]="]"
    set DB_CHR[94]="^"
    set DB_CHR[95]="_"
    set DB_CHR[96]="`"
    set DB_CHR[97]="a"
    set DB_CHR[98]="b"
    set DB_CHR[99]="c"
    set DB_CHR[100]="d"
    set DB_CHR[101]="e"
    set DB_CHR[102]="f"
    set DB_CHR[103]="g"
    set DB_CHR[104]="h"
    set DB_CHR[105]="i"
    set DB_CHR[106]="j"
    set DB_CHR[107]="k"
    set DB_CHR[108]="l"
    set DB_CHR[109]="m"
    set DB_CHR[110]="n"
    set DB_CHR[111]="o"
    set DB_CHR[112]="p"
    set DB_CHR[113]="q"
    set DB_CHR[114]="r"
    set DB_CHR[115]="s"
    set DB_CHR[116]="t"
    set DB_CHR[117]="u"
    set DB_CHR[118]="v"
    set DB_CHR[119]="w"
    set DB_CHR[120]="x"
    set DB_CHR[121]="y"
    set DB_CHR[122]="z"
    set DB_CHR[123]="{"
    set DB_CHR[124]="|"
    set DB_CHR[125]="}"
    set DB_CHR[126]="~"
endfunction

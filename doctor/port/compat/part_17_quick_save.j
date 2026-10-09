hashtable DB_sv_ht=null
constant integer DB_SV_FATIAS=16
constant integer DB_SV_ORCAMENTO=6000
trigger DB_sv_trig_grava=null
trigger DB_sv_trig_le=null
player DB_sv_dono=null
integer DB_sv_fase=0
integer DB_sv_i=0
integer DB_sv_etapa=0
integer DB_sv_pos=0
integer DB_sv_campos=0
string DB_sv_txt=""
integer DB_sv_ln=0
integer DB_sv_iv=0
integer DB_sv_n=0
string DB_sv_pasta=""
integer array DB_svb
integer DB_svn=0
integer DB_sv_x=0
integer DB_sv_y=0
integer DB_sv_h1=0
integer DB_sv_h2=0
string DB_sv_linha=""
integer DB_sv_ped=0
integer DB_sv_chars=0
boolean DB_sv_aberto=false
integer DB_sv_perdas=0
integer DB_sl_fase=0
integer DB_sl_bl=0
integer DB_sl_nbl=0
integer DB_sl_ln=0
integer DB_sl_feitos=0
integer DB_sl_x=0
integer DB_sl_y=0
integer DB_sl_h1=0
integer DB_sl_h2=0
string DB_sl_sig=""
string DB_sv_cur=""
integer DB_sv_cur_i=0
integer DB_sv_cur_p=0
string DB_sv_env=""
integer array DB_spb
integer DB_sp_est=0
boolean DB_sp_esc=false
string DB_sp_k=""
string DB_sp_v=""
integer DB_sp_u8n=0
integer DB_sp_u8k=0
integer DB_sp_n=0

function DB_sv_par_poe takes string s,integer v returns nothing
    local integer h=StringHash(s)
    local integer p=30
    loop
        exitwhen p>36
        if not HaveSavedString(DB_sv_ht, p, h) then
            call SaveStr(DB_sv_ht, p, h, s)
            call SaveInteger(DB_sv_ht, p+1, h, v)
            return
        endif
        set p=p+2
    endloop
endfunction

function DB_sv_fatia_grava takes nothing returns nothing
    call DB_sv_grava_passo()
endfunction

function DB_sv_fatia_le takes nothing returns nothing
    call DB_sl_passo()
endfunction

function DB_ini_tabelas_grandes takes nothing returns nothing
    if DB_seq_ht==null then
        call DB_seq_init()
    endif
    if DB_anim_ht==null then
        call DB_anim_init()
    endif
    if not DB_mod_ok then
        call DB_mod_indexa()
    endif
endfunction

function DB_sv_prepara takes nothing returns nothing
    local integer a=0
    local integer b
    local trigger t
    call DB_perfil_ht()
    call DB_nomes_crus()
    call DB_exit_garante()
    call DB_exab_garante()
    call DB_est_garante()
    call DB_ord_init()
    call DB_ui_ht_ok()
    //{{KK_INCLUI:sv_prepara_lua}}
    if DB_frame_ht==null then
        set DB_frame_ht=InitHashtable()
    endif
    if DB_ef_ht==null then
        set DB_ef_ht=InitHashtable()
    endif
    //{{KK_INCLUI:sv_prepara_tde}}
    set t=CreateTrigger()
    call TriggerAddAction(t, function DB_ini_tabelas_grandes)
    call TriggerExecute(t)
    call DestroyTrigger(t)
    set t=null
    if DB_efp_tmr==null then
        set DB_efp_tmr=CreateTimer()
    endif
    if DB_car_tmr==null then
        set DB_car_tmr=CreateTimer()
    endif
    if DB_mod_tmr==null then
        set DB_mod_tmr=CreateTimer()
    endif
    call DB_tabelas_init()
    call DB_sh_ini()
    call DB_hexl_init()
    if DB_foto_g==null then
        set DB_foto_g=CreateGroup()
    endif
    if DB_sv_ht!=null then
        return
    endif
    set DB_sv_ht=InitHashtable()
    set DB_sv_trig_grava=CreateTrigger()
    call TriggerAddAction(DB_sv_trig_grava, function DB_sv_fatia_grava)
    set DB_sv_trig_le=CreateTrigger()
    call TriggerAddAction(DB_sv_trig_le, function DB_sv_fatia_le)
    loop
        exitwhen a>63
        set b=0
        loop
            exitwhen b>63
            call DB_sv_par_poe(DB_ALFA[a]+DB_ALFA[b], a*64+b)
            set b=b+1
        endloop
        set a=a+1
    endloop
endfunction

function DB_sv_emite takes string ped returns nothing
    local integer slot=DB_sv_ped-(DB_sv_ped/DB_SLOT_N)*DB_SLOT_N
    local string linha
    if slot==0 then
        if DB_sv_aberto then
            call PreloadGenEnd(DB_caminho("profile_", DB_sv_ped/DB_SLOT_N))
        endif
        call PreloadGenClear()
        call PreloadGenStart()
        set DB_sv_aberto=true
    endif
    if DB_slot_kind[slot]==0 then
        set linha="call BlzSetAbilityTooltip("+DB_slot_txt[slot]+",\"@"+DB_pad5(DB_sv_ped+1)+ped+"\",0)"
    else
        set linha="call BlzSetAbilityExtendedTooltip("+DB_slot_txt[slot]+",\"@"+DB_pad5(DB_sv_ped+1)+ped+"\",0)"
    endif
    call Preload("\")\n"+linha+"\n//")
    set DB_sv_ped=DB_sv_ped+1
    set DB_sv_chars=DB_sv_chars+StringLength(ped)
endfunction

function DB_sv_bloco takes nothing returns nothing
    local integer x=DB_sv_x
    local integer y=DB_sv_y
    local integer h1=DB_sv_h1
    local integer h2=DB_sv_h2
    local integer z
    local integer w
    local integer u1
    local integer u2
    local integer u3
    local integer u4
    local integer u5
    local integer u6
    local integer u7
    local integer u8
    set x=BlzBitXor(x, x*8192)
    set x=BlzBitXor(x, BlzBitAnd((x-BlzBitAnd(x, 131071))/131072, 32767))
    set x=BlzBitXor(x, x*32)
    set y=BlzBitXor(y, y*8192)
    set y=BlzBitXor(y, BlzBitAnd((y-BlzBitAnd(y, 131071))/131072, 32767))
    set y=BlzBitXor(y, y*32)
    set z=x+y
    set w=BlzBitXor(x, y)
    set u1=BlzBitXor(DB_svb[0]*16+DB_svb[1]/16, BlzBitAnd((x-BlzBitAnd(x, 1048575))/1048576, 4095))
    set u2=BlzBitXor(BlzBitAnd(DB_svb[1], 15)*256+DB_svb[2], BlzBitAnd((x-BlzBitAnd(x, 255))/256, 4095))
    set u3=BlzBitXor(DB_svb[3]*16+DB_svb[4]/16, BlzBitAnd((y-BlzBitAnd(y, 1048575))/1048576, 4095))
    set u4=BlzBitXor(BlzBitAnd(DB_svb[4], 15)*256+DB_svb[5], BlzBitAnd((y-BlzBitAnd(y, 255))/256, 4095))
    set u5=BlzBitXor(DB_svb[6]*16+DB_svb[7]/16, BlzBitAnd((z-BlzBitAnd(z, 1048575))/1048576, 4095))
    set u6=BlzBitXor(BlzBitAnd(DB_svb[7], 15)*256+DB_svb[8], BlzBitAnd((z-BlzBitAnd(z, 255))/256, 4095))
    set u7=BlzBitXor(DB_svb[9]*16+DB_svb[10]/16, BlzBitAnd((w-BlzBitAnd(w, 16383))/16384, 4095))
    set u8=BlzBitXor(BlzBitAnd(DB_svb[10], 15)*256+DB_svb[11], BlzBitAnd((w-BlzBitAnd(w, 3))/4, 4095))
    set DB_sv_linha=DB_sv_linha+DB_ALFA[u1/64]+DB_ALFA[BlzBitAnd(u1, 63)]+DB_ALFA[u2/64]+DB_ALFA[BlzBitAnd(u2, 63)]+DB_ALFA[u3/64]+DB_ALFA[BlzBitAnd(u3, 63)]+DB_ALFA[u4/64]+DB_ALFA[BlzBitAnd(u4, 63)]+DB_ALFA[u5/64]+DB_ALFA[BlzBitAnd(u5, 63)]+DB_ALFA[u6/64]+DB_ALFA[BlzBitAnd(u6, 63)]+DB_ALFA[u7/64]+DB_ALFA[BlzBitAnd(u7, 63)]+DB_ALFA[u8/64]+DB_ALFA[BlzBitAnd(u8, 63)]
    set h1=h1+u1+u2*4096
    set h1=BlzBitXor(h1, BlzBitAnd((h1-BlzBitAnd(h1, 8191))/8192, 524287))
    set h1=h1+h1*512
    set h2=BlzBitXor(h2, u3+u4*4096)
    set h2=h2+h2*128
    set h2=BlzBitXor(h2, BlzBitAnd((h2-BlzBitAnd(h2, 2047))/2048, 2097151))
    set h1=BlzBitXor(h1, u5+u6*4096)
    set h2=h2+(u7+u8*4096)+h1
    set DB_sv_h1=h1
    set DB_sv_h2=h2
    set DB_sv_x=BlzBitXor(x, u8)
    set DB_sv_y=y+u1
    set DB_svn=0
    if StringLength(DB_sv_linha)>=DB_PEDACO then
        call DB_sv_emite(SubString(DB_sv_linha, 0, DB_PEDACO))
        set DB_sv_linha=SubString(DB_sv_linha, DB_PEDACO, StringLength(DB_sv_linha))
    endif
endfunction

function DB_sv_byte takes integer b returns nothing
    set DB_svb[DB_svn]=b
    set DB_svn=DB_svn+1
    if DB_svn==12 then
        call DB_sv_bloco()
    endif
endfunction

function DB_sv_tam takes string s returns integer
    local integer n=StringLength(s)
    local integer i=0
    local integer e=0
    local string c
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+1)
        if c=="\\" or c=="|" or c=="=" then
            set e=e+1
        endif
        set i=i+1
    endloop
    return n+e
endfunction

function DB_sv_multi takes string s,integer i returns integer
    local integer k=3
    local integer h
    if DB_sh_multi(SubString(s, i, i+3))!=3 then
        set k=2
        if DB_sh_multi(SubString(s, i, i+2))!=2 then
            set k=4
            if DB_sh_multi(SubString(s, i, i+4))!=4 then
                call DB_sv_byte(63)
                set DB_sv_perdas=DB_sv_perdas+1
                return 1
            endif
        endif
    endif
    set h=StringHash(SubString(s, i, i+k))
    call DB_sv_byte(LoadInteger(DB_sh_ht, 6, h))
    call DB_sv_byte(LoadInteger(DB_sh_ht, 7, h))
    if k>=3 then
        call DB_sv_byte(LoadInteger(DB_sh_ht, 8, h))
    endif
    if k>=4 then
        call DB_sv_byte(LoadInteger(DB_sh_ht, 9, h))
    endif
    return k
endfunction

function DB_sv_texto takes integer orc returns integer
    local string s=DB_sv_txt
    local integer n=StringLength(s)
    local integer i=DB_sv_pos
    local integer b
    local integer h
    local string c
    loop
        exitwhen i>=n or orc<=0
        set c=SubString(s, i, i+1)
        set h=StringHash(c)
        if LoadStr(DB_sh_ht, 0, h)==c then
            set b=LoadInteger(DB_sh_ht, 10, h)
        elseif LoadStr(DB_sh_ht, 2, h)==c then
            set b=LoadInteger(DB_sh_ht, 11, h)
        else
            set b=-1
        endif
        if b>=0 then
            if b==92 or b==124 or b==61 then
                set DB_svb[DB_svn]=92
                set DB_svn=DB_svn+1
                if DB_svn==12 then
                    call DB_sv_bloco()
                endif
            endif
            set DB_svb[DB_svn]=b
            set DB_svn=DB_svn+1
            if DB_svn==12 then
                call DB_sv_bloco()
            endif
            set i=i+1
        else
            set i=i+DB_sv_multi(s, i)
        endif
        set orc=orc-1
    endloop
    set DB_sv_pos=i
    return orc
endfunction

function DB_sv_fecha takes nothing returns nothing
    local string env
    local integer nf
    if DB_svn>0 then
        loop
            exitwhen DB_svn>=12
            set DB_svb[DB_svn]=0
            set DB_svn=DB_svn+1
        endloop
        call DB_sv_bloco()
    endif
    set env="|"+DB_C2_CH_ENV+"="+DB_C2_ENV+"|"+DB_C2_CH_GEN+"="+I2S(DB_C2_GEN)+"|"+DB_C2_CH_IV+"="+DB_hex32(DB_sv_iv)+"|"+DB_C2_CH_LEN+"="+I2S(DB_sv_ln)+"|"+DB_C2_CH_N+"="+I2S(DB_sv_n)+"|"+DB_C2_CH_SIG+"="+DB_hex32(DB_sv_h1)+DB_hex32(DB_sv_h2)
    set DB_sv_linha=DB_sv_linha+env
    loop
        exitwhen StringLength(DB_sv_linha)<=0
        if StringLength(DB_sv_linha)>=DB_PEDACO then
            call DB_sv_emite(SubString(DB_sv_linha, 0, DB_PEDACO))
            set DB_sv_linha=SubString(DB_sv_linha, DB_PEDACO, StringLength(DB_sv_linha))
        else
            call DB_sv_emite(DB_sv_linha)
            set DB_sv_linha=""
        endif
    endloop
    set nf=(DB_sv_ped-1)/DB_SLOT_N+1
    call PreloadGenEnd(DB_caminho("profile_", nf))
    set DB_sv_aberto=false
    call PreloadGenClear()
    call PreloadGenStart()
    call Preload("\")\ncall BlzSetAbilityTooltip("+DB_slot_txt[0]+",\"@META "+I2S(nf)+" "+I2S(DB_sv_ped)+" "+I2S(DB_sv_chars)+"\",0)\n//")
    call PreloadGenEnd(DB_caminho_meta(""))
    if DB_sv_perdas>0 then
        call DB_perfil_diag("SAVE "+I2S(GetPlayerId(DB_sv_dono))+" "+I2S(DB_sv_perdas)+" caractere(s) fora da tabela gravados como ?")
    endif
    set DB_sv_fase=3
endfunction

function DB_sv_grava_passo takes nothing returns nothing
    local integer orc=DB_SV_ORCAMENTO
    local string v
    local string cab
    if DB_sv_dono!=GetLocalPlayer() then
        return
    endif
    loop
        exitwhen orc<=0 or DB_sv_fase<1 or DB_sv_fase>2
        if DB_sv_fase==1 then
            if DB_sv_i<DB_pk_n then
                set v=DB_get(DB_sv_dono, DB_pk[DB_sv_i])
                if v!="" then
                    if DB_sv_campos>0 then
                        set DB_sv_ln=DB_sv_ln+1
                    endif
                    set DB_sv_ln=DB_sv_ln+DB_sv_tam(DB_pk[DB_sv_i])+1+DB_sv_tam(v)
                    set DB_sv_campos=DB_sv_campos+1
                    set orc=orc-StringLength(v)/4-4
                endif
                set DB_sv_i=DB_sv_i+1
            else
                set DB_s2_cont=DB_s2_cont+1
                if DB_s2_cont<1 or DB_s2_cont>1073741823 then
                    set DB_s2_cont=1
                endif
                set DB_sv_n=DB_s2_cont
                call DB_chaves(DB_sv_pasta, DB_C2_ENV)
                set DB_sv_iv=DB_SH(I2S(DB_sv_ln)+"|"+I2S(DB_sv_n)+"|"+DB_sv_pasta+"|"+DB_hex32(DB_k1))
                set cab=I2S(DB_C2_GEN)+"|"+DB_C2_ENV+"|"+DB_hex32(DB_sv_iv)+"|"+I2S(DB_sv_ln)+"|"+I2S(DB_sv_n)+"|"+DB_sv_pasta
                call DB_absorve(DB_k1, DB_k2, cab)
                set DB_sv_h1=DB_j_a
                set DB_sv_h2=DB_j_b
                set DB_sv_x=BlzBitXor(DB_k1, DB_sv_iv)
                set DB_sv_y=DB_k2+DB_sv_iv
                if DB_sv_x==0 then
                    set DB_sv_x=0x1B873593
                endif
                if DB_sv_y==0 then
                    set DB_sv_y=0x6C078965
                endif
                set DB_svn=0
                set DB_sv_ped=0
                set DB_sv_chars=0
                set DB_sv_aberto=false
                set DB_sv_perdas=0
                set DB_sv_linha=DB_C2_CH_BLOB+"="
                set DB_sv_i=0
                set DB_sv_campos=0
                set DB_sv_etapa=0
                set DB_sv_fase=2
                set orc=orc-200
            endif
        elseif DB_sv_etapa==0 then
            loop
                exitwhen DB_sv_i>=DB_pk_n
                exitwhen DB_get(DB_sv_dono, DB_pk[DB_sv_i])!=""
                set DB_sv_i=DB_sv_i+1
            endloop
            if DB_sv_i>=DB_pk_n then
                call DB_sv_fecha()
                return
            endif
            if DB_sv_campos>0 then
                call DB_sv_byte(124)
            endif
            set DB_sv_txt=DB_pk[DB_sv_i]
            set DB_sv_pos=0
            set DB_sv_etapa=1
        elseif DB_sv_etapa==1 then
            set orc=DB_sv_texto(orc)
            if DB_sv_pos>=StringLength(DB_sv_txt) then
                call DB_sv_byte(61)
                set DB_sv_txt=DB_get(DB_sv_dono, DB_pk[DB_sv_i])
                set DB_sv_pos=0
                set DB_sv_etapa=2
            endif
        else
            set orc=DB_sv_texto(orc)
            if DB_sv_pos>=StringLength(DB_sv_txt) then
                set DB_sv_campos=DB_sv_campos+1
                set DB_sv_i=DB_sv_i+1
                set DB_sv_etapa=0
            endif
        endif
    endloop
endfunction

function DB_sv_inicia takes player p returns boolean
    set DB_sv_fase=0
    set DB_sv_dono=p
    if p==null or p!=GetLocalPlayer() or DB_sv_ht==null or DB_sh_ht==null or DB_SLOT_N<1 then
        return false
    endif
    if DB_save2_recusa_gravacao() then
        return false
    endif
    if KK_teste_ligado then
        return false
    endif
    if DB_rede_bloq[GetPlayerId(p)] then
        return false
    endif
    set DB_sv_pasta=DB_conta()
    if DB_sv_pasta=="" then
        return false
    endif
    set DB_sv_i=0
    set DB_sv_ln=0
    set DB_sv_campos=0
    set DB_sv_fase=1
    return true
endfunction

function DB_perfil_salva takes player p returns boolean
    local integer k=0
    local boolean meu=false
    if GetLocalPlayer()==p then
        set meu=DB_sv_inicia(p)
    endif
    loop
        exitwhen k>=DB_SV_FATIAS
        call TriggerExecute(DB_sv_trig_grava)
        set k=k+1
    endloop
    if meu and DB_sv_fase!=3 then
        call DB_perfil_diag("SAVE "+I2S(GetPlayerId(p))+" nao terminou em "+I2S(DB_SV_FATIAS)+" fatias (fase "+I2S(DB_sv_fase)+")")
        set DB_sv_fase=4
    endif
    return meu and DB_sv_fase==3
endfunction

function DB_sv_junta takes string prefixo returns integer
    local string meta
    local integer nfiles
    local integer f=1
    local integer i
    local integer idx
    local integer maxi=0
    local string v
    local string antes
    local string mudou
    call FlushChildHashtable(DB_sv_ht, 0)
    call DB_sv_captura()
    set antes=DB_foto_antes()
    call Preloader(DB_caminho_meta(prefixo))
    set mudou=DB_foto_confere(antes)
    if mudou!="" then
        call DB_save2_cheatpld(prefixo+"meta.pld", mudou)
    endif
    set meta=DB_le_meta()
    if SubString(meta, 0, 6)!="@META " then
        call DB_restaura()
        return -1
    endif
    set nfiles=S2I(DB_campo(meta, 0))
    if nfiles<1 or nfiles>64 then
        call DB_restaura()
        return -1
    endif
    loop
        exitwhen f>nfiles
        set antes=DB_foto_antes()
        call Preloader(DB_caminho(prefixo+"profile_", f))
        set mudou=DB_foto_confere(antes)
        if mudou!="" then
            call DB_save2_cheatpld(prefixo+"profile_"+I2S(f)+".pld", mudou)
        endif
        set i=0
        loop
            exitwhen i>=DB_SLOT_N
            if DB_slot_kind[i]==0 then
                set v=BlzGetAbilityTooltip(DB_slot_code[i], 0)
            else
                set v=BlzGetAbilityExtendedTooltip(DB_slot_code[i], 0)
            endif
            if v!=null and StringLength(v)>6 and SubString(v, 0, 1)=="@" then
                set idx=S2I(SubString(v, 1, 6))
                if idx>=1 and idx<=60000 then
                    call SaveStr(DB_sv_ht, 0, idx, SubString(v, 6, StringLength(v)))
                    if idx>maxi then
                        set maxi=idx
                    endif
                endif
            endif
            set i=i+1
        endloop
        set f=f+1
    endloop
    call DB_restaura()
    return maxi
endfunction

function DB_sv_chr takes integer b returns string
    if b>=32 and b<=126 then
        return DB_CHR[b]
    elseif b==10 then
        return "\n"
    elseif b==13 then
        return "\r"
    elseif b==9 then
        return "\t"
    endif
    set DB_sv_perdas=DB_sv_perdas+1
    return "?"
endfunction

function DB_sp_poe takes string c returns nothing
    if DB_sp_est==0 then
        set DB_sp_k=DB_sp_k+c
    else
        set DB_sp_v=DB_sp_v+c
    endif
endfunction

function DB_sp_fecha takes nothing returns nothing
    if DB_sp_est==1 and DB_sp_k!="" then
        call SaveStr(DB_sv_ht, 1, DB_sp_n, DB_sp_k)
        call SaveStr(DB_sv_ht, 2, DB_sp_n, DB_sp_v)
        set DB_sp_n=DB_sp_n+1
    endif
    set DB_sp_k=""
    set DB_sp_v=""
    set DB_sp_est=0
    set DB_sp_esc=false
    set DB_sp_u8n=0
endfunction

function DB_sp_zera takes nothing returns nothing
    call FlushChildHashtable(DB_sv_ht, 1)
    call FlushChildHashtable(DB_sv_ht, 2)
    set DB_sp_n=0
    set DB_sp_k=""
    set DB_sp_v=""
    set DB_sp_est=0
    set DB_sp_esc=false
    set DB_sp_u8n=0
endfunction

function DB_sp_byte takes integer b returns nothing
    local string c
    if DB_sp_u8n>0 then
        if b>=128 and b<192 then
            set DB_sp_u8k=DB_sp_u8k*256+b
            set DB_sp_u8n=DB_sp_u8n-1
            if DB_sp_u8n==0 then
                set c=LoadStr(DB_sh_ht, 12, DB_sp_u8k)
                if c==null or c=="" then
                    set c="?"
                    set DB_sv_perdas=DB_sv_perdas+1
                endif
                call DB_sp_poe(c)
                set DB_sp_esc=false
            endif
            return
        endif
        set DB_sp_u8n=0
        call DB_sp_poe("?")
        set DB_sv_perdas=DB_sv_perdas+1
    endif
    if b>=192 then
        if b>=240 then
            set DB_sp_u8n=3
        elseif b>=224 then
            set DB_sp_u8n=2
        else
            set DB_sp_u8n=1
        endif
        set DB_sp_u8k=b
        return
    endif
    if b>=128 then
        call DB_sp_poe("?")
        set DB_sv_perdas=DB_sv_perdas+1
        return
    endif
    if DB_sp_esc then
        set DB_sp_esc=false
        call DB_sp_poe(DB_sv_chr(b))
    elseif b==92 then
        set DB_sp_esc=true
    elseif b==124 then
        call DB_sp_fecha()
    elseif b==61 and DB_sp_est==0 then
        set DB_sp_est=1
    else
        call DB_sp_poe(DB_sv_chr(b))
    endif
endfunction

function DB_sl_16 takes nothing returns string
    local string s
    local integer resto
    if DB_sv_cur_p+16<=StringLength(DB_sv_cur) then
        set s=SubString(DB_sv_cur, DB_sv_cur_p, DB_sv_cur_p+16)
        set DB_sv_cur_p=DB_sv_cur_p+16
        return s
    endif
    set s=SubString(DB_sv_cur, DB_sv_cur_p, StringLength(DB_sv_cur))
    set resto=16-StringLength(s)
    set DB_sv_cur_i=DB_sv_cur_i+1
    set DB_sv_cur=LoadStr(DB_sv_ht, 0, DB_sv_cur_i)
    if DB_sv_cur==null then
        set DB_sv_cur=""
        return s
    endif
    set s=s+SubString(DB_sv_cur, 0, resto)
    set DB_sv_cur_p=resto
    return s
endfunction

function DB_sl_unidade takes string t,integer k returns integer
    local string par=SubString(t, k*2, k*2+2)
    local integer h=StringHash(par)
    local integer a
    local integer b
    if LoadStr(DB_sv_ht, 30, h)==par then
        return LoadInteger(DB_sv_ht, 31, h)
    elseif LoadStr(DB_sv_ht, 32, h)==par then
        return LoadInteger(DB_sv_ht, 33, h)
    elseif LoadStr(DB_sv_ht, 34, h)==par then
        return LoadInteger(DB_sv_ht, 35, h)
    elseif LoadStr(DB_sv_ht, 36, h)==par then
        return LoadInteger(DB_sv_ht, 37, h)
    endif
    set a=DB_sh_byte_cru(SubString(par, 0, 1))
    set b=DB_sh_byte_cru(SubString(par, 1, 2))
    if a<0 or b<0 or a>255 or b>255 then
        return -1
    endif
    set a=DB_LV[a]
    set b=DB_LV[b]
    if a<0 or b<0 then
        return -1
    endif
    return a*64+b
endfunction

function DB_sl_passo takes nothing returns nothing
    local integer orc=DB_SV_ORCAMENTO/12
    local string t
    local integer x=DB_sl_x
    local integer y=DB_sl_y
    local integer h1=DB_sl_h1
    local integer h2=DB_sl_h2
    local integer z
    local integer w
    local integer u1
    local integer u2
    local integer u3
    local integer u4
    local integer u5
    local integer u6
    local integer u7
    local integer u8
    local integer v
    local integer k
    local integer j
    local integer b
    if DB_sl_fase!=1 then
        return
    endif
    loop
        exitwhen orc<=0 or DB_sl_bl>=DB_sl_nbl
        set t=DB_sl_16()
        if StringLength(t)!=16 then
            set DB_sl_fase=3
            return
        endif
        set u1=DB_sl_unidade(t, 0)
        set u2=DB_sl_unidade(t, 1)
        set u3=DB_sl_unidade(t, 2)
        set u4=DB_sl_unidade(t, 3)
        set u5=DB_sl_unidade(t, 4)
        set u6=DB_sl_unidade(t, 5)
        set u7=DB_sl_unidade(t, 6)
        set u8=DB_sl_unidade(t, 7)
        if u1<0 or u2<0 or u3<0 or u4<0 or u5<0 or u6<0 or u7<0 or u8<0 then
            set DB_sl_fase=3
            return
        endif
        set x=BlzBitXor(x, x*8192)
        set x=BlzBitXor(x, BlzBitAnd((x-BlzBitAnd(x, 131071))/131072, 32767))
        set x=BlzBitXor(x, x*32)
        set y=BlzBitXor(y, y*8192)
        set y=BlzBitXor(y, BlzBitAnd((y-BlzBitAnd(y, 131071))/131072, 32767))
        set y=BlzBitXor(y, y*32)
        set z=x+y
        set w=BlzBitXor(x, y)
        set h1=h1+u1+u2*4096
        set h1=BlzBitXor(h1, BlzBitAnd((h1-BlzBitAnd(h1, 8191))/8192, 524287))
        set h1=h1+h1*512
        set h2=BlzBitXor(h2, u3+u4*4096)
        set h2=h2+h2*128
        set h2=BlzBitXor(h2, BlzBitAnd((h2-BlzBitAnd(h2, 2047))/2048, 2097151))
        set h1=BlzBitXor(h1, u5+u6*4096)
        set h2=h2+(u7+u8*4096)+h1
        set v=BlzBitXor(u1, BlzBitAnd((x-BlzBitAnd(x, 1048575))/1048576, 4095))
        set k=BlzBitXor(u2, BlzBitAnd((x-BlzBitAnd(x, 255))/256, 4095))
        set DB_spb[0]=v/16
        set DB_spb[1]=BlzBitAnd(v, 15)*16+k/256
        set DB_spb[2]=BlzBitAnd(k, 255)
        set v=BlzBitXor(u3, BlzBitAnd((y-BlzBitAnd(y, 1048575))/1048576, 4095))
        set k=BlzBitXor(u4, BlzBitAnd((y-BlzBitAnd(y, 255))/256, 4095))
        set DB_spb[3]=v/16
        set DB_spb[4]=BlzBitAnd(v, 15)*16+k/256
        set DB_spb[5]=BlzBitAnd(k, 255)
        set v=BlzBitXor(u5, BlzBitAnd((z-BlzBitAnd(z, 1048575))/1048576, 4095))
        set k=BlzBitXor(u6, BlzBitAnd((z-BlzBitAnd(z, 255))/256, 4095))
        set DB_spb[6]=v/16
        set DB_spb[7]=BlzBitAnd(v, 15)*16+k/256
        set DB_spb[8]=BlzBitAnd(k, 255)
        set v=BlzBitXor(u7, BlzBitAnd((w-BlzBitAnd(w, 16383))/16384, 4095))
        set k=BlzBitXor(u8, BlzBitAnd((w-BlzBitAnd(w, 3))/4, 4095))
        set DB_spb[9]=v/16
        set DB_spb[10]=BlzBitAnd(v, 15)*16+k/256
        set DB_spb[11]=BlzBitAnd(k, 255)
        set j=0
        loop
            exitwhen j>11 or DB_sl_feitos+j>=DB_sl_ln
            set b=DB_spb[j]
            if DB_sp_u8n==0 and not DB_sp_esc and b>=32 and b<=126 and b!=92 and b!=124 and b!=61 then
                if DB_sp_est==0 then
                    set DB_sp_k=DB_sp_k+DB_CHR[b]
                else
                    set DB_sp_v=DB_sp_v+DB_CHR[b]
                endif
            else
                call DB_sp_byte(b)
            endif
            set j=j+1
        endloop
        set DB_sl_feitos=DB_sl_feitos+12
        set x=BlzBitXor(x, u8)
        set y=y+u1
        set DB_sl_bl=DB_sl_bl+1
        set orc=orc-1
    endloop
    set DB_sl_x=x
    set DB_sl_y=y
    set DB_sl_h1=h1
    set DB_sl_h2=h2
    if DB_sl_bl>=DB_sl_nbl then
        set DB_sl_fase=2
    endif
endfunction

function DB_sl_abre takes integer np,string pasta returns boolean
    local string cauda
    local integer base
    local integer pt
    local integer t
    local integer iv
    local string env8
    local string iv8
    local string gen
    local string nn
    local string len_s
    local integer k=1
    set DB_s2_motivo="formato"
    set DB_s2_n_lida=-1
    set DB_s2_gen_lida=-1
    loop
        exitwhen k>=np
        if StringLength(LoadStr(DB_sv_ht, 0, k))!=DB_PEDACO then
            return false
        endif
        set k=k+1
    endloop
    if np>=2 then
        set cauda=LoadStr(DB_sv_ht, 0, np-1)+LoadStr(DB_sv_ht, 0, np)
        set base=(np-2)*DB_PEDACO
    else
        set cauda=LoadStr(DB_sv_ht, 0, 1)
        set base=0
    endif
    set pt=DB_pos(cauda, "|"+DB_C2_CH_ENV+"=", 0)
    if pt<0 then
        return false
    endif
    set DB_sv_env=SubString(cauda, pt+1, StringLength(cauda))
    set t=base+pt-11
    if t<0 or t-(t/16)*16!=0 then
        return false
    endif
    set env8=DB_env_campo(DB_sv_env, DB_C2_CH_ENV)
    set iv8=DB_env_campo(DB_sv_env, DB_C2_CH_IV)
    set DB_sl_sig=DB_env_campo(DB_sv_env, DB_C2_CH_SIG)
    set gen=DB_env_campo(DB_sv_env, DB_C2_CH_GEN)
    set nn=DB_env_campo(DB_sv_env, DB_C2_CH_N)
    set len_s=DB_env_campo(DB_sv_env, DB_C2_CH_LEN)
    if env8=="" or iv8=="" or DB_sl_sig=="" or gen=="" or nn=="" or len_s=="" then
        return false
    endif
    if not DB_eh_digitos(nn) or not DB_eh_digitos(len_s) then
        return false
    endif
    set DB_sl_ln=S2I(len_s)
    if DB_sl_ln<0 or DB_sl_ln>(t/16)*12 then
        return false
    endif
    set iv=DB_hex8_int(iv8)
    if iv==-1 and iv8!="ffffffff" then
        return false
    endif
    set DB_s2_gen_lida=S2I(gen)
    set DB_s2_n_lida=S2I(nn)
    call DB_chaves(pasta, DB_C2_ENV)
    call DB_absorve(DB_k1, DB_k2, gen+"|"+env8+"|"+iv8+"|"+len_s+"|"+nn+"|"+pasta)
    set DB_sl_h1=DB_j_a
    set DB_sl_h2=DB_j_b
    set DB_sl_x=BlzBitXor(DB_k1, iv)
    set DB_sl_y=DB_k2+iv
    if DB_sl_x==0 then
        set DB_sl_x=0x1B873593
    endif
    if DB_sl_y==0 then
        set DB_sl_y=0x6C078965
    endif
    set DB_sv_cur_i=1
    set DB_sv_cur=LoadStr(DB_sv_ht, 0, 1)
    set DB_sv_cur_p=11
    call DB_sp_zera()
    set DB_sv_perdas=0
    set DB_sl_bl=0
    set DB_sl_nbl=t/16
    set DB_sl_feitos=0
    set DB_sl_fase=1
    return true
endfunction

function DB_sv_le takes string prefixo,string pasta returns integer
    local integer np=DB_sv_junta(prefixo)
    local integer r=0
    local integer k=0
    local string p1
    set DB_sl_fase=0
    if np>=1 then
        set p1=LoadStr(DB_sv_ht, 0, 1)
        if p1!=null and SubString(p1, 0, 11)==DB_C2_CH_BLOB+"=" then
            if DB_sl_abre(np, pasta) then
                set r=2
            endif
        elseif p1!=null then
            set DB_sv_env=DB_sv_g1(np)
            set r=1
        endif
    endif
    loop
        exitwhen k>=DB_SV_FATIAS
        call TriggerExecute(DB_sv_trig_le)
        set k=k+1
    endloop
    if r==2 then
        if DB_sl_fase==2 then
            call DB_sp_fecha()
            if DB_hex32(DB_sl_h1)+DB_hex32(DB_sl_h2)==DB_sl_sig then
                set DB_s2_motivo=""
                set DB_sl_fase=0
                return 2
            endif
            set DB_s2_motivo="assinatura"
        elseif DB_sl_fase==1 then
            set DB_s2_motivo="grande demais para "+I2S(DB_SV_FATIAS)+" fatias"
        else
            set DB_s2_motivo="assinatura"
        endif
        set DB_s2_n_lida=-1
        call DB_sp_zera()
        set DB_sl_fase=0
        return 0
    endif
    return r
endfunction

function DB_sv_aplica takes nothing returns nothing
    local integer j=0
    local player p=GetLocalPlayer()
    loop
        exitwhen j>=DB_sp_n
        call DB_put(p, LoadStr(DB_sv_ht, 1, j), LoadStr(DB_sv_ht, 2, j))
        set j=j+1
    endloop
    set p=null
endfunction

function DB_sv_g1 takes integer np returns string
    local integer k=1
    local string s=""
    loop
        exitwhen k>np
        set s=s+LoadStr(DB_sv_ht, 0, k)
        set k=k+1
    endloop
    return s
endfunction

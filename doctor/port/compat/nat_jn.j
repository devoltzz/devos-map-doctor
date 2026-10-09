function JNStringBase64Encoding takes string str returns string
    return JNStringToBase64(str)
endfunction

function JNStringEncrypt takes string plainText,string key returns string
    return plainText
endfunction

function JNStringDecrypt takes string cipherText,string key returns string
    return cipherText
endfunction

function JNGetSettingLogin takes nothing returns boolean
    return true
endfunction

function JNGetSettingLoginID takes nothing returns string
    return DB_nome_conta(GetLocalPlayer())
endfunction

function JNLocalLogin takes string id returns boolean
    return true
endfunction

function JNLogin takes string id,string password returns boolean
    return true
endfunction

timer KKN_sw_relogio = null
integer KKN_sw_n = 0
real array KKN_sw_ini
real array KKN_sw_acum
boolean array KKN_sw_roda

function KKN_sw_agora takes nothing returns real
    if KKN_sw_relogio==null then
        set KKN_sw_relogio=CreateTimer()
        call TimerStart(KKN_sw_relogio, 1000000.0, false, null)
    endif
    return TimerGetElapsed(KKN_sw_relogio)
endfunction

function KKN_sw_segundos takes integer id returns real
    if id<1 or id>KKN_sw_n then
        return 0.0
    endif
    if KKN_sw_roda[id] then
        return KKN_sw_acum[id]+KKN_sw_agora()-KKN_sw_ini[id]
    endif
    return KKN_sw_acum[id]
endfunction

function JNStopwatchCreate takes nothing returns integer
    if KKN_sw_n>=8190 then
        return 0
    endif
    set KKN_sw_n=KKN_sw_n+1
    set KKN_sw_acum[KKN_sw_n]=0.0
    set KKN_sw_roda[KKN_sw_n]=false
    return KKN_sw_n
endfunction

function JNStopwatchStart takes integer id returns nothing
    if id<1 or id>KKN_sw_n or KKN_sw_roda[id] then
        return
    endif
    set KKN_sw_ini[id]=KKN_sw_agora()
    set KKN_sw_roda[id]=true
endfunction

function JNStopwatchPause takes integer id returns nothing
    if id<1 or id>KKN_sw_n or not KKN_sw_roda[id] then
        return
    endif
    set KKN_sw_acum[id]=KKN_sw_segundos(id)
    set KKN_sw_roda[id]=false
endfunction

function JNStopwatchReset takes integer id returns nothing
    if id<1 or id>KKN_sw_n then
        return
    endif
    set KKN_sw_acum[id]=0.0
    set KKN_sw_ini[id]=KKN_sw_agora()
endfunction

function JNStopwatchDestroy takes integer id returns nothing
    if id<1 or id>KKN_sw_n then
        return
    endif
    set KKN_sw_acum[id]=0.0
    set KKN_sw_roda[id]=false
endfunction

function JNStopwatchElapsedMS takes integer id returns integer
    return R2I(KKN_sw_segundos(id)*1000.0)
endfunction

function JNStopwatchElapsedSecond takes integer id returns integer
    return R2I(KKN_sw_segundos(id))
endfunction

function JNStopwatchElapsedMinute takes integer id returns integer
    return R2I(KKN_sw_segundos(id)/60.0)
endfunction

function JNStopwatchElapsedHour takes integer id returns integer
    return R2I(KKN_sw_segundos(id)/3600.0)
endfunction

hashtable KKN_jn_ht = InitHashtable()

function KKN_jn_chave takes string a,string b returns integer
    return StringHash(a+"|"+b)
endfunction

function JNInitMail takes string MapId,string UserId,string SecretKey,string Character returns integer
    return 0
endfunction

function JNGetMailid takes integer index returns string
    return ""
endfunction

function JNGetMailItem takes integer index returns string
    return ""
endfunction

function JNGetMailMsg takes integer index returns string
    return ""
endfunction

function JNGetMailremove takes string MapId,string UserId,string SecretKey,string Character,string MailId returns boolean
    return true
endfunction

function JNGetScoreRank takes string MapId,string UserId,string SecretKey,string Character,string RankName returns integer
    return 0
endfunction

function JNGetScoreRankListInit takes string MapId,string SecretKey,string RankName returns integer
    return 0
endfunction

function JNGetScoreRankListInit50 takes string MapId,string SecretKey,string RankName returns integer
    return 0
endfunction

function JNGetScoreRankListUserId takes integer index returns string
    return ""
endfunction

function JNGetScoreRankListScore takes integer index returns integer
    return 0
endfunction

function JNGetScoreRankListCharacter takes integer index returns string
    return ""
endfunction

function JNObjectScorePrivateInit takes string MapId,string UserId,string SecretKey,string Character returns integer
    return 1
endfunction

function JNObjectScorePrivateSet takes string UserId,string Field,integer Value returns nothing
    call SaveInteger(KKN_jn_ht, KKN_jn_chave("SP"+UserId, Field), 0, Value)
endfunction

function JNObjectScorePrivateGet takes string UserId,string Field returns integer
    return LoadInteger(KKN_jn_ht, KKN_jn_chave("SP"+UserId, Field), 0)
endfunction

function JNObjectScorePrivateSave takes string MapId,string UserId,string SecretKey,string Character returns string
    return KKJN_SALVO
endfunction

function JNObjectCharacterShareInit takes string MapId,string UserId,string SecretKey,string Character returns integer
    return 1
endfunction

function JNObjectCharacterShareSetInt takes string UserId,string Field,integer Value returns nothing
    call SaveInteger(KKN_jn_ht, KKN_jn_chave("SH"+UserId, Field), 0, Value)
endfunction

function JNObjectCharacterShareGetInt takes string UserId,string Field returns integer
    return LoadInteger(KKN_jn_ht, KKN_jn_chave("SH"+UserId, Field), 0)
endfunction

function JNObjectCharacterShareSetString takes string UserId,string Field,string Value returns nothing
    call SaveStr(KKN_jn_ht, KKN_jn_chave("SH"+UserId, Field), 1, Value)
endfunction

function JNObjectCharacterShareGetString takes string UserId,string Field returns string
    local string s=LoadStr(KKN_jn_ht, KKN_jn_chave("SH"+UserId, Field), 1)
    if s==null then
        return ""
    endif
    return s
endfunction

function JNObjectCharacterShareSave takes string MapId,string UserId,string SecretKey,string Character returns string
    return KKJN_SALVO
endfunction

function JNObjectCharacterShareResetCharacter takes string UserId returns nothing
endfunction

function JNObjectMapGetBoolean takes string Field returns boolean
    return false
endfunction

function JNObjectCharacterPopGlobalMessageFormat takes string Format returns string
    return ""
endfunction

function JNGetIp takes string MapId,string SecretKey returns string
    return ""
endfunction

function JNUseUserRoleItem takes string MapId,string UserId,string SecretKey,string Character,string ItemId returns boolean
    return true
endfunction

function JNDailyCheckTodayList takes string MapId,string UserId,string SecretKey,string Character,string Key returns string
    return ""
endfunction

function JNDailyCountMonth takes string MapId,string UserId,string SecretKey,string Character,string Key returns string
    return ""
endfunction

function JNDailyCountWeek takes string MapId,string UserId,string SecretKey,string Character,string Key,string Day returns string
    return ""
endfunction

function JNGetBestAreasteal takes integer index,integer kind,string Field returns string
    return ""
endfunction

function JNGetMultipleBestAreasteal takes integer index,string Field returns string
    return ""
endfunction

function JNGetMyAreastealScore takes string MapId,string UserId,string SecretKey,string Character,integer Area returns integer
    return 0
endfunction

function JNInitBestAreastealtop10 takes string MapId,string UserId,string SecretKey,string Character,integer Area returns integer
    return 0
endfunction

function JNInitBestMultiAreasteal takes string MapId,string UserId,string SecretKey,string Character,string Areas returns integer
    return 0
endfunction

function JNSetAreasteal takes string MapId,string UserId,string SecretKey,string Character,integer Area,integer Score returns string
    return KKJN_SALVO
endfunction

function JNRemoveAreasteal takes string MapId,string UserId,string SecretKey,string Character,integer Area returns string
    return KKJN_SALVO
endfunction

function JNGetGroupMembers takes string MapId,string SecretKey,string GroupId returns integer
    return 0
endfunction

function JNGetGroupMember takes integer index returns string
    return ""
endfunction

function JNGetGroupWaitingLists takes string MapId,string SecretKey,string GroupId returns integer
    return 0
endfunction

function JNGetGroupWaitingUserId takes integer index returns string
    return ""
endfunction

function JNGetGroupWaitingUserMemo takes integer index returns string
    return ""
endfunction

function JNGroupApprovalJoin takes string MapId,string SecretKey,string GroupId,string UserId returns boolean
    return false
endfunction

function JNGroupIsManager takes string MapId,string SecretKey,string UserId returns boolean
    return false
endfunction

function JNGroupJoinRequest takes string MapId,string SecretKey,string GroupId,string UserId,string Memo returns string
    return ""
endfunction

function JNGroupKickOut takes string MapId,string SecretKey,string GroupId,string UserId returns boolean
    return false
endfunction

function JNGroupNumberAdd takes string MapId,string SecretKey,string GroupId,string Field,real Value returns string
    return ""
endfunction

function JNGroupNumberGet takes string MapId,string SecretKey,string GroupId,string Field returns real
    return 0.0
endfunction

function JNGroupNumberSet takes string MapId,string SecretKey,string GroupId,string Field,real Value returns string
    return ""
endfunction

function JNGroupStringGet takes string MapId,string SecretKey,string GroupId,string Field returns string
    return ""
endfunction

function JNGroupStringSet takes string MapId,string SecretKey,string GroupId,string Field,string Value returns string
    return ""
endfunction

function JNGroupUserOut takes string MapId,string SecretKey,string UserId returns boolean
    return false
endfunction

function JNJNGroupLastOutUnixDate takes string MapId,string SecretKey,string UserId returns integer
    return 0
endfunction

function JNUserJoinGroupInfo takes string MapId,string SecretKey,string UserId returns string
    return ""
endfunction

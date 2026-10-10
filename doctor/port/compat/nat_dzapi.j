function DzAPI_Map_SaveServerValue takes player whichPlayer,string key,string value returns boolean
    return RequestExtraBooleanData(4,whichPlayer,key,value,false,0,0,0)
endfunction

function DzAPI_Map_GetServerValue takes player whichPlayer,string key returns string
    return RequestExtraStringData(5,whichPlayer,key,null,false,0,0,0)
endfunction

function DzAPI_Map_GetServerValueErrorCode takes player whichPlayer returns integer
    return RequestExtraIntegerData(6,whichPlayer,null,null,false,0,0,0)
endfunction

function DzAPI_Map_Stat_SetStat takes player whichPlayer,string key,string value returns nothing
    call RequestExtraIntegerData(7,whichPlayer,key,value,false,0,0,0)
endfunction

function DzAPI_Map_Ladder_SetStat takes player whichPlayer,string key,string value returns nothing
    call RequestExtraIntegerData(8,whichPlayer,key,value,false,0,0,0)
endfunction

function DzAPI_Map_Ladder_SetPlayerStat takes player whichPlayer,string key,string value returns nothing
    call RequestExtraIntegerData(9,whichPlayer,key,value,false,0,0,0)
endfunction

function DzAPI_Map_GetGameStartTime takes nothing returns integer
    return RequestExtraIntegerData(11,null,null,null,false,0,0,0)
endfunction

function DzAPI_Map_GetMatchType takes nothing returns integer
    return RequestExtraIntegerData(13,null,null,null,false,0,0,0)
endfunction

function DzAPI_Map_GetMapLevelRank takes player whichPlayer returns integer
    return RequestExtraIntegerData(18,whichPlayer,null,null,false,0,0,0)
endfunction

function DzAPI_Map_GetMapConfig takes string key returns string
    return RequestExtraStringData(21,null,key,null,false,0,0,0)
endfunction

function DzAPI_Map_IsRPGLobby takes nothing returns boolean
    return RequestExtraBooleanData(10,null,null,null,false,0,0,0)
endfunction

function DzAPI_Map_SavePublicArchive takes player whichPlayer,string key,string value returns boolean
    return RequestExtraBooleanData(31,whichPlayer,key,value,false,0,0,0)
endfunction

function DzAPI_Map_GetPublicArchive takes player whichPlayer,string key returns string
    return RequestExtraStringData(32,whichPlayer,key,null,false,0,0,0)
endfunction

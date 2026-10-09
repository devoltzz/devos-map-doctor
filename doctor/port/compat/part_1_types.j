//@GLOBALS
framehandle array DB_frame
integer array DB_frame_id
integer DB_frame_n=0
framepointtype array DB_ponto
integer array DB_origem
integer array DB_origem_chave
integer DB_origem_n=0
integer array DB_ef_id
real array DB_ef_x
real array DB_ef_y
real array DB_ef_z
real array DB_ef_rz
real array DB_ef_ry
real array DB_ef_rx
real array DB_ef_size
integer DB_ef_n=0
integer array DB_sync_id
integer DB_sync_n=0
string array DB_sq_pref
string array DB_sq_dado
integer DB_sq_head=0
integer DB_sq_tail=0
timer DB_sq_timer=null
hashtable DB_ui_ht=null
frameeventtype array DB_evt
integer DB_mouse_focus=0
integer DB_wheel_delta=0
real array DB_mouse_wx
real array DB_mouse_wy
trigger DB_mundo_trig=null
group DB_sel_g=null
unit DB_sel_u=null
boolean array DB_key_down
trigger DB_roda_trig=null
trigger DB_quadro_trig=null
timer DB_quadro_timer=null
boolean DB_pos_init=false
trigger array DB_mov_fila
integer DB_mov_n=0
real DB_pad_dir=-1.0
framehandle DB_fundo_tela=null
boolean DB_toc_ok=false
constant integer DB_SYNC_DIRETO=200
constant integer DB_SYNC_TRECHO=160
constant integer DB_SQ_POR_TICK=25
constant integer DB_SYNC_PREFIXO_LEN=3
constant integer DB_MAX=4096

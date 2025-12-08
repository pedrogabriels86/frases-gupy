import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time
from datetime import datetime
import io
import unicodedata
import requests
from PIL import Image

# ==============================================================================
# 1. CONFIGURAÇÕES E IMAGENS
# ==============================================================================
FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"

# Carrega favicon
favicon = "💙" 
try:
    response = requests.get(FAVICON_URL, timeout=2)
    if response.status_code == 200: favicon = Image.open(io.BytesIO(response.content))
except: pass

st.set_page_config(page_title="Gupy Frases", page_icon=favicon, layout="wide")

# ==============================================================================
# 2. CSS CORPORATIVO (CLEAN & GUPY)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F5F7FA; }
    
    /* ESCONDER ITENS PADRÃO */
    [data-testid="stHeader"] { display: none; }
    [data-testid="stSidebar"] { display: none; }
    footer { display: none; }
    
    /* TOPO */
    .block-container {
        padding-top: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100%;
    }

    /* NAVBAR SUPERIOR */
    div[data-testid="stVerticalBlock"] > div:first-child {
        background-color: #00122F; /* Azul Midnight */
        padding: 1rem 2rem;
        margin-left: -2rem;
        margin-right: -2rem;
        margin-bottom: 2rem;
        border-bottom: 4px solid #2175D9; /* Linha de destaque */
        display: flex;
        align-items: center;
    }

    /* MENU (Abas Superiores) */
    .stRadio > div[role="radiogroup"] {
        background-color: rgba(255,255,255,0.1);
        padding: 4px;
        border-radius: 8px;
        display: inline-flex;
    }
    
    .stRadio label {
        color: rgba(255,255,255,0.7) !important;
        font-weight: 500;
        padding: 8px 16px;
        border-radius: 6px;
        margin: 0 !important;
        border: none;
        transition: all 0.2s;
    }
    
    .stRadio label:hover {
        color: #FFF !important;
        background-color: rgba(255,255,255,0.1);
    }
    
    .stRadio label[data-checked="true"] {
        background-color: #2175D9 !important;
        color: #FFF !important;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .stRadio div[role="radiogroup"] > label > div:first-child { display: none; }

    /* BOTÕES */
    .stButton > button {
        background-color: #2175D9; color: white; border-radius: 6px;
        font-weight: 600; border: none; padding: 0.5rem 1rem;
    }
    .stButton > button:hover { background-color: #1A64C0; color: white; }
    
    /* Botão Perigo (Vermelho) */
    button[kind="primary"] { background-color: #EF4444 !important; border: none !important; }
    button[kind="primary"]:hover { background-color: #DC2626 !important; }

    /* CARTÕES */
    .card-container, div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #FFFFFF; border: 1px solid #E1E4E8; border-radius: 8px;
        padding: 20px !important; box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    
    /* INPUTS */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 6px; color: #1F2937;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2175D9; box-shadow: 0 0 0 1px #2175D9;
    }

    /* Textos do Header */
    .logo-text { font-size: 1.5rem; font-weight: 800; color: white; margin: 0; }
    .user-text { color: rgba(255,255,255,0.8); font-size: 0.9rem; text-align: right; }
    .logout-btn button { background: transparent !important; border: 1px solid rgba(255,255,255,0.3) !important; padding: 0.3rem 0.8rem; }
    
</style>
""", unsafe_allow_html=True)

# --- 3. CONEXÃO ---
try:
    url_db = st.secrets["SUPABASE_URL"]
    key_db = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url_db, key_db)
except: st.stop()

# --- 4. FUNÇÕES ---
def verificar_login(u, s):
    try: res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute(); return res.data[0] if res.data else None
    except: return None
def buscar_dados(): return supabase.table("frases").select("*").order("id", desc=True).execute().data or []
def buscar_usuarios(): return supabase.table("usuarios").select("*").order("id").execute().data or []
def registrar_log(usuario, acao, detalhe):
    try: supabase.table("logs").insert({"usuario":usuario,"acao":acao,"detalhe":detalhe,"data_hora":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
    except: pass
def padronizar(texto, tipo="titulo"):
    if not texto: return ""; texto = str(texto).strip()
    if not texto: return ""
    return texto.title() if tipo == "titulo" else (texto[0].upper() + texto[1:])
def limpar_coluna(col):
    col = str(col).lower().strip(); return ''.join(c for c in unicodedata.normalize('NFD', col) if unicodedata.category(c) != 'Mn')

# ==============================================================================
# 5. LÓGICA DE TELAS
# ==============================================================================
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

# --- TELA DE LOGIN ---
if st.session_state["usuario_logado"] is None:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write(""); st.write(""); st.write("")
        with st.container(border=True):
            if LOGO_URL: 
                cl, cm, cr = st.columns([1, 2, 1])
                with cm: st.image(LOGO_URL, use_container_width=True)
            else: st.markdown("<h1 class='logo-text' style='color:#2175D9; text-align:center;'>gupy</h1>", unsafe_allow_html=True)
            
            st.markdown("<h3 style='text-align:center; color:#374151; font-size:1.2rem; margin-bottom:20px'>Frases de Recusa</h3>", unsafe_allow_html=True)
            with st.form("login"):
                u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
                st.write("")
                if st.form_submit_button("Entrar", use_container_width=True):
                    user = verificar_login(u, s)
                    if user: st.session_state["usuario_logado"] = user; st.rerun()
                    else: st.error("Credenciais inválidas.")

# --- ÁREA LOGADA ---
else:
    user = st.session_state["usuario_logado"]
    
    # NAVBAR FIXA
    with st.container():
        col_logo, col_menu, col_user = st.columns([1, 4, 1.5], gap="small")
        with col_logo:
            if LOGO_URL: st.image(LOGO_URL, width=90)
            else: st.markdown("<div class='logo-text'>gupy</div>", unsafe_allow_html=True)
        
        with col_menu:
            # Menu Dividido em 4 Opções Claras
            opcoes = ["📂 Frases de Recusa", "➕ Adicionar & Importar", "✏️ Editar & Excluir"]
            if user['admin']: opcoes.append("⚙️ Gerenciador")
            page = st.radio("Menu", opcoes, label_visibility="collapsed")
            
        with col_user:
            c_u, c_out = st.columns([2, 1])
            with c_u:
                st.markdown(f"<div class='user-text'>Olá, <b>{user['username']}</b></div>", unsafe_allow_html=True)
            with c_out:
                st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
                if st.button("Sair"): st.session_state["usuario_logado"] = None; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # CONTEÚDO
    if user.get('trocar_senha'):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.container(border=True):
                st.warning("⚠️ Segurança: Redefina sua senha"); n1=st.text_input("Nova Senha", type="password"); n2=st.text_input("Confirmar", type="password")
                if st.button("Salvar Nova Senha", use_container_width=True): 
                    if n1==n2 and n1: supabase.table("usuarios").update({"senha":n1,"trocar_senha":False}).eq("id",user['id']).execute(); user['trocar_senha']=False; st.rerun()
    else:
        
        # --- 1. BIBLIOTECA (VISUALIZAR APENAS) ---
        if "📂" in page:
            c_tit, c_search = st.columns([1, 2])
            with c_tit: st.title("Frases de Recusa")
            with c_search:
                st.write("")
                termo = st.text_input("Busca Rápida", placeholder="🔎 Digite para pesquisar...", label_visibility="collapsed")
            
            dados = buscar_dados()
            filtrados = [f for f in dados if termo.lower() in str(f).lower()] if termo else dados
            
            st.markdown(f"<div style='color:#6B7280; font-size:0.9rem; margin-bottom:10px;'>Encontrados <b>{len(filtrados)}</b> registros</div>", unsafe_allow_html=True)
            
            for f in filtrados:
                with st.container(border=True):
                    col_info, col_cont = st.columns([1.5, 3.5])
                    with col_info:
                        st.markdown(f"<h4 style='margin:0; color:#111827;'>{f['empresa']}</h4>", unsafe_allow_html=True)
                        st.markdown(f"""
                            <div style='margin-top:8px;'><span style='background:#F3F4F6; color:#374151; padding:4px 8px; border-radius:4px; font-size:0.8rem; font-weight:500;'>📄 {f['documento']}</span></div>
                            <div style='margin-top:8px; color:#4B5563; font-weight:500;'>📌 {f['motivo']}</div>
                        """, unsafe_allow_html=True)
                        if f.get('revisado_por'): 
                            try: dt = datetime.strptime(f['data_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y'); st.markdown(f"<div style='margin-top:12px; font-size:0.8rem; color:#059669;'>✔ Validado por {f['revisado_por']} em {dt}</div>", unsafe_allow_html=True)
                            except: pass
                    with col_cont:
                        st.markdown("**Mensagem Padrão:**")
                        st.code(f['conteudo'], language="text")

        # --- 2. ADICIONAR & IMPORTAR (CRIAR APENAS) ---
        elif "➕" in page:
            st.title("Adicionar Frases")
            
            t_manual, t_import = st.tabs(["Cadastro Manual", "Importação em Massa"])
            
            with t_manual:
                with st.container(border=True):
                    st.subheader("Nova Frase")
                    c1, c2, c3 = st.columns(3)
                    ne = c1.text_input("Empresa"); nd = c2.text_input("Documento"); nm = c3.text_input("Motivo")
                    nc = st.text_area("Conteúdo da Frase", height=150)
                    st.write("")
                    if st.button("💾 Salvar Registro", use_container_width=True):
                        if nc:
                            ne,nd,nm = padronizar(ne),padronizar(nd),padronizar(nm); nc = padronizar(nc,"frase")
                            if len(supabase.table("frases").select("id").eq("conteudo", nc).execute().data) > 0: st.error("Erro: Frase já existe.")
                            else:
                                supabase.table("frases").insert({"empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).execute()
                                registrar_log(user['username'], "Criou Frase", f"{ne}-{nm}"); st.success("Adicionado com sucesso!"); time.sleep(1); st.rerun()

            with t_import:
                with st.container(border=True):
                    st.subheader("Importar Excel/CSV")
                    st.info("Colunas necessárias: Empresa, Documento, Motivo, Conteúdo.")
                    upl = st.file_uploader("Selecione o arquivo", type=['csv','xlsx'])
                    if upl and st.button("Processar Importação", use_container_width=True):
                        try:
                            if upl.name.endswith('.csv'):
                                try: df = pd.read_csv(upl)
                                except: df = pd.read_csv(upl, encoding='latin-1', sep=';')
                            else: df = pd.read_excel(upl)
                            
                            # Detecção de Cabeçalho Inteligente
                            header_idx = -1; keywords = ['empresa', 'conteudo', 'frase', 'motivo']
                            for i, row in df.head(50).iterrows():
                                row_str = " ".join([str(val).lower() for val in row.values])
                                if sum(1 for k in keywords if k in row_str) >= 2: header_idx = i; break
                            if header_idx > -1 and header_idx > 0:
                                if upl.name.endswith('.csv'): upl.seek(0); df = pd.read_csv(upl, header=header_idx, encoding='latin-1', sep=None, engine='python')
                                else: upl.seek(0); df = pd.read_excel(upl, header=header_idx)

                            df.columns = [limpar_coluna(c) for c in df.columns]
                            mapa = {'empresa solicitante':'empresa','cliente':'empresa','tipo documento':'documento','doc':'documento','motivo recusa':'motivo','motivo da recusa':'motivo','justificativa':'motivo','frase':'conteudo','texto':'conteudo','mensagem':'conteudo','frase de recusa':'conteudo','revisado por':'revisado_por','revisor':'revisado_por','validado por':'revisado_por','data':'data_revisao','data revisao':'data_revisao','data da revisao':'data_revisao'}
                            df.rename(columns=mapa, inplace=True)
                            
                            if not all(c in df.columns for c in ['empresa', 'documento', 'motivo', 'conteudo']): st.error("Colunas obrigatórias não encontradas.")
                            else:
                                novos=[]; db_set=set([str(f['conteudo']).strip() for f in buscar_dados()])
                                for _, r in df.iterrows():
                                    if pd.isna(r['conteudo']) or str(r['conteudo']).strip()=="": continue
                                    emp=padronizar(str(r['empresa'])); doc=padronizar(str(r['documento'])); mot=padronizar(str(r['motivo'])); cont=padronizar(str(r['conteudo']),'frase')
                                    rev_por=user['username']; rev_data=datetime.now().strftime('%Y-%m-%d')
                                    if 'revisado_por' in df.columns and pd.notna(r['revisado_por']): rev_por=str(r['revisado_por'])
                                    if 'data_revisao' in df.columns and pd.notna(r['data_revisao']):
                                        try: val=r['data_revisao']; rev_data=val.strftime('%Y-%m-%d') if isinstance(val,datetime) else str(val).split('T')[0]
                                        except: pass
                                    if cont not in db_set: novos.append({'empresa':emp,'documento':doc,'motivo':mot,'conteudo':cont,'revisado_por':rev_por,'data_revisao':rev_data}); db_set.add(cont)
                                if novos: supabase.table("frases").insert(novos).execute(); registrar_log(user['username'],"Import",f"{len(novos)}"); st.success(f"{len(novos)} itens importados!"); time.sleep(2); st.rerun()
                                else: st.warning("Nenhuma frase nova encontrada.")
                        except Exception as e: st.error(str(e))

        # --- 3. EDITAR & EXCLUIR (MANUTENÇÃO) ---
        elif "✏️" in page:
            st.title("Gerenciar Frases")
            st.write("")
            q = st.text_input("🔎 Buscar registro para editar ou excluir...", placeholder="Digite palavras-chave")
            
            dados = buscar_dados()
            lista = [f for f in dados if q.lower() in str(f).lower()] if q else dados
            
            # Paginação Simples para não travar (Mostra os primeiros 50 se não tiver busca)
            if not q:
                st.info("Mostrando os 50 registros mais recentes. Use a busca para encontrar específicos.")
                lista = lista[:50]
            
            if not lista: st.warning("Nenhum registro encontrado.")
            else:
                for f in lista:
                    label = f"🏢 {f['empresa']}  |  📄 {f['documento']}  |  📌 {f['motivo']}"
                    with st.expander(label):
                        with st.form(f"ed_{f['id']}"):
                            c_a, c_b = st.columns(2)
                            fe = c_a.text_input("Empresa", f['empresa'])
                            fd = c_b.text_input("Documento", f['documento'])
                            fm = st.text_input("Motivo", f['motivo'])
                            fc = st.text_area("Conteúdo", f['conteudo'], height=100)
                            
                            c_save, c_del = st.columns([4, 1])
                            if c_save.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                                supabase.table("frases").update({
                                    "empresa":padronizar(fe),"documento":padronizar(fd),"motivo":padronizar(fm),"conteudo":padronizar(fc,"frase"),"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')
                                }).eq("id", f['id']).execute()
                                registrar_log(user['username'], "Editou Frase", str(f['id'])); st.rerun()
                            
                            # Botão de Excluir dentro do form (funciona isolado pelo IF)
                            if c_del.form_submit_button("🗑️ Excluir", type="primary", use_container_width=True):
                                supabase.table("frases").delete().eq("id", f['id']).execute()
                                registrar_log(user['username'], "Excluiu Frase", str(f['id'])); st.rerun()

        # --- 4. GERENCIADOR (ADMIN) ---
        elif "⚙️" in page and user['admin']:
            st.title("Gerenciador do Sistema")
            t1, t2 = st.tabs(["Usuários", "Dados & Logs"])
            
            with t1:
                c_new, c_list = st.columns([1, 2])
                with c_new:
                    with st.container(border=True):
                        st.subheader("Novo Usuário")
                        nu = st.text_input("Nome"); ns = st.text_input("Senha"); na = st.checkbox("Admin")
                        if st.button("Criar Usuário", use_container_width=True):
                            supabase.table("usuarios").insert({"username":nu,"senha":ns,"admin":na,"trocar_senha":True}).execute()
                            registrar_log(user['username'], "Criou Usuário", nu); st.rerun()
                with c_list:
                    st.subheader("Usuários Ativos")
                    for u in buscar_usuarios():
                        with st.expander(f"{u['username']} {'(Admin)' if u['admin'] else ''}"):
                            c_x, c_y = st.columns(2)
                            if c_x.button("Resetar Senha", key=f"r{u['id']}", use_container_width=True): supabase.table("usuarios").update({"trocar_senha":True}).eq("id", u['id']).execute(); st.toast("Resetado!")
                            if u['username']!=user['username'] and c_y.button("Excluir", key=f"d{u['id']}", type="primary", use_container_width=True): supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()
            
            with t2:
                st.subheader("Logs de Auditoria")
                logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(50).execute().data
                if logs: st.dataframe(pd.DataFrame(logs)[['data_hora','usuario','acao','detalhe']], use_container_width=True, height=300)
                st.write("---")
                c_bkp, c_danger = st.columns(2)
                with c_bkp:
                    st.subheader("Backup")
                    full = buscar_dados()
                    if full: st.download_button("📥 Baixar CSV (Backup)", pd.DataFrame(full).to_csv(index=False).encode('utf-8'), "backup.csv", "text/csv", use_container_width=True)
                with c_danger:
                    with st.container(border=True):
                        st.subheader("Zona de Perigo")
                        chk = st.text_input("Para limpar todas as frases digite: QUERO APAGAR TUDO")
                        if st.button("LIMPAR BANCO DE FRASES", type="primary", use_container_width=True):
                            if chk=="QUERO APAGAR TUDO":
                                supabase.table("frases").delete().neq("id", 0).execute()
                                registrar_log(user['username'], "LIMPEZA TOTAL", "Todas as frases foram apagadas"); st.rerun()

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
# 🖼️ ÁREA DAS IMAGENS
# ==============================================================================
FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"
# ==============================================================================

# --- TENTA CARREGAR O FAVICON ---
favicon = "💙" 
try:
    response = requests.get(FAVICON_URL, timeout=3)
    if response.status_code == 200:
        favicon = Image.open(io.BytesIO(response.content))
except: pass

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Frases de Recusa - Gupy", page_icon=favicon, layout="wide")

# --- CSS MODERNO (BARRA INVISÍVEL) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F5F7FA; }
    
    /* --- O SEGREDO PARA ESCONDER A BARRA --- */
    [data-testid="stHeader"] {
        display: none;
    }
    footer {
        display: none;
    }
    
    /* Subir o conteúdo já que a barra sumiu */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #00122F; }
    section[data-testid="stSidebar"] * { color: white !important; }
    
    /* BOTÕES */
    .stButton > button {
        border-radius: 6px; font-weight: 600; border: none;
        transition: transform 0.1s;
        background-color: #2175D9; color: white;
    }
    .stButton > button:hover { background-color: #175BB5; color: white; }
    .stButton > button:active { transform: scale(0.98); }
    
    /* CARTÕES DE GESTÃO */
    .card-container {
        background: white;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2175D9;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* INPUTS */
    .stTextInput input, .stTextArea textarea {
        border-radius: 6px; border: 1px solid #CBD5E0;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2175D9; box-shadow: 0 0 0 2px rgba(33, 117, 217, 0.2);
    }
    
    /* Expander mais limpo */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 6px;
    }
    
    /* Logo Fallback Text */
    .logo-text {
        font-size: 2rem; font-weight: 800; color: #2175D9; letter-spacing: -1px; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except: st.stop()

# --- 3. BACKEND ---
def verificar_login(u, s):
    try:
        res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute()
        return res.data[0] if res.data else None
    except: return None

def buscar_dados(): return supabase.table("frases").select("*").order("id", desc=True).execute().data
def buscar_usuarios(): return supabase.table("usuarios").select("*").order("id").execute().data
def registrar_log(usuario, acao, detalhe):
    try: supabase.table("logs").insert({"usuario":usuario,"acao":acao,"detalhe":detalhe,"data_hora":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
    except: pass

def padronizar(texto, tipo="titulo"):
    if not texto: return ""
    texto = str(texto).strip()
    return texto.title() if tipo == "titulo" else (texto[0].upper() + texto[1:])

def limpar_coluna(col):
    col = str(col).lower().strip()
    col = ''.join(c for c in unicodedata.normalize('NFD', col) if unicodedata.category(c) != 'Mn')
    return col

# --- 4. FRONTEND ---
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None:
    c1, c2, c3 = st.columns([1,1.2,1])
    with c2:
        st.write(""); st.write("")
        with st.container(border=True):
            if LOGO_URL: st.image(LOGO_URL, use_container_width=True)
            else: st.markdown("<h1 class='logo-text'>gupy</h1>", unsafe_allow_html=True)
            
            st.markdown("<h3 style='text-align:center; color:#555;'>Frases de Recusa</h3>", unsafe_allow_html=True)
            with st.form("login"):
                u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
                if st.form_submit_button("Acessar Plataforma", use_container_width=True):
                    user = verificar_login(u, s)
                    if user: st.session_state["usuario_logado"] = user; st.rerun()
                    else: st.error("Credenciais inválidas.")

else:
    user = st.session_state["usuario_logado"]
    
    with st.sidebar:
        if LOGO_URL: st.image(LOGO_URL, width=140)
        else: st.markdown("## gupy<span style='color:#2175D9'>.</span>", unsafe_allow_html=True)
        
        st.caption(f"Olá, {user['username']}")
        st.divider()
        
        opcoes = ["📂 Frases de Recusa", "📝 Gestão de Frases", "⚙️ Gerenciador"] if user['admin'] else ["📂 Frases de Recusa", "📝 Gestão de Frases"]
        page = st.radio("Navegação", opcoes, label_visibility="collapsed")
        
        st.divider()
        if st.button("Sair", use_container_width=True): st.session_state["usuario_logado"] = None; st.rerun()

    if user.get('trocar_senha'):
        st.warning("⚠️ Redefina sua senha"); n1=st.text_input("Nova"); n2=st.text_input("Confirmar")
        if st.button("Salvar"): 
            if n1==n2 and n1: supabase.table("usuarios").update({"senha":n1,"trocar_senha":False}).eq("id",user['id']).execute(); user['trocar_senha']=False; st.rerun()

    else:
        # --- 1. BIBLIOTECA ---
        if page == "📂 Frases de Recusa":
            c_tit, c_search = st.columns([1, 3])
            with c_tit:
                st.subheader("Frases de Recusa")
            with c_search:
                termo = st.text_input("Busca Rápida", placeholder="🔎 Digite para pesquisar...", label_visibility="collapsed")
            
            dados = buscar_dados()
            filtrados = [f for f in dados if termo.lower() in str(f).lower()] if termo else dados
            
            st.caption(f"{len(filtrados)} registros")
            
            for f in filtrados:
                with st.container(border=True):
                    col_info, col_cont = st.columns([1.2, 3])
                    with col_info:
                        st.markdown(f"**{f['empresa']}**")
                        st.caption(f"📄 {f['documento']}")
                        st.caption(f"📌 {f['motivo']}")
                        if f.get('revisado_por'): 
                            try:
                                dt = datetime.strptime(f['data_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y')
                                st.caption(f"<span style='color:green'>✔ {f['revisado_por']} ({dt})</span>", unsafe_allow_html=True)
                            except: pass
                    with col_cont:
                        st.code(f['conteudo'], language="text")

        # --- 2. GESTÃO ---
        elif page == "📝 Gestão de Frases":
            st.subheader("Gestão de Frases")
            
            with st.expander("➕  Adicionar Nova Frase", expanded=False):
                with st.form("quick_add"):
                    c1, c2, c3 = st.columns(3)
                    ne = c1.text_input("Empresa"); nd = c2.text_input("Documento"); nm = c3.text_input("Motivo")
                    nc = st.text_area("Conteúdo da Frase", height=150)
                    if st.form_submit_button("Salvar", use_container_width=True):
                        if nc:
                            ne, nd, nm = padronizar(ne), padronizar(nd), padronizar(nm); nc = padronizar(nc, "frase")
                            if len(supabase.table("frases").select("id").eq("conteudo", nc).execute().data) > 0: st.error("Duplicado.")
                            else:
                                supabase.table("frases").insert({"empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).execute()
                                registrar_log(user['username'], "Criou Frase", f"{ne} - {nm}"); st.success("Adicionado!"); time.sleep(1); st.rerun()
            
            st.write("")
            col_search, col_upload = st.columns([3, 1])
            q = col_search.text_input("🔎 Buscar...", placeholder="Digite para filtrar")
            
            with col_upload:
                with st.popover("📂 Importar", use_container_width=True):
                    upl = st.file_uploader("Excel/CSV", type=['csv','xlsx'])
                    if upl and st.button("Processar"):
                        try:
                            if upl.name.endswith('.csv'):
                                try: df = pd.read_csv(upl)
                                except: df = pd.read_csv(upl, encoding='latin-1', sep=';')
                            else: df = pd.read_excel(upl)

                            # Auto-header
                            header_idx = -1; keywords = ['empresa', 'conteudo', 'frase', 'motivo']
                            for i, row in df.head(50).iterrows():
                                row_str = " ".join([str(val).lower() for val in row.values])
                                if sum(1 for k in keywords if k in row_str) >= 2: header_idx = i; break
                            if header_idx > -1:
                                if header_idx > 0:
                                    if upl.name.endswith('.csv'): upl.seek(0); df = pd.read_csv(upl, header=header_idx, encoding='latin-1', sep=None, engine='python')
                                    else: upl.seek(0); df = pd.read_excel(upl, header=header_idx)

                            df.columns = [limpar_coluna(c) for c in df.columns]
                            mapa = {'empresa solicitante':'empresa','cliente':'empresa','tipo documento':'documento','doc':'documento','motivo recusa':'motivo','motivo da recusa':'motivo','justificativa':'motivo','frase':'conteudo','texto':'conteudo','mensagem':'conteudo','frase de recusa':'conteudo','revisado por':'revisado_por','revisor':'revisado_por','validado por':'revisado_por','data':'data_revisao','data revisao':'data_revisao','data da revisao':'data_revisao'}
                            df.rename(columns=mapa, inplace=True)

                            cols_obr = ['empresa', 'documento', 'motivo', 'conteudo']
                            if not all(c in df.columns for c in cols_obr): st.error("Colunas inválidas.")
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
                                if novos: supabase.table("frases").insert(novos).execute(); registrar_log(user['username'],"Import",f"{len(novos)}"); st.success("Importado!"); time.sleep(2); st.rerun()
                                else: st.warning("Sem novidades.")
                        except Exception as e: st.error(str(e))

            dados = buscar_dados()
            lista = [f for f in dados if q.lower() in str(f).lower()] if q else dados
            st.caption(f"{len(lista)} registros")
            
            for f in lista:
                with st.expander(f"🏢 {f['empresa']} | {f['documento']} | {f['motivo']}"):
                    with st.form(f"ed_{f['id']}"):
                        c_a, c_b = st.columns(2)
                        fe = c_a.text_input("Empresa", f['empresa'])
                        fd = c_b.text_input("Documento", f['documento'])
                        fm = st.text_input("Motivo", f['motivo'])
                        fc = st.text_area("Conteúdo", f['conteudo'], height=100)
                        
                        c_save, c_del = st.columns([4, 1])
                        if c_save.form_submit_button("Salvar", use_container_width=True):
                            supabase.table("frases").update({"empresa":padronizar(fe),"documento":padronizar(fd),"motivo":padronizar(fm),"conteudo":padronizar(fc,"frase"),"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).eq("id", f['id']).execute()
                            registrar_log(user['username'], "Edit", str(f['id'])); st.rerun()
                        if c_del.form_submit_button("Excluir", type="primary", use_container_width=True):
                            supabase.table("frases").delete().eq("id", f['id']).execute()
                            registrar_log(user['username'], "Delete", str(f['id'])); st.rerun()

        # --- 4. ADMIN ---
        elif page == "⚙️ Gerenciador" and user['admin']:
            st.subheader("Painel Admin")
            t1, t2 = st.tabs(["Usuários", "Dados"])
            with t1:
                c_new, c_list = st.columns([1, 2])
                with c_new:
                    with st.container(border=True):
                        st.markdown("**Novo Usuário**")
                        nu = st.text_input("Nome"); ns = st.text_input("Senha"); na = st.checkbox("Admin")
                        if st.button("Criar", use_container_width=True):
                            supabase.table("usuarios").insert({"username":nu,"senha":ns,"admin":na,"trocar_senha":True}).execute()
                            registrar_log(user['username'], "New User", nu); st.rerun()
                with c_list:
                    for u in buscar_usuarios():
                        with st.expander(f"{u['username']} {'(Admin)' if u['admin'] else ''}"):
                            c_x, c_y = st.columns(2)
                            if c_x.button("Reset Senha", key=f"r{u['id']}"): supabase.table("usuarios").update({"trocar_senha":True}).eq("id", u['id']).execute(); st.toast("Ok!")
                            if u['username']!=user['username'] and c_y.button("Excluir", key=f"d{u['id']}", type="primary"): supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()
            with t2:
                logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(50).execute().data
                if logs: st.dataframe(pd.DataFrame(logs)[['data_hora','usuario','acao','detalhe']], use_container_width=True, height=200)
                full = buscar_dados()
                if full: st.download_button("Baixar CSV", pd.DataFrame(full).to_csv(index=False).encode('utf-8'), "bkp.csv", "text/csv")
                st.divider()
                chk = st.text_input("Limpar tudo (Digite: QUERO APAGAR TUDO)")
                if st.button("LIMPAR FRASES", type="primary") and chk=="QUERO APAGAR TUDO":
                    supabase.table("frases").delete().neq("id", 0).execute()
                    registrar_log(user['username'], "WIPE", "ALL"); st.rerun()

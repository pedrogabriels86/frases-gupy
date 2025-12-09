import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime, timedelta
import io
import requests
import csv
import pandas as pd
from PIL import Image
import extra_streamlit_components as stx

# ==============================================================================
# 1. CONFIGURAÇÕES E INICIALIZAÇÃO
# ==============================================================================
@st.cache_data
def carregar_favicon(url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except: return "💙"
    return "💙"

FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"

favicon = carregar_favicon(FAVICON_URL)

st.set_page_config(page_title="Gupy Frases", page_icon=favicon, layout="wide")

# ==============================================================================
# 2. ESTILO CSS
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.5rem !important; }
    header { visibility: hidden; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05); background-color: white;
    }
    div.stButton > button { border-radius: 8px; font-weight: 600; }
    .stCodeBlock { margin-top: -10px; }
    .stRadio > div[role="radiogroup"] {
        background: white; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; display: flex; justify-content: center;
    }
    .danger-zone { border: 1px solid #ff4b4b; background-color: #fff5f5; padding: 20px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CONEXÃO E FUNÇÕES DO BANCO DE DADOS
# ==============================================================================
try:
    url_db = st.secrets["SUPABASE_URL"]
    key_db = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url_db, key_db)
except:
    st.error("Erro crítico: Segredos do Supabase não configurados.")
    st.stop()

def verificar_login(u, s):
    try:
        res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute()
        return res.data[0] if res.data else None
    except: return None

def recuperar_usuario_cookie(username):
    try:
        res = supabase.table("usuarios").select("*").eq("username", username).execute()
        return res.data[0] if res.data else None
    except: return None

def registrar_log(usuario, acao, detalhe):
    try:
        supabase.table("logs").insert({
            "usuario": usuario, "acao": acao, "detalhe": detalhe, 
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
    except: pass

def converter_para_csv(dados):
    if not dados: return ""
    output = io.StringIO()
    if len(dados) > 0:
        writer = csv.DictWriter(output, fieldnames=dados[0].keys())
        writer.writeheader()
        writer.writerows(dados)
    return output.getvalue()

def buscar_frases_otimizado(termo=None, empresa_filtro="Todas"):
    query = supabase.table("frases").select("*").order("id", desc=True)
    if termo:
        query = query.or_(f"conteudo.ilike.%{termo}%,empresa.ilike.%{termo}%,motivo.ilike.%{termo}%,revisado_por.ilike.%{termo}%,documento.ilike.%{termo}%")
    if empresa_filtro != "Todas":
        query = query.eq("empresa", empresa_filtro)
    return query.limit(50 if termo else 4).execute().data or []

@st.cache_data(ttl=300)
def listar_empresas_unicas():
    try:
        data = supabase.table("frases").select("empresa").execute().data
        return ["Todas"] + sorted(list(set([d['empresa'] for d in data])))
    except: return ["Todas"]

def padronizar(texto): return str(texto).strip() if texto else ""
def gerar_assinatura(e, m, c): return f"{padronizar(e).lower()}|{padronizar(m).lower()}|{padronizar(c).lower()}"

# ==============================================================================
# 4. COMPONENTES VISUAIS E TELAS
# ==============================================================================
def card_frase(frase):
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{frase['empresa']}**"); c1.caption(f"{frase['motivo']} • {frase['documento']}")
        c2.markdown(f"<div style='text-align:right; font-size:0.8em; color:#888'>#{frase['id']}</div>", unsafe_allow_html=True)
        st.code(frase['conteudo'], language=None)
        st.markdown(f"<div style='display:flex; justify-content:space-between; font-size:0.75rem; color:#666; margin-top:5px;'><span>✍️ {frase.get('revisado_por', 'Sistema')}</span><span>📅 {frase.get('data_revisao', '-')}</span></div>", unsafe_allow_html=True)

def tela_biblioteca(user):
    st.markdown("### 📂 Biblioteca")
    with st.container():
        c1, c2 = st.columns([3, 1])
        with c1:
            termo = st.text_input("🔍 Pesquisar", placeholder="Busque por Usuário, Empresa... (Enter para buscar)", label_visibility="collapsed")
        empresa = c2.selectbox("Empresa", listar_empresas_unicas(), label_visibility="collapsed")
    
    with st.spinner("..."): dados = buscar_frases_otimizado(termo if termo else None, empresa)
    if not termo and empresa=="Todas": st.caption("🔥 4 mais recentes")
    
    if not dados: st.info("Nada encontrado.")
    else:
        c1, c2 = st.columns(2)
        for i, f in enumerate(dados):
            with (c1 if i%2==0 else c2): card_frase(f)

def tela_adicionar(user):
    st.markdown("### ➕ Nova Frase")
    t1, t2 = st.tabs(["Manual", "Excel"])
    with t1:
        with st.form("add"):
            ne=st.text_input("Empresa"); nd=st.text_input("Doc"); nm=st.text_input("Motivo"); nc=st.text_area("Texto")
            if st.form_submit_button("Salvar"):
                supabase.table("frases").insert({"empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).execute()
                registrar_log(user['username'], "Add", ne); st.success("Salvo!"); time.sleep(1); st.rerun()
    with t2:
        arq = st.file_uploader("Excel", type=["xlsx"])
        if arq and st.button("Importar"):
            try:
                df = pd.read_excel(arq); df.columns = [c.lower().strip() for c in df.columns]
                sucesso = 0
                for i, row in df.iterrows():
                    try:
                        us = str(row.get('usuario')).strip() if pd.notnull(row.get('usuario')) else user['username']
                        dt = pd.to_datetime(row.get('data')).strftime('%Y-%m-%d') if pd.notnull(row.get('data')) else datetime.now().strftime('%Y-%m-%d')
                        supabase.table("frases").insert({"empresa":row['empresa'],"motivo":row['motivo'],"conteudo":row['conteudo'],"documento":row.get('documento','Geral'),"revisado_por":us,"data_revisao":dt}).execute()
                        sucesso += 1
                    except: pass
                st.success(f"Importado {sucesso} itens!"); time.sleep(2); st.rerun()
            except Exception as e: st.error(f"Erro no Excel: {e}")

def tela_manutencao(user):
    st.markdown("### 🛠️ Manutenção")
    q = st.text_input("Buscar ID ou Texto")
    query = supabase.table("frases").select("*").order("id", desc=True)
    query = query.or_(f"empresa.ilike.%{q}%,motivo.ilike.%{q}%") if q else query.limit(4)
    items = query.execute().data
    for item in items:
        with st.expander(f"#{item['id']} {item['empresa']}"):
            if st.button(f"Excluir {item['id']}"):
                supabase.table("frases").delete().eq("id", item['id']).execute(); st.rerun()

def tela_admin(user):
    st.markdown("### ⚙️ Admin")
    t1, t2, t3 = st.tabs(["Users", "Backup", "Danger"])
    with t1:
        st.dataframe(supabase.table("usuarios").select("username,admin").execute().data)
    with t2:
        df = supabase.table("frases").select("*").execute().data
        st.download_button("Backup CSV", converter_para_csv(df), "bkp.csv")
    with t3:
        if st.text_input("Digite CONFIRMAR") == "CONFIRMAR":
            if st.button("RESET FRASES", type="primary"):
                supabase.table("frases").delete().neq("id", 0).execute(); st.success("Zerado!"); st.rerun()

# ==============================================================================
# 5. LÓGICA DE AUTENTICAÇÃO (SISTEMA DE COOKIES)
# ==============================================================================

# Inicializa o Cookie Manager com chave fixa para não recarregar
cookie_manager = stx.CookieManager(key="auth_sys_cookie")

# 1. Recuperar Usuário do Cache (Session State)
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# 2. Se não houver usuário na sessão, tentar recuperar do Cookie
if st.session_state["usuario_logado"] is None:
    # Tenta ler o cookie 'gupy_token'
    cookies = cookie_manager.get_all()
    token = cookies.get("gupy_token")
    
    if token:
        user_db = recuperar_usuario_cookie(token)
        if user_db:
            st.session_state["usuario_logado"] = user_db
            # Força rerun apenas se encontrou usuario agora
            # st.rerun() 

# 3. Decide qual tela mostrar
if st.session_state["usuario_logado"] is None:
    # --- TELA DE LOGIN ---
    c1, c2, c3 = st.columns([1, 0.8, 1])
    with c2:
        st.write(""); st.write("")
        st.image(LOGO_URL, width=150)
        with st.container(border=True):
            st.markdown("<h3 style='text-align:center'>Login</h3>", unsafe_allow_html=True)
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            
            if st.button("Entrar", type="primary", use_container_width=True):
                user = verificar_login(u, s)
                if user:
                    # Salva no Session State
                    st.session_state["usuario_logado"] = user
                    # Salva no Cookie (Validade de 7 dias)
                    cookie_manager.set("gupy_token", u, expires_at=datetime.now() + timedelta(days=7))
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
else:
    # --- APLICAÇÃO LOGADA ---
    user = st.session_state["usuario_logado"]
    c_logo, c_nav, c_user = st.columns([1, 4, 1], vertical_alignment="center")
    
    with c_logo: st.image(LOGO_URL, width=80)
    
    with c_nav:
        opcoes = ["Biblioteca", "Adicionar", "Manutenção"]
        if user.get('admin') == True: opcoes.append("Admin")
        selecao = st.radio("Nav", opcoes, horizontal=True, label_visibility="collapsed")
    
    with c_user:
        if st.button("Sair"):
            # Logout seguro (tenta apagar cookie, se não der, ignora)
            try: cookie_manager.delete("gupy_token")
            except: pass
            st.session_state["usuario_logado"] = None
            st.rerun()
            
    st.divider()

    if selecao == "Biblioteca": tela_biblioteca(user)
    elif selecao == "Adicionar": tela_adicionar(user)
    elif selecao == "Manutenção": tela_manutencao(user)
    elif selecao == "Admin": tela_admin(user)

    st.markdown("<br><div style='text-align:center; color:#CCC; font-size:0.8rem'>Desenvolvido por Pedro Gabriel</div>", unsafe_allow_html=True)

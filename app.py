import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time
from datetime import datetime, timedelta
import io
import unicodedata
import requests
from PIL import Image
import extra_streamlit_components as stx

# ==============================================================================
# 1. CONFIGURAÇÕES E INICIALIZAÇÃO
# ==============================================================================
FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"

favicon = "💙" 
try:
    response = requests.get(FAVICON_URL, timeout=1)
    if response.status_code == 200: 
        favicon = Image.open(io.BytesIO(response.content))
except: pass

st.set_page_config(page_title="Gupy Frases", page_icon=favicon, layout="wide")

# ==============================================================================
# 2. CSS CUSTOMIZADO (CORREÇÃO DE LAYOUT E ESPAÇAMENTOS)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1E293B; }
    .stApp { background-color: #F8FAFC; }
    
    /* 1. LIMPEZA RADICAL DE ESPAÇOS DO STREAMLIT */
    .block-container {
        padding-top: 0rem !important; /* Remove espaço do topo */
        padding-bottom: 3rem; 
        padding-left: 3rem; 
        padding-right: 3rem;
        max-width: 100%;
    }
    
    /* Remove espaço entre componentes verticais */
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem !important; 
    }
    
    /* Esconde header e footer padrão */
    header[data-testid="stHeader"], footer { display: none !important; }

    /* 2. CABEÇALHO (HEADER) PERSONALIZADO */
    .header-container {
        background-color: white;
        padding: 1rem 3rem;
        margin-left: -3rem; /* Compensa o padding do body */
        margin-right: -3rem;
        border-bottom: 1px solid #E2E8F0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    /* Texto de boas-vindas compacto */
    .user-welcome {
        font-size: 0.9rem;
        color: #64748B;
        margin-right: 1rem;
        text-align: right;
    }

    /* Botão Sair - Pequeno e Discreto */
    .btn-logout button {
        background-color: transparent !important;
        border: 1px solid #CBD5E1 !important;
        color: #64748B !important;
        padding: 0.3rem 0.8rem !important;
        font-size: 0.8rem !important;
        height: auto !important;
        min-height: 0px !important;
        line-height: 1 !important;
    }
    .btn-logout button:hover {
        border-color: #EF4444 !important;
        color: #EF4444 !important;
        background-color: #FEF2F2 !important;
    }

    /* 3. MENU DE NAVEGAÇÃO (TABS) CENTRALIZADO E COMPACTO */
    .stRadio {
        background-color: transparent;
        margin-bottom: 1.5rem !important;
    }
    .stRadio > div[role="radiogroup"] {
        display: flex;
        justify-content: flex-start; /* Alinha à esquerda, junto ao título */
        gap: 0px; /* Remove buracos entre botões */
        background-color: white;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        padding: 4px;
        width: fit-content; /* Ocupa apenas o espaço necessário */
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stRadio > div[role="radiogroup"] label {
        padding: 6px 16px;
        border-radius: 6px;
        border: none;
        margin: 0 !important;
        font-size: 0.9rem;
        color: #64748B;
        transition: all 0.2s;
    }
    .stRadio > div[role="radiogroup"] label:hover {
        color: #1E293B;
        background-color: #F1F5F9;
    }
    .stRadio > div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EFF6FF !important;
        color: #2563EB !important;
        font-weight: 600;
    }
    /* Remove a bolinha do radio button padrão */
    .stRadio > div[role="radiogroup"] label > div:first-child { display: none; }

    /* 4. BARRA DE BUSCA (INPUTS UNIFICADOS) */
    .search-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    /* Força inputs a terem a mesma altura visual */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        border-color: #CBD5E1;
        min-height: 42px; 
    }

    /* 5. CARDS DE RESULTADO */
    .result-card {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        height: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .result-card:hover {
        border-color: #BFDBFE;
        box-shadow: 0 4px 12px -2px rgba(37, 99, 235, 0.1);
        transform: translateY(-2px);
    }
    .card-title { color: #1E3A8A; font-weight: 700; font-size: 1.05rem; }
    .card-badge { 
        background-color: #EFF6FF; color: #2563EB; 
        padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; border: 1px solid #DBEAFE;
    }
    .card-meta { font-size: 0.8rem; color: #94A3B8; margin-top: 10px; display: flex; gap: 15px;}

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CONEXÃO E FUNÇÕES (MANTIDO IGUAL)
# ==============================================================================
try:
    url_db = st.secrets["SUPABASE_URL"]
    key_db = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url_db, key_db)
except: 
    st.error("Erro de configuração: Secrets não encontrados.")
    st.stop()

def verificar_login(u, s):
    try: res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute(); return res.data[0] if res.data else None
    except: return None

def recuperar_usuario_cookie(username):
    try: res = supabase.table("usuarios").select("*").eq("username", username).execute(); return res.data[0] if res.data else None
    except: return None

@st.cache_data(ttl=60)
def buscar_dados(): 
    return supabase.table("frases").select("*").order("id", desc=True).execute().data or []
def buscar_usuarios(): 
    return supabase.table("usuarios").select("*").order("id").execute().data or []

def registrar_log(usuario, acao, detalhe):
    try: supabase.table("logs").insert({"usuario": usuario, "acao": acao, "detalhe": detalhe, "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
    except: pass
    
def padronizar(texto, tipo="titulo"): 
    if not texto: return ""
    texto = str(texto).strip()
    return texto.title() if tipo == "titulo" else texto[0].upper() + texto[1:]

def limpar_coluna(col): 
    return ''.join(c for c in unicodedata.normalize('NFD', str(col).lower().strip()) if unicodedata.category(c) != 'Mn')

# ==============================================================================
# 4. AUTENTICAÇÃO
# ==============================================================================
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None
cookie_manager = stx.CookieManager(key="main_auth")

if st.session_state["usuario_logado"] is None:
    cookies = cookie_manager.get_all()
    token = cookies.get("gupy_user_token") if cookies else None
    if token:
        user_db = recuperar_usuario_cookie(token)
        if user_db: st.session_state["usuario_logado"] = user_db

# ==============================================================================
# 5. FUNÇÕES DE RENDERIZAÇÃO
# ==============================================================================

def render_biblioteca(dados_totais, user):
    # Container unificado para busca
    with st.container():
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        # Vertical alignment="bottom" é o segredo para alinhar Input com Selectbox
        c_search, c_filter = st.columns([4, 2], vertical_alignment="bottom")
        
        with c_search:
            st.markdown("<span style='font-size:0.9rem; font-weight:600; color:#334155'>O que você procura?</span>", unsafe_allow_html=True)
            termo = st.text_input("Busca", placeholder="Ex: Gupy, Baixa Qualificação...", label_visibility="collapsed", key="lib_search_term")
        
        with c_filter:
            st.markdown("<span style='font-size:0.9rem; font-weight:600; color:#334155'>Filtrar por Empresa</span>", unsafe_allow_html=True)
            filtro_empresa = st.selectbox("Filtrar Empresa", ["Todas"] + sorted(list(set(d['empresa'] for d in dados_totais))), label_visibility="collapsed", key="lib_filter_empresa")
        st.markdown('</div>', unsafe_allow_html=True)

    filtrados = dados_totais
    if filtro_empresa != "Todas": filtrados = [f for f in filtrados if f['empresa'] == filtro_empresa]
    if termo: 
        termo_limpo = limpar_coluna(termo)
        filtrados = [f for f in filtrados if termo_limpo in limpar_coluna(f['empresa']) or termo_limpo in limpar_coluna(f['motivo']) or termo_limpo in limpar_coluna(f['conteudo'])]

    # Resultado da busca
    c_res_count, c_spacer = st.columns([1, 4])
    c_res_count.markdown(f"<div style='margin-bottom:10px; color:#64748B; font-size:0.9rem'>Encontrados: <b>{len(filtrados)}</b></div>", unsafe_allow_html=True)
    
    if not filtrados: 
        st.info("Nenhum resultado encontrado com os filtros atuais.")
    else:
        # Grid de Cards
        for i in range(0, len(filtrados), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(filtrados):
                    frase = filtrados[i+j]
                    with col:
                        st.markdown(f"""
                        <div class="result-card">
                            <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:8px;">
                                <div class="card-title">{frase['empresa']}</div>
                                <div class="card-badge">{frase['documento']}</div>
                            </div>
                            <div style="color:#475569; font-size:0.9rem; margin-bottom:12px; font-weight:500;">{frase['motivo']}</div>
                            <div style="background:#F8FAFC; padding:10px; border-radius:6px; border:1px solid #E2E8F0; font-family:monospace; font-size:0.85rem; color:#334155; margin-bottom:10px;">
                                {frase['conteudo'][:140]}...
                            </div>
                            <div class="card-meta">
                                <span>👤 {frase.get('revisado_por', 'Sistema')}</span>
                                <span>📅 {frase.get('data_revisao', '-')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        # Expander "invisível" para ver texto completo se necessário
                        with st.expander("Ver texto completo"):
                            st.code(frase['conteudo'], language="text")

def render_adicionar(dados_totais, user):
    st.markdown("### ➕ Adicionar Novas Frases")
    with st.container(border=True):
        with st.form("add_single", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ne = c1.text_input("Empresa Solicitante", placeholder="Ex: Gupy Tech"); 
            nd = c2.text_input("Tipo de Documento", placeholder="Ex: Carta Recusa");
            nm = st.text_input("Motivo da Recusa", placeholder="Ex: Baixa Qualificação"); 
            nc = st.text_area("Texto da Frase", height=120);
            
            if st.form_submit_button("Salvar Registro", type="primary", use_container_width=True):
                supabase.table("frases").insert({
                    "empresa":padronizar(ne), "documento":padronizar(nd), "motivo":padronizar(nm), "conteudo":padronizar(nc, "frase"), 
                    "revisado_por":user['username'], "data_revisao":datetime.now().strftime('%Y-%m-%d')
                }).execute()
                st.toast("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun() 

def render_manutencao(dados_totais, user):
    st.markdown("### ✏️ Manutenção Rápida")
    q = st.text_input("Filtrar para editar", placeholder="Busque a frase...")
    filtrados = [f for f in dados_totais if q.lower() in str(f).lower()] if q else dados_totais[:5]
    
    for item in filtrados:
        with st.expander(f"{item['empresa']} - {item['motivo']}"):
             st.json(item) # Simplificado para exemplo visual
             if st.button(f"Excluir ID {item['id']}", key=f"del_{item['id']}"):
                 supabase.table("frases").delete().eq("id", item['id']).execute()
                 st.rerun()

def render_admin(user, dados_totais):
    st.info("Painel Admin Ativo")

# ==============================================================================
# 6. FLUXO PRINCIPAL (LAYOUT REVISADO)
# ==============================================================================

if st.session_state["usuario_logado"] is None:
    # TELA DE LOGIN (SIMPLIFICADA)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.write("#")
        with st.container(border=True):
            st.markdown("<h2 style='text-align:center'>Acesso Gupy</h2>", unsafe_allow_html=True)
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.button("Entrar", type="primary", use_container_width=True):
                user = verificar_login(u, s)
                if user:
                    st.session_state["usuario_logado"] = user
                    cookie_manager.set("gupy_user_token", u, expires_at=datetime.now() + timedelta(days=7))
                    st.rerun()
                else: st.error("Login inválido")

else:
    user = st.session_state["usuario_logado"]
    dados_totais = buscar_dados()

    # --- HEADER NOVO (Sem st.columns tradicional para evitar quebras) ---
    # Usamos HTML/CSS puro para o topo para garantir alinhamento perfeito
    st.markdown(f"""
    <div class="header-container">
        <div style="display:flex; align-items:center; gap:15px;">
            <img src="{LOGO_URL}" width="100" style="object-fit:contain;">
            <div style="height:25px; width:1px; background:#E2E8F0;"></div>
            <span style="font-weight:600; color:#1E293B;">Central de Frases</span>
        </div>
        <div style="display:flex; align-items:center;">
            <div class="user-welcome">
                Olá, <b>{user['username']}</b>
                <div style="font-size:0.75rem; color:#94A3B8;">{'Administrador' if user['admin'] else 'Colaborador'}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # O botão de sair precisa ser Streamlit nativo para funcionar o Python, 
    # então usamos um truque de posicionamento absoluto ou colunas logo abaixo se necessário,
    # mas para ficar bonito, vamos colocar alinhado à direita no topo do corpo:
    
    # Layout do Corpo
    c_menu, c_logout = st.columns([6, 1], vertical_alignment="center")
    
    with c_menu:
        # Menu Compacto
        opcoes = {"Biblioteca": "📂 Biblioteca", "Adicionar": "➕ Adicionar", "Manutenção": "✏️ Gestão"}
        if user['admin']: opcoes["Admin"] = "⚙️ Admin"
        
        page_sel = st.radio("Menu", list(opcoes.values()), horizontal=True, label_visibility="collapsed")
        page = [k for k, v in opcoes.items() if v == page_sel][0]
    
    with c_logout:
        # Botão Sair Alinhado com o Menu
        st.markdown('<div class="btn-logout">', unsafe_allow_html=True)
        if st.button("Sair da Conta", key="btn_logout"):
             cookie_manager.delete("gupy_user_token")
             st.session_state["usuario_logado"] = None
             st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("---") # Separador sutil

    # Renderização das Páginas
    if page == "Biblioteca": render_biblioteca(dados_totais, user)
    elif page == "Adicionar": render_adicionar(dados_totais, user)
    elif page == "Manutenção": render_manutencao(dados_totais, user)
    elif page == "Admin": render_admin(user, dados_totais)

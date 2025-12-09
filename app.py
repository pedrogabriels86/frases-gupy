import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime, timedelta
import io
import requests
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
    except:
        return "💙"
    return "💙"

FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"

favicon = carregar_favicon(FAVICON_URL)

st.set_page_config(page_title="Gupy Frases", page_icon=favicon, layout="wide")

# ==============================================================================
# 2. ESTILO CSS (CLEAN & MINIMALISTA)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .block-container { padding-top: 1.5rem !important; }
    header { visibility: hidden; }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        background-color: white;
    }
    
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    .stCodeBlock { margin-top: -10px; }
    
    .stRadio > div[role="radiogroup"] {
        background: white;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        display: flex;
        justify-content: center;
    }
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

def buscar_frases_otimizado(termo=None, empresa_filtro="Todas"):
    query = supabase.table("frases").select("*").order("id", desc=True)
    if termo:
        filtro_texto = f"conteudo.ilike.%{termo}%,empresa.ilike.%{termo}%,motivo.ilike.%{termo}%"
        query = query.or_(filtro_texto)
    if empresa_filtro != "Todas":
        query = query.eq("empresa", empresa_filtro)
    return query.limit(50).execute().data or []

@st.cache_data(ttl=300)
def listar_empresas_unicas():
    try:
        data = supabase.table("frases").select("empresa").execute().data
        empresas = sorted(list(set([d['empresa'] for d in data])))
        return ["Todas"] + empresas
    except: return ["Todas"]

def padronizar(texto):
    return str(texto).strip() if texto else ""

# ==============================================================================
# 4. COMPONENTES VISUAIS (WIDGETS REUTILIZÁVEIS)
# ==============================================================================

def card_frase(frase):
    with st.container(border=True):
        c_head1, c_head2 = st.columns([3, 1])
        with c_head1:
            st.markdown(f"**{frase['empresa']}**")
            st.caption(f"{frase['motivo']} • {frase['documento']}")
        with c_head2:
             st.markdown(f"<div style='text-align:right; font-size:0.8em; color:#888'>#{frase['id']}</div>", unsafe_allow_html=True)
        st.code(frase['conteudo'], language=None)
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; font-size:0.75rem; color:#666; margin-top:5px;'>
            <span>✍️ {frase.get('revisado_por', 'Sistema')}</span>
            <span>📅 {frase.get('data_revisao', '-')}</span>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# 5. TELAS DO SISTEMA
# ==============================================================================

def tela_biblioteca(user):
    st.markdown("### 📂 Biblioteca de Frases")
    with st.container():
        c1, c2 = st.columns([3, 1])
        termo = c1.text_input("🔍 Pesquisar", placeholder="Ex: Baixa qualificação, Gupy...", label_visibility="collapsed")
        lista_empresas = listar_empresas_unicas()
        empresa = c2.selectbox("Empresa", lista_empresas, label_visibility="collapsed")

    with st.spinner("Buscando..."):
        dados = buscar_frases_otimizado(termo if termo else None, empresa)

    st.caption(f"Mostrando {len(dados)} resultados mais recentes.")
    st.divider()

    if not dados:
        st.info("Nenhuma frase encontrada com esses filtros.")
        return

    col1, col2 = st.columns(2)
    for i, frase in enumerate(dados):
        with (col1 if i % 2 == 0 else col2):
            card_frase(frase)

def tela_adicionar(user):
    st.markdown("### ➕ Nova Frase")
    st.info("Preencha os dados abaixo para cadastrar um novo modelo de resposta.")
    with st.container(border=True):
        with st.form("form_add", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ne = c1.text_input("Empresa Solicitante", placeholder="Ex: Gupy Tech")
            nd = c2.text_input("Tipo de Documento", placeholder="Ex: Carta Recusa")
            nm = st.text_input("Motivo", placeholder="Ex: Baixa Qualificação Técnica")
            nc = st.text_area("Texto da Frase (Conteúdo)", height=150)
            submitted = st.form_submit_button("💾 Salvar Frase", type="primary", use_container_width=True)
            if submitted:
                if not ne or not nm or not nc:
                    st.warning("Preencha todos os campos.")
                else:
                    try:
                        supabase.table("frases").insert({
                            "empresa": padronizar(ne), 
                            "documento": padronizar(nd), 
                            "motivo": padronizar(nm), 
                            "conteudo": padronizar(nc), 
                            "revisado_por": user['username'], 
                            "data_revisao": datetime.now().strftime('%Y-%m-%d')
                        }).execute()
                        st.success("Frase salva com sucesso!")
                        time.sleep(1)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

def tela_gestao(user):
    st.markdown("### ✏️ Gestão Rápida")
    res = supabase.table("frases").select("id, empresa, motivo, conteudo").order("id", desc=True).limit(20).execute()
    items = res.data
    for item in items:
        with st.expander(f"#{item['id']} | {item['empresa']} - {item['motivo']}"):
            st.text_area("Conteúdo", item['conteudo'], disabled=True, height=100)
            if st.button(f"🗑️ Excluir #{item['id']}", key=f"del_{item['id']}"):
                supabase.table("frases").delete().eq("id", item['id']).execute()
                st.toast(f"Item {item['id']} excluído!")
                time.sleep(1)
                st.rerun()

def tela_admin(user):
    st.markdown("### ⚙️ Painel Administrativo")
    st.warning("⚠️ Área restrita a administradores.")
    
    with st.container(border=True):
        st.markdown("#### 👥 Utilizadores Cadastrados")
        try:
            # Busca usuarios (sem mostrar senhas por segurança visual)
            users_res = supabase.table("usuarios").select("id, username, admin").execute()
            users = users_res.data
            
            # Mostra uma tabela simples
            st.dataframe(users, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 🛡️ Logs do Sistema")
            st.caption("Aqui poderias implementar uma tabela de logs (quem apagou o quê).")
            
        except Exception as e:
            st.error(f"Erro ao carregar dados de admin: {e}")

# ==============================================================================
# 6. CONTROLE DE FLUXO
# ==============================================================================

if "usuario_logado" not in st.session_state: 
    st.session_state["usuario_logado"] = None

cookie_manager = stx.CookieManager(key="auth_sys")

if not st.session_state["usuario_logado"]:
    cookies = cookie_manager.get_all()
    token = cookies.get("gupy_token")
    if token:
        user_db = recuperar_usuario_cookie(token)
        if user_db: st.session_state["usuario_logado"] = user_db

if not st.session_state["usuario_logado"]:
    # TELA LOGIN
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
                    st.session_state["usuario_logado"] = user
                    cookie_manager.set("gupy_token", u, expires_at=datetime.now() + timedelta(days=7))
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
else:
    # APLICAÇÃO LOGADA
    user = st.session_state["usuario_logado"]
    
    c_logo, c_nav, c_user = st.columns([1, 4, 1], vertical_alignment="center")
    with c_logo:
        st.image(LOGO_URL, width=80)
    
    with c_nav:
        # LÓGICA DO MENU DINÂMICO AQUI
        opcoes = ["Biblioteca", "Adicionar", "Gestão"]
        
        # Verifica se é admin com segurança (.get evita erro se a coluna nao existir)
        if user.get('admin') == True:
            opcoes.append("Admin")
            
        selecao = st.radio("Navegação", opcoes, horizontal=True, label_visibility="collapsed")
    
    with c_user:
        if st.button("Sair", key="logout_btn"):
            cookie_manager.delete("gupy_token")
            st.session_state["usuario_logado"] = None
            st.rerun()

    st.divider()

    if selecao == "Biblioteca": tela_biblioteca(user)
    elif selecao == "Adicionar": tela_adicionar(user)
    elif selecao == "Gestão": tela_gestao(user)
    elif selecao == "Admin": tela_admin(user) # Chama a nova função

    st.markdown("<br><div style='text-align:center; color:#CCC; font-size:0.8rem'>Gupy Frases v2.1 • Admin Ativo</div>", unsafe_allow_html=True)

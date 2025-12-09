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
import hashlib

# ==============================================================================
# 1. CONFIGURAÇÕES E INICIALIZAÇÃO
# ==============================================================================
FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"

@st.cache_data
def carregar_favicon(url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except Exception:
        return "💙"
    return "💙"

favicon = carregar_favicon(FAVICON_URL)
st.set_page_config(page_title="Gupy Frases", page_icon=favicon, layout="wide")

# ==============================================================================
# 2. ESTILO CSS (CORREÇÃO AGRESSIVA PARA QUEBRA DE LINHA)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.5rem !important; }
    header { visibility: hidden; }
    
    /* Card Container */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        background-color: white;
        margin-bottom: 1rem;
    }
    
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    /* --- CORREÇÃO DEFINITIVA DE QUEBRA DE LINHA (WRAP TEXT) --- */
    
    /* 1. Garante que o bloco ocupe a largura mas não estoure */
    div[data-testid="stCodeBlock"] {
        width: 100% !important;
    }
    
    /* 2. Força a tag PRE (container) a quebrar linha e esconder scroll */
    div[data-testid="stCodeBlock"] pre {
        white-space: pre-wrap !important;   /* OBRIGA a quebrar a linha */
        word-wrap: break-word !important;   /* Quebra palavras longas se precisar */
        overflow-x: hidden !important;      /* Remove a barra de rolagem horizontal */
        max-height: none !important;        /* Permite crescer verticalmente */
    }
    
    /* 3. Força a tag CODE (texto interno) a herdar a quebra */
    div[data-testid="stCodeBlock"] code {
        white-space: pre-wrap !important;
        word-break: break-word !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 0.9rem !important;
    }
    /* ----------------------------------------------------------- */

    .danger-zone { border: 1px solid #ff4b4b; background-color: #fff5f5; padding: 20px; border-radius: 10px; color: #7f1d1d; }
    .filter-label { font-size: 0.85rem; font-weight: 600; color: #475569; margin-bottom: 5px; }
    .footer { text-align: center; color: #CCC; font-size: 0.8rem; margin-top: 50px; border-top: 1px solid #EEE; padding-top: 20px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. GERENCIAMENTO DE DADOS (SUPABASE & PANDAS)
# ==============================================================================
try:
    url_db = st.secrets["SUPABASE_URL"]
    key_db = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url_db, key_db)
except Exception as e:
    st.error(f"Erro crítico de configuração: {e}")
    st.stop()

# --- Funções Auxiliares ---
def padronizar(texto):
    return str(texto).strip() if texto else ""

def gerar_assinatura(e, m, c):
    return f"{padronizar(e).lower()}|{padronizar(m).lower()}|{padronizar(c).lower()}"

def converter_para_csv(dados):
    if not dados: return ""
    output = io.StringIO()
    if len(dados) > 0:
        writer = csv.DictWriter(output, fieldnames=dados[0].keys())
        writer.writeheader()
        writer.writerows(dados)
    return output.getvalue()

# --- Funções de Banco de Dados ---
def verificar_login(u, s):
    try:
        res = supabase.table("usuarios").select("*").eq("username", u).execute()
        if res.data:
            user = res.data[0]
            if user['senha'] == s: 
                return user
        return None
    except Exception: return None

def recuperar_usuario_cookie(username):
    try:
        res = supabase.table("usuarios").select("*").eq("username", username).execute()
        return res.data[0] if res.data else None
    except Exception: return None

def registrar_log(usuario, acao, detalhe):
    try:
        supabase.table("logs").insert({
            "usuario": usuario, "acao": acao, "detalhe": detalhe, 
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
    except Exception: pass

# --- Funções de Busca Inteligente ---

@st.cache_data(ttl=300)
def obter_dataframe_filtros():
    """Baixa metadados leves para alimentar os filtros dinâmicos na memória."""
    try:
        res = supabase.table("frases").select("id, empresa, documento, motivo, conteudo").execute()
        df = pd.DataFrame(res.data)
        return df
    except Exception:
        return pd.DataFrame()

def buscar_frases_final(termo=None, empresa_filtro="Todas", doc_filtro="Todos"):
    """Busca pesada final no banco de dados para exibição."""
    query = supabase.table("frases").select("*").order("id", desc=True)
    
    if termo:
        filtro = f"conteudo.ilike.%{termo}%,empresa.ilike.%{termo}%,motivo.ilike.%{termo}%"
        query = query.or_(filtro)
    
    if empresa_filtro != "Todas": query = query.eq("empresa", empresa_filtro)
    if doc_filtro != "Todos": query = query.eq("documento", doc_filtro)
        
    return query.limit(50 if termo else 8).execute().data or []

# ==============================================================================
# 4. COMPONENTES VISUAIS (CORREÇÃO DO ST.CODE)
# ==============================================================================

def card_frase(frase):
    with st.container(border=True):
        c_head1, c_head2 = st.columns([4, 1])
        with c_head1:
            st.markdown(f"🏢 **{frase['empresa']}**")
            st.caption(f"📄 {frase['documento']} • {frase['motivo']}")
        with c_head2:
             st.markdown(f"<div style='text-align:right; font-size:0.8em; color:#CCC'>#{frase['id']}</div>", unsafe_allow_html=True)
        
        # IMPORTANTE: language=None desativa a formatação de código e permite que o CSS funcione
        st.code(frase['conteudo'], language=None)
        
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; font-size:0.75rem; color:#888; margin-top:5px; border-top:1px dashed #eee; padding-top:5px;'>
            <span>✍️ Rev: {frase.get('revisado_por', 'Sistema')}</span>
            <span>📅 {frase.get('data_revisao', '-')}</span>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# 5. TELAS DO SISTEMA
# ==============================================================================

def tela_biblioteca(user):
    st.markdown("### 📂 Biblioteca de Modelos")
    
    # 1. Carrega dados leves para os filtros (Cacheado)
    df_filtros = obter_dataframe_filtros()
    
    # --- FILTROS LINKADOS (CASCATA) ---
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        
        with c1:
            st.markdown('<div class="filter-label">🔎 Busca Rápida</div>', unsafe_allow_html=True)
            termo = st.text_input("Busca", placeholder="Palavra-chave...", label_visibility="collapsed")

        df_temp = df_filtros.copy()
        
        # Passo 1: Filtrar DF pelo termo digitado
        if termo and not df_temp.empty:
            termo_lower = termo.lower()
            mask = (
                df_temp['conteudo'].str.contains(termo_lower, case=False, na=False) |
                df_temp['empresa'].str.contains(termo_lower, case=False, na=False) |
                df_temp['motivo'].str.contains(termo_lower, case=False, na=False)
            )
            df_temp = df_temp[mask]

        # Passo 2: Popula lista de empresas baseada no filtro anterior
        if not df_temp.empty:
            lista_empresas = sorted(df_temp['empresa'].dropna().unique().tolist())
        else: lista_empresas = []
        opcoes_empresas = ["Todas"] + lista_empresas

        with c2:
            st.markdown('<div class="filter-label">🏢 Empresa</div>', unsafe_allow_html=True)
            empresa = st.selectbox("Empresa", options=opcoes_empresas, label_visibility="collapsed")

        # Passo 3: Filtra DF pela empresa selecionada
        if empresa != "Todas" and not df_temp.empty:
            df_temp = df_temp[df_temp['empresa'] == empresa]
        
        # Passo 4: Popula lista de docs baseada nos filtros anteriores
        if not df_temp.empty:
            lista_docs = sorted(df_temp['documento'].dropna().unique().tolist())
        else: lista_docs = []
        opcoes_docs = ["Todos"] + lista_docs

        with c3:
            st.markdown('<div class="filter-label">📄 Documento</div>', unsafe_allow_html=True)
            doc_tipo = st.selectbox("Doc", options=opcoes_docs, label_visibility="collapsed")

    # --- BUSCA REAL NO BANCO ---
    with st.spinner("Carregando frases..."):
        dados = buscar_frases_final(termo if termo else None, empresa, doc_tipo)

    # Feedback
    if not dados:
        st.warning("📭 Nenhuma frase encontrada.")
        return

    st.markdown(f"<small style='color:#666'>Encontrados: {len(dados)} modelos</small>", unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns(2)
    for i, frase in enumerate(dados):
        with (col1 if i % 2 == 0 else col2):
            card_frase(frase)

def tela_adicionar(user):
    st.markdown("### ➕ Adicionar Novo Modelo")
    tab_manual, tab_import = st.tabs(["📝 Manual", "📗 Importar Excel"])
    
    with tab_manual:
        with st.form("form_add", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ne = c1.text_input("Empresa", placeholder="Ex: Gupy Tech")
            nd = c2.text_input("Tipo de Documento", placeholder="Ex: Carta Recusa")
            nm = st.text_input("Motivo", placeholder="Ex: Baixa Qualificação")
            nc = st.text_area("Texto do Modelo", height=150)
            
            if st.form_submit_button("💾 Salvar Frase", type="primary", use_container_width=True):
                if not (ne and nm and nc): st.error("Preencha campos obrigatórios.")
                else:
                    try:
                        check = supabase.table("frases").select("id").eq("conteudo", padronizar(nc)).execute()
                        if check.data: st.warning("Frase duplicada.")
                        else:
                            supabase.table("frases").insert({
                                "empresa": padronizar(ne), "documento": padronizar(nd), "motivo": padronizar(nm), 
                                "conteudo": padronizar(nc), "revisado_por": user['username'], 
                                "data_revisao": datetime.now().strftime('%Y-%m-%d')
                            }).execute()
                            registrar_log(user['username'], "Adicionar Frase", f"Empresa: {ne}")
                            st.toast("✅ Salvo com sucesso!"); time.sleep(1); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

    with tab_import:
        st.info("Colunas Excel: `empresa`, `motivo`, `conteudo`, `documento` (opc).")
        arquivo = st.file_uploader("Arquivo .xlsx", type=["xlsx"])
        if arquivo and st.button("🚀 Processar", type="primary"):
            try:
                df = pd.read_excel(arquivo); df.columns = [c.lower().strip() for c in df.columns]
                if not {'empresa', 'motivo', 'conteudo'}.issubset(df.columns): st.error("Colunas incorretas.")
                else:
                    with st.status("Importando...", expanded=True):
                        res = supabase.table("frases").select("empresa, motivo, conteudo").execute()
                        existentes = set([gerar_assinatura(i['empresa'], i['motivo'], i['conteudo']) for i in res.data])
                        sucesso, dupl, erros = 0, 0, 0
                        prog = st.progress(0)
                        for i, row in df.iterrows():
                            try:
                                el, ml, cl = padronizar(row['empresa']), padronizar(row['motivo']), padronizar(row['conteudo'])
                                if gerar_assinatura(el, ml, cl) in existentes: dupl += 1
                                else:
                                    supabase.table("frases").insert({
                                        "empresa": el, "documento": padronizar(row.get('documento', 'Geral')),
                                        "motivo": ml, "conteudo": cl, "revisado_por": user['username'],
                                        "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                    }).execute()
                                    existentes.add(gerar_assinatura(el, ml, cl)); sucesso += 1
                            except: erros += 1
                            prog.progress((i+1)/len(df))
                    st.success(f"Sucesso: {sucesso} | Duplicados: {dupl}"); time.sleep(2); st.cache_data.clear(); st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

def tela_manutencao(user):
    st.markdown("### 🛠️ Editar ou Excluir")
    q = st.text_input("Buscar ID ou Termo", placeholder="ID ou texto...")
    query = supabase.table("frases").select("*").order("id", desc=True)
    
    if q:
        if q.isdigit(): query = query.eq("id", q)
        else: query = query.or_(f"empresa.ilike.%{q}%,motivo.ilike.%{q}%")
    else: query = query.limit(5)
        
    items = query.execute().data
    if not items and q: st.info("Nada encontrado.")
    
    for item in items:
        with st.expander(f"#{item['id']} | {item['empresa']} - {item['motivo']}"):
            with st.form(key=f"fe_{item['id']}"):
                c1, c2, c3 = st.columns([1.5, 1.5, 1])
                ne = c1.text_input("Empresa", value=item['empresa'])
                nm = c2.text_input("Motivo", value=item['motivo'])
                nd = c3.text_input("Doc", value=item['documento'])
                nc = st.text_area("Conteúdo", value=item['conteudo'], height=150)
                c_sv, c_del = st.columns([1, 4])
                
                if c_sv.form_submit_button("💾 Salvar"):
                    supabase.table("frases").update({
                        "empresa": ne, "motivo": nm, "documento": nd, "conteudo": nc, "revisado_por": user['username']
                    }).eq("id", item['id']).execute()
                    registrar_log(user['username'], "Editar", f"ID: {item['id']}"); st.toast("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
                
                if c_del.form_submit_button("🗑️ Excluir"):
                    supabase.table("frases").delete().eq("id", item['id']).execute()
                    registrar_log(user['username'], "Excluir", f"ID: {item['id']}"); st.toast("Excluído!"); time.sleep(1); st.cache_data.clear(); st.rerun()

def tela_admin(user_logado):
    st.markdown("### ⚙️ Administração")
    tab_users, tab_logs, tab_bkp, tab_danger = st.tabs(["👥 Usuários", "📜 Logs", "💾 Backup", "🚨 Danger"])
    
    with tab_users:
        users = supabase.table("usuarios").select("*").order("id").execute().data
        for u in users:
            with st.expander(f"👤 {u['username']}"):
                with st.form(f"eu_{u['id']}"):
                    np = st.text_input("Nova Senha", value=u['senha'], type="password")
                    ia = st.checkbox("Admin", value=u.get('admin', False))
                    if st.form_submit_button("Atualizar"):
                        supabase.table("usuarios").update({"senha": np, "admin": ia}).eq("id", u['id']).execute()
                        st.success("Atualizado!"); time.sleep(1); st.rerun()
                    if st.form_submit_button("Excluir"):
                         if u['username'] != user_logado['username']:
                             supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()
        
        with st.container(border=True):
            st.markdown("New User"); nu = st.text_input("User"); ns = st.text_input("Pass", type="password"); na = st.checkbox("Admin")
            if st.button("Criar") and nu and ns:
                supabase.table("usuarios").insert({"username": nu, "senha": ns, "admin": na}).execute(); st.rerun()

    with tab_logs:
        if st.button("Atualizar"): st.rerun()
        try: st.dataframe(supabase.table("logs").select("*").order("id", desc=True).limit(50).execute().data, hide_index=True)
        except: st.write("Sem logs.")

    with tab_bkp:
        df = supabase.table("frases").select("*").execute().data
        st.download_button("⬇️ Backup CSV", data=converter_para_csv(df), file_name="backup.csv", mime="text/csv")

    with tab_danger:
        st.markdown('<div class="danger-zone"><h4>Zona de Perigo</h4></div>', unsafe_allow_html=True)
        if st.button("💥 APAGAR TUDO", type="primary") and st.text_input("Digite CONFIRMAR") == "CONFIRMAR":
            supabase.table("frases").delete().neq("id", 0).execute()
            registrar_log(user_logado['username'], "RESET", "Apagou tudo"); st.success("Feito."); time.sleep(2); st.rerun()

# ==============================================================================
# 6. CONTROLE DE SESSÃO E LOGIN
# ==============================================================================
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None
cookie_manager = stx.CookieManager(key="auth_sys")

if not st.session_state["usuario_logado"]:
    try:
        token = cookie_manager.get_all().get("gupy_token")
        if token:
            user_db = recuperar_usuario_cookie(token)
            if user_db: st.session_state["usuario_logado"] = user_db
    except: pass

if not st.session_state["usuario_logado"]:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.write(""); st.image(LOGO_URL, width=180)
        with st.container(border=True):
            st.markdown("<h3 style='text-align:center'>Login</h3>", unsafe_allow_html=True)
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.button("Entrar", type="primary", use_container_width=True):
                user = verificar_login(u, s)
                if user:
                    st.session_state["usuario_logado"] = user
                    cookie_manager.set("gupy_token", u, expires_at=datetime.now() + timedelta(days=7))
                    st.toast(f"Olá, {user['username']}!"); time.sleep(1); st.rerun()
                else: st.error("Erro no login.")
else:
    user = st.session_state["usuario_logado"]
    c_logo, c_nav, c_user = st.columns([1, 5, 1], vertical_alignment="center")
    with c_logo: st.image(LOGO_URL, width=100)
    with c_nav:
        opcoes = ["Biblioteca", "Adicionar", "Manutenção"]
        if user.get('admin'): opcoes.append("Admin")
        selecao = st.radio("M", opcoes, horizontal=True, label_visibility="collapsed")
    with c_user:
        if st.button("Sair", use_container_width=True):
            cookie_manager.delete("gupy_token"); st.session_state["usuario_logado"] = None; st.rerun()
    st.divider()

    if selecao == "Biblioteca": tela_biblioteca(user)
    elif selecao == "Adicionar": tela_adicionar(user)
    elif selecao == "Manutenção": tela_manutencao(user)
    elif selecao == "Admin": tela_admin(user)
    
    st.markdown('<div class="footer">Desenvolvido com Streamlit • Gupy Frases v2.3</div>', unsafe_allow_html=True)

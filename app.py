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
# 2. ESTILO CSS OTIMIZADO
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
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        background-color: white;
        transition: transform 0.2s;
    }
    
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    /* CSS Mágico para st.code (Mantido mas ajustado) */
    div[data-testid="stCodeBlock"] pre {
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }
    div[data-testid="stCodeBlock"] code {
        white-space: pre-wrap !important;
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* Área de Perigo */
    .danger-zone {
        border: 1px solid #ff4b4b;
        background-color: #fff5f5;
        padding: 20px;
        border-radius: 10px;
        color: #7f1d1d;
    }
    
    /* Labels Personalizados */
    .filter-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #475569;
        margin-bottom: 5px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #CCC;
        font-size: 0.8rem;
        margin-top: 50px;
        border-top: 1px solid #EEE;
        padding-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. GERENCIAMENTO DE DADOS (SUPABASE)
# ==============================================================================
try:
    url_db = st.secrets["SUPABASE_URL"]
    key_db = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url_db, key_db)
except Exception as e:
    st.error(f"Erro crítico de configuração: {e}")
    st.stop()

# --- Funções Auxiliares ---
def hash_senha(senha):
    """Cria um hash SHA256 simples da senha."""
    return hashlib.sha256(senha.encode()).hexdigest()

def padronizar(texto):
    return str(texto).strip() if texto else ""

def gerar_assinatura(e, m, c):
    return f"{padronizar(e).lower()}|{padronizar(m).lower()}|{padronizar(c).lower()}"

# --- Funções de Banco de Dados ---
def verificar_login(u, s):
    try:
        # Tenta buscar usuário
        res = supabase.table("usuarios").select("*").eq("username", u).execute()
        if res.data:
            user = res.data[0]
            # Verifica se a senha bate (suporta texto simples ou hash futuro)
            if user['senha'] == s:
                return user
        return None
    except Exception:
        return None

def recuperar_usuario_cookie(username):
    try:
        res = supabase.table("usuarios").select("*").eq("username", username).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def registrar_log(usuario, acao, detalhe):
    try:
        supabase.table("logs").insert({
            "usuario": usuario, 
            "acao": acao, 
            "detalhe": detalhe, 
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
    except Exception:
        pass

def buscar_frases_final(termo=None, empresa_filtro="Todas", doc_filtro="Todos"):
    query = supabase.table("frases").select("*").order("id", desc=True)
    
    if termo:
        # Busca otimizada
        filtro = f"conteudo.ilike.%{termo}%,empresa.ilike.%{termo}%,motivo.ilike.%{termo}%"
        query = query.or_(filtro)
    
    if empresa_filtro != "Todas":
        query = query.eq("empresa", empresa_filtro)
    if doc_filtro != "Todos":
        query = query.eq("documento", doc_filtro)
        
    # Limite aumentado levemente, mas seguro
    return query.limit(60 if termo else 8).execute().data or []

@st.cache_data(ttl=300) # Cache de 5 minutos para filtros
def obter_filtros_inteligentes():
    try:
        # Busca apenas as colunas necessárias para montar o filtro
        data = supabase.table("frases").select("empresa, documento").execute().data or []
        empresas = sorted(list(set([d['empresa'] for d in data if d['empresa']])))
        docs = sorted(list(set([d['documento'] for d in data if d['documento']])))
        return ["Todas"] + empresas, ["Todos"] + docs
    except:
        return ["Todas"], ["Todos"]

# ==============================================================================
# 4. COMPONENTES VISUAIS
# ==============================================================================

def card_frase(frase):
    with st.container(border=True):
        c_head1, c_head2 = st.columns([4, 1])
        with c_head1:
            st.markdown(f"🏢 **{frase['empresa']}**")
            st.caption(f"📄 {frase['documento']} • {frase['motivo']}")
        with c_head2:
             st.markdown(f"<div style='text-align:right; font-size:0.8em; color:#CCC'>#{frase['id']}</div>", unsafe_allow_html=True)
        
        # O st.code nativo já possui botão de copiar. O CSS ajusta a quebra de linha.
        st.code(frase['conteudo'], language="markdown")
        
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
    
    # Área de Filtros
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        
        # Carrega filtros (cacheado)
        opcoes_empresas, opcoes_docs = obter_filtros_inteligentes()

        with c1:
            st.markdown('<div class="filter-label">🔎 Busca Rápida</div>', unsafe_allow_html=True)
            termo = st.text_input("Busca", placeholder="Palavra-chave...", label_visibility="collapsed")
        with c2:
            st.markdown('<div class="filter-label">🏢 Empresa</div>', unsafe_allow_html=True)
            empresa = st.selectbox("Empresa", options=opcoes_empresas, label_visibility="collapsed")
        with c3:
            st.markdown('<div class="filter-label">📄 Documento</div>', unsafe_allow_html=True)
            doc_tipo = st.selectbox("Doc", options=opcoes_docs, label_visibility="collapsed")

    # Lógica de Busca
    with st.spinner("Carregando frases..."):
        dados = buscar_frases_final(termo if termo else None, empresa, doc_tipo)

    # Feedback de Resultados
    filtros_ativos = (termo or empresa != "Todas" or doc_tipo != "Todos")
    
    if not dados:
        st.warning("📭 Nenhuma frase encontrada. Tente outros filtros.")
        return

    st.markdown(f"**Resultados:** {len(dados)} frases encontradas.")
    st.divider()

    # Grid de Exibição
    col1, col2 = st.columns(2)
    for i, frase in enumerate(dados):
        with (col1 if i % 2 == 0 else col2):
            card_frase(frase)

def tela_adicionar(user):
    st.markdown("### ➕ Adicionar Novo Modelo")
    
    tab_manual, tab_import = st.tabs(["📝 Manual", "📗 Importar Excel"])
    
    # --- ABA MANUAL ---
    with tab_manual:
        with st.form("form_add", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ne = c1.text_input("Empresa Solicitante", placeholder="Ex: Gupy Tech")
            nd = c2.text_input("Tipo de Documento", placeholder="Ex: Carta Recusa")
            nm = st.text_input("Motivo", placeholder="Ex: Baixa Qualificação Técnica")
            nc = st.text_area("Texto do Modelo", height=150, help="Cole aqui o texto que será copiado.")
            
            if st.form_submit_button("💾 Salvar Frase", type="primary", use_container_width=True):
                if not (ne and nm and nc):
                    st.error("Preencha todos os campos obrigatórios.")
                else:
                    try:
                        # Verifica duplicidade exata
                        check = supabase.table("frases").select("id").eq("conteudo", padronizar(nc)).execute()
                        if check.data:
                            st.warning("Já existe uma frase com este conteúdo exato.")
                        else:
                            supabase.table("frases").insert({
                                "empresa": padronizar(ne), 
                                "documento": padronizar(nd), 
                                "motivo": padronizar(nm), 
                                "conteudo": padronizar(nc), 
                                "revisado_por": user['username'], 
                                "data_revisao": datetime.now().strftime('%Y-%m-%d')
                            }).execute()
                            
                            registrar_log(user['username'], "Adicionar Frase", f"Empresa: {ne}")
                            st.toast("✅ Frase salva com sucesso!")
                            time.sleep(1)
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # --- ABA EXCEL ---
    with tab_import:
        st.info("Importe uma planilha (.xlsx) com as colunas: `empresa`, `motivo`, `conteudo`.")
        arquivo = st.file_uploader("Selecione o arquivo", type=["xlsx"])
        
        if arquivo:
            if st.button("🚀 Processar Arquivo", type="primary"):
                try:
                    df = pd.read_excel(arquivo)
                    # Normaliza nomes das colunas
                    df.columns = [c.lower().strip() for c in df.columns]
                    
                    required = {'empresa', 'motivo', 'conteudo'}
                    if not required.issubset(df.columns):
                        st.error(f"Colunas obrigatórias faltando. Encontradas: {list(df.columns)}")
                    else:
                        with st.status("Processando dados...", expanded=True) as status:
                            # Carrega assinaturas existentes para evitar duplicatas em massa
                            st.write("Verificando duplicatas...")
                            res_existentes = supabase.table("frases").select("empresa, motivo, conteudo").execute()
                            assinaturas_existentes = set([gerar_assinatura(i['empresa'], i['motivo'], i['conteudo']) for i in res_existentes.data])
                            
                            sucesso, duplicados, erros = 0, 0, 0
                            novos_dados = []
                            
                            # Prepara dados (Batch insert seria melhor, mas insert um a um é mais seguro para erros individuais)
                            progress_bar = st.progress(0)
                            total_rows = len(df)
                            
                            for i, row in df.iterrows():
                                try:
                                    el, ml, cl = padronizar(row['empresa']), padronizar(row['motivo']), padronizar(row['conteudo'])
                                    ass_atual = gerar_assinatura(el, ml, cl)
                                    
                                    if ass_atual in assinaturas_existentes:
                                        duplicados += 1
                                    else:
                                        supabase.table("frases").insert({
                                            "empresa": el, 
                                            "documento": padronizar(row.get('documento', 'Geral')), 
                                            "motivo": ml, 
                                            "conteudo": cl, 
                                            "revisado_por": user['username'], 
                                            "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                        }).execute()
                                        assinaturas_existentes.add(ass_atual)
                                        sucesso += 1
                                except:
                                    erros += 1
                                progress_bar.progress((i + 1) / total_rows)
                            
                            status.update(label="Processamento concluído!", state="complete", expanded=False)
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Sucesso", sucesso)
                        c2.metric("Duplicados (Ignorados)", duplicados)
                        c3.metric("Erros", erros)
                        
                        if sucesso > 0:
                            registrar_log(user['username'], "Importação Excel", f"{sucesso} itens")
                            time.sleep(2)
                            st.cache_data.clear()
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"Erro ao ler arquivo: {e}")

def tela_manutencao(user):
    st.markdown("### 🛠️ Editar ou Excluir")
    
    q = st.text_input("Buscar ID ou Termo", placeholder="Digite ID (número) ou texto...", key="search_manut")
    
    query = supabase.table("frases").select("*").order("id", desc=True)
    if q:
        if q.isdigit():
            query = query.eq("id", q)
        else:
            query = query.or_(f"empresa.ilike.%{q}%,motivo.ilike.%{q}%")
    else:
        query = query.limit(5)
        st.caption("Mostrando as 5 últimas modificações.")
        
    items = query.execute().data
    
    if not items and q:
        st.info("Nada encontrado.")
        return

    for item in items:
        with st.expander(f"#{item['id']} | {item['empresa']} - {item['motivo']}"):
            with st.form(key=f"form_edit_{item['id']}"):
                c1, c2, c3 = st.columns([1.5, 1.5, 1])
                ne = c1.text_input("Empresa", value=item['empresa'])
                nm = c2.text_input("Motivo", value=item['motivo'])
                nd = c3.text_input("Doc", value=item['documento'])
                nc = st.text_area("Conteúdo", value=item['conteudo'], height=150)
                
                c_btn1, c_btn2 = st.columns([1, 4])
                if c_btn1.form_submit_button("💾 Salvar"):
                    supabase.table("frases").update({
                        "empresa": ne, "motivo": nm, "documento": nd, 
                        "conteudo": nc, "revisado_por": user['username']
                    }).eq("id", item['id']).execute()
                    
                    registrar_log(user['username'], "Editar Frase", f"ID: {item['id']}")
                    st.toast("Atualizado!")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()
                    
                if c_btn2.form_submit_button("🗑️ Excluir Definitivamente", type="secondary"):
                    supabase.table("frases").delete().eq("id", item['id']).execute()
                    registrar_log(user['username'], "Excluir Frase", f"ID: {item['id']}")
                    st.toast("Excluído!")
                    time.sleep(1)
                    st.cache_data.clear()
                    st.rerun()

def tela_admin(user_logado):
    st.markdown("### ⚙️ Administração")
    
    tab_users, tab_logs, tab_danger = st.tabs(["👥 Usuários", "📜 Logs do Sistema", "🚨 Zona de Perigo"])
    
    with tab_users:
        users = supabase.table("usuarios").select("*").order("id").execute().data
        for u in users:
            with st.expander(f"👤 {u['username']} {'(Admin)' if u.get('admin') else ''}"):
                with st.form(key=f"eu_{u['id']}"):
                    np = st.text_input("Nova Senha", value=u['senha'], type="password", help="Cuidado ao alterar.")
                    ia = st.checkbox("É Administrador?", value=u.get('admin', False))
                    
                    if st.form_submit_button("Atualizar Usuário"):
                        supabase.table("usuarios").update({"senha": np, "admin": ia}).eq("id", u['id']).execute()
                        registrar_log(user_logado['username'], "Editar Usuário", u['username'])
                        st.success("Usuário atualizado.")
                        time.sleep(1)
                        st.rerun()
                        
                    if st.form_submit_button("❌ Remover Usuário"):
                        if u['username'] == user_logado['username']:
                            st.error("Você não pode se excluir.")
                        else:
                            supabase.table("usuarios").delete().eq("id", u['id']).execute()
                            st.rerun()
                            
        with st.container(border=True):
            st.markdown("**Criar Novo Usuário**")
            nu = st.text_input("Novo User", key="new_u")
            ns = st.text_input("Nova Senha", type="password", key="new_p")
            na = st.checkbox("Admin?", key="new_a")
            if st.button("Criar Usuário"):
                if nu and ns:
                    supabase.table("usuarios").insert({"username": nu, "senha": ns, "admin": na}).execute()
                    st.success("Criado!")
                    time.sleep(1)
                    st.rerun()
    
    with tab_logs:
        if st.button("🔄 Atualizar Logs"): st.rerun()
        try:
            logs = supabase.table("logs").select("*").order("id", desc=True).limit(50).execute().data
            st.dataframe(logs, use_container_width=True, hide_index=True)
        except:
            st.info("Sem logs registrados.")

    with tab_danger:
        st.markdown('<div class="danger-zone"><h4>Zona de Perigo</h4><p>Cuidado: Ações aqui não podem ser desfeitas.</p></div>', unsafe_allow_html=True)
        st.write("")
        if st.button("💥 APAGAR TODAS AS FRASES DO BANCO", type="primary", use_container_width=True):
            # Implementei um check duplo por segurança
            if st.text_input("Digite 'CONFIRMAR' para apagar tudo") == "CONFIRMAR":
                supabase.table("frases").delete().neq("id", 0).execute()
                registrar_log(user_logado['username'], "RESET TOTAL", "Apagou todas as frases")
                st.success("Banco limpo.")
                time.sleep(2)
                st.rerun()

# ==============================================================================
# 6. CONTROLE DE SESSÃO E LOGIN
# ==============================================================================
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# Gerenciador de Cookies para persistência (Login dura 7 dias)
cookie_manager = stx.CookieManager(key="auth_sys")

# Tenta login automático via cookie
if not st.session_state["usuario_logado"]:
    try:
        cookies = cookie_manager.get_all()
        token = cookies.get("gupy_token")
        if token:
            user_db = recuperar_usuario_cookie(token)
            if user_db:
                st.session_state["usuario_logado"] = user_db
    except:
        pass # Falha silenciosa no cookie

# TELA DE LOGIN
if not st.session_state["usuario_logado"]:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.write(""); st.write("")
        st.image(LOGO_URL, width=180)
        with st.container(border=True):
            st.markdown("<h3 style='text-align:center'>Login</h3>", unsafe_allow_html=True)
            u_input = st.text_input("Usuário")
            s_input = st.text_input("Senha", type="password")
            
            if st.button("Entrar", type="primary", use_container_width=True):
                user = verificar_login(u_input, s_input)
                if user:
                    st.session_state["usuario_logado"] = user
                    # Salva cookie
                    cookie_manager.set("gupy_token", u_input, expires_at=datetime.now() + timedelta(days=7))
                    st.toast(f"Bem-vindo, {user['username']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

# APLICAÇÃO PRINCIPAL
else:
    user = st.session_state["usuario_logado"]
    
    # Barra de Navegação Superior
    c_logo, c_nav, c_user = st.columns([1, 5, 1], vertical_alignment="center")
    
    with c_logo:
        st.image(LOGO_URL, width=100)
    
    with c_nav:
        # Menu responsivo
        opcoes = ["Biblioteca", "Adicionar", "Manutenção"]
        if user.get('admin') == True:
            opcoes.append("Admin")
        
        # Uso de icons no radio button para ficar mais visual
        selecao = st.radio("Menu", opcoes, horizontal=True, label_visibility="collapsed")
    
    with c_user:
        if st.button("Sair", use_container_width=True):
            try:
                cookie_manager.delete("gupy_token")
            except: pass
            st.session_state["usuario_logado"] = None
            st.rerun()
            
    st.divider()

    # Roteamento de Telas
    if selecao == "Biblioteca":
        tela_biblioteca(user)
    elif selecao == "Adicionar":
        tela_adicionar(user)
    elif selecao == "Manutenção":
        tela_manutencao(user)
    elif selecao == "Admin":
        tela_admin(user)

    st.markdown('<div class="footer">Desenvolvido com Streamlit • Gupy Frases v2.0</div>', unsafe_allow_html=True)

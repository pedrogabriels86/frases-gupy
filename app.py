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
    except:
        return "💙"
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
    
    .danger-zone {
        border: 1px solid #ff4b4b;
        background-color: #fff5f5;
        padding: 20px;
        border-radius: 10px;
    }
    
    .filter-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #475569;
        margin-bottom: 5px;
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

def registrar_log(usuario, acao, detalhe):
    try:
        supabase.table("logs").insert({
            "usuario": usuario, 
            "acao": acao, 
            "detalhe": detalhe, 
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

# FUNÇÃO 1: BUSCA PRINCIPAL (RESULTADOS)
def buscar_frases_final(termo=None, empresa_filtro="Todas", doc_filtro="Todos"):
    query = supabase.table("frases").select("*").order("id", desc=True)
    
    # Filtro de Texto
    if termo:
        filtro = f"conteudo.ilike.%{termo}%,empresa.ilike.%{termo}%,motivo.ilike.%{termo}%,revisado_por.ilike.%{termo}%,documento.ilike.%{termo}%"
        query = query.or_(filtro)
    
    # Filtros de Seleção
    if empresa_filtro != "Todas": query = query.eq("empresa", empresa_filtro)
    if doc_filtro != "Todos": query = query.eq("documento", doc_filtro)
    
    return query.limit(50 if termo else 4).execute().data or []

# FUNÇÃO 2: BUSCA AUXILIAR (PARA POPULAR OS FILTROS)
# Esta função olha para o termo digitado e devolve apenas as empresas/docs que existem nesse resultado
@st.cache_data(ttl=60) # Cache curto para ser rápido
def obter_filtros_inteligentes(termo=None):
    query = supabase.table("frases").select("empresa, documento")
    
    if termo:
        filtro = f"conteudo.ilike.%{termo}%,empresa.ilike.%{termo}%,motivo.ilike.%{termo}%,revisado_por.ilike.%{termo}%,documento.ilike.%{termo}%"
        query = query.or_(filtro)
    
    # Busca dados leves (só 2 colunas)
    data = query.execute().data or []
    
    # Processa listas únicas
    empresas = sorted(list(set([d['empresa'] for d in data if d['empresa']])))
    docs = sorted(list(set([d['documento'] for d in data if d['documento']])))
    
    return ["Todas"] + empresas, ["Todos"] + docs

def padronizar(texto):
    return str(texto).strip() if texto else ""

def gerar_assinatura(empresa, motivo, conteudo):
    t1 = padronizar(empresa).lower()
    t2 = padronizar(motivo).lower()
    t3 = padronizar(conteudo).lower()
    return f"{t1}|{t2}|{t3}"

# ==============================================================================
# 4. COMPONENTES VISUAIS
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
        c1, c2, c3 = st.columns([2, 1, 1])
        
        with c1:
            st.markdown('<div class="filter-label">🔎 O que procura?</div>', unsafe_allow_html=True)
            # A busca é o gatilho principal
            termo = st.text_input("Busca", placeholder="Digite algo para filtrar...", label_visibility="collapsed")
        
        # LÓGICA INTELIGENTE:
        # As opções dos filtros abaixo dependem do que foi digitado acima
        opcoes_empresas, opcoes_docs = obter_filtros_inteligentes(termo)
        
        with c2:
            st.markdown('<div class="filter-label">🏢 Empresa</div>', unsafe_allow_html=True)
            empresa = st.selectbox("Empresa", options=opcoes_empresas, label_visibility="collapsed")

        with c3:
            st.markdown('<div class="filter-label">📄 Tipo de Documento</div>', unsafe_allow_html=True)
            doc_tipo = st.selectbox("Doc", options=opcoes_docs, label_visibility="collapsed")

    # Busca final para o grid
    with st.spinner("Atualizando resultados..."):
        dados = buscar_frases_final(termo if termo else None, empresa, doc_tipo)

    # Feedback Visual
    filtros_ativos = (termo or empresa != "Todas" or doc_tipo != "Todos")
    
    if not filtros_ativos:
        st.caption("🔥 Destaques: Mostrando as 4 frases mais recentes.")
    else:
        st.caption(f"🔎 Resultados encontrados: {len(dados)}")
    
    st.divider()

    if not dados:
        st.info("Nenhuma frase encontrada com essa combinação.")
        return

    col1, col2 = st.columns(2)
    for i, frase in enumerate(dados):
        with (col1 if i % 2 == 0 else col2):
            card_frase(frase)

def tela_adicionar(user):
    st.markdown("### ➕ Nova Frase")
    tab_manual, tab_import = st.tabs(["📝 Cadastro Manual", "📗 Importar Excel"])
    
    with tab_manual:
        st.info("Preencha os dados abaixo para cadastrar um novo modelo.")
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
                        st.warning("Preencha todos os campos obrigatórios.")
                    else:
                        try:
                            check = supabase.table("frases").select("id").eq("conteudo", padronizar(nc)).execute()
                            if check.data:
                                st.warning("Atenção: Já existe uma frase com este conteúdo exato.")
                            else:
                                supabase.table("frases").insert({
                                    "empresa": padronizar(ne), "documento": padronizar(nd), "motivo": padronizar(nm), "conteudo": padronizar(nc), 
                                    "revisado_por": user['username'], "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                }).execute()
                                registrar_log(user['username'], "Adicionar Frase", f"Empresa: {ne} - Motivo: {nm}")
                                st.success("Frase salva com sucesso!"); time.sleep(1); st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error(f"Erro ao salvar: {e}")

    with tab_import:
        st.info("Carregue uma planilha Excel (.xlsx).")
        with st.expander("📌 Ver colunas da planilha"):
            st.markdown("**Colunas:** `empresa`, `motivo`, `conteudo`, `documento` (opc), `usuario` (opc), `data` (opc).")
        
        arquivo = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])
        if arquivo:
            if st.button("🚀 Processar e Importar", type="primary"):
                try:
                    df = pd.read_excel(arquivo)
                    df.columns = [c.lower().strip() for c in df.columns]
                    required_cols = {'empresa', 'motivo', 'conteudo'}
                    if not required_cols.issubset(df.columns):
                        st.error(f"Erro: Faltam colunas obrigatórias: {', '.join(required_cols)}")
                    else:
                        with st.spinner("Analisando duplicatas..."):
                            res_existentes = supabase.table("frases").select("empresa, motivo, conteudo").execute()
                            assinaturas_existentes = set()
                            for item in res_existentes.data:
                                assinaturas_existentes.add(gerar_assinatura(item['empresa'], item['motivo'], item['conteudo']))

                        progress = st.progress(0); total = len(df); sucesso = 0; duplicados = 0; erros = 0
                        
                        for i, row in df.iterrows():
                            try:
                                el = padronizar(row['empresa']); ml = padronizar(row['motivo']); cl = padronizar(row['conteudo'])
                                ass_atual = gerar_assinatura(el, ml, cl)
                                if ass_atual in assinaturas_existentes: duplicados += 1
                                else:
                                    user_excel = row.get('usuario')
                                    user_final = str(user_excel).strip() if pd.notnull(user_excel) and str(user_excel).strip() != "" else user['username']
                                    data_excel = row.get('data')
                                    data_final = datetime.now().strftime('%Y-%m-%d')
                                    if pd.notnull(data_excel):
                                        try: data_final = pd.to_datetime(data_excel).strftime('%Y-%m-%d')
                                        except: pass

                                    supabase.table("frases").insert({
                                        "empresa": el, "documento": padronizar(row.get('documento', 'Geral')), 
                                        "motivo": ml, "conteudo": cl,
                                        "revisado_por": user_final, "data_revisao": data_final
                                    }).execute()
                                    assinaturas_existentes.add(ass_atual); sucesso += 1
                            except: erros += 1
                            progress.progress((i + 1) / total)
                        
                        st.success("Concluído!")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("✅", sucesso); c2.metric("🚫", duplicados); c3.metric("⚠️", erros)
                        if sucesso > 0:
                            registrar_log(user['username'], "Importação em Massa", f"Importou {sucesso} itens.")
                            time.sleep(4); st.cache_data.clear(); st.rerun()
                except Exception as e: st.error(f"Erro ao ler arquivo: {e}")

def tela_manutencao(user):
    st.markdown("### 🛠️ Manutenção de Frases")
    q = st.text_input("Buscar frase", placeholder="Digite empresa, motivo ou ID...", key="search_manut")
    query = supabase.table("frases").select("*").order("id", desc=True)
    if q:
        if q.isdigit(): query = query.eq("id", q)
        else: query = query.or_(f"empresa.ilike.%{q}%,motivo.ilike.%{q}%")
        st.info(f"Resultados para: '{q}'")
    else:
        query = query.limit(4)
        st.caption("4 últimas adições.")
        
    items = query.execute().data
    if not items and q: st.warning("Nada encontrado.")
    
    for item in items:
        with st.expander(f"#{item['id']} | {item['empresa']} - {item['motivo']}"):
            with st.form(key=f"form_edit_{item['id']}"):
                c1, c2, c3 = st.columns([1.5, 1.5, 1])
                ne = c1.text_input("Empresa", value=item['empresa'])
                nm = c2.text_input("Motivo", value=item['motivo'])
                nd = c3.text_input("Doc", value=item['documento'])
                nc = st.text_area("Conteúdo", value=item['conteudo'], height=150)
                st.write("---")
                cs, cd = st.columns([1, 0.25])
                if cs.form_submit_button("💾 Salvar", type="primary"):
                    supabase.table("frases").update({"empresa": ne, "motivo": nm, "documento": nd, "conteudo": nc, "revisado_por": user['username']}).eq("id", item['id']).execute()
                    registrar_log(user['username'], "Editar Frase", f"ID: {item['id']}"); st.success("Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
                if cd.form_submit_button("🗑️ Excluir"):
                    supabase.table("frases").delete().eq("id", item['id']).execute()
                    registrar_log(user['username'], "Excluir Frase", f"ID: {item['id']}"); st.toast("Excluído!"); time.sleep(1); st.cache_data.clear(); st.rerun()

def tela_admin(user_logado):
    st.markdown("### ⚙️ Painel Administrativo")
    tab_users, tab_logs, tab_backup, tab_danger = st.tabs(["👥 Usuários", "📜 Logs", "💾 Backup", "🚨 Zona de Perigo"])
    
    with tab_users:
        st.info("Gestão de Acessos.")
        users = supabase.table("usuarios").select("*").order("id").execute().data
        for u in users:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.write(f"👤 **{u['username']}** {'(Admin)' if u.get('admin') else ''}")
                with st.expander("Editar"):
                    with st.form(key=f"eu_{u['id']}"):
                        np = st.text_input("Senha", value=u['senha'], type="password")
                        ia = st.checkbox("Admin", value=u.get('admin', False))
                        if st.form_submit_button("Atualizar"):
                            supabase.table("usuarios").update({"senha": np, "admin": ia}).eq("id", u['id']).execute()
                            registrar_log(user_logado['username'], "Editar Usuário", u['username']); st.rerun()
                        if st.form_submit_button("Excluir"):
                            if u['username'] == user_logado['username']: st.error("Não podes excluir-te a ti mesmo.")
                            else:
                                supabase.table("usuarios").delete().eq("id", u['id']).execute()
                                registrar_log(user_logado['username'], "Excluir Usuário", u['username']); st.rerun()
        with st.expander("➕ Novo Usuário"):
            with st.form("nu"):
                nu = st.text_input("User"); ns = st.text_input("Pass", type="password"); na = st.checkbox("Admin")
                if st.form_submit_button("Criar"):
                    try: 
                        supabase.table("usuarios").insert({"username": nu, "senha": ns, "admin": na}).execute()
                        st.success("Criado!"); st.rerun()
                    except: st.error("Erro.")

    with tab_logs:
        if st.button("Atualizar Logs"): st.rerun()
        try:
            logs = supabase.table("logs").select("*").order("id", desc=True).limit(50).execute().data
            if logs: st.dataframe(logs, use_container_width=True, hide_index=True)
        except: st.error("Sem logs.")

    with tab_backup:
        c1, c2 = st.columns(2)
        with c1:
            df = supabase.table("frases").select("*").execute().data
            st.download_button("⬇️ Backup Frases", data=converter_para_csv(df), file_name="frases.csv", mime="text/csv", use_container_width=True)
        with c2:
            du = supabase.table("usuarios").select("*").execute().data
            st.download_button("⬇️ Backup Usuários", data=converter_para_csv(du), file_name="users.csv", mime="text/csv", use_container_width=True)

    with tab_danger:
        st.markdown("""<div class="danger-zone"><h3 style="color:#b91c1c; margin-top:0;">☢️ Reset do Sistema</h3><p style="color:#7f1d1d;">Ações irreversíveis.</p></div>""", unsafe_allow_html=True); st.write("")
        col_danger1, col_danger2 = st.columns(2)
        with col_danger1:
            st.markdown("#### 🗑️ Excluir Frases"); st.caption("Remove todo o conteúdo.")
            confirm_phrases = st.text_input("Digite 'CONFIRMAR':", key="confirm_phrases")
            if st.button("💥 APAGAR TODAS AS FRASES", type="primary", disabled=confirm_phrases!="CONFIRMAR", use_container_width=True):
                try:
                    supabase.table("frases").delete().neq("id", 0).execute()
                    registrar_log(user_logado['username'], "RESET FRASES", "Apagou todas as frases")
                    st.success("Removido."); time.sleep(2); st.cache_data.clear(); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")
        with col_danger2:
            st.markdown("#### 🏭 Reset Usuários"); st.caption("Remove outros usuários.")
            confirm_users = st.text_input("Digite 'RESETAR TUDO':", key="confirm_users")
            if st.button("💥 APAGAR OUTROS USUÁRIOS", type="primary", disabled=confirm_users!="RESETAR TUDO", use_container_width=True):
                try:
                    supabase.table("usuarios").delete().neq("username", user_logado['username']).execute()
                    registrar_log(user_logado['username'], "RESET USUARIOS", "Apagou outros usuários")
                    st.success("Removido."); time.sleep(2); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

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
                else: st.error("Credenciais inválidas.")
else:
    user = st.session_state["usuario_logado"]
    c_logo, c_nav, c_user = st.columns([1, 4, 1], vertical_alignment="center")
    with c_logo: st.image(LOGO_URL, width=80)
    with c_nav:
        opcoes = ["Biblioteca", "Adicionar", "Manutenção"]
        if user.get('admin') == True: opcoes.append("Admin")
        selecao = st.radio("Nav", opcoes, horizontal=True, label_visibility="collapsed")
    with c_user:
        if st.button("Sair"):
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

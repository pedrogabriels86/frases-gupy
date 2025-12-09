import streamlit as st
from supabase import create_client, Client
import time
from datetime import datetime, timedelta
import io
import requests
import csv
import pandas as pd # Reintroduzido para leitura robusta de Excel
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

def registrar_log(usuario, acao, detalhe):
    """Registra ações importantes na tabela de logs"""
    try:
        supabase.table("logs").insert({
            "usuario": usuario, 
            "acao": acao, 
            "detalhe": detalhe, 
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
    except: pass

def converter_para_csv(dados):
    """Converte lista de dicionários para string CSV"""
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
    
    # Divisão em Abas: Manual vs Excel
    tab_manual, tab_import = st.tabs(["📝 Cadastro Manual", "📗 Importar Excel"])
    
    # --- ABA 1: MANUAL ---
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
                            supabase.table("frases").insert({
                                "empresa": padronizar(ne), 
                                "documento": padronizar(nd), 
                                "motivo": padronizar(nm), 
                                "conteudo": padronizar(nc), 
                                "revisado_por": user['username'], 
                                "data_revisao": datetime.now().strftime('%Y-%m-%d')
                            }).execute()
                            registrar_log(user['username'], "Adicionar Frase", f"Empresa: {ne} - Motivo: {nm}")
                            st.success("Frase salva com sucesso!")
                            time.sleep(1)
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")

    # --- ABA 2: IMPORTAR EXCEL ---
    with tab_import:
        st.info("Carregue uma planilha Excel (.xlsx) com múltiplas frases.")
        
        # Helper para o usuário saber o formato
        with st.expander("📌 Ver modelo da planilha (Colunas Obrigatórias)"):
            st.markdown("""
            O seu arquivo Excel deve conter **exatamente** estas colunas na primeira linha (cabeçalho):
            - `empresa`
            - `documento`
            - `motivo`
            - `conteudo`
            """)
        
        arquivo = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])
        
        if arquivo:
            if st.button("🚀 Processar e Importar", type="primary"):
                try:
                    df = pd.read_excel(arquivo)
                    
                    # Padronizar nomes das colunas (tudo minúsculo, sem espaços)
                    df.columns = [c.lower().strip() for c in df.columns]
                    
                    required_cols = {'empresa', 'motivo', 'conteudo'} # Documento é opcional
                    if not required_cols.issubset(df.columns):
                        st.error(f"Erro: O arquivo deve conter as colunas: {', '.join(required_cols)}")
                    else:
                        # Barra de progresso visual
                        progress_bar = st.progress(0)
                        total = len(df)
                        sucesso = 0
                        erros = 0
                        
                        for i, row in df.iterrows():
                            try:
                                supabase.table("frases").insert({
                                    "empresa": padronizar(row['empresa']),
                                    "documento": padronizar(row.get('documento', 'Geral')), # Default se nao tiver
                                    "motivo": padronizar(row['motivo']),
                                    "conteudo": padronizar(row['conteudo']),
                                    "revisado_por": user['username'],
                                    "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                }).execute()
                                sucesso += 1
                            except:
                                erros += 1
                            
                            # Atualiza barra
                            progress_bar.progress((i + 1) / total)
                        
                        st.success(f"Processo finalizado! Importados: {sucesso} | Erros: {erros}")
                        registrar_log(user['username'], "Importação em Massa", f"Importou {sucesso} frases via Excel")
                        
                        time.sleep(2)
                        st.cache_data.clear()
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Erro ao ler arquivo: {e}")

def tela_manutencao(user):
    st.markdown("### 🛠️ Manutenção de Frases")
    st.caption("Edite textos, corrija empresas ou exclua registros.")
    
    q_manutencao = st.text_input("Buscar frase", placeholder="Digite empresa, motivo ou ID...", key="search_manutencao")
    
    query = supabase.table("frases").select("*").order("id", desc=True)
    if q_manutencao:
        if q_manutencao.isdigit():
             query = query.eq("id", q_manutencao)
        else:
             filtro = f"empresa.ilike.%{q_manutencao}%,motivo.ilike.%{q_manutencao}%"
             query = query.or_(filtro)
        st.info(f"Resultados da busca por: '{q_manutencao}'")
    else:
        query = query.limit(4)
        st.caption("Mostrando as 4 últimas adições.")
        
    items = query.execute().data
    
    if not items and q_manutencao:
        st.warning("Nenhum item encontrado.")
    
    for item in items:
        with st.expander(f"#{item['id']} | {item['empresa']} - {item['motivo']}"):
            with st.form(key=f"form_edit_{item['id']}"):
                c1, c2, c3 = st.columns([1.5, 1.5, 1])
                new_empresa = c1.text_input("Empresa", value=item['empresa'])
                new_motivo = c2.text_input("Motivo", value=item['motivo'])
                new_doc = c3.text_input("Documento", value=item['documento'])
                new_conteudo = st.text_area("Conteúdo da Frase", value=item['conteudo'], height=150)
                
                st.write("---")
                col_save, col_del = st.columns([1, 0.25])
                
                if col_save.form_submit_button("💾 Salvar Alterações", type="primary"):
                    try:
                        supabase.table("frases").update({
                            "empresa": padronizar(new_empresa),
                            "motivo": padronizar(new_motivo),
                            "documento": padronizar(new_doc),
                            "conteudo": padronizar(new_conteudo),
                            "revisado_por": user['username'],
                            "data_revisao": datetime.now().strftime('%Y-%m-%d')
                        }).eq("id", item['id']).execute()
                        registrar_log(user['username'], "Editar Frase", f"ID: {item['id']} - {new_empresa}")
                        st.success("Alterações salvas!")
                        time.sleep(1)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

                if col_del.form_submit_button("🗑️ Excluir"):
                    try:
                        supabase.table("frases").delete().eq("id", item['id']).execute()
                        registrar_log(user['username'], "Excluir Frase", f"ID: {item['id']} - {item['empresa']}")
                        st.toast(f"Item {item['id']} excluído!")
                        time.sleep(1)
                        st.cache_data.clear()
                        st.rerun()
                    except: st.error("Erro ao excluir.")

def tela_admin(user_logado):
    st.markdown("### ⚙️ Painel Administrativo")
    tab_users, tab_logs, tab_backup = st.tabs(["👥 Gerir Usuários", "📜 Logs do Sistema", "💾 Backup"])
    
    with tab_users:
        st.info("Edite permissões ou remova acesso de colaboradores.")
        users_res = supabase.table("usuarios").select("*").order("id").execute()
        users = users_res.data
        for u in users:
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.5, 3, 1])
                c1.write("👤")
                c2.write(f"**{u['username']}** {'(Admin)' if u.get('admin') else ''}")
                with st.expander("Editar / Excluir"):
                    with st.form(key=f"edit_user_{u['id']}"):
                        new_pass = st.text_input("Nova Senha", value=u['senha'], type="password")
                        is_admin = st.checkbox("É Administrador?", value=u.get('admin', False))
                        c_save, c_del = st.columns(2)
                        if c_save.form_submit_button("💾 Atualizar", use_container_width=True):
                            supabase.table("usuarios").update({"senha": new_pass, "admin": is_admin}).eq("id", u['id']).execute()
                            registrar_log(user_logado['username'], "Editar Usuário", f"Alterou usuário {u['username']}")
                            st.success("Atualizado!"); time.sleep(1); st.rerun()
                        if c_del.form_submit_button("🗑️ Excluir", use_container_width=True):
                            if u['username'] == user_logado['username']: st.error("Você não pode excluir a si mesmo!")
                            else:
                                supabase.table("usuarios").delete().eq("id", u['id']).execute()
                                registrar_log(user_logado['username'], "Excluir Usuário", f"Removeu usuário {u['username']}")
                                st.warning("Usuário removido."); time.sleep(1); st.rerun()

        with st.expander("➕ Cadastrar Novo Usuário", expanded=False):
            with st.form("new_user"):
                nu = st.text_input("Nome de Usuário"); ns = st.text_input("Senha", type="password"); na = st.checkbox("Conceder Acesso Admin")
                if st.form_submit_button("Criar Usuário"):
                    if nu and ns:
                        try:
                            supabase.table("usuarios").insert({"username": nu, "senha": ns, "admin": na}).execute()
                            registrar_log(user_logado['username'], "Criar Usuário", f"Criou {nu}")
                            st.success("Criado com sucesso!"); time.sleep(1); st.rerun()
                        except: st.error("Erro ou usuário já existe.")

    with tab_logs:
        st.caption("Histórico das últimas 50 ações realizadas no sistema.")
        if st.button("🔄 Atualizar Logs"): st.rerun()
        try:
            logs_res = supabase.table("logs").select("*").order("id", desc=True).limit(50).execute()
            logs = logs_res.data
            if logs: st.dataframe(logs, column_config={"data_hora": "Data/Hora", "usuario": "Quem fez", "acao": "Ação", "detalhe": "Detalhes"}, use_container_width=True, hide_index=True)
            else: st.info("Nenhum registro de log encontrado.")
        except: st.error("Tabela 'logs' não encontrada.")

    with tab_backup:
        st.info("Baixe os dados completos para segurança ou relatórios.")
        c_bkp1, c_bkp2 = st.columns(2)
        with c_bkp1:
            st.markdown("#### 📚 Frases")
            dados_frases = supabase.table("frases").select("*").execute().data
            csv_frases = converter_para_csv(dados_frases)
            st.download_button(label="⬇️ Baixar Frases (CSV)", data=csv_frases, file_name=f"backup_frases_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
            st.caption(f"{len(dados_frases)} registros.")
        with c_bkp2:
            st.markdown("#### 👥 Usuários")
            dados_users = supabase.table("usuarios").select("*").execute().data
            csv_users = converter_para_csv(dados_users)
            st.download_button(label="⬇️ Baixar Usuários (CSV)", data=csv_users, file_name=f"backup_usuarios_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
            st.caption(f"{len(dados_users)} registros.")

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
                else:
                    st.error("Credenciais inválidas.")
else:
    user = st.session_state["usuario_logado"]
    
    c_logo, c_nav, c_user = st.columns([1, 4, 1], vertical_alignment="center")
    with c_logo:
        st.image(LOGO_URL, width=80)
    
    with c_nav:
        opcoes = ["Biblioteca", "Adicionar", "Manutenção"]
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
    elif selecao == "Manutenção": tela_manutencao(user)
    elif selecao == "Admin": tela_admin(user)

    st.markdown("<br><div style='text-align:center; color:#CCC; font-size:0.8rem'>Gupy Frases v3.3 • Com Importação Excel</div>", unsafe_allow_html=True)

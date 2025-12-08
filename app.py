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
# 2. CSS CUSTOMIZADO (Minimalista e Moderno)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    
    /* 1. Ocultar Elementos Streamlit Padrão */
    header[data-testid="stHeader"], div[data-testid="stToolbar"], div[data-testid="stDecoration"], footer { 
        display: none !important; 
    }

    /* 2. Puxar o conteúdo para o topo e ajustar padding */
    .block-container {
        padding-top: 1rem !important; 
        padding-bottom: 5rem;
        margin-top: 0 !important;
        max-width: 100%;
    }
    
    /* 3. Estilo do Container do Header */
    div[data-testid="stVerticalBlock"] > div:first-child > div:first-child { 
        background-color: white;
        border-bottom: 1px solid #E2E8F0;
        padding: 1rem 2rem;
        margin: -1rem -5rem 2rem -5rem; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        z-index: 100;
        width: 100vw; 
    }
    
    /* 4. Estilização do Menu (Tabs) */
    .stRadio > div[role="radiogroup"] {
        display: flex; gap: 8px; justify-content: center;
    }
    .stRadio > div[role="radiogroup"] label {
        padding: 6px 16px; border-radius: 6px; transition: all 0.2s ease;
        color: #64748B; font-weight: 500; font-size: 0.9rem;
    }
    .stRadio > div[role="radiogroup"] label:hover { background-color: #F1F5F9; color: #0F172A; }
    .stRadio > div[role="radiogroup"] label[data-checked="true"] {
        background-color: #2563EB !important; color: white !important;
        font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .stRadio > div[role="radiogroup"] label > div:first-child { display: none; } /* Oculta bolinha do radio */

    /* 5. Alinhamento de Usuário e Botão SAIR no Header */
    div[data-testid="stVerticalBlock"] > div:first-child > div:first-child > div:nth-child(3) > div {
        display: flex; align-items: center; justify-content: flex-end; 
        gap: 10px; height: 100%;
    }
    .user-text { text-align: right; font-size: 0.85rem; color: #475569; line-height: 1.2; }
    
    /* 6. Estilo de Card/Código */
    .frase-header { background-color: white; border-radius: 12px 12px 0 0; border: 1px solid #E2E8F0; border-bottom: none; padding: 15px 20px; }
    .card-meta { margin-top: 10px; padding-top: 10px; border-top: 1px solid #F1F5F9; font-size: 0.75rem; color: #94A3B8; display: flex; justify-content: space-between; align-items: center; }
    .stCodeBlock { border: 1px solid #E2E8F0; border-top: none; border-radius: 0 0 12px 12px; background-color: white !important; }
    .stButton button { border-radius: 6px; font-weight: 600; transition: all 0.2s; height: auto; padding: 0.4rem 1rem; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .badge-blue { background: #DBEAFE; color: #1E40AF; }

    /* Estilo para Container de Busca/Filtro Compacto */
    div[data-testid="stVerticalBlock"] div[data-testid="stTextInput"], 
    div[data-testid="stVerticalBlock"] div[data-testid="stSelectbox"] {
        margin-bottom: 0px !important; 
    }
    
    /* Ajuste para o Expander (Manutenção) */
    .stExpander details summary p { color: #1E3A8A; font-weight: 600; }

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CONEXÃO E FUNÇÕES
# ==============================================================================
try:
    url_db = st.secrets["SUPABASE_URL"]
    key_db = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url_db, key_db)
except: 
    st.error("Erro de configuração: Secrets não encontrados.")
    st.stop()

# Funções de DB e Utilitárias (Mantidas, apenas a busca foi ajustada para melhor clareza)
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
    try: 
        supabase.table("logs").insert({"usuario": usuario, "acao": acao, "detalhe": detalhe, "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
    except: pass
    
def padronizar(texto, tipo="titulo"): 
    if not texto: return ""
    texto = str(texto).strip()
    return texto.title() if tipo == "titulo" else texto[0].upper() + texto[1:]

def limpar_coluna(col): 
    return ''.join(c for c in unicodedata.normalize('NFD', str(col).lower().strip()) if unicodedata.category(c) != 'Mn')

# ==============================================================================
# 4. SISTEMA DE AUTENTICAÇÃO
# ==============================================================================
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None
if "logout_sync" not in st.session_state: st.session_state["logout_sync"] = False

cookie_manager = stx.CookieManager(key="main_auth")

if st.session_state["usuario_logado"] is None:
    if st.session_state["logout_sync"]:
        st.session_state["logout_sync"] = False
    else:
        cookies = cookie_manager.get_all()
        token = cookies.get("gupy_user_token") if cookies else None
        if token:
            user_db = recuperar_usuario_cookie(token)
            if user_db:
                st.session_state["usuario_logado"] = user_db

# ==============================================================================
# 5. FUNÇÕES DE RENDERIZAÇÃO POR PÁGINA (Novo: Organização por Função)
# ==============================================================================

def render_biblioteca(dados_totais, user):
    """Renderiza a página Biblioteca com busca e exibição em cards."""
    st.subheader("Biblioteca de Frases")
    
    # CONTAINER DE BUSCA E FILTRO (Mais compacto)
    with st.container(border=True): 
        c_search, c_filter = st.columns([5, 2]) 
        
        with c_search:
            termo = st.text_input("Pesquisa Inteligente", 
                                placeholder="🔎 Busque por empresa, motivo ou conteúdo...", 
                                label_visibility="collapsed")
        
        with c_filter:
            filtro_empresa = st.selectbox("Filtrar Empresa", 
                                            ["Todas"] + sorted(list(set(d['empresa'] for d in dados_totais))), 
                                            label_visibility="collapsed")
    
    # LÓGICA DE FILTRAGEM
    filtrados = dados_totais
    if filtro_empresa != "Todas": 
        filtrados = [f for f in filtrados if f['empresa'] == filtro_empresa]
        
    if termo: 
        termo_limpo = limpar_coluna(termo)
        filtrados = [f for f in filtrados if termo_limpo in limpar_coluna(f['empresa']) or \
                                              termo_limpo in limpar_coluna(f['motivo']) or \
                                              termo_limpo in limpar_coluna(f['conteudo'])]


    st.markdown(f"<div style='margin-top: 15px; margin-bottom:15px; color:#64748B;'>Encontrados <b>{len(filtrados)}</b> resultados</div>", unsafe_allow_html=True)
    
    # EXIBIÇÃO DOS CARDS EM DUAS COLUNAS
    if not filtrados: st.info("Nenhum resultado encontrado.")
    else:
        for i in range(0, len(filtrados), 2):
            row_c1, row_c2 = st.columns(2)
            
            # Helper para renderizar um card
            def render_frase_card(container, frase):
                author = frase.get('revisado_por', 'Sistema')
                date = frase.get('data_revisao', '')
                with container:
                    st.markdown(f"""
                    <div class="frase-header">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                            <h4 style="margin:0; color:#1E3A8A; font-weight:700;">{frase['empresa']}</h4>
                            <span class="badge badge-blue">{frase['documento']}</span>
                        </div>
                        <div style="color:#64748B; font-size:0.9rem; margin-bottom:8px;">{frase['motivo']}</div>
                        <div class="card-meta"><span>👤 {author}</span><span>📅 {date}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(frase['conteudo'], language="text")
                    st.write("") # Espaço entre cards

            render_frase_card(row_c1, filtrados[i])
            if i + 1 < len(filtrados):
                render_frase_card(row_c2, filtrados[i+1])
                
def render_adicionar(dados_totais, user):
    """Renderiza a página Adicionar (Manual e Importação)."""
    st.markdown("### Adicionar Novas Frases")
    tab_man, tab_imp = st.tabs(["✍️ Manual", "📥 Importação em Massa"])
    
    with tab_man:
        # Formulário Centralizado para maior foco
        c_e, c_f, c_d = st.columns([1, 2, 1])
        with c_f:
            with st.form("add_single", border=True):
                st.subheader("Registro Manual")
                c1, c2 = st.columns(2)
                ne = c1.text_input("Empresa Solicitante", placeholder="Ex: Gupy Tech"); 
                nd = c2.text_input("Tipo de Documento", placeholder="Ex: Carta Recusa");
                nm = st.text_input("Motivo da Recusa", placeholder="Ex: Baixa Qualificação"); 
                nc = st.text_area("Texto da Frase (Conteúdo)", height=150, placeholder="Prezado(a), Agradecemos o seu interesse...");
                
                st.write("---")
                if st.form_submit_button("✅ Salvar Novo Registro", type="primary", use_container_width=True):
                    if ne and nd and nm and nc:
                        ne_p, nd_p, nm_p = padronizar(ne), padronizar(nd), padronizar(nm); nc_p = padronizar(nc, "frase")
                        if [d for d in dados_totais if d.get('conteudo') == nc_p]: st.error("Frase idêntica já existe.")
                        else:
                            supabase.table("frases").insert({
                                "empresa":ne_p, "documento":nd_p, "motivo":nm_p, "conteudo":nc_p, 
                                "revisado_por":user['username'], "data_revisao":datetime.now().strftime('%Y-%m-%d')
                            }).execute()
                            registrar_log(user['username'], "Criou Frase", f"{ne_p}-{nm_p}"); 
                            st.toast("✅ Salvo com sucesso!"); 
                            time.sleep(1); 
                            st.cache_data.clear(); 
                            st.rerun()
                    else: st.warning("Preencha todos os campos obrigatórios.")

    with tab_imp:
        st.info("Colunas obrigatórias: **Empresa**, **Documento**, **Motivo** e **Conteudo**.")
        upl = st.file_uploader("Selecione um Arquivo CSV ou XLSX", type=['csv','xlsx'])
        if upl and st.button("Processar Arquivo", type="primary"):
            # Lógica de Importação (Mantida)
            try:
                if upl.name.endswith('.csv'):
                    try: df = pd.read_csv(upl)
                    except: df = pd.read_csv(upl, encoding='latin-1', sep=';')
                else: df = pd.read_excel(upl)
                
                df.columns = [limpar_coluna(c) for c in df.columns]
                mapa = {
                    'empresa solicitante':'empresa','cliente':'empresa','tipo documento':'documento',
                    'motivo recusa':'motivo','frase':'conteudo','texto':'conteudo',
                    'revisado por': 'revisado_por', 'autor': 'revisado_por'
                }
                df.rename(columns=mapa, inplace=True)
                
                if not all(c in df.columns for c in ['empresa', 'documento', 'motivo', 'conteudo']): 
                    st.error("Colunas obrigatórias ausentes.")
                else:
                    novos = []; db_conteudos = set(d.get('conteudo') for d in dados_totais if d.get('conteudo')) # Garante que não é None
                    
                    for _, row in df.iterrows():
                        cont = padronizar(str(row['conteudo']), 'frase')
                        # Verifica se o conteúdo é válido e não está duplicado
                        if cont and cont not in db_conteudos:
                            autor_final = user['username']
                            if 'revisado_por' in df.columns and pd.notna(row['revisado_por']) and str(row['revisado_por']).strip():
                                autor_final = str(row['revisado_por']).strip()
                            
                            novos.append({
                                "empresa": padronizar(str(row['empresa'])), "documento": padronizar(str(row['documento'])), 
                                "motivo": padronizar(str(row['motivo'])), "conteudo": cont, 
                                "revisado_por": autor_final, "data_revisao": datetime.now().strftime('%Y-%m-%d')
                            })
                            db_conteudos.add(cont)
                            
                    if novos: 
                        supabase.table("frases").insert(novos).execute()
                        registrar_log(user['username'], "Importação", f"{len(novos)}"); 
                        st.success(f"🎉 {len(novos)} frases importadas com sucesso!"); 
                        st.cache_data.clear();
                    else: st.warning("Nenhuma frase nova para importar (Verifique por duplicatas).")
            except Exception as e: st.error(f"Erro ao processar arquivo: {e}")

def render_manutencao(dados_totais, user):
    """Renderiza a página de Manutenção com expansores para edição."""
    st.markdown("### Gerenciar e Editar Registros")
    q = st.text_input("Buscar por Frase, Empresa ou Motivo para editar...", placeholder="Digite para filtrar a lista...")
    
    # Filtra os dados (Sem limite padrão, para evitar confusão)
    filtrados_manut = [f for f in dados_totais if q.lower() in str(f).lower()] if q else dados_totais

    if not filtrados_manut: 
        st.warning("Nada encontrado. Digite um termo de busca para listar ou volte à Biblioteca.")
        return
        
    st.markdown(f"**Total de resultados:** {len(filtrados_manut)}")
    st.write("---")

    for item in filtrados_manut:
        # Título do Expander mais descritivo e limpo
        with st.expander(f"🏢 {item['empresa']} | {item['motivo']}"):
            with st.form(f"edit_{item['id']}"):
                st.markdown(f"##### Editando Registro ID: {item['id']}")
                c1, c2, c3 = st.columns([1,1,1])
                ne = c1.text_input("Empresa", item['empresa']); 
                nd = c2.text_input("Documento", item['documento']); 
                nm = c3.text_input("Motivo", item['motivo'])
                
                nc = st.text_area("Conteúdo da Frase", item['conteudo'], height=150)
                
                c_auth, c_date = st.columns(2)
                na = c_auth.text_input("Autor/Revisor", item.get('revisado_por', user['username']))
                c_date.text_input("Data da Última Revisão", item.get('data_revisao', ''), disabled=True) # Mantém a data original

                st.write("---")
                c_s, c_d = st.columns([4, 1])
                if c_s.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True):
                    supabase.table("frases").update({
                        "empresa": ne, "documento": nd, "motivo": nm, "conteudo": nc, 
                        "revisado_por": na, "data_revisao": datetime.now().strftime('%Y-%m-%d') # Atualiza a data
                    }).eq("id", item['id']).execute()
                    registrar_log(user['username'], "Edição", str(item['id'])); 
                    st.toast("✅ Salvo e Atualizado!"); 
                    st.cache_data.clear(); 
                    time.sleep(1); 
                    st.rerun()
                
                if c_d.form_submit_button("🗑️ Excluir", use_container_width=True):
                    # Confirmação simples
                    st.session_state[f"confirm_delete_{item['id']}"] = True
                    
            # Lógica de Confirmação (fora do form)
            if st.session_state.get(f"confirm_delete_{item['id']}", False):
                st.error("Tem certeza que deseja EXCLUIR este item?")
                c_conf, c_canc = st.columns([1, 1])
                if c_conf.button("Sim, Excluir Definitivamente", key=f"del_final_{item['id']}"):
                    supabase.table("frases").delete().eq("id", item['id']).execute()
                    registrar_log(user['username'], "Exclusão", str(item['id'])); 
                    st.toast("Item Excluído."); 
                    st.cache_data.clear(); 
                    time.sleep(1); 
                    st.rerun()
                if c_canc.button("Cancelar", key=f"del_cancel_{item['id']}"):
                    st.session_state[f"confirm_delete_{item['id']}"] = False
                    st.rerun()

def render_admin(user):
    """Renderiza a página Administrativa (apenas para admins)."""
    st.markdown("### Painel Administrativo 👑")
    tab_users, tab_logs = st.tabs(["👥 Gerenciar Usuários", "🔒 Logs & Backup"])
    
    with tab_users:
        with st.expander("➕ Criar Novo Usuário", expanded=False):
            with st.form("new_user"):
                c_nu, c_ns, c_na = st.columns([2, 2, 1])
                nu = c_nu.text_input("Username", placeholder="Novo Usuário"); 
                ns = c_ns.text_input("Senha Inicial", type="password"); 
                na = c_na.checkbox("É Admin?", value=False)
                if st.form_submit_button("Criar Usuário"):
                    try: 
                        supabase.table("usuarios").insert({"username":nu, "senha":ns, "admin":na, "trocar_senha":True}).execute()
                        registrar_log(user['username'], "Criou Usuário", nu); 
                        st.success(f"Usuário {nu} criado! A senha deve ser trocada no primeiro login."); 
                        time.sleep(1); 
                        st.rerun()
                    except: st.error("Erro ao criar (usuário pode já existir).")
                    
        st.write("---"); st.subheader("Lista de Usuários")
        lista_usuarios = buscar_usuarios()
        for u in lista_usuarios:
            role_label = "👑 Admin" if u['admin'] else "👤 User"
            with st.expander(f"{role_label} | {u['username']}"):
                with st.form(key=f"edit_u_{u['id']}"):
                    st.write("**Permissões e Ações**")
                    c_edit_1, c_edit_2 = st.columns(2)
                    new_username = c_edit_1.text_input("Username", value=u['username'])
                    disabled_admin = (u['id'] == user['id'])
                    new_admin = c_edit_2.checkbox("Admin", value=u['admin'], disabled=disabled_admin, help="Um admin pode acessar este painel.")
                    st.write("---")
                    c_act_1, c_act_2, c_act_3 = st.columns([2, 2, 1])
                    if c_act_1.form_submit_button("💾 Salvar", type="primary"):
                        supabase.table("usuarios").update({"username": new_username, "admin": new_admin}).eq("id", u['id']).execute()
                        registrar_log(user['username'], "Editou Usuário", u['username']); st.toast("Atualizado!"); time.sleep(1); st.rerun()
                        
                    if c_act_2.form_submit_button("🔄 Reset Senha"): 
                        supabase.table("usuarios").update({"trocar_senha": True}).eq("id", u['id']).execute(); 
                        st.toast("Senha Resetada! O usuário será forçado a trocar.")
                        
                    if u['username'] != user['username']:
                        if c_act_3.form_submit_button("🗑️ Excluir"): 
                            supabase.table("usuarios").delete().eq("id", u['id']).execute()
                            registrar_log(user['username'], "Excluiu Usuário", u['username']); 
                            st.rerun()
                    else: c_act_3.write("") 
                    
    with tab_logs:
        st.subheader("Logs de Atividade (Últimos 100)")
        logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(100).execute().data
        if logs: 
            st.dataframe(pd.DataFrame(logs)[['data_hora', 'usuario', 'acao', 'detalhe']], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum log encontrado.")

        st.write("---")
        st.download_button("📥 Fazer Backup Completo (CSV)", 
                           data=pd.DataFrame(buscar_dados()).to_csv(index=False).encode('utf-8'), 
                           file_name="backup_frases.csv", 
                           mime="text/csv")
        st.write("---")
        
        with st.expander("🚨 Zona de Perigo (Apagar Tudo)", expanded=False):
            st.warning("⚠️ CUIDADO: Esta ação apagará **TODAS** as frases. Ação irreversível.")
            chk = st.text_input("Para confirmar, digite: QUERO APAGAR TUDO", key="chk_del_all")
            if st.button("🗑️ APAGAR TODA A BIBLIOTECA", type="primary", use_container_width=True):
                if chk == "QUERO APAGAR TUDO":
                    try:
                        supabase.table("frases").delete().neq("id", 0).execute()
                        registrar_log(user['username'], "LIMPEZA TOTAL", "Apagou todas as frases")
                        st.success("Banco de dados limpo com sucesso!")
                        time.sleep(2); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro ao apagar: {e}")
                else: st.error("Texto de confirmação incorreto.")

# ==============================================================================
# 6. FLUXO PRINCIPAL
# ==============================================================================

# --- TELA DE LOGIN ---
if st.session_state["usuario_logado"] is None:
    st.write("#"); st.write("#")
    c_esq, c_centro, c_dir = st.columns([1, 0.8, 1])
    with c_centro:
        with st.container(border=True):
            st.markdown("<div style='text-align:center; margin-bottom: 20px;'>", unsafe_allow_html=True)
            if LOGO_URL: st.image(LOGO_URL, width=120)
            else: st.markdown("<h1>Gupy Frases</h1>", unsafe_allow_html=True)
            st.markdown("</div><p style='text-align:center; color:#64748B;'>Gestão de Conteúdo e Recusas</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
                st.write("")
                if st.form_submit_button("Acessar Plataforma", use_container_width=True, type="primary"):
                    user = verificar_login(u, s)
                    if user:
                        st.session_state["usuario_logado"] = user
                        expires = datetime.now() + timedelta(days=7)
                        cookie_manager.set("gupy_user_token", u, expires_at=expires)
                        time.sleep(0.5)
                        st.rerun()
                    else: st.toast("🚫 Credenciais inválidas.", icon="error")

# --- ÁREA LOGADA ---
else:
    user = st.session_state["usuario_logado"]
    dados_totais = buscar_dados() # Busca os dados apenas uma vez

    # 6.1 HEADER
    with st.container():
        c_logo, c_menu, c_user = st.columns([1, 3, 1], vertical_alignment="center")
        
        with c_logo:
            if LOGO_URL: st.image(LOGO_URL, width=90) 
            else: st.markdown("### Gupy")

        with c_menu:
            opcoes_map = {"Biblioteca": "📂 Biblioteca", "Adicionar": "➕ Adicionar", "Manutenção": "✏️ Gestão"}
            if user['admin']: opcoes_map["Admin"] = "⚙️ Admin"
            
            opcoes_labels = list(opcoes_map.values())
            # Mantém a seleção de página na sessão para evitar piscadas
            if 'page_sel' not in st.session_state: st.session_state.page_sel = opcoes_labels[0]
            
            page_sel = st.radio("Menu", options=opcoes_labels, horizontal=True, label_visibility="collapsed", key='page_sel')
            page = [k for k, v in opcoes_map.items() if v == page_sel][0]

        with c_user:
            st.markdown(f"<div class='user-text'>Olá, <br><b>{user['username']}</b></div>", unsafe_allow_html=True)
            if st.button("Sair", key="btn_logout"):
                cookie_manager.delete("gupy_user_token")
                st.session_state["usuario_logado"] = None
                st.session_state["logout_sync"] = True
                st.rerun()

    # 6.2 LÓGICA DE TROCA DE SENHA
    if user.get('trocar_senha'):
        st.warning("⚠️ Segurança: Sua senha precisa ser redefinida.")
        with st.form("new_pass"):
            n1 = st.text_input("Nova Senha", type="password"); n2 = st.text_input("Confirmar Senha", type="password")
            if st.form_submit_button("Atualizar Senha", type="primary"):
                if n1 == n2 and len(n1) > 3:
                    supabase.table("usuarios").update({"senha":n1, "trocar_senha":False}).eq("id", user['id']).execute()
                    user['trocar_senha'] = False; st.success("Senha atualizada!"); time.sleep(1); st.rerun()
                else: st.error("Senhas inválidas.")
    
    # 6.3 RENDERIZAÇÃO DE PÁGINAS
    else:
        if page == "Biblioteca":
            render_biblioteca(dados_totais, user)
        elif page == "Adicionar":
            render_adicionar(dados_totais, user)
        elif page == "Manutenção":
            render_manutencao(dados_totais, user)
        elif page == "Admin" and user['admin']:
            render_admin(user)

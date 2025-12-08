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
# 1. CONFIGURAÇÕES E INICIALIZAÇÃO
# ==============================================================================
FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"

# Carrega favicon de forma segura
favicon = "💙" 
try:
    response = requests.get(FAVICON_URL, timeout=1)
    if response.status_code == 200: 
        favicon = Image.open(io.BytesIO(response.content))
except: 
    pass

st.set_page_config(page_title="Gupy Frases", page_icon=favicon, layout="wide")

# ==============================================================================
# 2. CSS AVANÇADO (MODERN UI)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; } /* Cinza muito suave */
    
    /* REMOVER PADRÃO STREAMLIT */
    header[data-testid="stHeader"] { display: none; }
    footer { display: none; }
    div[data-testid="stToolbar"] { display: none; }

    /* BARRA DE NAVEGAÇÃO */
    .nav-container {
        background: white;
        padding: 1rem 2rem;
        border-bottom: 1px solid #E2E8F0;
        margin: -4rem -4rem 2rem -4rem; 
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* CARD DE FRASE (ESTILO) */
    .frase-card {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s;
    }
    .frase-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #BFDBFE;
    }

    /* BOTÕES E INPUTS */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    /* Tabs personalizadas */
    .stRadio > div[role="radiogroup"] {
        background: white;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* STATUS BADGES */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-blue { background: #DBEAFE; color: #1E40AF; }
    .badge-green { background: #D1FAE5; color: #065F46; }
</style>
""", unsafe_allow_html=True)

# --- 3. CONEXÃO & FUNÇÕES AUXILIARES ---
try:
    url_db = st.secrets["SUPABASE_URL"]
    key_db = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url_db, key_db)
except: 
    st.error("Erro de configuração: Secrets não encontrados.")
    st.stop()

def verificar_login(u, s):
    try: 
        res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute()
        return res.data[0] if res.data else None
    except: return None

@st.cache_data(ttl=60) # Cache para não bater no banco a cada clique (1 min)
def buscar_dados(): 
    return supabase.table("frases").select("*").order("id", desc=True).execute().data or []

def buscar_usuarios(): 
    return supabase.table("usuarios").select("*").order("id").execute().data or []

def registrar_log(usuario, acao, detalhe):
    try: 
        supabase.table("logs").insert({
            "usuario": usuario,
            "acao": acao,
            "detalhe": detalhe,
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
    except: pass

def padronizar(texto, tipo="titulo"):
    if not texto: return ""
    texto = str(texto).strip()
    return texto.title() if tipo == "titulo" else (texto[0].upper() + texto[1:])

def limpar_coluna(col):
    col = str(col).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', col) if unicodedata.category(c) != 'Mn')

# ==============================================================================
# 4. LÓGICA DE APLICAÇÃO
# ==============================================================================
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

# --- TELA DE LOGIN ---
if st.session_state["usuario_logado"] is None:
    col_spacer_top, col_login, col_spacer_bottom = st.columns([1, 1, 1])
    st.write("#"); st.write("#")

    c_esq, c_centro, c_dir = st.columns([1, 0.8, 1])
    with c_centro:
        with st.container(border=True):
            st.markdown("<div style='text-align:center; margin-bottom: 20px;'>", unsafe_allow_html=True)
            if LOGO_URL: st.image(LOGO_URL, width=120)
            else: st.markdown("<h1>Gupy Frases</h1>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align:center; color:#64748B;'>Gestão de Conteúdo e Recusas</p>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                u = st.text_input("Usuário", placeholder="Digite seu usuário")
                s = st.text_input("Senha", type="password", placeholder="••••••")
                st.write("")
                if st.form_submit_button("Acessar Plataforma", use_container_width=True, type="primary"):
                    user = verificar_login(u, s)
                    if user: 
                        st.session_state["usuario_logado"] = user
                        st.rerun()
                    else: 
                        st.toast("🚫 Usuário ou senha incorretos.", icon="error")

# --- ÁREA LOGADA ---
else:
    user = st.session_state["usuario_logado"]
    dados_totais = buscar_dados() # Busca dados
    
    # --- HEADER / NAVBAR ---
    with st.container():
        c_nav_logo, c_nav_menu, c_nav_user = st.columns([1, 3, 1], gap="medium")
        
        with c_nav_logo:
             if LOGO_URL: st.image(LOGO_URL, width=80)
             else: st.markdown("### Gupy")

        with c_nav_menu:
            opcoes = ["Biblioteca", "Adicionar", "Manutenção"]
            icons = ["📂", "➕", "✏️"]
            if user['admin']: 
                opcoes.append("Admin")
                icons.append("⚙️")
            
            opcoes_fmt = [f"{icons[i]} {opcoes[i]}" for i in range(len(opcoes))]
            page_sel = st.radio("Navegação", options=opcoes_fmt, horizontal=True, label_visibility="collapsed")
            page = opcoes[opcoes_fmt.index(page_sel)]

        with c_nav_user:
            c_u_text, c_u_btn = st.columns([2, 1])
            with c_u_text:
                st.markdown(f"<div style='text-align:right; font-size:0.85rem; color:#64748B; margin-top:5px;'>Olá, <b>{user['username']}</b></div>", unsafe_allow_html=True)
            with c_u_btn:
                if st.button("Sair", key="btn_logout"):
                    st.session_state["usuario_logado"] = None
                    st.rerun()
    
    st.markdown("---") 

    # --- SEGURANÇA: TROCA DE SENHA ---
    if user.get('trocar_senha'):
        st.warning("⚠️ Segurança: Sua senha precisa ser redefinida.")
        with st.form("new_pass"):
            n1 = st.text_input("Nova Senha", type="password")
            n2 = st.text_input("Confirmar Senha", type="password")
            if st.form_submit_button("Atualizar Senha", type="primary"):
                if n1 == n2 and len(n1) > 3:
                    supabase.table("usuarios").update({"senha":n1, "trocar_senha":False}).eq("id", user['id']).execute()
                    user['trocar_senha'] = False
                    st.success("Senha atualizada!")
                    time.sleep(1); st.rerun()
                else:
                    st.error("Senhas não conferem ou muito curtas.")
    
    else:
        # ======================================================================
        # PÁGINA: BIBLIOTECA (SEM MÉTRICAS)
        # ======================================================================
        if page == "Biblioteca":
            st.subheader("Biblioteca de Frases")
            
            # Busca e Filtros
            with st.container(border=True):
                c_search, c_filter = st.columns([3, 1])
                termo = c_search.text_input("Pesquisa Inteligente", placeholder="🔎 Busque por empresa, motivo ou conteúdo...", label_visibility="collapsed")
                filtro_empresa = c_filter.selectbox("Filtrar Empresa", ["Todas"] + sorted(list(set(d['empresa'] for d in dados_totais))))

            # Lógica de Filtragem
            filtrados = dados_totais
            if filtro_empresa != "Todas": filtrados = [f for f in filtrados if f['empresa'] == filtro_empresa]
            if termo: filtrados = [f for f in filtrados if termo.lower() in str(f).lower()]

            st.markdown(f"**Resultados:** {len(filtrados)}")
            
            if not filtrados: st.info("Nenhum resultado encontrado para os filtros aplicados.")
            else:
                for i in range(0, len(filtrados), 2):
                    row_c1, row_c2 = st.columns(2)
                    f1 = filtrados[i]
                    with row_c1:
                        with st.container():
                            st.markdown(f"""
                            <div class="frase-card">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                                    <h4 style="margin:0; color:#1E3A8A;">{f1['empresa']}</h4>
                                    <span class="badge badge-blue">{f1['documento']}</span>
                                </div>
                                <div style="color:#64748B; font-size:0.9rem; margin-bottom:10px;">
                                    <strong>Motivo:</strong> {f1['motivo']}
                                </div>
                                <div style="background:#F1F5F9; padding:10px; border-radius:8px; font-family:monospace; font-size:0.85rem; color:#334155;">
                                    {f1['conteudo']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    if i + 1 < len(filtrados):
                        f2 = filtrados[i+1]
                        with row_c2:
                            with st.container():
                                st.markdown(f"""
                                <div class="frase-card">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                                        <h4 style="margin:0; color:#1E3A8A;">{f2['empresa']}</h4>
                                        <span class="badge badge-blue">{f2['documento']}</span>
                                    </div>
                                    <div style="color:#64748B; font-size:0.9rem; margin-bottom:10px;">
                                        <strong>Motivo:</strong> {f2['motivo']}
                                    </div>
                                    <div style="background:#F1F5F9; padding:10px; border-radius:8px; font-family:monospace; font-size:0.85rem; color:#334155;">
                                        {f2['conteudo']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    st.write("")

        # ======================================================================
        # PÁGINA: ADICIONAR
        # ======================================================================
        elif page == "Adicionar":
            st.markdown("### Adicionar Novas Frases")
            tab_man, tab_imp = st.tabs(["✍️ Manual", "📥 Importação em Massa"])
            
            with tab_man:
                with st.form("add_single"):
                    c1, c2 = st.columns(2)
                    ne = c1.text_input("Empresa Solicitante")
                    nd = c2.text_input("Tipo de Documento")
                    nm = st.text_input("Motivo da Recusa")
                    nc = st.text_area("Texto da Frase (Conteúdo)", height=120)
                    if st.form_submit_button("Salvar Registro", type="primary", use_container_width=True):
                        if ne and nd and nm and nc:
                            ne, nd, nm = padronizar(ne), padronizar(nd), padronizar(nm); nc = padronizar(nc, "frase")
                            exists = [d for d in dados_totais if d['conteudo'] == nc]
                            if exists: st.error("Esta frase já existe.")
                            else:
                                supabase.table("frases").insert({"empresa":ne, "documento":nd, "motivo":nm, "conteudo":nc, "revisado_por":user['username'], "data_revisao":datetime.now().strftime('%Y-%m-%d')}).execute()
                                registrar_log(user['username'], "Criou Frase", f"{ne}-{nm}"); st.toast("✅ Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
                        else: st.warning("Preencha todos os campos.")

            with tab_imp:
                st.info("Upload CSV/Excel. Colunas: Empresa, Documento, Motivo, Conteudo.")
                upl = st.file_uploader("Arquivo", type=['csv','xlsx'])
                if upl and st.button("Processar Arquivo", type="primary"):
                    try:
                        if upl.name.endswith('.csv'):
                            try: df = pd.read_csv(upl)
                            except: df = pd.read_csv(upl, encoding='latin-1', sep=';')
                        else: df = pd.read_excel(upl)
                        
                        df.columns = [limpar_coluna(c) for c in df.columns]
                        mapa = {'empresa solicitante':'empresa','cliente':'empresa','tipo documento':'documento','doc':'documento','motivo recusa':'motivo','frase':'conteudo','texto':'conteudo','mensagem':'conteudo'}
                        df.rename(columns=mapa, inplace=True)
                        
                        if not all(c in df.columns for c in ['empresa', 'documento', 'motivo', 'conteudo']): st.error("Colunas inválidas.")
                        else:
                            novos = []; db_conteudos = set(d['conteudo'] for d in dados_totais)
                            for _, row in df.iterrows():
                                cont = padronizar(str(row['conteudo']), 'frase')
                                if cont and cont not in db_conteudos:
                                    novos.append({"empresa": padronizar(str(row['empresa'])), "documento": padronizar(str(row['documento'])), "motivo": padronizar(str(row['motivo'])), "conteudo": cont, "revisado_por": user['username'], "data_revisao": datetime.now().strftime('%Y-%m-%d')}); db_conteudos.add(cont)
                            if novos: supabase.table("frases").insert(novos).execute(); registrar_log(user['username'], "Importação", f"{len(novos)}"); st.success(f"{len(novos)} importados!"); st.cache_data.clear()
                            else: st.warning("Nada novo.")
                    except Exception as e: st.error(f"Erro: {e}")

        # ======================================================================
        # PÁGINA: MANUTENÇÃO
        # ======================================================================
        elif page == "Manutenção":
            st.markdown("### Gerenciar Registros")
            q = st.text_input("Buscar para editar...", placeholder="Digite para filtrar a lista...")
            lista_edit = [f for f in dados_totais if q.lower() in str(f).lower()] if q else dados_totais[:50]
            
            if not lista_edit: st.warning("Nada encontrado.")
            else:
                for item in lista_edit:
                    with st.expander(f"🏢 {item['empresa']} - {item['motivo']}"):
                        with st.form(f"edit_{item['id']}"):
                            c1, c2, c3 = st.columns([1,1,1])
                            ne = c1.text_input("Empresa", item['empresa'])
                            nd = c2.text_input("Documento", item['documento'])
                            nm = c3.text_input("Motivo", item['motivo'])
                            nc = st.text_area("Conteúdo", item['conteudo'])
                            c_s, c_d = st.columns([4, 1])
                            if c_s.form_submit_button("💾 Salvar", type="primary"):
                                supabase.table("frases").update({"empresa": ne, "documento": nd, "motivo": nm, "conteudo": nc, "revisado_por": user['username'], "data_revisao": datetime.now().strftime('%Y-%m-%d')}).eq("id", item['id']).execute()
                                registrar_log(user['username'], "Edição", str(item['id'])); st.toast("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                            if c_d.form_submit_button("🗑️ Excluir"):
                                supabase.table("frases").delete().eq("id", item['id']).execute()
                                registrar_log(user['username'], "Exclusão", str(item['id'])); st.toast("Excluído."); st.cache_data.clear(); time.sleep(1); st.rerun()

        # ======================================================================
        # PÁGINA: ADMIN (USUÁRIOS E LOGS)
        # ======================================================================
        elif page == "Admin" and user['admin']:
            st.markdown("### Painel Administrativo")
            tab_users, tab_logs = st.tabs(["👥 Usuários", "🔒 Logs & Dados"])
            
            with tab_users:
                # Criar Usuário
                with st.expander("➕ Criar Novo Usuário", expanded=False):
                    with st.form("new_user"):
                        c_nu, c_ns, c_na = st.columns([2, 2, 1])
                        nu = c_nu.text_input("Username")
                        ns = c_ns.text_input("Senha Inicial", type="password")
                        na = c_na.checkbox("É Admin?", value=False)
                        if st.form_submit_button("Criar Usuário"):
                            try:
                                supabase.table("usuarios").insert({"username":nu, "senha":ns, "admin":na, "trocar_senha":True}).execute()
                                registrar_log(user['username'], "Criou Usuário", nu)
                                st.success(f"Usuário {nu} criado com sucesso!")
                                time.sleep(1); st.rerun()
                            except: st.error("Erro ao criar usuário (talvez nome duplicado?)")

                st.write("---")
                st.subheader("Gerenciar Usuários")
                
                lista_usuarios = buscar_usuarios()
                
                for u in lista_usuarios:
                    role_label = "👑 Admin" if u['admin'] else "👤 User"
                    with st.expander(f"{role_label} | {u['username']}"):
                        with st.form(key=f"edit_u_{u['id']}"):
                            st.write("**Editar Permissões e Dados**")
                            c_edit_1, c_edit_2 = st.columns(2)
                            new_username = c_edit_1.text_input("Nome de Usuário", value=u['username'])
                            
                            disabled_admin = (u['id'] == user['id'])
                            new_admin = c_edit_2.checkbox("Acesso de Administrador", value=u['admin'], disabled=disabled_admin)
                            if disabled_admin: c_edit_2.caption("Você não pode remover seu próprio acesso de admin.")

                            st.write("---")
                            c_act_1, c_act_2, c_act_3 = st.columns([1, 1, 1])
                            
                            if c_act_1.form_submit_button("💾 Salvar Alterações", type="primary"):
                                supabase.table("usuarios").update({"username": new_username, "admin": new_admin}).eq("id", u['id']).execute()
                                registrar_log(user['username'], "Editou Usuário", u['username'])
                                st.toast("Dados atualizados!"); time.sleep(1); st.rerun()
                            
                            if c_act_2.form_submit_button("🔄 Resetar Senha"):
                                supabase.table("usuarios").update({"trocar_senha": True}).eq("id", u['id']).execute()
                                st.toast(f"Senha de {u['username']} resetada!")

                            if u['username'] != user['username']:
                                if c_act_3.form_submit_button("🗑️ Excluir Usuário"):
                                    supabase.table("usuarios").delete().eq("id", u['id']).execute()
                                    registrar_log(user['username'], "Excluiu Usuário", u['username']); st.rerun()
                            else: c_act_3.write("") 

            with tab_logs:
                logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(100).execute().data
                if logs:
                    st.dataframe(pd.DataFrame(logs)[['data_hora', 'usuario', 'acao', 'detalhe']], use_container_width=True, hide_index=True)
                
                st.write("---")
                st.download_button("📥 Backup CSV", data=pd.DataFrame(dados_totais).to_csv(index=False).encode('utf-8'), file_name="backup.csv", mime="text/csv")

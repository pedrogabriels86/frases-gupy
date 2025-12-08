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
# 2. CSS AVANÇADO
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    header[data-testid="stHeader"], footer, div[data-testid="stToolbar"] { display: none; }
    
    .nav-container { background: white; padding: 1rem 2rem; border-bottom: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    
    /* CARD HEADER */
    .frase-header { background-color: white; border-radius: 12px 12px 0 0; border: 1px solid #E2E8F0; border-bottom: none; padding: 15px 20px; }
    
    /* RODAPÉ DO CARD (AUTOR) */
    .card-meta { margin-top: 10px; padding-top: 10px; border-top: 1px solid #F1F5F9; font-size: 0.75rem; color: #94A3B8; display: flex; justify-content: space-between; align-items: center; }

    .stCodeBlock { border: 1px solid #E2E8F0; border-top: none; border-radius: 0 0 12px 12px; background-color: white !important; }
    .stButton button { border-radius: 8px; font-weight: 600; transition: all 0.2s; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .badge-blue { background: #DBEAFE; color: #1E40AF; }
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

def verificar_login(u, s):
    try: res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute(); return res.data[0] if res.data else None
    except: return None

def recuperar_usuario_cookie(username):
    try: res = supabase.table("usuarios").select("*").eq("username", username).execute(); return res.data[0] if res.data else None
    except: return None

@st.cache_data(ttl=60)
def buscar_dados(): return supabase.table("frases").select("*").order("id", desc=True).execute().data or []
def buscar_usuarios(): return supabase.table("usuarios").select("*").order("id").execute().data or []
def registrar_log(usuario, acao, detalhe):
    try: supabase.table("logs").insert({"usuario": usuario, "acao": acao, "detalhe": detalhe, "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
    except: pass
def padronizar(texto, tipo="titulo"): return (str(texto).strip().title() if tipo == "titulo" else str(texto).strip()[0].upper() + str(texto).strip()[1:]) if texto else ""
def limpar_coluna(col): return ''.join(c for c in unicodedata.normalize('NFD', str(col).lower().strip()) if unicodedata.category(c) != 'Mn')

# ==============================================================================
# 4. SISTEMA DE AUTENTICAÇÃO
# ==============================================================================
cookie_manager = stx.CookieManager(key="main_auth")

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None:
    cookies = cookie_manager.get_all()
    if not cookies:
        with st.spinner("Conectando..."):
            time.sleep(1) 
            cookies = cookie_manager.get_all()
    
    token = cookies.get("gupy_user_token") if cookies else None
    if token:
        user_db = recuperar_usuario_cookie(token)
        if user_db:
            st.session_state["usuario_logado"] = user_db

# ==============================================================================
# 5. RENDERIZAÇÃO
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
    dados_totais = buscar_dados()
    
    # NAVBAR
    with st.container():
        c_nav_logo, c_nav_menu, c_nav_user = st.columns([1, 3, 1], gap="medium")
        with c_nav_logo:
             if LOGO_URL: st.image(LOGO_URL, width=80)
             else: st.markdown("### Gupy")
        with c_nav_menu:
            opcoes = ["Biblioteca", "Adicionar", "Manutenção"]
            icons = ["📂", "➕", "✏️"]
            if user['admin']: opcoes.append("Admin"); icons.append("⚙️")
            opcoes_fmt = [f"{icons[i]} {opcoes[i]}" for i in range(len(opcoes))]
            page_sel = st.radio("Navegação", options=opcoes_fmt, horizontal=True, label_visibility="collapsed")
            page = opcoes[opcoes_fmt.index(page_sel)]
        with c_nav_user:
            c_u_text, c_u_btn = st.columns([2, 1])
            with c_u_text: st.markdown(f"<div style='text-align:right; font-size:0.85rem; color:#64748B; margin-top:5px;'>Olá, <b>{user['username']}</b></div>", unsafe_allow_html=True)
            with c_u_btn:
                if st.button("Sair", key="btn_logout"):
                    cookie_manager.delete("gupy_user_token")
                    st.session_state["usuario_logado"] = None
                    st.rerun()
    st.markdown("---") 

    if user.get('trocar_senha'):
        st.warning("⚠️ Segurança: Sua senha precisa ser redefinida.")
        with st.form("new_pass"):
            n1 = st.text_input("Nova Senha", type="password"); n2 = st.text_input("Confirmar Senha", type="password")
            if st.form_submit_button("Atualizar Senha", type="primary"):
                if n1 == n2 and len(n1) > 3:
                    supabase.table("usuarios").update({"senha":n1, "trocar_senha":False}).eq("id", user['id']).execute()
                    user['trocar_senha'] = False; st.success("Senha atualizada!"); time.sleep(1); st.rerun()
                else: st.error("Senhas inválidas.")
    else:
        # PÁGINA: BIBLIOTECA
        if page == "Biblioteca":
            st.subheader("Biblioteca de Frases")
            with st.container(border=True):
                c_search, c_filter = st.columns([3, 1], vertical_alignment="bottom")
                termo = c_search.text_input("Pesquisa Inteligente", placeholder="🔎 Busque por empresa, motivo ou conteúdo...", label_visibility="collapsed")
                filtro_empresa = c_filter.selectbox("Filtrar Empresa", ["Todas"] + sorted(list(set(d['empresa'] for d in dados_totais))))

            filtrados = dados_totais
            if filtro_empresa != "Todas": filtrados = [f for f in filtrados if f['empresa'] == filtro_empresa]
            if termo: filtrados = [f for f in filtrados if termo.lower() in str(f).lower()]

            st.markdown(f"**Resultados:** {len(filtrados)}")
            if not filtrados: st.info("Nenhum resultado encontrado.")
            else:
                for i in range(0, len(filtrados), 2):
                    row_c1, row_c2 = st.columns(2)
                    f1 = filtrados[i]
                    author1 = f1.get('revisado_por', 'Sistema')
                    date1 = f1.get('data_revisao', '')
                    with row_c1:
                        st.markdown(f"""
                        <div class="frase-header">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                                <h4 style="margin:0; color:#1E3A8A;">{f1['empresa']}</h4>
                                <span class="badge badge-blue">{f1['documento']}</span>
                            </div>
                            <div style="color:#64748B; font-size:0.9rem;"><strong>Motivo:</strong> {f1['motivo']}</div>
                            <div class="card-meta"><span>👤 {author1}</span><span>📅 {date1}</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.code(f1['conteudo'], language="text")

                    if i + 1 < len(filtrados):
                        f2 = filtrados[i+1]
                        author2 = f2.get('revisado_por', 'Sistema')
                        date2 = f2.get('data_revisao', '')
                        with row_c2:
                            st.markdown(f"""
                            <div class="frase-header">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                                    <h4 style="margin:0; color:#1E3A8A;">{f2['empresa']}</h4>
                                    <span class="badge badge-blue">{f2['documento']}</span>
                                </div>
                                <div style="color:#64748B; font-size:0.9rem;"><strong>Motivo:</strong> {f2['motivo']}</div>
                                <div class="card-meta"><span>👤 {author2}</span><span>📅 {date2}</span></div>
                            </div>
                            """, unsafe_allow_html=True)
                            st.code(f2['conteudo'], language="text")
                    st.write("")

        # PÁGINA: ADICIONAR
        elif page == "Adicionar":
            st.markdown("### Adicionar Novas Frases")
            tab_man, tab_imp = st.tabs(["✍️ Manual", "📥 Importação em Massa"])
            with tab_man:
                with st.form("add_single"):
                    c1, c2 = st.columns(2)
                    ne = c1.text_input("Empresa Solicitante"); nd = c2.text_input("Tipo de Documento")
                    nm = st.text_input("Motivo da Recusa"); nc = st.text_area("Texto da Frase (Conteúdo)", height=120)
                    if st.form_submit_button("Salvar Registro", type="primary", use_container_width=True):
                        if ne and nd and nm and nc:
                            ne, nd, nm = padronizar(ne), padronizar(nd), padronizar(nm); nc = padronizar(nc, "frase")
                            if [d for d in dados_totais if d['conteudo'] == nc]: st.error("Frase já existe.")
                            else:
                                supabase.table("frases").insert({
                                    "empresa":ne, "documento":nd, "motivo":nm, "conteudo":nc, 
                                    "revisado_por":user['username'], "data_revisao":datetime.now().strftime('%Y-%m-%d')
                                }).execute()
                                registrar_log(user['username'], "Criou Frase", f"{ne}-{nm}"); st.toast("✅ Salvo!"); time.sleep(1); st.cache_data.clear(); st.rerun()
                        else: st.warning("Preencha todos os campos.")
            
            with tab_imp:
                st.info("Colunas sugeridas: Empresa, Documento, Motivo, Conteudo, Revisado Por.")
                upl = st.file_uploader("Arquivo", type=['csv','xlsx'])
                if upl and st.button("Processar Arquivo", type="primary"):
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
                            novos = []; db_conteudos = set(d['conteudo'] for d in dados_totais)
                            for _, row in df.iterrows():
                                cont = padronizar(str(row['conteudo']), 'frase')
                                if cont and cont not in db_conteudos:
                                    autor_final = user['username']
                                    if 'revisado_por' in df.columns and pd.notna(row['revisado_por']):
                                        val = str(row['revisado_por']).strip()
                                        if val: autor_final = val
                                    
                                    novos.append({
                                        "empresa": padronizar(str(row['empresa'])), "documento": padronizar(str(row['documento'])), 
                                        "motivo": padronizar(str(row['motivo'])), "conteudo": cont, 
                                        "revisado_por": autor_final, "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                    })
                                    db_conteudos.add(cont)
                            if novos: 
                                supabase.table("frases").insert(novos).execute()
                                registrar_log(user['username'], "Importação", f"{len(novos)}")
                                st.success(f"{len(novos)} importados!"); st.cache_data.clear()
                            else: st.warning("Nenhuma frase nova.")
                    except Exception as e: st.error(f"Erro: {e}")

        # PÁGINA: MANUTENÇÃO
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
                            ne = c1.text_input("Empresa", item['empresa']); nd = c2.text_input("Documento", item['documento']); nm = c3.text_input("Motivo", item['motivo'])
                            nc = st.text_area("Conteúdo", item['conteudo'])
                            c_auth, c_date = st.columns(2)
                            na = c_auth.text_input("Autor/Revisor", item.get('revisado_por', user['username']))
                            c_s, c_d = st.columns([4, 1])
                            if c_s.form_submit_button("💾 Salvar", type="primary"):
                                supabase.table("frases").update({
                                    "empresa": ne, "documento": nd, "motivo": nm, "conteudo": nc, 
                                    "revisado_por": na, "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                }).eq("id", item['id']).execute()
                                registrar_log(user['username'], "Edição", str(item['id'])); st.toast("Salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                            if c_d.form_submit_button("🗑️ Excluir"):
                                supabase.table("frases").delete().eq("id", item['id']).execute()
                                registrar_log(user['username'], "Exclusão", str(item['id'])); st.toast("Excluído."); st.cache_data.clear(); time.sleep(1); st.rerun()

        # PÁGINA: ADMIN
        elif page == "Admin" and user['admin']:
            st.markdown("### Painel Administrativo")
            tab_users, tab_logs = st.tabs(["👥 Usuários", "🔒 Logs & Dados"])
            with tab_users:
                with st.expander("➕ Criar Novo Usuário", expanded=False):
                    with st.form("new_user"):
                        c_nu, c_ns, c_na = st.columns([2, 2, 1])
                        nu = c_nu.text_input("Username"); ns = c_ns.text_input("Senha Inicial", type="password"); na = c_na.checkbox("É Admin?", value=False)
                        if st.form_submit_button("Criar Usuário"):
                            try: supabase.table("usuarios").insert({"username":nu, "senha":ns, "admin":na, "trocar_senha":True}).execute(); registrar_log(user['username'], "Criou Usuário", nu); st.success(f"Usuário {nu} criado!"); time.sleep(1); st.rerun()
                            except: st.error("Erro ao criar.")
                st.write("---"); st.subheader("Gerenciar Usuários")
                lista_usuarios = buscar_usuarios()
                for u in lista_usuarios:
                    role_label = "👑 Admin" if u['admin'] else "👤 User"
                    with st.expander(f"{role_label} | {u['username']}"):
                        with st.form(key=f"edit_u_{u['id']}"):
                            st.write("**Editar Permissões**")
                            c_edit_1, c_edit_2 = st.columns(2)
                            new_username = c_edit_1.text_input("Username", value=u['username'])
                            disabled_admin = (u['id'] == user['id'])
                            new_admin = c_edit_2.checkbox("Admin", value=u['admin'], disabled=disabled_admin)
                            st.write("---")
                            c_act_1, c_act_2, c_act_3 = st.columns([1, 1, 1])
                            if c_act_1.form_submit_button("💾 Salvar", type="primary"):
                                supabase.table("usuarios").update({"username": new_username, "admin": new_admin}).eq("id", u['id']).execute()
                                registrar_log(user['username'], "Editou Usuário", u['username']); st.toast("Atualizado!"); time.sleep(1); st.rerun()
                            if c_act_2.form_submit_button("🔄 Reset Senha"): supabase.table("usuarios").update({"trocar_senha": True}).eq("id", u['id']).execute(); st.toast("Resetado!")
                            if u['username'] != user['username']:
                                if c_act_3.form_submit_button("🗑️ Excluir"): supabase.table("usuarios").delete().eq("id", u['id']).execute(); registrar_log(user['username'], "Excluiu Usuário", u['username']); st.rerun()
                            else: c_act_3.write("") 
            with tab_logs:
                logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(100).execute().data
                if logs: st.dataframe(pd.DataFrame(logs)[['data_hora', 'usuario', 'acao', 'detalhe']], use_container_width=True, hide_index=True)
                st.write("---")
                
                # ZONA DE PERIGO (APAGAR TUDO)
                with st.expander("🚨 Zona de Perigo (Apagar Tudo)", expanded=False):
                    st.warning("⚠️ CUIDADO: Esta ação apagará TODAS as frases do banco de dados. Não é possível desfazer.")
                    chk = st.text_input("Para confirmar, digite: QUERO APAGAR TUDO")
                    if st.button("🗑️ APAGAR TODA A BIBLIOTECA", type="primary", use_container_width=True):
                        if chk == "QUERO APAGAR TUDO":
                            try:
                                supabase.table("frases").delete().neq("id", 0).execute()
                                registrar_log(user['username'], "LIMPEZA TOTAL", "Apagou todas as frases")
                                st.success("Banco de dados limpo com sucesso!")
                                time.sleep(2); st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(f"Erro ao apagar: {e}")
                        else: st.error("Texto de confirmação incorreto.")
                
                st.write("---"); st.download_button("📥 Backup CSV", data=pd.DataFrame(dados_totais).to_csv(index=False).encode('utf-8'), file_name="backup.csv", mime="text/csv")

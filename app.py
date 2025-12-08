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
# 🖼️ IMAGENS
# ==============================================================================
FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"
# ==============================================================================

# --- CARREGAR FAVICON ---
favicon = "💙" 
try:
    response = requests.get(FAVICON_URL, timeout=3)
    if response.status_code == 200:
        favicon = Image.open(io.BytesIO(response.content))
except: pass

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Frases de Recusa - Gupy", page_icon=favicon, layout="wide")

# ==============================================================================
# 🎨 CSS PROFISSIONAL (CORES, DETALHES E LAYOUT)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    /* Fundo geral da aplicação (um cinza azulado sutil para contraste) */
    .stApp { 
        background-color: #F3F6F9; 
    }
    
    /* ESCONDER ITENS PADRÃO */
    [data-testid="stHeader"], [data-testid="stSidebar"], footer { display: none; }
    
    /* AJUSTE DO TOPO */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100%;
    }

    /* =======================
       ESTILO DA COLUNA DO MENU LATERAL (ESQUERDA)
    ======================= */
    div[data-testid="column"]:nth-of-type(1) {
        /* Gradiente Gupy Profundo */
        background: linear-gradient(160deg, #00122F 0%, #0A2347 100%);
        padding: 2rem 1.5rem;
        min-height: 95vh;
        border-radius: 0 16px 16px 0; /* Bordas arredondadas apenas na direita */
        box-shadow: 5px 0 15px rgba(0,0,0,0.1); /* Sombra para dar profundidade */
        color: white;
        display: flex;
        flex-direction: column;
    }
    
    /* Força textos dentro do menu a serem brancos */
    div[data-testid="column"]:nth-of-type(1) * {
        color: white !important;
    }
    
    /* Separadores mais sutis */
    div[data-testid="column"]:nth-of-type(1) hr {
        border-color: rgba(255,255,255,0.15) !important;
    }

    /* --- ESTILO DOS LINKS DO MENU (RADIO BUTTONS MELHORADOS) --- */
    .stRadio > div { background-color: transparent; }
    
    .stRadio label { 
        color: rgba(255,255,255,0.8) !important; 
        font-size: 0.95rem;
        font-weight: 500;
        padding: 12px 15px;
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        cursor: pointer;
    }
    
    /* Efeito Hover (passar o mouse) */
    .stRadio label:hover {
        background-color: rgba(255,255,255,0.1);
        color: white !important;
        transform: translateX(5px); /* Pequeno movimento para direita */
    }
    
    /* Item Selecionado (Ativo) */
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #2175D9 !important; /* Azul Gupy Vibrante */
        color: white !important;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(33, 117, 217, 0.3);
    }
    .stRadio div[role="radiogroup"] > label > div:first-child { display: none; } /* Esconde bolinha */

    /* Botão de Sair (Estilo diferente) */
    div[data-testid="column"]:nth-of-type(1) .stButton > button {
        background-color: transparent;
        border: 1px solid rgba(255,255,255,0.3);
        color: rgba(255,255,255,0.8) !important;
    }
    div[data-testid="column"]:nth-of-type(1) .stButton > button:hover {
         background-color: rgba(255, 50, 50, 0.2); /* Avermelhado ao passar o mouse */
         border-color: rgba(255, 50, 50, 0.5);
         color: white !important;
    }

    /* =======================
       ESTILO DO CONTEÚDO (DIREITA)
    ======================= */
    div[data-testid="column"]:nth-of-type(2) {
        padding-top: 2rem;
        padding-left: 2rem;
    }

    /* BOTÕES GERAIS (Primary) */
    .stButton > button {
        border-radius: 8px; font-weight: 600; border: none;
        background: linear-gradient(90deg, #2175D9 0%, #175BB5 100%); /* Gradiente sutil no botão */
        color: white;
        box-shadow: 0 2px 6px rgba(33, 117, 217, 0.25);
        transition: all 0.2s;
    }
    .stButton > button:hover { box-shadow: 0 4px 12px rgba(33, 117, 217, 0.4); transform: translateY(-1px); }
    .stButton > button:active { transform: scale(0.98); }

    /* Botão de Perigo (Delete) - Seletor mais específico */
    button[kind="primary"] {
        background: #EF4444 !important; /* Vermelho */
        box-shadow: 0 2px 6px rgba(239, 68, 68, 0.25) !important;
    }
    button[kind="primary"]:hover { background: #DC2626 !important; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important; }

    /* CARTÕES E CONTAINERS */
    /* Dá uma sombra mais suave e bordas mais arredondadas para os cartões brancos */
    .card-container, div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background: #FFFFFF; 
        border: 0px solid #E2E8F0; /* Remove borda dura */
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05); /* Sombra suave e difusa */
        padding: 24px !important;
    }
    
    /* Inputs com visual mais limpo */
    .stTextInput input, .stTextArea textarea {
        border-radius: 8px; border: 1px solid #DCE1E7; background-color: #F8FAFC;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2175D9; box-shadow: 0 0 0 3px rgba(33, 117, 217, 0.15); background-color: #FFF;
    }
    
    .logo-text { font-size: 2.5rem; font-weight: 800; color: #2175D9; text-align: center; letter-spacing: -1.5px; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES BACKEND (MANTIDAS) ---
try:
    url_db = st.secrets["SUPABASE_URL"]; key_db = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url_db, key_db)
except: st.stop()

def verificar_login(u, s):
    try: res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute(); return res.data[0] if res.data else None
    except: return None
def buscar_dados(): return supabase.table("frases").select("*").order("id", desc=True).execute().data
def buscar_usuarios(): return supabase.table("usuarios").select("*").order("id").execute().data
def registrar_log(usuario, acao, detalhe):
    try: supabase.table("logs").insert({"usuario":usuario,"acao":acao,"detalhe":detalhe,"data_hora":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
    except: pass
def padronizar(texto, tipo="titulo"):
    if not texto: return ""; texto = str(texto).strip()
    return texto.title() if tipo == "titulo" else (texto[0].upper() + texto[1:])
def limpar_coluna(col):
    col = str(col).lower().strip(); return ''.join(c for c in unicodedata.normalize('NFD', col) if unicodedata.category(c) != 'Mn')

# ==============================================================================
# 📱 FRONTEND
# ==============================================================================
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

# --- TELA DE LOGIN (Visual Melhorado) ---
if st.session_state["usuario_logado"] is None:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write(""); st.write(""); st.write("")
        with st.container(border=True):
            if LOGO_URL: 
                cl, cm, cr = st.columns([1, 2, 1])
                with cm: st.image(LOGO_URL, use_container_width=True)
            else: st.markdown("<h1 class='logo-text'>gupy</h1>", unsafe_allow_html=True)
            
            st.markdown("<h3 style='text-align:center; color:#475569; font-weight: 600; margin-bottom: 25px;'>Frases de Recusa</h3>", unsafe_allow_html=True)
            with st.form("login"):
                u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
                st.write("")
                if st.form_submit_button("Acessar Plataforma", use_container_width=True):
                    user = verificar_login(u, s)
                    if user: st.session_state["usuario_logado"] = user; st.rerun()
                    else: st.error("Credenciais inválidas.")

# --- ÁREA LOGADA (LAYOUT PREMIUM) ---
else:
    user = st.session_state["usuario_logado"]
    
    # Proporção [1, 5] com espaçamento grande entre colunas
    col_menu, col_content = st.columns([1, 5], gap="large")
    
    # === MENU LATERAL DETALHADO ===
    with col_menu:
        st.write("")
        if LOGO_URL: st.image(LOGO_URL, use_container_width=True)
        else: st.markdown("## gupy.")
        st.write(""); st.write("") # Espaço extra

        # --- Perfil Visual ---
        # Usando HTML para criar um bloco de perfil bonito
        st.markdown(f"""
            <div style="display: flex; align-items: center; background: rgba(255,255,255,0.1); padding: 12px; border-radius: 12px; margin-bottom: 20px;">
                <div style="width: 40px; height: 40px; background: #2175D9; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 1.2rem; margin-right: 12px;">
                    {user['username'][0].upper()}
                </div>
                <div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">Bem-vindo(a),</div>
                    <div style="font-weight: 600; font-size: 1.1rem;">{user['username']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.markdown("<span style='font-size:0.75rem; font-weight:600; letter-spacing:1px; opacity:0.6'>MENU PRINCIPAL</span>", unsafe_allow_html=True)

        # Navegação com Ícones (Emojis)
        opcoes = ["📂  Biblioteca de Frases", "📝  Gestão & Criação", "⚙️  Administração"] if user['admin'] else ["📂  Biblioteca de Frases", "📝  Gestão & Criação"]
        page = st.radio("Navegação", opcoes, label_visibility="collapsed")
        
        # Espaço flexível para empurrar o botão de sair para baixo
        st.write(""); st.write(""); st.write(""); st.write(""); 

        st.divider()
        if st.button("← Sair da Conta", use_container_width=True): 
            st.session_state["usuario_logado"] = None; st.rerun()

    # === CONTEÚDO PRINCIPAL ===
    with col_content:
        # Validação de Senha (Mantida, mas dentro de um card bonito)
        if user.get('trocar_senha'):
             with st.container(border=True):
                st.warning("⚠️ Segurança: Você precisa redefinir sua senha."); n1=st.text_input("Nova Senha", type="password"); n2=st.text_input("Confirmar Senha", type="password")
                if st.button("Atualizar Senha"): 
                    if n1==n2 and n1: supabase.table("usuarios").update({"senha":n1,"trocar_senha":False}).eq("id",user['id']).execute(); user['trocar_senha']=False; st.toast("Senha atualizada!"); time.sleep(1); st.rerun()
        else:
            # --- PÁGINA 1: BIBLIOTECA (Com Badges Coloridos) ---
            if "📂" in page:
                c_tit, c_search = st.columns([1.5, 2])
                with c_tit: st.title("Biblioteca de Frases")
                with c_search:
                    st.write("")
                    termo = st.text_input("Busca", placeholder="🔎 Pesquisar por empresa, motivo...", label_visibility="collapsed")
                
                dados = buscar_dados()
                filtrados = [f for f in dados if termo.lower() in str(f).lower()] if termo else dados
                st.markdown(f"<span style='color:#64748B; font-size:0.9rem'>Mostrando **{len(filtrados)}** resultados</span>", unsafe_allow_html=True)
                
                for f in filtrados:
                    with st.container(border=True):
                        ci, cc = st.columns([1.3, 3])
                        with ci:
                            st.subheader(f['empresa'])
                            # Usando Badges HTML para detalhes
                            st.markdown(f"""
                                <div style='margin-top:10px;'>
                                    <span style='background:#E0F2FE; color:#0369A1; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 500;'>📄 {f['documento']}</span>
                                </div>
                                <div style='margin-top:8px; font-weight:500; color:#475569'>📌 {f['motivo']}</div>
                            """, unsafe_allow_html=True)

                            if f.get('revisado_por'): 
                                try: dt = datetime.strptime(f['data_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y'); 
                                # Badge Verde para Revisado
                                st.markdown(f"<div style='margin-top:12px;'><span style='background:#DCFCE7; color:#15803D; padding: 4px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'>✔ Revisado por {f['revisado_por']} em {dt}</span></div>", unsafe_allow_html=True)
                                except: pass
                        with cc: st.code(f['conteudo'], language="text")

            # --- PÁGINA 2: GESTÃO (Com Tabs mais bonitas) ---
            elif "📝" in page:
                st.title("Gestão & Criação")
                # Tabs do Streamlit já são bonitas, vão se adaptar ao tema
                t_add, t_manage = st.tabs(["➕ Cadastrar Nova", "✏️ Gerenciar Existentes"])
                
                with t_add:
                    with st.container(border=True):
                        st.subheader("Nova Frase")
                        with st.form("quick_add", border=False): # Remove borda interna do form
                            c1, c2, c3 = st.columns(3)
                            ne = c1.text_input("Empresa"); nd = c2.text_input("Documento"); nm = c3.text_input("Motivo")
                            nc = st.text_area("Conteúdo da Frase", height=120, placeholder="Escreva a frase de recusa aqui...")
                            st.write("")
                            if st.form_submit_button("💾 Salvar Registro", use_container_width=True):
                                if nc:
                                    ne,nd,nm = padronizar(ne),padronizar(nd),padronizar(nm); nc = padronizar(nc,"frase")
                                    if len(supabase.table("frases").select("id").eq("conteudo", nc).execute().data) > 0: st.error("Frase já existente.")
                                    else:
                                        supabase.table("frases").insert({"empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).execute()
                                        registrar_log(user['username'], "Criou Frase", f"{ne}-{nm}"); st.success("Salvo com sucesso!"); time.sleep(1); st.rerun()
                
                with t_manage:
                    cs, cu = st.columns([2, 1])
                    q = cs.text_input("🔎 Buscar para editar...", placeholder="Digite para filtrar...")
                    with cu:
                         with st.popover("📂 Importação em Massa (CSV/Excel)", use_container_width=True):
                            upl = st.file_uploader("Carregar arquivo", type=['csv','xlsx'])
                            if upl and st.button("Iniciar Processamento", use_container_width=True):
                                # Lógica de Importação Mantida (Funcional)
                                try:
                                    if upl.name.endswith('.csv'):
                                        try: df = pd.read_csv(upl); 
                                        except: df = pd.read_csv(upl, encoding='latin-1', sep=';')
                                    else: df = pd.read_excel(upl)
                                    header_idx = -1; keywords = ['empresa', 'conteudo', 'frase', 'motivo']
                                    for i, row in df.head(50).iterrows():
                                        row_str = " ".join([str(val).lower() for val in row.values])
                                        if sum(1 for k in keywords if k in row_str) >= 2: header_idx = i; break
                                    if header_idx > -1:
                                        if header_idx > 0:
                                            if upl.name.endswith('.csv'): upl.seek(0); df = pd.read_csv(upl, header=header_idx, encoding='latin-1', sep=None, engine='python')
                                            else: upl.seek(0); df = pd.read_excel(upl, header=header_idx)
                                    df.columns = [limpar_coluna(c) for c in df.columns]
                                    mapa = {'empresa solicitante':'empresa','cliente':'empresa','tipo documento':'documento','doc':'documento','motivo recusa':'motivo','motivo da recusa':'motivo','justificativa':'motivo','frase':'conteudo','texto':'conteudo','mensagem':'conteudo','frase de recusa':'conteudo','revisado por':'revisado_por','revisor':'revisado_por','validado por':'revisado_por','data':'data_revisao','data revisao':'data_revisao','data da revisao':'data_revisao'}
                                    df.rename(columns=mapa, inplace=True)
                                    cols = ['empresa','documento','motivo','conteudo']
                                    if not all(c in df.columns for c in cols): st.error("Colunas obrigatórias ausentes.")
                                    else:
                                        novos=[]; db_set=set([str(f['conteudo']).strip() for f in buscar_dados()])
                                        for _, r in df.iterrows():
                                            if pd.isna(r['conteudo']) or str(r['conteudo']).strip()=="": continue
                                            emp=padronizar(str(r['empresa'])); doc=padronizar(str(r['documento'])); mot=padronizar(str(r['motivo'])); cont=padronizar(str(r['conteudo']),'frase')
                                            rev_por=user['username']; rev_data=datetime.now().strftime('%Y-%m-%d')
                                            if 'revisado_por' in df.columns and pd.notna(r['revisado_por']): rev_por=str(r['revisado_por'])
                                            if 'data_revisao' in df.columns and pd.notna(r['data_revisao']):
                                                try: val=r['data_revisao']; rev_data=val.strftime('%Y-%m-%d') if isinstance(val,datetime) else str(val).split('T')[0]
                                                except: pass
                                            if cont not in db_set: novos.append({'empresa':emp,'documento':doc,'motivo':mot,'conteudo':cont,'revisado_por':rev_por,'data_revisao':rev_data}); db_set.add(cont)
                                        if novos: supabase.table("frases").insert(novos).execute(); registrar_log(user['username'],"Import",f"{len(novos)}"); st.success(f"{len(novos)} itens importados!"); time.sleep(2); st.rerun()
                                        else: st.warning("Nenhuma frase nova.")
                                except Exception as e: st.error(f"Erro: {e}")

                    dados = buscar_dados(); lista = [f for f in dados if q.lower() in str(f).lower()] if q else dados
                    st.markdown(f"<span style='color:#64748B; font-size:0.9rem'>Encontrados **{len(lista)}** registros</span>", unsafe_allow_html=True)
                    for f in lista:
                        with st.expander(f"🏢 {f['empresa']} | 📌 {f['motivo']}"):
                            with st.form(f"ed_{f['id']}"):
                                c_a, c_b = st.columns(2)
                                fe = c_a.text_input("Empresa", f['empresa']); fd = c_b.text_input("Documento", f['documento'])
                                fm = st.text_input("Motivo", f['motivo']); fc = st.text_area("Conteúdo", f['conteudo'], height=100)
                                cs, cd = st.columns([4, 1])
                                if cs.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                                    supabase.table("frases").update({"empresa":padronizar(fe),"documento":padronizar(fd),"motivo":padronizar(fm),"conteudo":padronizar(fc,"frase"),"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).eq("id", f['id']).execute()
                                    registrar_log(user['username'], "Edit", str(f['id'])); st.rerun()
                                # Botão de excluir vermelho (kind="primary" ativa o CSS vermelho)
                                if cd.form_submit_button("🗑️ Excluir", type="primary", use_container_width=True):
                                    supabase.table("frases").delete().eq("id", f['id']).execute()
                                    registrar_log(user['username'], "Delete", str(f['id'])); st.rerun()

            # --- 3. ADMIN ---
            elif "⚙️" in page and user['admin']:
                st.title("Administração do Sistema")
                t1, t2 = st.tabs(["👥 Gestão de Usuários", "🛡️ Auditoria & Segurança"])
                with t1:
                    c_new, c_list = st.columns([1, 2])
                    with c_new:
                        with st.container(border=True):
                            st.subheader("Novo Usuário")
                            nu = st.text_input("Nome"); ns = st.text_input("Senha", type="password"); na = st.checkbox("Privilégios de Admin")
                            if st.button("Criar Usuário", use_container_width=True):
                                supabase.table("usuarios").insert({"username":nu,"senha":ns,"admin":na,"trocar_senha":True}).execute()
                                registrar_log(user['username'], "New User", nu); st.success("Criado!"); time.sleep(1); st.rerun()
                    with c_list:
                        st.subheader("Usuários Ativos")
                        for u in buscar_usuarios():
                            with st.expander(f"{u['username']} {'(Admin)' if u['admin'] else ''}"):
                                c_x, c_y = st.columns(2)
                                if c_x.button("Forçar Redefinição de Senha", key=f"r{u['id']}", use_container_width=True): supabase.table("usuarios").update({"trocar_senha":True}).eq("id", u['id']).execute(); st.toast("Solicitação enviada!")
                                if u['username']!=user['username'] and c_y.button("Excluir Usuário", key=f"d{u['id']}", type="primary", use_container_width=True): supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()
                with t2:
                    st.subheader("Logs de Atividade Recente")
                    logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(50).execute().data
                    if logs: st.dataframe(pd.DataFrame(logs)[['data_hora','usuario','acao','detalhe']], use_container_width=True, height=300)
                    st.divider()
                    c_bkp, c_danger = st.columns(2)
                    with c_bkp:
                        st.subheader("Backup de Dados")
                        full = buscar_dados()
                        if full: st.download_button("📥 Baixar CSV Completo", pd.DataFrame(full).to_csv(index=False).encode('utf-8'), f"backup_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)
                    with c_danger:
                         with st.container(border=True):
                            st.subheader("Zona de Perigo")
                            st.error("Ações destrutivas. Cuidado.")
                            chk = st.text_input("Para apagar TUDO, digite: QUERO APAGAR TUDO")
                            if st.button("LIMPAR BANCO DE DADOS", type="primary", use_container_width=True) and chk=="QUERO APAGAR TUDO":
                                supabase.table("frases").delete().neq("id", 0).execute()
                                registrar_log(user['username'], "WIPE", "ALL"); st.rerun()

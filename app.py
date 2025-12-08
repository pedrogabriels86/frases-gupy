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
# 🎨 CSS PROFISSIONAL (MENU MODERNO & LAYOUT)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F5F7FA; } /* Fundo geral claro */
    
    /* --- ESCONDER BARRA NATIVA DO STREAMLIT --- */
    [data-testid="stHeader"] { display: none; }
    footer { display: none; }
    
    /* Ajuste fino do espaçamento global */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 100%;
    }

    /* ========================================================================
       ESTILO DA COLUNA ESQUERDA (MENU LATERAL CUSTOMIZADO)
    ======================================================================== */
    /* Seleciona a primeira coluna do layout principal */
    div[data-testid="column"]:nth-of-type(1) {
        background: linear-gradient(180deg, #0A192F 0%, #00122F 100%); /* Gradiente profundo */
        padding: 32px 24px; /* Mais espaço interno */
        border-radius: 16px;
        box-shadow: 4px 0 24px rgba(0,0,0,0.08); /* Sombra suave para profundidade */
        color: white;
        min-height: 92vh; /* Ocupa quase toda a altura */
        display: flex;
        flex-direction: column;
        justify-content: space-between; /* Empurra o botão sair para baixo */
    }
    
    /* Força textos dentro do menu a serem brancos */
    div[data-testid="column"]:nth-of-type(1) h1,
    div[data-testid="column"]:nth-of-type(1) h2,
    div[data-testid="column"]:nth-of-type(1) h3,
    div[data-testid="column"]:nth-of-type(1) p,
    div[data-testid="column"]:nth-of-type(1) span,
    div[data-testid="column"]:nth-of-type(1) div {
        color: white !important;
    }
    
    /* Separador (Divider) mais sutil */
    div[data-testid="column"]:nth-of-type(1) hr {
        border-color: rgba(255,255,255,0.1) !important;
    }

    /* --- ESTILIZAÇÃO AVANÇADA DOS LINKS DE NAVEGAÇÃO (ST.RADIO) --- */
    /* 1. Esconde as bolinhas do rádio */
    .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    
    /* 2. Estilo base do link (inativo) */
    .stRadio label {
        padding: 14px 18px !important;
        margin-bottom: 10px !important;
        border-radius: 10px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important; /* Animação suave */
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        color: rgba(255,255,255,0.65) !important; /* Cor texto inativo (mais apagado) */
        border: 1px solid transparent;
        cursor: pointer;
        display: flex;
        align-items: center;
    }

    /* 3. Estado Hover (Passar o mouse) */
    .stRadio label:hover {
        background-color: rgba(255,255,255,0.08) !important; /* Fundo claro sutil */
        color: white !important;
        transform: translateX(4px); /* Leve movimento para direita */
    }

    /* 4. Estado Ativo (Página Selecionada) - O PULO DO GATO */
    /* O Streamlit adiciona data-checked="true" no label selecionado */
    .stRadio label[data-checked="true"] {
         background-color: #2175D9 !important; /* Azul Gupy vibrante */
         color: white !important;
         font-weight: 600 !important;
         box-shadow: 0 4px 12px rgba(33, 117, 217, 0.3); /* Brilho azul */
    }

    /* --- DEMAIS ESTILOS DO APP (Conteúdo Principal) --- */
    .logo-text { font-size: 2rem; font-weight: 800; color: #2175D9; text-align: center; }

    /* Botões (Exceto os do menu lateral que tratamos acima) */
    div[data-testid="column"]:nth-of-type(2) .stButton > button {
        border-radius: 6px; font-weight: 600; border: none;
        transition: transform 0.1s;
        background-color: #2175D9; color: white;
    }
    div[data-testid="column"]:nth-of-type(2) .stButton > button:hover { background-color: #175BB5; }
    div[data-testid="column"]:nth-of-type(2) .stButton > button:active { transform: scale(0.98); }
    
    /* Botão Sair (no menu lateral) - Estilo diferente */
    div[data-testid="column"]:nth-of-type(1) .stButton > button {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.8) !important;
        font-weight: 500;
    }
    div[data-testid="column"]:nth-of-type(1) .stButton > button:hover {
        background-color: rgba(255, 50, 50, 0.15);
        border-color: rgba(255, 50, 50, 0.3);
        color: white !important;
    }

    /* Cartões e Inputs do Conteúdo */
    .card-container, div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background: white; border: 1px solid #E2E8F0; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04); padding: 20px !important;
    }
    .stTextInput input, .stTextArea textarea { border-radius: 6px; border: 1px solid #CBD5E0; }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color: #2175D9; box-shadow: 0 0 0 2px rgba(33, 117, 217, 0.2); }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO & FUNÇÕES BACKEND ---
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
# 📱 FRONTEND DO APLICATIVO
# ==============================================================================
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

# --- TELA DE LOGIN ---
if st.session_state["usuario_logado"] is None:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write(""); st.write(""); st.write("")
        with st.container(border=True):
            if LOGO_URL: 
                cl, cm, cr = st.columns([1, 2, 1]) # Centraliza logo
                with cm: st.image(LOGO_URL, use_container_width=True)
            else: st.markdown("<h1 class='logo-text'>gupy</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center; color:#555; margin-bottom:25px;'>Frases de Recusa</h3>", unsafe_allow_html=True)
            with st.form("login"):
                u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
                st.write("")
                if st.form_submit_button("Entrar na Plataforma", use_container_width=True):
                    user = verificar_login(u, s)
                    if user: st.session_state["usuario_logado"] = user; st.rerun()
                    else: st.error("Credenciais inválidas.")

# --- ÁREA LOGADA (LAYOUT DE DUAS COLUNAS) ---
else:
    user = st.session_state["usuario_logado"]
    
    # Define as proporções: Menu (1.3) e Conteúdo (5)
    col_menu, col_content = st.columns([1.3, 5], gap="large")
    
    # =======================
    # 🟦 COLUNA 1: MENU LATERAL PROFISSIONAL
    # =======================
    with col_menu:
        # 1. Logo (com espaçamento adequado)
        st.write("")
        if LOGO_URL: 
            c_logo_l, c_logo_m, c_logo_r = st.columns([0.1, 0.8, 0.1])
            with c_logo_m: st.image(LOGO_URL, use_container_width=True)
        else: st.markdown("## gupy.")
        st.write(""); st.write("") # Espaço

        # 2. Perfil do Usuário Moderno (Avatar + Nome)
        # Usamos HTML/CSS inline para criar um componente de perfil bonito
        avatar_letter = user['username'][0].upper() if user['username'] else "U"
        st.markdown(f"""
            <div style='display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 12px; margin-bottom: 24px;'>
                <div style='width: 42px; height: 42px; background: linear-gradient(135deg, #2175D9, #175BB5); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.2rem; color: white; box-shadow: 0 2px 8px rgba(33, 117, 217, 0.3);'>
                    {avatar_letter}
                </div>
                <div style='display: flex; flex-direction: column;'>
                    <span style='font-size: 0.75rem; opacity: 0.7; letter-spacing: 0.5px;'>BEM-VINDO(A)</span>
                    <span style='font-weight: 600; font-size: 1.05rem; letter-spacing: -0.5px;'>{user['username']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.markdown("<span style='font-size:0.75rem; opacity:0.5; margin-left:10px;'>MENU PRINCIPAL</span>", unsafe_allow_html=True)

        # 3. Navegação (Estilizada pelo CSS acima)
        # Adicionei emojis para servir como ícones
        opcoes = ["📂  Biblioteca de Frases", "📝  Gestão & Criação", "⚙️  Administração"] if user['admin'] else ["📂  Biblioteca de Frases", "📝  Gestão & Criação"]
        page = st.radio("Navegação", opcoes, label_visibility="collapsed")
        
        # Espaço flexível para empurrar o botão sair para baixo
        st.write(""); st.write(""); st.write(""); 
        
        st.divider()
        # 4. Botão Sair (Estilo mais sutil definido no CSS)
        if st.button("← Desconectar", use_container_width=True): 
            st.session_state["usuario_logado"] = None
            st.rerun()

    # =======================
    # ⬜ COLUNA 2: CONTEÚDO PRINCIPAL
    # =======================
    with col_content:
        st.write("") # Espaço topo
        
        if user.get('trocar_senha'):
             with st.container(border=True):
                st.warning("⚠️ Segurança: Redefina sua senha"); n1=st.text_input("Nova Senha", type="password"); n2=st.text_input("Confirmar Senha", type="password")
                if st.button("Atualizar Senha", type="primary"): 
                    if n1==n2 and n1: supabase.table("usuarios").update({"senha":n1,"trocar_senha":False}).eq("id",user['id']).execute(); user['trocar_senha']=False; st.toast("Senha atualizada!"); time.sleep(1); st.rerun()
        else:
            # --- PÁGINA 1: BIBLIOTECA ---
            if "📂" in page:
                c_tit, c_search = st.columns([1.5, 2])
                with c_tit: st.title("Biblioteca")
                with c_search:
                    st.write("")
                    termo = st.text_input("Busca", placeholder="🔎 Pesquisar frases...", label_visibility="collapsed")
                
                dados = buscar_dados(); filtrados = [f for f in dados if termo.lower() in str(f).lower()] if termo else dados
                st.caption(f"Mostrando {len(filtrados)} frases")
                
                for f in filtrados:
                    with st.container(border=True):
                        ci, cc = st.columns([1.2, 3])
                        with ci:
                            st.markdown(f"#### {f['empresa']}")
                            st.caption(f"📄 {f['documento']} | 📌 {f['motivo']}")
                            if f.get('revisado_por'): 
                                try: dt = datetime.strptime(f['data_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y'); st.markdown(f"<small style='color:#2175D9'>✔ Revisado por {f['revisado_por']} em {dt}</small>", unsafe_allow_html=True)
                                except: pass
                        with cc: st.code(f['conteudo'], language="text")

            # --- PÁGINA 2: GESTÃO ---
            elif "📝" in page:
                st.title("Gestão & Criação")
                t_add, t_manage = st.tabs(["➕ Nova Frase", "✏️ Gerenciar Existentes"])
                
                with t_add:
                     with st.container(border=True):
                        st.subheader("Cadastrar Nova")
                        with st.form("quick_add", border=False):
                            c1, c2, c3 = st.columns(3)
                            ne = c1.text_input("Empresa"); nd = c2.text_input("Documento"); nm = c3.text_input("Motivo")
                            nc = st.text_area("Conteúdo da Frase", height=120, placeholder="Digite a frase completa aqui...")
                            if st.form_submit_button("💾 Salvar Frase", use_container_width=True, type="primary"):
                                if nc:
                                    ne,nd,nm = padronizar(ne),padronizar(nd),padronizar(nm); nc = padronizar(nc,"frase")
                                    if len(supabase.table("frases").select("id").eq("conteudo", nc).execute().data) > 0: st.error("Esta frase já existe.")
                                    else:
                                        supabase.table("frases").insert({"empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).execute()
                                        registrar_log(user['username'], "Criou Frase", f"{ne}-{nm}"); st.success("Frase criada com sucesso!"); time.sleep(1); st.rerun()
                
                with t_manage:
                    cs, cu = st.columns([2, 1])
                    q = cs.text_input("🔎 Buscar para editar...", placeholder="Ex: Nome da empresa ou trecho da frase")
                    with cu:
                        with st.popover("📂 Importar em Massa", use_container_width=True):
                            upl = st.file_uploader("Arraste seu Excel/CSV", type=['csv','xlsx'])
                            if upl and st.button("Iniciar Importação", use_container_width=True):
                                # Lógica de Importação (Mantida)
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
                                    if not all(c in df.columns for c in cols): st.error("Arquivo inválido. Verifique as colunas.")
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
                                        if novos: supabase.table("frases").insert(novos).execute(); registrar_log(user['username'],"Import",f"{len(novos)}"); st.success(f"{len(novos)} frases importadas!"); time.sleep(2); st.rerun()
                                        else: st.warning("Nenhuma frase nova encontrada.")
                                except Exception as e: st.error(f"Erro na importação: {e}")

                    dados = buscar_dados(); lista = [f for f in dados if q.lower() in str(f).lower()] if q else dados
                    st.caption(f"{len(lista)} registros encontrados")
                    for f in lista:
                        with st.expander(f"🏢 {f['empresa']} | 📌 {f['motivo']}"):
                            with st.form(f"ed_{f['id']}"):
                                c_a, c_b = st.columns(2)
                                fe = c_a.text_input("Empresa", f['empresa']); fd = c_b.text_input("Documento", f['documento'])
                                fm = st.text_input("Motivo", f['motivo']); fc = st.text_area("Conteúdo", f['conteudo'], height=100)
                                cs, cd = st.columns([4, 1])
                                if cs.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary"):
                                    supabase.table("frases").update({"empresa":padronizar(fe),"documento":padronizar(fd),"motivo":padronizar(fm),"conteudo":padronizar(fc,"frase"),"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).eq("id", f['id']).execute()
                                    registrar_log(user['username'], "Edit", str(f['id'])); st.rerun()
                                if cd.form_submit_button("🗑️ Excluir", use_container_width=True):
                                    supabase.table("frases").delete().eq("id", f['id']).execute()
                                    registrar_log(user['username'], "Delete", str(f['id'])); st.rerun()

            # --- 3. ADMIN ---
            elif "⚙️" in page and user['admin']:
                st.title("Administração")
                t1, t2 = st.tabs(["👥 Usuários", "🛡️ Auditoria & Dados"])
                with t1:
                    c_new, c_list = st.columns([1, 2])
                    with c_new:
                        with st.container(border=True):
                            st.subheader("Novo Usuário")
                            nu = st.text_input("Nome"); ns = st.text_input("Senha", type="password"); na = st.checkbox("É Admin?")
                            if st.button("Criar Usuário", use_container_width=True, type="primary"):
                                supabase.table("usuarios").insert({"username":nu,"senha":ns,"admin":na,"trocar_senha":True}).execute()
                                registrar_log(user['username'], "New User", nu); st.success("Criado!"); time.sleep(1); st.rerun()
                    with c_list:
                        st.subheader("Usuários Ativos")
                        for u in buscar_usuarios():
                            with st.expander(f"{u['username']} {'(Admin)' if u['admin'] else ''}"):
                                c_x, c_y = st.columns(2)
                                if c_x.button("Forçar Troca de Senha", key=f"r{u['id']}", use_container_width=True): supabase.table("usuarios").update({"trocar_senha":True}).eq("id", u['id']).execute(); st.toast("Solicitação enviada!")
                                if u['username']!=user['username'] and c_y.button("Excluir Usuário", key=f"d{u['id']}", type="primary", use_container_width=True): supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()
                with t2:
                    st.subheader("Logs de Atividade")
                    logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(50).execute().data
                    if logs: st.dataframe(pd.DataFrame(logs)[['data_hora','usuario','acao','detalhe']], use_container_width=True, height=300)
                    st.divider()
                    c_bkp, c_danger = st.columns(2)
                    with c_bkp:
                        st.subheader("Backup")
                        full = buscar_dados()
                        if full: st.download_button("📥 Baixar Todos os Dados (CSV)", pd.DataFrame(full).to_csv(index=False).encode('utf-8'), f"backup_frases_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True, type="primary")
                    with c_danger:
                        st.subheader("Zona de Perigo")
                        with st.popover("⚠️ Apagar Todas as Frases", use_container_width=True):
                            st.error("Ação irreversível!")
                            chk = st.text_input("Digite 'QUERO APAGAR TUDO' para confirmar:")
                            if st.button("CONFIRMAR EXCLUSÃO TOTAL", type="primary", use_container_width=True):
                                if chk=="QUERO APAGAR TUDO":
                                    supabase.table("frases").delete().neq("id", 0).execute()
                                    registrar_log(user['username'], "WIPE", "ALL"); st.rerun()
                                else: st.error("Confirmação incorreta.")

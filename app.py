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
# CONFIGURAÇÃO INICIAL E IMAGENS
# ==============================================================================
FAVICON_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/favicon.png"
LOGO_URL = "https://urmwvabkikftsefztadb.supabase.co/storage/v1/object/public/imagens/logo_gupy.png.png"

# Carrega favicon
favicon = "💙"
try:
    response = requests.get(FAVICON_URL, timeout=2)
    if response.status_code == 200: favicon = Image.open(io.BytesIO(response.content))
except: pass

st.set_page_config(page_title="Frases Gupy", page_icon=favicon, layout="wide")

# ==============================================================================
# CSS CORPORATIVO "CLEAN & CRISP" (SEM DESFOQUE, FOCO NA LEITURA)
# ==============================================================================
st.markdown("""
<style>
    /* Fonte Oficial */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif !important; }
    
    /* Fundo da Página: Cinza muito claro, padrão de sistemas SaaS */
    .stApp { background-color: #F4F5F7; }
    
    /* REMOÇÃO DE ITENS PADRÃO */
    [data-testid="stHeader"] { display: none; }
    footer { display: none; }
    
    /* AJUSTE DO TOPO (Padding) */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }

    /* --- CABEÇALHO PERSONALIZADO --- */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #FFFFFF;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 25px;
        border-left: 5px solid #2175D9;
    }
    .header-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #00122F; /* Azul Midnight */
        margin: 0;
    }
    .header-user {
        font-size: 0.9rem;
        color: #555;
    }

    /* --- ESTILO DAS ABAS (MENU DE NAVEGAÇÃO) --- */
    /* Transforma as abas padrão em um menu limpo */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
        padding-bottom: 10px;
        border-bottom: 1px solid #E0E0E0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        padding: 0 20px;
        font-weight: 600;
        border: 1px solid #EEE;
        color: #555;
    }
    /* Aba Selecionada */
    .stTabs [aria-selected="true"] {
        background-color: #2175D9 !important; /* Azul Gupy */
        color: white !important;
        border: none;
    }

    /* --- CARTÕES DE CONTEÚDO (CARDS) --- */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 20px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03); /* Sombra nítida e leve */
    }

    /* --- BOTÕES --- */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        background-color: #2175D9;
        color: white;
        border: none;
        box-shadow: none;
        height: 42px;
    }
    .stButton > button:hover { background-color: #175BB5; color: white; }
    
    /* Botão Secundário (Ex: Sair) */
    .secondary-btn button {
        background-color: white !important;
        color: #333 !important;
        border: 1px solid #CCC !important;
    }
    .secondary-btn button:hover { background-color: #F9FAFB !important; }

    /* Botão Perigo */
    button[kind="primary"] {
        background-color: #EF4444 !important;
        border-color: #EF4444 !important;
    }

    /* --- INPUTS E CAMPOS --- */
    .stTextInput input, .stTextArea textarea, .stSelectbox div {
        background-color: #FFFFFF;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        color: #111827;
    }
    .stTextInput input:focus {
        border-color: #2175D9;
        box-shadow: 0 0 0 1px #2175D9;
    }

    /* BADGES / TAGS */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 5px;
    }
    .badge-blue { background: #EBF8FF; color: #2175D9; border: 1px solid #BEE3F8; }
    .badge-gray { background: #F3F4F6; color: #4B5563; border: 1px solid #E5E7EB; }
    .badge-green { background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; }

</style>
""", unsafe_allow_html=True)

# --- CONEXÃO ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except: st.stop()

# --- BACKEND ---
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
# INTERFACE
# ==============================================================================
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

# --- TELA DE LOGIN (Clean & Centralizada) ---
if st.session_state["usuario_logado"] is None:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.write(""); st.write(""); st.write("")
        with st.container(border=True):
            if LOGO_URL: 
                col_img_1, col_img_2, col_img_3 = st.columns([1,2,1])
                with col_img_2: st.image(LOGO_URL, use_container_width=True)
            else: st.markdown("<h2 style='text-align:center; color:#2175D9'>gupy.</h2>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align:center; color:#666; margin-bottom:20px;'>Portal de Frases de Recusa</p>", unsafe_allow_html=True)
            with st.form("login"):
                u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
                st.write("")
                if st.form_submit_button("Entrar", use_container_width=True):
                    user = verificar_login(u, s)
                    if user: st.session_state["usuario_logado"] = user; st.rerun()
                    else: st.error("Acesso negado.")

else:
    user = st.session_state["usuario_logado"]
    
    # --- CABEÇALHO SUPERIOR (Fixo e Bonito) ---
    # Substitui a sidebar por um cabeçalho horizontal no topo
    with st.container():
        c_head_logo, c_head_user, c_head_out = st.columns([6, 2, 1], gap="small")
        with c_head_logo:
            # Título do App
            st.markdown(f"""
            <div class="header-container">
                <div class="header-title">Frases de Recusa</div>
                <div class="header-user">Olá, <b>{user['username']}</b></div>
            </div>
            """, unsafe_allow_html=True)
        
        with c_head_user:
            st.write("") # alinhamento
        
        with c_head_out:
            st.write("") 
            st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
            if st.button("Sair", use_container_width=True):
                st.session_state["usuario_logado"] = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    if user.get('trocar_senha'):
        st.warning("⚠️ Troca de Senha Obrigatória"); n1=st.text_input("Nova"); n2=st.text_input("Confirmar")
        if st.button("Salvar"): 
            if n1==n2 and n1: supabase.table("usuarios").update({"senha":n1,"trocar_senha":False}).eq("id",user['id']).execute(); user['trocar_senha']=False; st.rerun()
    else:
        # --- MENU PRINCIPAL (ABAS NATIVAS - RESPONSIVAS) ---
        # Isso cria a navegação no topo que funciona bem no celular (scroll lateral)
        tabs_list = ["📂 Biblioteca", "📝 Adicionar / Importar", "✏️ Gerenciar"]
        if user['admin']: tabs_list.append("⚙️ Admin")
        
        tabs = st.tabs(tabs_list)

        # --- ABA 1: BIBLIOTECA (Visualização) ---
        with tabs[0]:
            st.write("")
            c_busca, c_vazio = st.columns([2, 2])
            termo = c_busca.text_input("Pesquisar na biblioteca...", placeholder="Digite empresa, documento ou motivo...")
            
            dados = buscar_dados()
            filtrados = [f for f in dados if termo.lower() in str(f).lower()] if termo else dados
            
            st.markdown(f"**{len(filtrados)}** registros encontrados")
            
            for f in filtrados:
                with st.container(border=True):
                    # Cabeçalho do Card
                    st.markdown(f"#### {f['empresa']}")
                    
                    # Badges (Tags)
                    st.markdown(f"""
                        <span class="badge badge-blue">📄 {f['documento']}</span>
                        <span class="badge badge-gray">📌 {f['motivo']}</span>
                    """, unsafe_allow_html=True)
                    
                    st.write("")
                    st.code(f['conteudo'], language="text")
                    
                    if f.get('revisado_por'):
                        try: dt = datetime.strptime(f['data_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y'); st.markdown(f"<span class='badge badge-green'>✔ Validado por {f['revisado_por']} em {dt}</span>", unsafe_allow_html=True)
                        except: pass

        # --- ABA 2: ADICIONAR / IMPORTAR ---
        with tabs[1]:
            st.write("")
            c_manual, c_import = st.columns([1, 1], gap="large")
            
            with c_manual:
                with st.container(border=True):
                    st.subheader("Cadastro Manual")
                    ne = st.text_input("Empresa"); nd = st.text_input("Documento"); nm = st.text_input("Motivo")
                    nc = st.text_area("Conteúdo da Frase", height=150)
                    if st.button("Salvar Registro", use_container_width=True):
                        if nc:
                            ne,nd,nm = padronizar(ne),padronizar(nd),padronizar(nm); nc = padronizar(nc,"frase")
                            if len(supabase.table("frases").select("id").eq("conteudo", nc).execute().data) > 0: st.error("Duplicado.")
                            else:
                                supabase.table("frases").insert({"empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).execute()
                                registrar_log(user['username'], "Criou Frase", f"{ne}-{nm}"); st.success("Salvo!"); time.sleep(1); st.rerun()

            with c_import:
                with st.container(border=True):
                    st.subheader("Importar Planilha")
                    upl = st.file_uploader("Excel (.xlsx) ou CSV", type=['csv','xlsx'])
                    if upl and st.button("Processar Arquivo", use_container_width=True):
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
                            
                            if not all(c in df.columns for c in ['empresa','documento','motivo','conteudo']): st.error("Colunas inválidas.")
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
                        except Exception as e: st.error(str(e))

        # --- ABA 3: GERENCIAR (Busca e Edição) ---
        with tabs[2]:
            st.write("")
            q = st.text_input("Buscar para editar ou excluir:", placeholder="Digite aqui...")
            dados = buscar_dados()
            lista = [f for f in dados if q.lower() in str(f).lower()] if q else dados
            
            st.caption(f"{len(lista)} registros")
            for f in lista:
                with st.expander(f"{f['empresa']} | {f['documento']}"):
                    with st.form(f"ed_{f['id']}"):
                        c_a, c_b = st.columns(2)
                        fe = c_a.text_input("Empresa", f['empresa'])
                        fd = c_b.text_input("Documento", f['documento'])
                        fm = st.text_input("Motivo", f['motivo'])
                        fc = st.text_area("Conteúdo", f['conteudo'], height=100)
                        
                        cs, cd = st.columns([4, 1])
                        if cs.form_submit_button("Salvar Alterações", use_container_width=True):
                            supabase.table("frases").update({"empresa":padronizar(fe),"documento":padronizar(fd),"motivo":padronizar(fm),"conteudo":padronizar(fc,"frase"),"revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')}).eq("id", f['id']).execute()
                            registrar_log(user['username'], "Editou Frase", str(f['id'])); st.rerun()
                        if cd.form_submit_button("Excluir", type="primary", use_container_width=True):
                            supabase.table("frases").delete().eq("id", f['id']).execute()
                            registrar_log(user['username'], "Excluiu Frase", str(f['id'])); st.rerun()

        # --- ABA 4: ADMIN (Só Admins) ---
        if user['admin']:
            with tabs[3]:
                st.write("")
                c_adm1, c_adm2 = st.columns(2)
                with c_adm1:
                    with st.container(border=True):
                        st.subheader("Usuários")
                        # Criar
                        with st.form("new_u", border=False):
                            c_u1, c_u2 = st.columns(2)
                            nu = c_u1.text_input("Nome"); ns = c_u2.text_input("Senha"); na = st.checkbox("Admin")
                            if st.form_submit_button("Criar Usuário"):
                                supabase.table("usuarios").insert({"username":nu,"senha":ns,"admin":na,"trocar_senha":True}).execute()
                                registrar_log(user['username'], "Criou Usuário", nu); st.rerun()
                        st.divider()
                        # Listar
                        for u in buscar_usuarios():
                            with st.expander(f"{u['username']} {'(Admin)' if u['admin'] else ''}"):
                                c_x, c_y = st.columns(2)
                                if c_x.button("Resetar Senha", key=f"r{u['id']}"): supabase.table("usuarios").update({"trocar_senha":True}).eq("id", u['id']).execute(); st.toast("Feito!")
                                if u['username']!=user['username'] and c_y.button("Excluir", key=f"d{u['id']}", type="primary"): supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()

                with c_adm2:
                    with st.container(border=True):
                        st.subheader("Dados & Segurança")
                        # Backup
                        full = buscar_dados()
                        if full: st.download_button("📥 Baixar Backup (CSV)", pd.DataFrame(full).to_csv(index=False).encode('utf-8'), "backup.csv", "text/csv", use_container_width=True)
                        st.divider()
                        # Logs
                        logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(20).execute().data
                        if logs: st.dataframe(pd.DataFrame(logs)[['data_hora','usuario','acao','detalhe']], use_container_width=True, height=200)
                        st.divider()
                        # Danger
                        chk = st.text_input("Limpeza total (Digite: QUERO APAGAR TUDO)")
                        if st.button("LIMPAR BANCO DE DADOS", type="primary", use_container_width=True) and chk=="QUERO APAGAR TUDO":
                            supabase.table("frases").delete().neq("id", 0).execute()
                            registrar_log(user['username'], "LIMPEZA TOTAL", "FRASES"); st.rerun()

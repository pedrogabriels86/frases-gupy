import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time
from datetime import datetime
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA (Identidade Gupy) ---
st.set_page_config(page_title="Gupy Frases", page_icon="💙", layout="wide")

# --- CSS CORPORATIVO GUPY ---
st.markdown("""
<style>
    /* IMPORTAR FONTE INTER */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #262626;
    }

    /* FUNDO GERAL */
    .stApp {
        background-color: #F5F7FA;
    }

    /* SIDEBAR (Azul Escuro Gupy) */
    section[data-testid="stSidebar"] {
        background-color: #00122F;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] p {
        color: #FFFFFF !important;
    }
    
    /* LOGO NO SIDEBAR */
    .sidebar-logo {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2175D9 !important;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* BOTÕES (Azul Gupy) */
    .stButton > button {
        background-color: #2175D9;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: background-color 0.2s;
    }
    .stButton > button:hover {
        background-color: #175BB5;
        color: white;
    }
    /* Botão Danger */
    button[kind="primary"] {
        background-color: #D93025 !important;
        border: 1px solid #D93025 !important;
    }

    /* CARTÕES (Clean & Flat) */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #FFFFFF;
        border: 1px solid #E1E4E8;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        padding: 24px !important;
    }

    /* INPUTS */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {
        background-color: #FFFFFF;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        color: #374151;
    }
    .stTextInput > div > div > input:focus {
        border-color: #2175D9;
        box-shadow: 0 0 0 1px #2175D9;
    }

    /* BADGES */
    .badge-gupy {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .bg-blue { background-color: #E3F2FD; color: #1565C0; border: 1px solid #BBDEFB; }
    .bg-purple { background-color: #F3E5F5; color: #7B1FA2; border: 1px solid #E1BEE7; }
    .bg-green { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #C8E6C9; }

    /* MENU RADIO */
    .stRadio > div { background-color: transparent; }
    .stRadio label { color: white !important; }

    /* CODE BLOCK */
    .stCode {
        background-color: #F9FAFB !important;
        border: 1px solid #F3F4F6;
        border-radius: 6px;
    }

</style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO COM O BANCO ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Erro de conexão. Verifique secrets.toml")
    st.stop()

# --- 3. LÓGICA (BACKEND) ---
def verificar_login(u, s):
    try:
        res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute()
        return res.data[0] if res.data else None
    except: return None

def buscar_dados(): 
    return supabase.table("frases").select("*").order("id", desc=True).execute().data

def buscar_usuarios(): 
    return supabase.table("usuarios").select("*").order("id").execute().data

def registrar_log(usuario, acao, detalhe):
    try:
        supabase.table("logs").insert({
            "usuario": usuario, "acao": acao, "detalhe": detalhe,
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
    except: pass

def padronizar_texto(texto, tipo="titulo"):
    if not texto: return ""
    texto = str(texto).strip()
    if not texto: return ""
    return texto.title() if tipo == "titulo" else (texto[0].upper() + texto[1:])

# --- 4. INTERFACE (FRONTEND) ---

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# TELA DE LOGIN
if st.session_state["usuario_logado"] is None:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write("")
        st.write("")
        st.write("")
        with st.container(border=True):
            st.markdown("""
                <div style="text-align: center; margin-bottom: 20px;">
                    <span style="font-size: 40px; font-weight: 800; color: #2175D9; letter-spacing: -1px;">gupy</span>
                    <span style="font-size: 20px; color: #555;">| frases</span>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                u = st.text_input("E-mail ou Usuário")
                s = st.text_input("Senha", type="password")
                st.write("")
                if st.form_submit_button("Entrar na plataforma", use_container_width=True):
                    user = verificar_login(u, s)
                    if user:
                        st.session_state["usuario_logado"] = user
                        st.rerun()
                    else: st.error("Acesso negado.")
            st.markdown("<div style='text-align:center; color:#888; font-size:12px; margin-top:10px;'>Ambiente Seguro • Gupy Corporate</div>", unsafe_allow_html=True)

# SISTEMA PRINCIPAL
else:
    user = st.session_state["usuario_logado"]
    
    # 1. SIDEBAR
    with st.sidebar:
        st.markdown("""
            <div class="sidebar-logo">
               <span style="color:#fff;">gupy</span><span style="color:#2175D9;">.</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"<div style='color:#A0AEC0; font-size: 0.85rem; margin-bottom: 5px;'>LOGADO COMO</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#FFF; font-weight:600; font-size: 1.1rem;'>{user['username']}</div>", unsafe_allow_html=True)
        status = "Administrador" if user['admin'] else "Colaborador"
        st.markdown(f"<div style='color:#2175D9; font-size: 0.8rem; margin-bottom: 20px;'>● {status}</div>", unsafe_allow_html=True)
        
        st.divider()
        
        opcoes = {
            "Biblioteca": "library",
            "Nova Frase": "add",
            "Gestão": "manage"
        }
        if user['admin']: opcoes["Administração"] = "admin"
        
        selection = st.radio("MENU PRINCIPAL", list(opcoes.keys()))
        page = opcoes[selection]
        
        st.write("")
        st.write("")
        if st.button("Sair", use_container_width=True):
            st.session_state["usuario_logado"] = None
            st.rerun()

    # Validação Senha
    if user.get('trocar_senha'):
        st.warning("⚠️ Atualização de Segurança Necessária")
        with st.container(border=True):
            st.subheader("Redefinir Senha")
            n1 = st.text_input("Nova Senha", type="password")
            n2 = st.text_input("Confirmar Senha", type="password")
            if st.button("Salvar Nova Senha"):
                if n1==n2 and n1:
                    supabase.table("usuarios").update({"senha":n1, "trocar_senha":False}).eq("id", user['id']).execute()
                    user['trocar_senha']=False; st.session_state["usuario_logado"]=user; st.rerun()
                else: st.error("Erro.")
    else:
        # --- BIBLIOTECA ---
        if page == "library":
            c_title, c_search = st.columns([1, 2])
            with c_title:
                st.title("Biblioteca")
            with c_search:
                st.write("")
                termo = st.text_input("Buscar", placeholder="Pesquise por palavras-chave...", label_visibility="collapsed")
            
            dados = buscar_dados()
            filtrados = [f for f in dados if termo.lower() in str(f).lower()] if termo else dados
            
            with st.container(border=True):
                cf1, cf2, cf3 = st.columns([1,1,2])
                emps = sorted(list(set([f['empresa'] for f in filtrados])))
                docs = sorted(list(set([f['documento'] for f in filtrados])))
                
                sel_emp = cf1.selectbox("Empresa", ["Todas"] + emps)
                sel_doc = cf2.selectbox("Documento", ["Todos"] + docs)
                
                if sel_emp != "Todas": filtrados = [f for f in filtrados if f['empresa'] == sel_emp]
                if sel_doc != "Todos": filtrados = [f for f in filtrados if f['documento'] == sel_doc]
                
                cf3.markdown(f"<div style='text-align:right; padding-top: 35px; color:#666;'>Mostrando <b>{len(filtrados)}</b> resultados</div>", unsafe_allow_html=True)

            st.write("")
            grid = st.columns(2)
            for i, f in enumerate(filtrados):
                with grid[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:10px;">
                            <div>
                                <span class="badge-gupy bg-blue">{f['empresa']}</span>
                                <span class="badge-gupy bg-purple">{f['documento']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"**{f['motivo']}**")
                        st.code(f['conteudo'], language="text")
                        
                        if f.get('revisado_por'):
                            try:
                                dt = datetime.strptime(f['data_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y')
                                st.markdown(f"""
                                <div style='border-top:1px solid #EEE; margin-top:10px; padding-top:10px; font-size:12px; color:#888; display:flex; align-items:center; gap:5px;'>
                                    <span style='color:#2E7D32;'>✔ Validado</span> por {f['revisado_por']} em {dt}
                                </div>
                                """, unsafe_allow_html=True)
                            except: pass

        # --- NOVA FRASE ---
        elif page == "add":
            st.title("Adicionar Conteúdo")
            with st.container(border=True):
                st.markdown("#### Preencha os detalhes")
                with st.form("new"):
                    c1, c2 = st.columns(2)
                    e = c1.text_input("Empresa", placeholder="Ex: Gupy")
                    d = c2.text_input("Documento", placeholder="Ex: Contrato")
                    m = st.text_input("Motivo", placeholder="Ex: Cláusula de Rescisão")
                    c = st.text_area("Frase Padrão", height=150)
                    
                    if st.form_submit_button("Salvar Registro"):
                        if c:
                            e, d, m = padronizar_texto(e), padronizar_texto(d), padronizar_texto(m)
                            c = padronizar_texto(c, "frase")
                            if not supabase.table("frases").select("id").eq("conteudo", c).execute().data:
                                supabase.table("frases").insert({
                                    "empresa":e,"documento":d,"motivo":m,"conteudo":c,
                                    "revisado_por": user['username'], "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                }).execute()
                                registrar_log(user['username'], "Criar Frase", f"{e}-{m}")
                                st.success("Salvo com sucesso!"); time.sleep(1); st.rerun()
                            else: st.error("Duplicado.")
                        else: st.warning("Preencha o texto.")
            
            st.write("")
            with st.expander("📥 Importação em Massa (CSV/Excel)"):
                upl = st.file_uploader("Arquivo", type=['csv','xlsx'])
                if upl and st.button("Importar Dados"):
                    try:
                        df = pd.read_csv(upl) if upl.name.endswith('.csv') else pd.read_excel(upl)
                        df.columns = [x.lower().strip() for x in df.columns]
                        novos = []
                        existentes = set([str(f['conteudo']).strip() for f in buscar_dados()])
                        for _, r in df.iterrows():
                            if 'empresa' in df.columns: r['empresa'] = padronizar_texto(r['empresa'])
                            if 'conteudo' in df.columns: r['conteudo'] = padronizar_texto(r['conteudo'], 'frase')
                            if str(r['conteudo']).strip() not in existentes:
                                item = {k: r[k] for k in ['empresa','documento','motivo','conteudo'] if k in df.columns}
                                item['revisado_por'] = user['username']; item['data_revisao'] = datetime.now().strftime('%Y-%m-%d')
                                novos.append(item)
                        if novos:
                            supabase.table("frases").insert(novos).execute()
                            registrar_log(user['username'], "Importar", str(len(novos)))
                            st.success(f"{len(novos)} importados!"); time.sleep(2); st.rerun()
                    except Exception as e: st.error(str(e))

        # --- GESTÃO ---
        elif page == "manage":
            st.title("Gestão de Registros")
            dados = buscar_dados()
            if dados:
                options = {f"{x['id']} | {x['empresa']} - {x['motivo']}": x for x in dados}
                sel = st.selectbox("Selecione o registro:", list(options.keys()))
                if sel:
                    obj = options[sel]
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            ne = st.text_input("Empresa", obj['empresa'])
                            nd = st.text_input("Documento", obj['documento'])
                            nm = st.text_input("Motivo", obj['motivo'])
                            nc = st.text_area("Conteúdo", obj['conteudo'])
                        with c2:
                            st.write("")
                            st.write("")
                            if st.button("💾 Atualizar", use_container_width=True):
                                supabase.table("frases").update({
                                    "empresa":padronizar_texto(ne),"documento":padronizar_texto(nd),
                                    "motivo":padronizar_texto(nm),"conteudo":padronizar_texto(nc,"frase"),
                                    "revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')
                                }).eq("id",obj['id']).execute()
                                registrar_log(user['username'], "Editar Frase", str(obj['id']))
                                st.success("Feito!"); time.sleep(1); st.rerun()
                            
                            st.write("")
                            if st.button("🗑️ Remover", type="primary", use_container_width=True):
                                supabase.table("frases").delete().eq("id", obj['id']).execute()
                                registrar_log(user['username'], "Excluir Frase", str(obj['id']))
                                st.rerun()

        # --- ADMIN (TRADUZIDO E COMPLETO) ---
        elif page == "admin":
            st.title("Painel Administrativo")
            
            # Abas em Português
            t1, t2, t3 = st.tabs(["👥 Gerenciar Usuários", "📜 Logs e Backup", "⚠️ Zona de Perigo"])
            
            with t1:
                st.subheader("Controle de Acesso")
                # Formulário de criação
                with st.form("novo_usuario"):
                    c1, c2, c3 = st.columns(3)
                    nu = c1.text_input("Nome do Usuário")
                    ns = c2.text_input("Senha Inicial")
                    na = c3.checkbox("É Administrador?")
                    if st.form_submit_button("Criar Usuário"):
                        supabase.table("usuarios").insert({"username":nu,"senha":ns,"admin":na,"trocar_senha":True}).execute()
                        registrar_log(user['username'], "Criar Usuário", nu)
                        st.success("Usuário criado!"); time.sleep(1); st.rerun()
                
                st.write("---")
                st.subheader("Usuários Ativos")
                users = buscar_usuarios()
                for u in users:
                    with st.container(border=True):
                        c_a, c_b, c_c = st.columns([2,1,1])
                        c_a.markdown(f"**{u['username']}** <span style='color:#999; font-size:12px;'>{'ADMIN' if u['admin'] else 'USER'}</span>", unsafe_allow_html=True)
                        if c_b.button("Resetar Senha", key=f"r{u['id']}"):
                            supabase.table("usuarios").update({"trocar_senha":True}).eq("id", u['id']).execute()
                            st.toast("Usuário terá que trocar a senha no próximo login.")
                        if u['username'] != user['username']:
                            if c_c.button("Excluir", key=f"d{u['id']}", type="primary"):
                                supabase.table("usuarios").delete().eq("id", u['id']).execute()
                                registrar_log(user['username'], "Excluir Usuário", u['username'])
                                st.rerun()

            with t2:
                st.subheader("Auditoria do Sistema")
                logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(50).execute().data
                if logs: st.dataframe(pd.DataFrame(logs)[['data_hora','usuario','acao','detalhe']], use_container_width=True)
                
                st.write("---")
                st.subheader("Backup de Dados")
                st.write("Baixe todos os dados das frases em formato CSV.")
                all_data = buscar_dados()
                if all_data:
                    csv = pd.DataFrame(all_data).to_csv(index=False).encode('utf-8')
                    if st.download_button("📥 Baixar CSV Completo", csv, "backup_gupy.csv", "text/csv"):
                        registrar_log(user['username'], "Backup Realizado", "Download CSV")

            with t3:
                st.error("Área de Risco: Ações Irreversíveis")
                
                col_danger1, col_danger2 = st.columns(2)
                
                with col_danger1:
                    with st.container(border=True):
                        st.subheader("🔥 Apagar Todas as Frases")
                        check = st.text_input("Digite 'QUERO APAGAR TUDO' para confirmar:", key="del_frases")
                        if st.button("EXCLUIR TUDO (FRASES)", type="primary", use_container_width=True):
                            if check == "QUERO APAGAR TUDO":
                                supabase.table("frases").delete().neq("id", 0).execute()
                                registrar_log(user['username'], "RESET TOTAL", "Apagou todas as frases")
                                st.toast("Banco de frases limpo!"); time.sleep(2); st.rerun()
                            else:
                                st.error("Frase de confirmação incorreta.")

                with col_danger2:
                     with st.container(border=True):
                        st.subheader("💀 Apagar Usuários")
                        check2 = st.text_input("Digite 'RESETAR USUARIOS' para confirmar:", key="del_users")
                        if st.button("EXCLUIR TUDO (USUÁRIOS)", type="primary", use_container_width=True):
                            if check2 == "RESETAR USUARIOS":
                                supabase.table("usuarios").delete().neq("username", user['username']).execute()
                                registrar_log(user['username'], "RESET USERS", "Apagou todos os usuários")
                                st.toast("Usuários resetados!"); time.sleep(2); st.rerun()
                            else:
                                st.error("Frase de confirmação incorreta.")

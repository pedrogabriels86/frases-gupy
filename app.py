import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time
from datetime import datetime
import io

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Frases Gupy OS", page_icon="⚡", layout="wide")

# --- O CSS MÁGICO (AQUI ESTÁ O SEGREDO DO VISUAL) ---
st.markdown("""
<style>
    /* FONTES MODERNAS */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
        # background: linear-gradient(135deg, #f6f8fd 0%, #eef2f7 100%);
        background-color: #F0F2F5; /* Fundo limpo para destacar os elementos 3D */
    }

    /* --- SIDEBAR GLASSMORPHISM --- */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.7); /* Vidro semi-transparente */
        backdrop-filter: blur(15px); /* Efeito de desfoque */
        border-right: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 5px 0 25px rgba(0,0,0,0.05);
    }

    /* --- TÍTULOS COM GRADIENTE --- */
    h1, h2, h3 {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }

    /* --- INPUTS SUPER MODERNOS --- */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > div {
        background: #ffffff;
        border: 2px solid #e0e6ed;
        border-radius: 12px;
        padding: 10px 15px;
        box-shadow: inset 4px 4px 8px #d9dce1, inset -4px -4px 8px #ffffff; /* Neumorphism interno sutil */
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #4facfe;
        box-shadow: 0 0 15px rgba(79, 172, 254, 0.3); /* Brilho azul ao focar */
    }

    /* --- BOTÕES COM GRADIENTE E EFEITO 3D --- */
    .stButton > button {
        background: linear-gradient(92.88deg, #455EB5 9.16%, #5643CC 43.89%, #673FD7 64.72%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 10px 20px -10px rgba(69, 94, 181, 0.5);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); /* Efeito elástico */
    }
    .stButton > button:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 20px 30px -10px rgba(69, 94, 181, 0.7);
    }
    /* Botão Danger */
    button[kind="primary"] {
        background: linear-gradient(135deg, #ff416c, #ff4b2b) !important;
        box-shadow: 0 10px 20px -10px rgba(255, 75, 43, 0.5) !important;
    }

    /* --- CARDS 3D QUE "SALTAM" (A ESTRELA DO SHOW) --- */
    /* Alvo: os containers com borda que usamos para as frases */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255,255,255,0.8) !important;
        border-radius: 20px !important;
        /* Sombra profunda para dar a sensação de flutuar */
        box-shadow: 0 15px 35px rgba(0,0,0,0.1), 0 5px 15px rgba(0,0,0,0.05) !important;
        backdrop-filter: blur(10px);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        padding: 25px !important;
        margin-bottom: 20px;
    }
    /* Efeito ao passar o mouse no card */
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        border-color: rgba(79, 172, 254, 0.5) !important;
        /* Levanta e aumenta ligeiramente */
        transform: translateY(-12px) scale(1.02) !important;
        /* Sombra fica maior e ganha um brilho azul */
        box-shadow: 0 30px 60px rgba(0,0,0,0.15), 0 0 30px rgba(79, 172, 254, 0.3) !important;
    }

    /* --- BADGES MODERNAS --- */
    .badge-container { margin-bottom: 15px; }
    .modern-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-right: 8px;
        margin-bottom: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        background: white;
        border: 2px solid transparent;
    }
    .mb-emp { color: #005bea; border-color: #005bea; background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%); color: #333;}
    .mb-doc { color: #ff0084; border-color: #ff0084; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white;}
    .mb-mot { color: #00c853; border-color: #00c853; background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); color: #333;}

    /* Bloco de Código mais limpo */
    .stCode {
        border-radius: 12px;
        box-shadow: inset 0 0 15px rgba(0,0,0,0.05);
        border: none;
    }

    /* Animação de entrada da página */
    .stApp {
        animation: fadeIn 0.8s ease-in-out;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
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

# --- 3. FUNÇÕES DE LÓGICA ---
def verificar_login(u, s):
    try:
        res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute()
        return res.data[0] if res.data else None
    except: return None

def buscar_dados(): return supabase.table("frases").select("*").order("id", desc=True).execute().data
def buscar_usuarios(): return supabase.table("usuarios").select("*").order("id").execute().data
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

# --- 4. INTERFACE ---

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# TELA DE LOGIN (Visual Glassy)
if st.session_state["usuario_logado"] is None:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.write("")
        st.write("")
        st.write("")
        # Container com borda para pegar o efeito 3D do CSS
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>⚡ Frases Gupy OS</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; opacity: 0.7;'>Acesse o sistema de conhecimento.</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                u = st.text_input("Usuário")
                s = st.text_input("Senha", type="password")
                st.write("")
                if st.form_submit_button("🚀 Entrar no Sistema", use_container_width=True):
                    user = verificar_login(u, s)
                    if user:
                        st.session_state["usuario_logado"] = user
                        st.rerun()
                    else: st.error("Credenciais inválidas.")

# SISTEMA
else:
    user = st.session_state["usuario_logado"]
    
    # Troca de senha obrigatória
    if user.get('trocar_senha'):
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            with st.container(border=True):
                st.subheader("🔒 Segurança Primeiro")
                st.info("Defina sua nova senha para continuar.")
                with st.form("reset_pass"):
                    n1 = st.text_input("Nova Senha", type="password")
                    n2 = st.text_input("Confirmar", type="password")
                    if st.form_submit_button("✨ Atualizar e Acessar", use_container_width=True):
                        if n1 == n2 and n1:
                            supabase.table("usuarios").update({"senha": n1, "trocar_senha": False}).eq("id", user['id']).execute()
                            user['trocar_senha'] = False; st.session_state["usuario_logado"] = user
                            st.success("Senha alterada! Redirecionando..."); time.sleep(1); st.rerun()
                        else: st.error("Senhas não conferem.")
    
    else:
        # SIDEBAR GLASSMÓRFICA
        with st.sidebar:
            # st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
            st.markdown(f"## Olá, **{user['username']}** 👋")
            st.caption(f"Perfil: {'👑 Super Admin' if user['admin'] else '👤 Colaborador'}")
            st.divider()
            
            menu_opts = {
                "🏠 Biblioteca Visual": "library",
                "✨ Nova Frase": "add",
                "🛠️ Gestão": "manage",
            }
            if user['admin']: menu_opts["🛡️ Central Admin"] = "admin"
            
            selected_label = st.radio("Navegação", list(menu_opts.keys()))
            page = menu_opts[selected_label]
            
            st.divider()
            if st.button("Sair do Sistema", use_container_width=True):
                st.session_state["usuario_logado"] = None
                st.rerun()

        # --- PÁGINA: BIBLIOTECA VISUAL 3D ---
        if page == "library":
            st.title("Biblioteca Visual")
            st.caption("Explore o conhecimento da empresa em cards interativos.")
            
            termo = st.text_input("🔍 Pesquisa rápida...", placeholder="Digite para filtrar instantaneamente...")

            dados = buscar_dados()
            if not dados:
                st.info("Nenhuma frase cadastrada.")
            else:
                filtrados = dados
                if termo:
                    t = termo.lower()
                    filtrados = [f for f in dados if t in str(f).lower()]
                
                # Filtros estilo "Chips"
                c1, c2, c3 = st.columns([2,2,3])
                empresas = sorted(list(set([f['empresa'] for f in filtrados])))
                docs = sorted(list(set([f['documento'] for f in filtrados])))
                
                with c1: emp_filter = st.selectbox("Filtrar Empresa", ["Todas"] + empresas)
                with c2: doc_filter = st.selectbox("Filtrar Documento", ["Todos"] + docs)
                
                if emp_filter != "Todas": filtrados = [f for f in filtrados if f['empresa'] == emp_filter]
                if doc_filter != "Todos": filtrados = [f for f in filtrados if f['documento'] == doc_filter]
                
                st.divider()
                st.markdown(f"Isso resultou em **{len(filtrados)}** cards.")
                
                # GRID 3D
                grid = st.columns(2)
                for i, frase in enumerate(filtrados):
                    with grid[i % 2]:
                        # O segredo é usar st.container(border=True) que nosso CSS transformou em card 3D
                        with st.container(border=True):
                            # Badges com gradientes
                            st.markdown(f"""
                                <div class="badge-container">
                                    <span class="modern-badge mb-emp">🏢 {frase['empresa']}</span>
                                    <span class="modern-badge mb-doc">📄 {frase['documento']}</span>
                                    <span class="modern-badge mb-mot">📌 {frase['motivo']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            st.code(frase['conteudo'], language="text")
                            
                            if frase.get('revisado_por'):
                                try:
                                    d = datetime.strptime(frase['data_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y')
                                    st.markdown(f"<div style='text-align: right; opacity: 0.7; font-size: 0.8rem;'>✅ Revisado por <b>{frase['revisado_por']}</b> em {d}</div>", unsafe_allow_html=True)
                                except: pass

        # --- PÁGINA: NOVA FRASE ---
        elif page == "add":
            st.title("Adicionar Conhecimento")
            
            with st.container(border=True):
                with st.form("nova_frase_form"):
                    c1, c2 = st.columns(2)
                    e = c1.text_input("Empresa")
                    d = c2.text_input("Documento")
                    m = st.text_input("Motivo")
                    c = st.text_area("Conteúdo da Frase", height=150)
                    
                    st.caption("✨ Padronização automática e auditoria ativadas.")
                    
                    if st.form_submit_button("💾 Salvar no Banco", use_container_width=True):
                        if c:
                            e, d, m = padronizar_texto(e), padronizar_texto(d), padronizar_texto(m)
                            c = padronizar_texto(c, "frase")
                            if len(supabase.table("frases").select("id").eq("conteudo", c).execute().data) > 0:
                                st.error("Frase duplicada!")
                            else:
                                supabase.table("frases").insert({
                                    "empresa":e, "documento":d, "motivo":m, "conteudo":c,
                                    "revisado_por": user['username'], "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                }).execute()
                                registrar_log(user['username'], "Criar", f"{e} - {m}")
                                st.success("Sucesso! Card criado."); time.sleep(1); st.rerun()
                        else: st.warning("Conteúdo vazio.")
            
            st.divider()
            with st.expander("📂 Importação em Massa (Drag & Drop)"):
                upl = st.file_uploader("Solte seu arquivo Excel/CSV", type=['csv','xlsx'])
                if upl and st.button("🚀 Processar Arquivo", use_container_width=True):
                    try:
                        df = pd.read_csv(upl) if upl.name.endswith('.csv') else pd.read_excel(upl)
                        df.columns = [c.lower().strip() for c in df.columns]
                        cols_map = {'empresa':'titulo', 'documento':'titulo', 'motivo':'titulo', 'conteudo':'frase'}
                        for col, tipo in cols_map.items():
                            if col in df.columns: df[col] = df[col].apply(lambda x: padronizar_texto(x, tipo))
                        existentes = set([str(f['conteudo']).strip() for f in buscar_dados()])
                        novos = []
                        for _, row in df.iterrows():
                            if str(row['conteudo']).strip() not in existentes:
                                item = {k: row[k] for k in ['empresa','documento','motivo','conteudo'] if k in df.columns}
                                if 'revisado_por' in df.columns: item['revisado_por'] = str(row['revisado_por'])
                                if 'data_revisao' in df.columns: item['data_revisao'] = str(row['data_revisao']).split('T')[0]
                                novos.append(item)
                        if novos:
                            supabase.table("frases").insert(novos).execute()
                            registrar_log(user['username'], "Importar", f"{len(novos)} itens")
                            st.success(f"{len(novos)} cards importados!")
                        else: st.warning("Nada novo."); time.sleep(2); st.rerun()
                    except Exception as err: st.error(f"Erro: {err}")

        # --- PÁGINA: GESTÃO ---
        elif page == "manage":
            st.title("Gestão de Cards")
            dados = buscar_dados()
            if dados:
                mapa = {f"ID {f['id']} | {f['empresa']} - {f['motivo']}": f for f in dados}
                sel = st.selectbox("Selecione o card para editar:", list(mapa.keys()))
                if sel:
                    obj = mapa[sel]
                    with st.container(border=True):
                        with st.form("edit_form"):
                            c1, c2 = st.columns(2)
                            ne = c1.text_input("Empresa", obj['empresa']); nd = c2.text_input("Documento", obj['documento'])
                            nm = st.text_input("Motivo", obj['motivo']); nc = st.text_area("Conteúdo", obj['conteudo'], height=120)
                            cols = st.columns([1.5, 1])
                            if cols[0].form_submit_button("💾 Salvar Alterações", use_container_width=True):
                                ne, nd, nm = padronizar_texto(ne), padronizar_texto(nd), padronizar_texto(nm)
                                nc = padronizar_texto(nc, "frase")
                                supabase.table("frases").update({
                                    "empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,
                                    "revisado_por": user['username'],"data_revisao": datetime.now().strftime('%Y-%m-%d')
                                }).eq("id", obj['id']).execute()
                                registrar_log(user['username'], "Editar", f"ID {obj['id']}")
                                st.success("Atualizado!"); time.sleep(1); st.rerun()
                            if cols[1].form_submit_button("🔥 Apagar Card", type="primary", use_container_width=True):
                                supabase.table("frases").delete().eq("id", obj['id']).execute()
                                registrar_log(user['username'], "Excluir", f"ID {obj['id']}")
                                st.rerun()

        # --- PÁGINA: ADMIN ---
        elif page == "admin":
            st.title("Central de Controle")
            t_usr, t_log, t_dang = st.tabs(["👥 Usuários", "📜 Auditoria Visual", "⚠️ Zona de Perigo"])
            
            with t_usr:
                with st.container(border=True):
                    st.subheader("Novo Acesso")
                    with st.form("nu"):
                        c1,c2,c3=st.columns([2,2,1]); u=c1.text_input("User"); s=c2.text_input("Pass"); a=c3.checkbox("Admin")
                        if st.form_submit_button("✨ Criar Usuário"):
                            supabase.table("usuarios").insert({"username":u,"senha":s,"admin":a,"trocar_senha":True}).execute()
                            registrar_log(user['username'], "Criar User", u); st.success("Feito!"); time.sleep(1); st.rerun()
                st.divider()
                for u in buscar_usuarios():
                    with st.expander(f"👤 {u['username']} {'(Admin)' if u['admin'] else ''}"):
                        if st.button("Resetar Senha", key=f"r_{u['id']}"):
                            supabase.table("usuarios").update({"trocar_senha":True}).eq("id", u['id']).execute(); st.toast("Resetado.")
                        if u['username']!=user['username'] and st.button("Excluir", key=f"d_{u['id']}", type="primary"):
                            supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()

            with t_log:
                logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(100).execute().data
                if logs: st.dataframe(pd.DataFrame(logs)[['data_hora','usuario','acao','detalhe']], use_container_width=True, hide_index=True)
                dados_full = buscar_dados()
                if dados_full:
                    st.download_button("📥 Baixar Backup Completo (CSV)", pd.DataFrame(dados_full).to_csv(index=False).encode('utf-8'), "bkp.csv", "text/csv", use_container_width=True)

            with t_dang:
                st.error("Cuidado: Ações destrutivas.")
                if st.button("🔥 LIMPAR TODAS AS FRASES", type="primary", use_container_width=True):
                    supabase.table("frases").delete().neq("id", 0).execute()
                    registrar_log(user['username'], "RESET GERAL", "Frases"); st.rerun()

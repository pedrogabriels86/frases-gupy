import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time
from datetime import datetime
import io

# --- 1. CONFIGURAÇÃO GUPY ---
st.set_page_config(page_title="Gupy Frases", page_icon="💙", layout="wide")

# --- CSS MODERNO E LIMPO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F5F7FA; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #00122F; }
    section[data-testid="stSidebar"] * { color: white !important; }
    
    /* BOTÕES */
    .stButton > button {
        border-radius: 6px; font-weight: 600; border: none;
        transition: transform 0.1s;
        background-color: #2175D9; color: white;
    }
    .stButton > button:hover { background-color: #175BB5; color: white; }
    .stButton > button:active { transform: scale(0.98); }
    
    /* CARTÕES DE GESTÃO */
    .card-container {
        background: white;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2175D9;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* INPUTS */
    .stTextInput input, .stTextArea textarea {
        border-radius: 6px; border: 1px solid #CBD5E0;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2175D9; box-shadow: 0 0 0 2px rgba(33, 117, 217, 0.2);
    }
    
    /* Expander mais limpo */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONEXÃO ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except: st.stop()

# --- 3. BACKEND ---
def verificar_login(u, s):
    try:
        res = supabase.table("usuarios").select("*").eq("username", u).eq("senha", s).execute()
        return res.data[0] if res.data else None
    except: return None

def buscar_dados(): return supabase.table("frases").select("*").order("id", desc=True).execute().data
def buscar_usuarios(): return supabase.table("usuarios").select("*").order("id").execute().data
def registrar_log(usuario, acao, detalhe):
    try: supabase.table("logs").insert({"usuario":usuario,"acao":acao,"detalhe":detalhe,"data_hora":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}).execute()
    except: pass
def padronizar(texto, tipo="titulo"):
    if not texto: return ""
    texto = str(texto).strip()
    return texto.title() if tipo == "titulo" else (texto[0].upper() + texto[1:])

# --- 4. FRONTEND ---
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None:
    c1, c2, c3 = st.columns([1,1.2,1])
    with c2:
        st.write(""); st.write("")
        with st.container(border=True):
            # Logo na tela de login
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Gupy_logo.svg/2560px-Gupy_logo.svg.png", width=150)
            st.markdown("<h3 style='text-align:left; color:#555;'>Frases</h3>", unsafe_allow_html=True)
            with st.form("login"):
                u = st.text_input("Usuário"); s = st.text_input("Senha", type="password")
                if st.form_submit_button("Acessar Plataforma", use_container_width=True):
                    user = verificar_login(u, s)
                    if user: st.session_state["usuario_logado"] = user; st.rerun()
                    else: st.error("Credenciais inválidas.")

else:
    user = st.session_state["usuario_logado"]
    
    with st.sidebar:
        # LOGO GUPY NO MENU
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Gupy_logo.svg/2560px-Gupy_logo.svg.png", width=140)
        
        st.caption(f"Olá, {user['username']}")
        st.divider()
        
        # MENU SEM A PALAVRA "MENU" (label_visibility="collapsed")
        opcoes = ["Biblioteca", "Gestão Inteligente", "Administração"] if user['admin'] else ["Biblioteca", "Gestão Inteligente"]
        page = st.radio("Navegação", opcoes, label_visibility="collapsed")
        
        st.divider()
        if st.button("Sair", use_container_width=True): st.session_state["usuario_logado"] = None; st.rerun()

    if user.get('trocar_senha'):
        st.warning("⚠️ Redefina sua senha"); n1=st.text_input("Nova"); n2=st.text_input("Confirmar")
        if st.button("Salvar"): 
            if n1==n2 and n1: supabase.table("usuarios").update({"senha":n1,"trocar_senha":False}).eq("id",user['id']).execute(); user['trocar_senha']=False; st.rerun()

    else:
        # --- BIBLIOTECA ---
        if page == "Biblioteca":
            st.title("Biblioteca de Frases") # Título alterado conforme pedido
            c_busca, c_filtro = st.columns([2,1])
            termo = c_busca.text_input("Busca Rápida", placeholder="🔎 Digite para pesquisar...", label_visibility="collapsed")
            dados = buscar_dados()
            filtrados = [f for f in dados if termo.lower() in str(f).lower()] if termo else dados
            
            with c_filtro:
                st.caption(f"{len(filtrados)} resultados encontrados")
            
            for f in filtrados:
                with st.container(border=True):
                    col_info, col_cont = st.columns([1, 3])
                    with col_info:
                        st.markdown(f"**{f['empresa']}**")
                        st.caption(f"{f['documento']}")
                        st.caption(f"📌 {f['motivo']}")
                        if f.get('revisado_por'): st.caption(f"✅ {f['revisado_por']}")
                    with col_cont:
                        st.code(f['conteudo'], language="text")

        # --- GESTÃO INTELIGENTE ---
        elif page == "Gestão Inteligente":
            c_head, c_btn = st.columns([3, 1])
            c_head.title("Gestão de Registros")
            
            with st.expander("➕  ADICIONAR NOVA FRASE (Clique para abrir)", expanded=False):
                with st.form("quick_add"):
                    c1, c2, c3 = st.columns(3)
                    ne = c1.text_input("Empresa"); nd = c2.text_input("Documento"); nm = c3.text_input("Motivo")
                    nc = st.text_area("Conteúdo")
                    if st.form_submit_button("💾 Salvar Registro", use_container_width=True):
                        if nc:
                            ne, nd, nm = padronizar(ne), padronizar(nd), padronizar(nm); nc = padronizar(nc, "frase")
                            if len(supabase.table("frases").select("id").eq("conteudo", nc).execute().data) > 0:
                                st.error("Frase duplicada.")
                            else:
                                supabase.table("frases").insert({
                                    "empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,
                                    "revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')
                                }).execute()
                                registrar_log(user['username'], "Create", f"{ne}-{nm}")
                                st.success("Adicionado!"); time.sleep(1); st.rerun()

            st.write("")
            col_search, col_upload = st.columns([2, 1])
            q = col_search.text_input("🔎 Buscar registro para editar...", placeholder="Digite palavras-chave")
            
            with col_upload:
                with st.popover("📂 Importar Excel/CSV", use_container_width=True):
                    upl = st.file_uploader("Arquivo", type=['csv','xlsx'])
                    if upl and st.button("Processar"):
                        try:
                            df = pd.read_csv(upl) if upl.name.endswith('.csv') else pd.read_excel(upl)
                            df.columns = [x.lower().strip() for x in df.columns]
                            novos = []
                            db_set = set([str(f['conteudo']).strip() for f in buscar_dados()])
                            for _, r in df.iterrows():
                                if 'empresa' in df.columns: r['empresa'] = padronizar(r['empresa'])
                                if 'conteudo' in df.columns: r['conteudo'] = padronizar(r['conteudo'], 'frase')
                                if str(r['conteudo']).strip() not in db_set:
                                    item = {k: r[k] for k in ['empresa','documento','motivo','conteudo'] if k in df.columns}
                                    item['revisado_por'] = user['username']; item['data_revisao'] = datetime.now().strftime('%Y-%m-%d')
                                    novos.append(item)
                            if novos:
                                supabase.table("frases").insert(novos).execute()
                                registrar_log(user['username'], "Import", str(len(novos)))
                                st.success(f"{len(novos)} importados!"); time.sleep(1); st.rerun()
                        except: st.error("Erro no arquivo")

            dados = buscar_dados()
            lista_final = [f for f in dados if q.lower() in str(f).lower()] if q else dados
            
            if not lista_final:
                st.info("Nenhum registro encontrado.")
            else:
                st.markdown(f"**Encontrados:** {len(lista_final)}")
                for f in lista_final:
                    label_cartao = f"🏢 {f['empresa']}  |  📄 {f['documento']}  |  📌 {f['motivo']}"
                    with st.expander(label_cartao):
                        with st.form(f"edit_{f['id']}"):
                            c_a, c_b = st.columns(2)
                            fe = c_a.text_input("Empresa", f['empresa'])
                            fd = c_b.text_input("Documento", f['documento'])
                            fm = st.text_input("Motivo", f['motivo'])
                            fc = st.text_area("Conteúdo", f['conteudo'])
                            
                            c_save, c_del = st.columns([4, 1])
                            if c_save.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                                supabase.table("frases").update({
                                    "empresa":padronizar(fe),"documento":padronizar(fd),
                                    "motivo":padronizar(fm),"conteudo":padronizar(fc,"frase"),
                                    "revisado_por":user['username'],"data_revisao":datetime.now().strftime('%Y-%m-%d')
                                }).eq("id", f['id']).execute()
                                registrar_log(user['username'], "Edit", str(f['id'])); st.rerun()
                            if c_del.form_submit_button("🗑️ Excluir", type="primary", use_container_width=True):
                                supabase.table("frases").delete().eq("id", f['id']).execute()
                                registrar_log(user['username'], "Delete", str(f['id'])); st.rerun()

        # --- ADMINISTRAÇÃO ---
        elif page == "Administração" and user['admin']:
            st.title("Painel Admin")
            t1, t2 = st.tabs(["Usuários", "Sistema"])
            with t1:
                c_new, c_list = st.columns([1, 2])
                with c_new:
                    with st.container(border=True):
                        st.subheader("Novo")
                        nu = st.text_input("Nome"); ns = st.text_input("Senha"); na = st.checkbox("Admin")
                        if st.button("Criar User", use_container_width=True):
                            supabase.table("usuarios").insert({"username":nu,"senha":ns,"admin":na,"trocar_senha":True}).execute()
                            registrar_log(user['username'], "New User", nu); st.rerun()
                with c_list:
                    users = buscar_usuarios()
                    for u in users:
                        with st.expander(f"{u['username']} {'(Admin)' if u['admin'] else ''}"):
                            c_x, c_y = st.columns(2)
                            if c_x.button("Resetar Senha", key=f"r{u['id']}"):
                                supabase.table("usuarios").update({"trocar_senha":True}).eq("id", u['id']).execute()
                                st.toast("Resetado!")
                            if u['username'] != user['username'] and c_y.button("Excluir", key=f"d{u['id']}", type="primary"):
                                supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()
            with t2:
                st.subheader("Segurança")
                logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(50).execute().data
                if logs: st.dataframe(pd.DataFrame(logs)[['data_hora','usuario','acao','detalhe']], use_container_width=True, height=200)
                full_data = buscar_dados()
                if full_data: st.download_button("📥 Backup (CSV)", pd.DataFrame(full_data).to_csv(index=False).encode('utf-8'), "backup.csv", "text/csv")
                st.divider()
                check = st.text_input("Para limpar frases digite: QUERO APAGAR TUDO")
                if st.button("LIMPAR BANCO DE FRASES", type="primary"):
                    if check == "QUERO APAGAR TUDO":
                        supabase.table("frases").delete().neq("id", 0).execute()
                        registrar_log(user['username'], "WIPE", "ALL"); st.rerun()

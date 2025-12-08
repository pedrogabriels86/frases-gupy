import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Frases Gupy", page_icon="📋", layout="wide")

# --- CONEXÃO COM O BANCO DE DADOS ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Erro na configuração das senhas.")
    st.stop()

# --- FUNÇÕES ---
def verificar_login(usuario, senha):
    try:
        response = supabase.table("usuarios").select("*").eq("username", usuario).eq("senha", senha).execute()
        if len(response.data) > 0: return response.data[0]
        return None
    except: return None

def buscar_dados():
    return supabase.table("frases").select("*").execute().data

# --- INTERFACE ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# LOGIN
if st.session_state["usuario_logado"] is None:
    st.title("🔐 Acesso Restrito")
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("login"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                user = verificar_login(u, s)
                if user:
                    st.session_state["usuario_logado"] = user
                    st.rerun()
                else:
                    st.error("Acesso negado.")

# SISTEMA
else:
    user = st.session_state["usuario_logado"]
    
    with st.sidebar:
        st.header(f"Olá, {user['username']}")
        st.divider()
        menu = st.radio("Navegação", ["🏠 Biblioteca", "📝 Gerenciar", "👥 Usuários", "Sair"])
        if menu == "Sair":
            st.session_state["usuario_logado"] = None
            st.rerun()

    # --- BIBLIOTECA ---
    if menu == "🏠 Biblioteca":
        st.title("📂 Frases Gupy")
        
        # DICA VISUAL PARA O USUÁRIO
        st.info("💡 **Dica:** Para copiar uma frase, passe o mouse sobre ela e clique no ícone 📋 que aparece no canto direito.")
        
        dados = buscar_dados()
        
        if dados:
            # BUSCA
            termo = st.text_input("🔎 Pesquisar (Enter para buscar)", placeholder="Digite empresa, documento ou conteúdo...")
            
            filtrados = dados
            if termo:
                t = termo.lower()
                filtrados = [f for f in dados if t in str(f).lower()]
            
            # FILTROS
            c1, c2 = st.columns(2)
            empresas = sorted(list(set([f['empresa'] for f in filtrados])))
            emp_sel = c1.selectbox("Empresa", ["Todas"] + empresas)
            if emp_sel != "Todas": filtrados = [f for f in filtrados if f['empresa'] == emp_sel]
            
            docs = sorted(list(set([f['documento'] for f in filtrados])))
            doc_sel = c2.selectbox("Documento", ["Todos"] + docs)
            if doc_sel != "Todos": filtrados = [f for f in filtrados if f['documento'] == doc_sel]
            
            st.divider()
            
            # EXIBIÇÃO EM CARTÕES (NOVO VISUAL)
            motivos = sorted(list(set([f['motivo'] for f in filtrados])))
            for m in motivos:
                st.subheader(f"📌 {m}")
                grupo = [f for f in filtrados if f['motivo'] == m]
                
                for f in grupo:
                    # Container com borda para destacar cada frase
                    with st.container(border=True):
                        col_txt, col_info = st.columns([3, 1])
                        with col_txt:
                            st.caption(f"🏢 {f['empresa']}  |  📄 {f['documento']}")
                            # O st.code é o segredo do botão copiar
                            st.code(f['conteudo'], language="text")
        else:
            st.warning("Banco de dados vazio.")

    # --- GERENCIAR ---
    elif menu == "📝 Gerenciar":
        st.title("Gerenciar Frases")
        t1, t2, t3 = st.tabs(["Nova", "Editar", "Importar"])
        
        with t1:
            with st.form("add"):
                e = st.text_input("Empresa")
                d = st.text_input("Documento")
                m = st.text_input("Motivo")
                c = st.text_area("Frase")
                if st.form_submit_button("Salvar"):
                    supabase.table("frases").insert({"empresa":e,"documento":d,"motivo":m,"conteudo":c}).execute()
                    st.success("Salvo!")
                    time.sleep(1)
                    st.rerun()
                    
        with t2:
            dados = buscar_dados()
            # Dicionário reverso para achar o ID
            mapa = {f"{f['empresa']} | {f['documento']} | {f['id']}": f for f in dados}
            sel = st.selectbox("Selecione para editar:", list(mapa.keys()))
            if sel:
                obj = mapa[sel]
                with st.form("edit"):
                    ne = st.text_input("Empresa", obj['empresa'])
                    nd = st.text_input("Documento", obj['documento'])
                    nm = st.text_input("Motivo", obj['motivo'])
                    nc = st.text_area("Conteúdo", obj['conteudo'])
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Salvar"):
                        supabase.table("frases").update({"empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc}).eq("id", obj['id']).execute()
                        st.success("Atualizado!")
                        time.sleep(1)
                        st.rerun()
                    if c2.form_submit_button("Excluir", type="primary"):
                        supabase.table("frases").delete().eq("id", obj['id']).execute()
                        st.rerun()
                        
        with t3:
            st.write("Importar CSV ou Excel (Colunas: empresa, documento, motivo, conteudo)")
            upl = st.file_uploader("Arquivo", type=['csv','xlsx'])
            if upl:
                try:
                    df = pd.read_csv(upl) if upl.name.endswith('.csv') else pd.read_excel(upl)
                    df.columns = [c.lower().strip() for c in df.columns]
                    if st.button("Confirmar Importação"):
                        supabase.table("frases").insert(df.to_dict('records')).execute()
                        st.success("Importado!")
                except Exception as e: st.error(f"Erro: {e}")

    # --- USUARIOS ---
    elif menu == "👥 Usuários":
        if user['admin']:
            with st.form("u"):
                u = st.text_input("User")
                s = st.text_input("Pass")
                a = st.checkbox("Admin")
                if st.form_submit_button("Criar"):
                    supabase.table("usuarios").insert({"username":u,"senha":s,"admin":a}).execute()
                    st.success("Criado!")
            st.dataframe(supabase.table("usuarios").select("username,admin").execute().data)
        else:
            st.error("Acesso restrito.")

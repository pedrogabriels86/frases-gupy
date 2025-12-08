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
        # Busca o usuário e a flag trocar_senha
        response = supabase.table("usuarios").select("*").eq("username", usuario).eq("senha", senha).execute()
        if len(response.data) > 0: return response.data[0]
        return None
    except: return None

def buscar_dados():
    return supabase.table("frases").select("*").execute().data

def buscar_usuarios():
    return supabase.table("usuarios").select("*").order("id").execute().data

# --- INTERFACE ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# 1. TELA DE LOGIN (Se ninguém estiver logado)
if st.session_state["usuario_logado"] is None:
    st.title("🔐 Acesso Restrito")
    st.caption("Sistema interno de gestão de frases")
    
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
                    st.error("Usuário ou senha incorretos.")

# 2. SISTEMA (Usuário logado)
else:
    user = st.session_state["usuario_logado"]
    
    # --- BLOQUEIO: TROCA DE SENHA OBRIGATÓRIA ---
    # Se a coluna 'trocar_senha' for TRUE, travamos o usuário aqui.
    if user.get('trocar_senha') is True:
        st.warning("⚠️ **Atenção:** Este é seu primeiro acesso ou sua senha foi resetada.")
        st.subheader("🔒 Defina sua nova senha")
        
        with st.form("troca_senha_obrigatoria"):
            nova_senha_1 = st.text_input("Nova Senha", type="password")
            nova_senha_2 = st.text_input("Confirme a Nova Senha", type="password")
            
            if st.form_submit_button("Atualizar Senha e Entrar"):
                if nova_senha_1 == nova_senha_2 and len(nova_senha_1) > 0:
                    # Atualiza a senha e desmarca a obrigação de troca
                    supabase.table("usuarios").update({
                        "senha": nova_senha_1, 
                        "trocar_senha": False
                    }).eq("id", user['id']).execute()
                    
                    st.success("Senha atualizada com sucesso! Redirecionando...")
                    
                    # Atualiza a sessão local para liberar o acesso
                    user['trocar_senha'] = False
                    user['senha'] = nova_senha_1
                    st.session_state["usuario_logado"] = user
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("As senhas não conferem ou estão vazias.")
    
    # --- SISTEMA LIBERADO (Se trocar_senha for FALSE) ---
    else:
        with st.sidebar:
            st.header(f"Olá, {user['username']}")
            if user['admin']: st.caption("Status: Administrador")
            else: st.caption("Status: Usuário Padrão")
            
            st.divider()
            menu = st.radio("Navegação", ["🏠 Biblioteca", "📝 Gerenciar Frases", "👥 Gerenciar Usuários", "Sair"])
            
            if menu == "Sair":
                st.session_state["usuario_logado"] = None
                st.rerun()

        # --- MENU: BIBLIOTECA ---
        if menu == "🏠 Biblioteca":
            st.title("📂 Frases Gupy")
            st.info("💡 **Dica:** Para copiar, passe o mouse sobre a frase e clique no ícone 📋.")
            
            dados = buscar_dados()
            if dados:
                termo = st.text_input("🔎 Pesquisar", placeholder="Busque por qualquer termo...")
                filtrados = dados
                if termo:
                    t = termo.lower()
                    filtrados = [f for f in dados if t in str(f).lower()]
                
                c1, c2 = st.columns(2)
                empresas = sorted(list(set([f['empresa'] for f in filtrados])))
                emp_sel = c1.selectbox("Empresa", ["Todas"] + empresas)
                if emp_sel != "Todas": filtrados = [f for f in filtrados if f['empresa'] == emp_sel]
                
                docs = sorted(list(set([f['documento'] for f in filtrados])))
                doc_sel = c2.selectbox("Documento", ["Todos"] + docs)
                if doc_sel != "Todos": filtrados = [f for f in filtrados if f['documento'] == doc_sel]
                
                st.divider()
                
                motivos = sorted(list(set([f['motivo'] for f in filtrados])))
                for m in motivos:
                    st.subheader(f"📌 {m}")
                    grupo = [f for f in filtrados if f['motivo'] == m]
                    for f in grupo:
                        with st.container(border=True):
                            st.caption(f"🏢 {f['empresa']}  |  📄 {f['documento']}")
                            st.code(f['conteudo'], language="text")
            else:
                st.warning("Banco de dados vazio.")

        # --- MENU: GERENCIAR FRASES ---
        elif menu == "📝 Gerenciar Frases":
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
                st.write("Importar CSV ou Excel")
                upl = st.file_uploader("Arquivo", type=['csv','xlsx'])
                if upl:
                    try:
                        df = pd.read_csv(upl) if upl.name.endswith('.csv') else pd.read_excel(upl)
                        df.columns = [c.lower().strip() for c in df.columns]
                        if st.button("Confirmar Importação"):
                            supabase.table("frases").insert(df.to_dict('records')).execute()
                            st.success("Importado!")
                    except Exception as e: st.error(f"Erro: {e}")

        # --- MENU: GERENCIAR USUÁRIOS ---
        elif menu == "👥 Gerenciar Usuários":
            if user['admin']:
                st.title("Controle de Usuários")
                tab_u1, tab_u2 = st.tabs(["➕ Novo Usuário", "⚙️ Editar/Excluir"])
                
                with tab_u1:
                    st.caption("Ao criar um usuário, ele será obrigado a trocar a senha no primeiro acesso.")
                    with st.form("new_user"):
                        u = st.text_input("Nome do Usuário")
                        s = st.text_input("Senha Inicial")
                        a = st.checkbox("É Administrador?")
                        
                        if st.form_submit_button("Criar Usuário"):
                            try:
                                # Forçamos trocar_senha = True na criação
                                supabase.table("usuarios").insert({
                                    "username":u, 
                                    "senha":s, 
                                    "admin":a, 
                                    "trocar_senha": True
                                }).execute()
                                st.success(f"Usuário {u} criado! Ele pedirá troca de senha ao entrar.")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e: st.error(f"Erro: {e}")

                with tab_u2:
                    lista_usuarios = buscar_usuarios()
                    if lista_usuarios:
                        opcoes_user = {f"{u['id']} - {u['username']}": u for u in lista_usuarios}
                        escolha_user = st.selectbox("Selecione usuário:", list(opcoes_user.keys()))
                        if escolha_user:
                            alvo = opcoes_user[escolha_user]
                            st.divider()
                            with st.form("edit_user"):
                                n_nome = st.text_input("Nome", alvo['username'])
                                n_senha = st.text_input("Senha", alvo['senha'])
                                n_admin = st.checkbox("Admin?", alvo['admin'])
                                # Admin pode forçar o reset de senha de alguém
                                n_reset = st.checkbox("Forçar troca de senha no próximo login?", value=alvo['trocar_senha'])
                                
                                c1, c2 = st.columns(2)
                                if c1.form_submit_button("Salvar"):
                                    supabase.table("usuarios").update({
                                        "username":n_nome, "senha":n_senha, 
                                        "admin":n_admin, "trocar_senha":n_reset
                                    }).eq("id", alvo['id']).execute()
                                    st.success("Atualizado!")
                                    time.sleep(1)
                                    st.rerun()
                                if c2.form_submit_button("Excluir", type="primary"):
                                    if alvo['username'] != user['username']:
                                        supabase.table("usuarios").delete().eq("id", alvo['id']).execute()
                                        st.rerun()
                                    else: st.error("Não pode se excluir.")
                        
                        st.dataframe(pd.DataFrame(lista_usuarios)[['username', 'admin', 'trocar_senha']], use_container_width=True)
            else:
                st.error("Acesso restrito.")

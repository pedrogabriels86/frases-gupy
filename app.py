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

def buscar_usuarios():
    return supabase.table("usuarios").select("*").order("id").execute().data

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
        if user['admin']: st.caption("Status: Administrador")
        else: st.caption("Status: Usuário Padrão")
        
        st.divider()
        menu = st.radio("Navegação", ["🏠 Biblioteca", "📝 Gerenciar Frases", "👥 Gerenciar Usuários", "Sair"])
        if menu == "Sair":
            st.session_state["usuario_logado"] = None
            st.rerun()

    # --- BIBLIOTECA ---
    if menu == "🏠 Biblioteca":
        st.title("📂 Frases Gupy")
        st.info("💡 **Dica:** Para copiar uma frase, passe o mouse sobre ela e clique no ícone 📋 no canto direito.")
        
        dados = buscar_dados()
        
        if dados:
            termo = st.text_input("🔎 Pesquisar (Enter para buscar)", placeholder="Digite empresa, documento ou conteúdo...")
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

    # --- GERENCIAR FRASES ---
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

    # --- GERENCIAR USUÁRIOS (ATUALIZADO) ---
    elif menu == "👥 Gerenciar Usuários":
        if user['admin']:
            st.title("Controle de Usuários")
            
            tab_u1, tab_u2 = st.tabs(["➕ Novo Usuário", "⚙️ Editar/Excluir"])
            
            # ABA 1: CRIAR
            with tab_u1:
                with st.form("new_user"):
                    u = st.text_input("Nome do Usuário")
                    s = st.text_input("Senha")
                    a = st.checkbox("É Administrador?")
                    if st.form_submit_button("Criar Usuário"):
                        try:
                            supabase.table("usuarios").insert({"username":u, "senha":s, "admin":a}).execute()
                            st.success(f"Usuário {u} criado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao criar: {e}")

            # ABA 2: EDITAR E EXCLUIR (NOVA)
            with tab_u2:
                lista_usuarios = buscar_usuarios()
                
                if lista_usuarios:
                    # Cria um dicionário para identificar o usuário no selectbox
                    opcoes_user = {f"{u['id']} - {u['username']}": u for u in lista_usuarios}
                    escolha_user = st.selectbox("Selecione o usuário para editar:", list(opcoes_user.keys()))
                    
                    if escolha_user:
                        usuario_alvo = opcoes_user[escolha_user]
                        
                        st.divider()
                        st.write(f"Editando dados de: **{usuario_alvo['username']}**")
                        
                        with st.form("edit_user_form"):
                            # Campos preenchidos com os dados atuais
                            novo_nome = st.text_input("Nome", value=usuario_alvo['username'])
                            nova_senha = st.text_input("Senha", value=usuario_alvo['senha'])
                            novo_admin = st.checkbox("É Administrador?", value=usuario_alvo['admin'])
                            
                            col_salvar, col_excluir = st.columns(2)
                            
                            # Botão Salvar
                            if col_salvar.form_submit_button("💾 Salvar Alterações"):
                                supabase.table("usuarios").update({
                                    "username": novo_nome,
                                    "senha": nova_senha,
                                    "admin": novo_admin
                                }).eq("id", usuario_alvo['id']).execute()
                                st.success("Usuário atualizado!")
                                time.sleep(1)
                                st.rerun()
                            
                            # Botão Excluir
                            if col_excluir.form_submit_button("🗑️ Excluir Usuário", type="primary"):
                                # Proteção simples para não excluir a si mesmo sem querer
                                if usuario_alvo['username'] == user['username']:
                                    st.error("Você não pode excluir a si mesmo enquanto está logado!")
                                else:
                                    supabase.table("usuarios").delete().eq("id", usuario_alvo['id']).execute()
                                    st.warning(f"Usuário {usuario_alvo['username']} foi excluído.")
                                    time.sleep(1)
                                    st.rerun()
                                    
                    st.divider()
                    st.subheader("Lista Geral")
                    # Mostra a tabela completa apenas para visualização
                    st.dataframe(pd.DataFrame(lista_usuarios)[['id', 'username', 'admin', 'senha']], use_container_width=True)
                else:
                    st.warning("Nenhum usuário encontrado.")
            
        else:
            st.error("🚫 Acesso restrito. Você não tem permissão de administrador.")

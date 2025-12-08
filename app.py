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

# 1. TELA DE LOGIN
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
                    st.error("Dados incorretos.")

# 2. SISTEMA
else:
    user = st.session_state["usuario_logado"]
    
    # --- BLOQUEIO: TROCA DE SENHA ---
    if user.get('trocar_senha') is True:
        st.warning("⚠️ Atenção: Defina sua nova senha.")
        with st.form("troca"):
            n1 = st.text_input("Nova Senha", type="password")
            n2 = st.text_input("Confirme", type="password")
            if st.form_submit_button("Atualizar"):
                if n1 == n2 and len(n1) > 0:
                    supabase.table("usuarios").update({"senha": n1, "trocar_senha": False}).eq("id", user['id']).execute()
                    st.success("Senha atualizada!")
                    user['trocar_senha'] = False
                    st.session_state["usuario_logado"] = user
                    time.sleep(1); st.rerun()
                else: st.error("Senhas inválidas.")
    
    # --- MENU PRINCIPAL ---
    else:
        with st.sidebar:
            st.header(f"Olá, {user['username']}")
            if user['admin']: st.caption("Status: Super Usuário / Admin")
            st.divider()
            
            opcoes_menu = ["🏠 Biblioteca", "📝 Gerenciar Frases", "👥 Gerenciar Usuários"]
            if user['admin']:
                opcoes_menu.append("🚧 Super Admin (Danger)") # Só aparece para admin
            opcoes_menu.append("Sair")
            
            menu = st.radio("Navegação", opcoes_menu)
            
            if menu == "Sair":
                st.session_state["usuario_logado"] = None
                st.rerun()

        # --- BIBLIOTECA ---
        if menu == "🏠 Biblioteca":
            st.title("📂 Frases Gupy")
            st.info("💡 **Dica:** Clique no ícone 📋 para copiar.")
            dados = buscar_dados()
            if dados:
                termo = st.text_input("🔎 Pesquisar", placeholder="Busque...")
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
                for m in sorted(list(set([f['motivo'] for f in filtrados]))):
                    st.subheader(f"📌 {m}")
                    for f in [x for x in filtrados if x['motivo'] == m]:
                        with st.container(border=True):
                            st.caption(f"🏢 {f['empresa']} | 📄 {f['documento']}")
                            st.code(f['conteudo'], language="text")
            else: st.warning("Banco vazio.")

        # --- GERENCIAR FRASES ---
        elif menu == "📝 Gerenciar Frases":
            st.title("Gerenciar Frases")
            t1, t2, t3 = st.tabs(["➕ Nova", "✏️ Editar", "📤 Importar"])
            
            with t1:
                with st.form("add"):
                    e = st.text_input("Empresa"); d = st.text_input("Documento"); m = st.text_input("Motivo"); c = st.text_area("Frase")
                    if st.form_submit_button("Salvar") and c:
                        if len(supabase.table("frases").select("id").eq("conteudo", c).execute().data) > 0:
                            st.error("Frase já existe!")
                        else:
                            supabase.table("frases").insert({"empresa":e,"documento":d,"motivo":m,"conteudo":c}).execute()
                            st.success("Salvo!"); time.sleep(1); st.rerun()
            
            with t2:
                dados = buscar_dados()
                if dados:
                    mapa = {f"{f['empresa']} | {f['documento']} | {f['id']}": f for f in dados}
                    sel = st.selectbox("Editar:", list(mapa.keys()))
                    if sel:
                        obj = mapa[sel]
                        with st.form("edit"):
                            ne = st.text_input("Empresa", obj['empresa']); nd = st.text_input("Documento", obj['documento'])
                            nm = st.text_input("Motivo", obj['motivo']); nc = st.text_area("Conteúdo", obj['conteudo'])
                            c1, c2 = st.columns(2)
                            if c1.form_submit_button("Salvar"):
                                supabase.table("frases").update({"empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc}).eq("id", obj['id']).execute()
                                st.success("Atualizado!"); time.sleep(1); st.rerun()
                            if c2.form_submit_button("Excluir", type="primary"):
                                supabase.table("frases").delete().eq("id", obj['id']).execute()
                                st.rerun()
            
            with t3:
                upl = st.file_uploader("CSV/Excel", type=['csv','xlsx'])
                if upl and st.button("Importar"):
                    try:
                        df = pd.read_csv(upl) if upl.name.endswith('.csv') else pd.read_excel(upl)
                        df.columns = [c.lower().strip() for c in df.columns]
                        existentes = set([str(f['conteudo']).strip() for f in buscar_dados()])
                        novos = [row for i, row in df.iterrows() if str(row['conteudo']).strip() not in existentes]
                        if novos:
                            supabase.table("frases").insert([{"empresa":r['empresa'],"documento":r['documento'],"motivo":r['motivo'],"conteudo":r['conteudo']} for r in novos]).execute()
                            st.success(f"{len(novos)} frases importadas!")
                        else: st.warning("Nenhuma frase nova.")
                        time.sleep(2); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

        # --- GERENCIAR USUÁRIOS ---
        elif menu == "👥 Gerenciar Usuários":
            if user['admin']:
                st.title("Usuários")
                t1, t2 = st.tabs(["Novo", "Editar"])
                with t1:
                    with st.form("nu"):
                        u = st.text_input("Nome"); s = st.text_input("Senha"); a = st.checkbox("Admin")
                        if st.form_submit_button("Criar"):
                            supabase.table("usuarios").insert({"username":u,"senha":s,"admin":a,"trocar_senha":True}).execute()
                            st.success("Criado!"); time.sleep(1); st.rerun()
                with t2:
                    usrs = buscar_usuarios()
                    if usrs:
                        sel = st.selectbox("User:", [f"{u['id']}-{u['username']}" for u in usrs])
                        if sel:
                            uid = int(sel.split('-')[0])
                            tgt = next(u for u in usrs if u['id']==uid)
                            with st.form("eu"):
                                nn = st.text_input("Nome", tgt['username']); ns = st.text_input("Senha", tgt['senha'])
                                na = st.checkbox("Admin", tgt['admin']); nr = st.checkbox("Resetar Senha?", tgt['trocar_senha'])
                                c1,c2=st.columns(2)
                                if c1.form_submit_button("Salvar"):
                                    supabase.table("usuarios").update({"username":nn,"senha":ns,"admin":na,"trocar_senha":nr}).eq("id",uid).execute()
                                    st.success("Salvo!"); time.sleep(1); st.rerun()
                                if c2.form_submit_button("Excluir",type="primary"):
                                    if tgt['username'] != user['username']:
                                        supabase.table("usuarios").delete().eq("id",uid).execute(); st.rerun()
                                    else: st.error("Não pode se excluir.")
            else: st.error("Restrito.")

        # --- SUPER ADMIN (ZONA DE PERIGO) ---
        elif menu == "🚧 Super Admin (Danger)":
            st.title("🚧 Zona de Perigo (Super Usuário)")
            st.error("Atenção: As ações abaixo são irreversíveis. Use com extremo cuidado.")
            
            st.divider()
            
            col_danger1, col_danger2 = st.columns(2)
            
            # 1. APAGAR TODAS AS FRASES
            with col_danger1:
                with st.container(border=True):
                    st.subheader("🔥 Apagar TODAS as Frases")
                    st.write("Isso vai limpar a biblioteca inteira. O banco ficará vazio.")
                    st.write(f"Total atual: **{len(buscar_dados())} frases**")
                    
                    with st.expander("Abrir controles de exclusão"):
                        confirmacao_frase = st.text_input("Digite 'QUERO APAGAR TUDO' para confirmar:", key="del_all_phrases")
                        
                        if st.button("💣 EXCLUIR TODAS AS FRASES", type="primary"):
                            if confirmacao_frase == "QUERO APAGAR TUDO":
                                # Deleta tudo onde ID não é zero (ou seja, tudo)
                                supabase.table("frases").delete().neq("id", 0).execute()
                                st.toast("💥 Todas as frases foram deletadas!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.warning("Frase de confirmação incorreta.")

            # 2. APAGAR TODOS OS USUÁRIOS (MENOS VOCÊ)
            with col_danger2:
                with st.container(border=True):
                    st.subheader("💀 Apagar Usuários")
                    st.write("Isso exclui TODOS os usuários cadastrados, **exceto você**.")
                    st.write(f"Total atual: **{len(buscar_usuarios())} usuários**")
                    
                    with st.expander("Abrir controles de exclusão"):
                        confirmacao_user = st.text_input("Digite 'RESETAR USUARIOS' para confirmar:", key="del_all_users")
                        
                        if st.button("💣 EXCLUIR TODOS OS USUÁRIOS", type="primary"):
                            if confirmacao_user == "RESETAR USUARIOS":
                                # Deleta todos onde username é diferente do seu
                                supabase.table("usuarios").delete().neq("username", user['username']).execute()
                                st.toast(f"💥 Usuários deletados! Apenas {user['username']} restou.")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.warning("Frase de confirmação incorreta.")

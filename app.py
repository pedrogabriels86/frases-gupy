import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time
from datetime import datetime
import io

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

# FUNÇÃO NOVA: REGISTRAR LOG
def registrar_log(usuario, acao, detalhe):
    try:
        supabase.table("logs").insert({
            "usuario": usuario,
            "acao": acao,
            "detalhe": detalhe,
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
    except Exception as e:
        print(f"Erro ao logar: {e}")

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
                    registrar_log(user['username'], "Troca de Senha", "Usuário definiu nova senha")
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
                opcoes_menu.append("🚧 Super Admin (Logs/Backup)") 
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
                            if f.get('revisado_por'):
                                try:
                                    dt = datetime.strptime(f['data_revisao'], '%Y-%m-%d').strftime('%d/%m/%Y')
                                    st.markdown(f":white_check_mark: <small style='color:green'>Revisado por <b>{f['revisado_por']}</b> em {dt}</small>", unsafe_allow_html=True)
                                except: pass
            else: st.warning("Banco vazio.")

        # --- GERENCIAR FRASES ---
        elif menu == "📝 Gerenciar Frases":
            st.title("Gerenciar Frases")
            t1, t2, t3 = st.tabs(["➕ Nova", "✏️ Editar", "📤 Importar"])
            
            # 1. NOVA
            with t1:
                with st.form("add"):
                    col_a, col_b = st.columns(2)
                    e = col_a.text_input("Empresa"); d = col_b.text_input("Documento")
                    m = st.text_input("Motivo"); c = st.text_area("Frase")
                    st.caption(f"ℹ️ Auditoria: **{user['username']}** em **{datetime.now().strftime('%d/%m/%Y')}**")

                    if st.form_submit_button("Salvar") and c:
                        if len(supabase.table("frases").select("id").eq("conteudo", c).execute().data) > 0:
                            st.error("Frase já existe!")
                        else:
                            payload = {
                                "empresa":e, "documento":d, "motivo":m, "conteudo":c,
                                "revisado_por": user['username'],
                                "data_revisao": datetime.now().strftime('%Y-%m-%d')
                            }
                            supabase.table("frases").insert(payload).execute()
                            # LOG
                            registrar_log(user['username'], "Criou Frase", f"Empresa: {e} | Motivo: {m}")
                            st.success("Salvo!"); time.sleep(1); st.rerun()
            
            # 2. EDITAR
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
                            st.caption(f"📝 Atualizando auditoria para: **{user['username']}**")
                            
                            c1, c2 = st.columns(2)
                            if c1.form_submit_button("Salvar"):
                                supabase.table("frases").update({
                                    "empresa":ne,"documento":nd,"motivo":nm,"conteudo":nc,
                                    "revisado_por": user['username'],
                                    "data_revisao": datetime.now().strftime('%Y-%m-%d')
                                }).eq("id", obj['id']).execute()
                                # LOG
                                registrar_log(user['username'], "Editou Frase", f"ID: {obj['id']} | Empresa: {ne}")
                                st.success("Atualizado!"); time.sleep(1); st.rerun()
                                
                            if c2.form_submit_button("Excluir", type="primary"):
                                supabase.table("frases").delete().eq("id", obj['id']).execute()
                                # LOG
                                registrar_log(user['username'], "Excluiu Frase", f"Conteúdo: {obj['conteudo'][:50]}...")
                                st.rerun()
            
            # 3. IMPORTAR
            with t3:
                upl = st.file_uploader("CSV/Excel", type=['csv','xlsx'])
                if upl and st.button("Importar"):
                    try:
                        df = pd.read_csv(upl) if upl.name.endswith('.csv') else pd.read_excel(upl)
                        df.columns = [c.lower().strip() for c in df.columns]
                        existentes = set([str(f['conteudo']).strip() for f in buscar_dados()])
                        novos = []
                        for i, row in df.iterrows():
                            if str(row['conteudo']).strip() not in existentes:
                                item = {"empresa":row['empresa'],"documento":row['documento'],"motivo":row['motivo'],"conteudo":row['conteudo']}
                                if 'revisado_por' in df.columns: item['revisado_por'] = str(row['revisado_por'])
                                if 'data_revisao' in df.columns: item['data_revisao'] = str(row['data_revisao']).split('T')[0]
                                novos.append(item)
                        if novos:
                            supabase.table("frases").insert(novos).execute()
                            registrar_log(user['username'], "Importação em Massa", f"Importou {len(novos)} frases")
                            st.success(f"{len(novos)} importados!")
                        else: st.warning("Nada novo.")
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
                            registrar_log(user['username'], "Criou Usuário", f"User: {u}")
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
                                    registrar_log(user['username'], "Editou Usuário", f"User ID: {uid}")
                                    st.success("Salvo!"); time.sleep(1); st.rerun()
                                if c2.form_submit_button("Excluir",type="primary"):
                                    if tgt['username'] != user['username']:
                                        supabase.table("usuarios").delete().eq("id",uid).execute()
                                        registrar_log(user['username'], "Excluiu Usuário", f"User: {tgt['username']}")
                                        st.rerun()
                                    else: st.error("Erro.")
            else: st.error("Restrito.")

        # --- SUPER ADMIN (BACKUP E LOGS) ---
        elif menu == "🚧 Super Admin (Logs/Backup)":
            st.title("🚧 Auditoria e Backup")
            
            tab_logs, tab_backup, tab_danger = st.tabs(["📜 Logs do Sistema", "💾 Backup de Dados", "🔥 Zona de Perigo"])
            
            # 1. LOGS
            with tab_logs:
                st.write("Histórico de ações (Quem fez o quê):")
                logs = supabase.table("logs").select("*").order("data_hora", desc=True).limit(50).execute().data
                if logs:
                    df_logs = pd.DataFrame(logs)
                    # Formata a data para ficar bonita
                    st.dataframe(df_logs[['data_hora', 'usuario', 'acao', 'detalhe']], use_container_width=True)
                else:
                    st.info("Nenhum registro de log ainda.")

            # 2. BACKUP (DOWNLOAD)
            with tab_backup:
                st.subheader("Download de Segurança")
                st.write("Baixe uma cópia de todas as frases cadastradas para o seu computador.")
                
                # Prepara o arquivo CSV
                frases_backup = buscar_dados()
                if frases_backup:
                    df_backup = pd.DataFrame(frases_backup)
                    # Converte para CSV
                    csv = df_backup.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="📥 Baixar Backup das Frases (CSV)",
                        data=csv,
                        file_name=f"backup_frases_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )
                    
                    # LOG DE BACKUP (Para saber quem baixou os dados da empresa)
                    if st.button("Registrar Backup no Log"):
                        registrar_log(user['username'], "Realizou Backup", "Download completo CSV")
                        st.success("Download registrado!")
                else:
                    st.warning("Nada para baixar.")

            # 3. ZONA DE PERIGO
            with tab_danger:
                st.error("Ações irreversíveis.")
                col1, col2 = st.columns(2)
                with col1:
                    with st.container(border=True):
                        st.subheader("🔥 Apagar Frases")
                        check = st.text_input("Digite 'QUERO APAGAR TUDO':")
                        if st.button("EXCLUIR FRASES", type="primary"):
                            if check == "QUERO APAGAR TUDO":
                                supabase.table("frases").delete().neq("id", 0).execute()
                                registrar_log(user['username'], "MASS DELETE", "Apagou todas as frases")
                                st.toast("Deletado!"); time.sleep(2); st.rerun()
                with col2:
                    with st.container(border=True):
                        st.subheader("💀 Apagar Usuários")
                        check2 = st.text_input("Digite 'RESETAR USUARIOS':")
                        if st.button("EXCLUIR USUÁRIOS", type="primary"):
                            if check2 == "RESETAR USUARIOS":
                                supabase.table("usuarios").delete().neq("username", user['username']).execute()
                                registrar_log(user['username'], "MASS DELETE USERS", "Apagou todos os usuários")
                                st.toast("Deletado!"); time.sleep(2); st.rerun()

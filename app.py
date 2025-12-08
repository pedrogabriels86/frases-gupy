import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor de Frases", layout="wide")

# --- CONEXÃO COM O BANCO DE DADOS ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Erro na configuração das senhas (secrets.toml).")
    st.stop()

# --- FUNÇÕES AUXILIARES ---
def verificar_login(usuario, senha):
    try:
        response = supabase.table("usuarios").select("*").eq("username", usuario).eq("senha", senha).execute()
        if len(response.data) > 0:
            return response.data[0]
        return None
    except:
        return None

def buscar_dados():
    return supabase.table("frases").select("*").execute().data

# --- INTERFACE ---

# Controle de Sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# TELA DE LOGIN
if st.session_state["usuario_logado"] is None:
    st.title("🔐 Acesso ao Sistema")
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                user = verificar_login(usuario, senha)
                if user:
                    st.session_state["usuario_logado"] = user
                    st.rerun()
                else:
                    st.error("Dados incorretos.")

# TELA PRINCIPAL
else:
    usuario_atual = st.session_state["usuario_logado"]
    
    # MENU LATERAL
    with st.sidebar:
        st.write(f"Olá, **{usuario_atual['username']}**")
        st.divider()
        menu = st.radio("Menu", ["🏠 Biblioteca (Busca)", "📝 Cadastrar/Importar", "👥 Usuários", "Sair"])
        
        if menu == "Sair":
            st.session_state["usuario_logado"] = None
            st.rerun()

    # --- 1. BIBLIOTECA ---
    if menu == "🏠 Biblioteca (Busca)":
        st.title("📂 Biblioteca de Frases")
        
        todos_dados = buscar_dados()
        
        if not todos_dados:
            st.warning("Nenhuma frase cadastrada no banco.")
        else:
            # PESQUISA
            st.markdown("### 🔎 Pesquisa Global")
            termo_busca = st.text_input("Digite e aperte ENTER para buscar", placeholder="Ex: Nike, Boleto, Atraso...")
            
            # FILTRAGEM
            dados_filtrados = todos_dados
            if termo_busca:
                termo = termo_busca.lower()
                dados_filtrados = [
                    f for f in todos_dados 
                    if termo in str(f['empresa']).lower() or 
                       termo in str(f['documento']).lower() or 
                       termo in str(f['motivo']).lower() or 
                       termo in str(f['conteudo']).lower()
                ]

            st.divider()

            # FILTROS
            col1, col2 = st.columns(2)
            
            empresas_unicas = sorted(list(set([f['empresa'] for f in dados_filtrados])))
            if not empresas_unicas: empresas_unicas = []
            empresa_selecionada = col1.selectbox("Refinar por Empresa", ["Todas"] + empresas_unicas)
            if empresa_selecionada != "Todas":
                dados_filtrados = [f for f in dados_filtrados if f['empresa'] == empresa_selecionada]
            
            docs_unicos = sorted(list(set([f['documento'] for f in dados_filtrados])))
            if not docs_unicos: docs_unicos = []
            doc_selecionado = col2.selectbox("Refinar por Documento", ["Todos"] + docs_unicos)
            if doc_selecionado != "Todos":
                dados_filtrados = [f for f in dados_filtrados if f['documento'] == doc_selecionado]
            
            # EXIBIÇÃO
            st.caption(f"Resultados encontrados: {len(dados_filtrados)}")
            motivos_nesta_selecao = sorted(list(set([f['motivo'] for f in dados_filtrados])))
            
            if not dados_filtrados:
                st.warning("⚠️ Nada encontrado.")
            
            for motivo in motivos_nesta_selecao:
                st.subheader(f"📌 {motivo}")
                frases_do_grupo = [f for f in dados_filtrados if f['motivo'] == motivo]
                for frase in frases_do_grupo:
                    texto_legenda = f"🏢 {frase['empresa']} | 📄 {frase['documento']}"
                    st.caption(texto_legenda) 
                    st.code(frase['conteudo'], language="text")
                    st.markdown("---") 

    # --- 2. GERENCIAR ---
    elif menu == "📝 Cadastrar/Importar":
        st.title("Gerenciamento")
        tab1, tab2, tab3 = st.tabs(["➕ Nova Frase", "✏️ Editar/Excluir", "📤 Importar (Excel/CSV)"])
        
        # ABA 1: NOVA FRASE
        with tab1:
            with st.form("nova"):
                emp = st.text_input("Empresa")
                doc = st.text_input("Documento")
                mot = st.text_input("Motivo")
                cont = st.text_area("Frase")
                if st.form_submit_button("Salvar"):
                    supabase.table("frases").insert({
                        "empresa": emp, "documento": doc, 
                        "motivo": mot, "conteudo": cont
                    }).execute()
                    st.success("Salvo!")
                    time.sleep(1)
                    st.rerun()
        
        # ABA 2: EDITAR
        with tab2:
            dados = buscar_dados()
            opcoes = {f"{f['empresa']} | {f['documento']} | {f['motivo']} (ID: {f['id']})": f for f in dados}
            escolha = st.selectbox("Busque a frase para editar:", list(opcoes.keys()))
            
            if escolha:
                alvo = opcoes[escolha]
                with st.form("editar"):
                    n_emp = st.text_input("Empresa", value=alvo['empresa'])
                    n_doc = st.text_input("Documento", value=alvo['documento'])
                    n_mot = st.text_input("Motivo", value=alvo['motivo'])
                    n_cont = st.text_area("Conteúdo", value=alvo['conteudo'])
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("💾 Atualizar"):
                        supabase.table("frases").update({
                            "empresa": n_emp, "documento": n_doc, 
                            "motivo": n_mot, "conteudo": n_cont
                        }).eq("id", alvo['id']).execute()
                        st.success("Atualizado!")
                        time.sleep(1)
                        st.rerun()
                    
                    if c2.form_submit_button("🗑️ Excluir", type="primary"):
                        supabase.table("frases").delete().eq("id", alvo['id']).execute()
                        st.error("Excluído!")
                        time.sleep(1)
                        st.rerun()
        
        # ABA 3: IMPORTAÇÃO (Excel + CSV)
        with tab3:
            st.header("Importação em Massa")
            st.info("Aceitamos arquivos Excel (.xlsx) ou CSV. As colunas obrigatórias são: empresa, documento, motivo, conteudo.")
            
            # Download de Modelo (Gera um CSV simples de exemplo)
            csv_modelo = "empresa,documento,motivo,conteudo\nMinha Empresa,NF,Atraso,Exemplo de frase aqui"
            st.download_button("📥 Baixar Modelo (CSV)", csv_modelo, "modelo.csv", "text/csv")
            
            st.divider()
            
            # Aceita CSV e Excel
            arquivo = st.file_uploader("Solte seu arquivo aqui", type=["csv", "xlsx"])
            
            if arquivo:
                try:
                    # Lógica inteligente para detectar o tipo
                    if arquivo.name.endswith('.csv'):
                        df = pd.read_csv(arquivo, sep=None, engine='python')
                    else:
                        df = pd.read_excel(arquivo) # Aqui usamos o openpyxl
                    
                    # Normalizar colunas (tudo minúsculo e sem espaços nas pontas)
                    df.columns = [str(c).lower().strip() for c in df.columns]
                    
                    # Verifica colunas
                    colunas_necessarias = ['empresa', 'documento', 'motivo', 'conteudo']
                    
                    # Verifica se todas as necessárias estão presentes
                    if all(col in df.columns for col in colunas_necessarias):
                        st.write("Prévia dos dados:")
                        st.dataframe(df.head())
                        st.caption(f"Total de linhas para importar: {len(df)}")
                        
                        if st.button("✅ Confirmar Importação"):
                            # Pega só as colunas certas e converte para dicionário
                            dados_para_enviar = df[colunas_necessarias].astype(str).to_dict(orient='records')
                            
                            # Envia para o Supabase
                            supabase.table("frases").insert(dados_para_enviar).execute()
                            
                            st.success(f"{len(df)} frases importadas com sucesso!")
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.error(f"Erro: O arquivo precisa ter as colunas: {', '.join(colunas_necessarias)}")
                        st.warning(f"Colunas que o sistema encontrou no seu arquivo: {list(df.columns)}")
                
                except Exception as e:
                    st.error(f"Erro ao ler arquivo: {e}")

    # --- 3. USUÁRIOS ---
    elif menu == "👥 Usuários":
        if usuario_atual['admin']:
            st.title("Admin: Usuários")
            with st.form("new_user"):
                u = st.text_input("User")
                s = st.text_input("Pass")
                a = st.checkbox("Admin?")
                if st.form_submit_button("Criar"):
                    supabase.table("usuarios").insert({"username":u, "senha":s, "admin":a}).execute()
                    st.success("Criado!")
            st.dataframe(supabase.table("usuarios").select("id, username, admin").execute().data)
        else:
            st.warning("Acesso restrito a administradores.")
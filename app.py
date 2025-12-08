import streamlit as st
from supabase import create_client, Client
# ... (outras importações)
import extra_streamlit_components as stx

# ... (Seções 1 e 2)

# ==============================================================================
# 2. CSS CUSTOMIZADO (MÁXIMA ESTABILIDADE E LARGURA TOTAL)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    
    /* 1. Ocultar e Zerar Margens/Paddings do Streamlit Padrão */
    header[data-testid="stHeader"], div[data-testid="stToolbar"], div[data-testid="stDecoration"], footer { 
        display: none !important; 
    }
    
    /* Zera Margem do Corpo Principal: PADDING LATERAL AGRESSIVO PARA LARGURA TOTAL */
    .block-container {
        padding-top: 0.8rem !important; 
        padding-bottom: 3rem; 
        margin-top: 0 !important;
        max-width: 100%;
        padding-left: 1.5rem; /* MUITO MENOS espaço em branco nas laterais */
        padding-right: 1.5rem;
    }
    
    /* Zera Margens Internas de Colunas e Blocks que causam espaços indesejados */
    div[data-testid^="stVerticalBlock"] > div:first-child > div:nth-child(2) {
        margin-top: 0rem !important;
        padding-top: 0rem !important;
    }
    
    /* 2. Estilo do Container do Header (Com Largura Estreita) */
    div[data-testid="stVerticalBlock"] > div:first-child > div:first-child { 
        background-color: white;
        border-bottom: 1px solid #E2E8F0;
        padding: 0.9rem 1.5rem; /* Ajustado para 1.5rem para corresponder ao padding do block-container */
        margin: -0.8rem -1.5rem 1.5rem -1.5rem; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        z-index: 100;
        width: 100vw; 
    }

    /* 3. Estilização do Menu (Tabs) */
    .stRadio > div[role="radiogroup"] { display: flex; gap: 8px; justify-content: flex-end; } 
    /* Mudamos para flex-end, pois o botão SAIR não estará mais nessa linha, o menu fica na extrema direita */
    
    .stRadio > div[role="radiogroup"] label {
        padding: 5px 15px; 
        border-radius: 6px; transition: all 0.2s ease;
        color: #64748B; font-weight: 500; font-size: 0.9rem;
    }
    .stRadio > div[role="radiogroup"] label:hover { background-color: #F1F5F9; color: #0F172A; }
    .stRadio > div[role="radiogroup"] label[data-checked="true"] {
        background-color: #2563EB !important; color: white !important;
        font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .stRadio > div[role="radiogroup"] label > div:first-child { display: none; }

    /* 4. Alinhamento de Usuário/Sair - DESABILITADO NA COLUNA */
    /* Este seletor não será mais usado, pois o botão Sair foi movido */
    /* Caso seja necessário exibir o usuário, ele será colocado no topo ou em um widget separado */
    
    /* 5. Ajustes gerais (para compactação) */
    h3 { margin-top: 0.5rem; margin-bottom: 0.5rem; }
    .stButton button { padding: 0.3rem 0.8rem !important; } 

    /* Elementos da Biblioteca */
    .frase-header { background-color: white; border-radius: 12px 12px 0 0; border: 1px solid #E2E8F0; border-bottom: none; padding: 10px 15px; } /* Reduzindo padding interno */
    .stCodeBlock { padding: 10px 15px !important; } /* Reduzindo padding do código */
    .card-meta { margin-top: 5px; padding-top: 5px; } /* Reduzindo espaço nos meta dados */
    
</style>
""", unsafe_allow_html=True)

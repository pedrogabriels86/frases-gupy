# ==============================================================================
# 2. CSS CUSTOMIZADO (ATUALIZADO COM ESTILO DE COPY)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1E293B; }
    .stApp { background-color: #F8FAFC; }
    
    /* 1. LIMPEZA E ESTRUTURA */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 3rem; 
        padding-left: 3rem; 
        padding-right: 3rem;
        max-width: 100%;
    }
    div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    header[data-testid="stHeader"], footer { display: none !important; }

    /* 2. HEADER E MENU */
    .header-container {
        background-color: white;
        padding: 1rem 3rem;
        margin-left: -3rem; margin-right: -3rem;
        border-bottom: 1px solid #E2E8F0;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .user-welcome { font-size: 0.9rem; color: #64748B; margin-right: 1rem; text-align: right; }
    .btn-logout button {
        background-color: transparent !important; border: 1px solid #CBD5E1 !important;
        color: #64748B !important; padding: 0.3rem 0.8rem !important; font-size: 0.8rem !important;
    }
    .btn-logout button:hover { border-color: #EF4444 !important; color: #EF4444 !important; background-color: #FEF2F2 !important; }

    .stRadio { background-color: transparent; margin-bottom: 1.5rem !important; }
    .stRadio > div[role="radiogroup"] {
        display: flex; gap: 0px; background-color: white; border-radius: 8px;
        border: 1px solid #E2E8F0; padding: 4px; width: fit-content;
    }
    .stRadio > div[role="radiogroup"] label {
        padding: 6px 16px; border-radius: 6px; border: none; margin: 0 !important;
        font-size: 0.9rem; color: #64748B; transition: all 0.2s;
    }
    .stRadio > div[role="radiogroup"] label:hover { color: #1E293B; background-color: #F1F5F9; }
    .stRadio > div[role="radiogroup"] label[data-checked="true"] {
        background-color: #EFF6FF !important; color: #2563EB !important; font-weight: 600;
    }
    .stRadio > div[role="radiogroup"] label > div:first-child { display: none; }

    /* 3. BUSCA E FILTROS */
    .search-container {
        background-color: white; padding: 1.5rem; border-radius: 12px;
        border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 1.5rem;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div { border-color: #CBD5E1; min-height: 42px; }

    /* 4. CARDS DE RESULTADO (MODULAR) */
    /* Parte Superior do Card (HTML) */
    .card-top {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-bottom: none; /* Conecta com o code block */
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 1.2rem 1.2rem 0.5rem 1.2rem;
    }
    
    /* Parte Inferior do Card (HTML) */
    .card-bottom {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-top: none; /* Conecta com o code block */
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
        padding: 0.5rem 1.2rem 1.2rem 1.2rem;
        margin-bottom: 1rem; /* Espaço entre cards verticalmente */
    }

    /* Ajuste para o Code Block parecer parte do card */
    .stCodeBlock {
        margin-bottom: 0px !important;
    }
    .stCodeBlock > div {
        border-radius: 0px !important; /* Remove arredondamento para colar nas partes de cima/baixo */
        border-left: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
    }

    .card-title { color: #1E3A8A; font-weight: 700; font-size: 1.05rem; }
    .card-badge { 
        background-color: #EFF6FF; color: #2563EB; 
        padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; border: 1px solid #DBEAFE;
    }
    .card-meta { font-size: 0.8rem; color: #94A3B8; display: flex; gap: 15px; margin-top: 5px;}

</style>
""", unsafe_allow_html=True)

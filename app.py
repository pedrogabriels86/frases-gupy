# ==============================================================================
# FUNÇÕES DE DADOS ATUALIZADAS (FILTROS LINKADOS)
# ==============================================================================

@st.cache_data(ttl=300)
def obter_dataframe_filtros():
    """Baixa apenas colunas leves para alimentar os filtros dinâmicos."""
    try:
        # Trazemos apenas o necessário para os dropdowns
        res = supabase.table("frases").select("id, empresa, documento, motivo, conteudo").execute()
        df = pd.DataFrame(res.data)
        return df
    except Exception:
        return pd.DataFrame()

def buscar_frases_final(termo=None, empresa_filtro="Todas", doc_filtro="Todos"):
    """Realiza a busca final pesada no banco de dados."""
    query = supabase.table("frases").select("*").order("id", desc=True)
    
    if termo:
        filtro = f"conteudo.ilike.%{termo}%,empresa.ilike.%{termo}%,motivo.ilike.%{termo}%"
        query = query.or_(filtro)
    
    if empresa_filtro != "Todas":
        query = query.eq("empresa", empresa_filtro)
    if doc_filtro != "Todos":
        query = query.eq("documento", doc_filtro)
        
    return query.limit(50).execute().data or []

import csv # <--- Adicionar esta importação no topo

# Função para registrar atividades no banco
def registrar_log(usuario, acao, detalhe):
    try:
        supabase.table("logs").insert({
            "usuario": usuario, 
            "acao": acao, 
            "detalhe": detalhe, 
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
    except: pass

# Função para converter dados do Supabase (JSON) para CSV (Excel)
def converter_para_csv(dados):
    if not dados: return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=dados[0].keys())
    writer.writeheader()
    writer.writerows(dados)
    return output.getvalue()

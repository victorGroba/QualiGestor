# app/utils/helpers.py

def opcao_pergunta_por_id(opcao_id):
    """Função auxiliar para templates"""
    # Importação feita AQUI DENTRO para evitar ciclo de importação (Circular Import)
    from app.models import OpcaoPergunta
    
    if not opcao_id:
        return None
    return OpcaoPergunta.query.get(opcao_id)
from app.models import OpcaoPergunta

def opcao_pergunta_por_id(opcao_id):
    """Função auxiliar para templates"""
    if not opcao_id:
        return None
    return OpcaoPergunta.query.get(opcao_id)

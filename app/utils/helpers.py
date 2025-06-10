from app.models import OpcaoPergunta

def opcao_pergunta_por_id(opcao_id):
    return OpcaoPergunta.query.get(opcao_id)

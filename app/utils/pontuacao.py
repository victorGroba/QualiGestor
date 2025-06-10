from app.models import Formulario, Auditoria, Resposta, OpcaoPergunta
from app import db
import json

def calcular_pontuacao_auditoria(auditoria):
    if not auditoria.formulario.pontuacao_ativa:
        return None

    total_peso = 0
    total_nota = 0

    for resposta in auditoria.respostas:
        pergunta = resposta.pergunta
        peso = pergunta.peso or 1  # valor padrão

        # Pega o ID da opção selecionada
        if resposta.valor_opcoes_selecionadas:
            try:
                selecao = json.loads(resposta.valor_opcoes_selecionadas)
                if isinstance(selecao, list) and selecao:
                    opcao_id = selecao[0]  # só funciona se for seleção única
                    opcao = OpcaoPergunta.query.get(opcao_id)
                    if opcao and opcao.valor:
                        try:
                            valor = float(opcao.valor)
                            resposta.nota_obtida = valor * peso
                            total_nota += resposta.nota_obtida
                            total_peso += peso
                        except ValueError:
                            resposta.nota_obtida = None
                db.session.add(resposta)
            except Exception as e:
                print("[Erro na leitura da opção]:", e)

    db.session.commit()

    return {
        "total_nota": total_nota,
        "total_peso": total_peso,
        "percentual": round((total_nota / total_peso) * 100, 2) if total_peso else 0
    }

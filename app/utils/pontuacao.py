# app/utils/pontuacao.py
"""
Utilitário para cálculo de pontuação de auditorias/checklists
ATUALIZADO: Compatível com AplicacaoQuestionario e RespostaPergunta.
Corrige erro de importação de modelos legados e ajusta cálculo de N/A.
"""

import json
from datetime import datetime
from sqlalchemy import desc

# Importa os modelos ATUAIS (Obrigatórios) - IMPORTAÇÃO CORRIGIDA PARA A VPS (..)
from ..models import AplicacaoQuestionario, RespostaPergunta, Pergunta, OpcaoPergunta

# Tenta importar modelos LEGADOS (Opcionais) para manter compatibilidade se existirem
try:
    from app.models import Auditoria
except ImportError:
    Auditoria = None

try:
    from app.models import Resposta
except ImportError:
    Resposta = None

def calcular_pontuacao_auditoria(auditoria):
    """
    Calcula a pontuação de uma auditoria (AplicacaoQuestionario) baseado nas respostas.

    Lógica de Cálculo:
      - SIM / Conforme: Ganha os pontos do peso (100%).
      - NÃO / Não Conforme: Ganha 0 pontos, mas conta na base (reduz a nota).
      - N/A (Não se Aplica): NÃO conta na base (reduz a pontuação máxima possível).

    Args:
        auditoria: Objeto AplicacaoQuestionario (ou Auditoria legado)

    Returns:
        dict: Dicionário com pontuação obtida, máxima, percentual e detalhes.
    """

    if not auditoria:
        return None

    pontuacao_obtida = 0
    pontuacao_maxima = 0
    detalhes_blocos = {}
    perguntas_nc = []

    # 1. Busca as respostas baseada no tipo de objeto (Novo ou Antigo)
    respostas = []

    # Verifica se é o modelo novo (AplicacaoQuestionario)
    if hasattr(auditoria, 'data_inicio'):
        respostas = RespostaPergunta.query.filter_by(aplicacao_id=auditoria.id).all()
    # Fallback para modelo antigo (Auditoria), se o objeto for compatível
    elif Auditoria and isinstance(auditoria, Auditoria):
        if Resposta:
            respostas = Resposta.query.filter_by(auditoria_id=auditoria.id).all()

    # Se não houver respostas, retorna estrutura zerada
    if not respostas:
        return {
            'pontuacao_obtida': 0, 'pontuacao_maxima': 0, 'percentual': 0,
            'status': 'N/A', 'cor': 'secondary', 'detalhes_blocos': {},
            'nao_conformidades': [], 'total_perguntas': 0
        }

    for resposta in respostas:
        pergunta = resposta.pergunta

        # Ignora perguntas sem peso ou Títulos
        if not pergunta.peso or pergunta.peso == 0:
            continue
        if str(pergunta.tipo).upper() == "TITULO":
            continue

        # --- LÓGICA DE N/A (Ajuste Solicitado) ---
        valor = obter_valor_resposta(resposta)
        lista_na = ['N/A', 'NA', 'N.A.', 'NÃO SE APLICA', 'NAO SE APLICA']

        # Se for N/A, ignora totalmente (não soma no máximo, nem no obtido)
        # Isso faz com que a "base 100%" seja reduzida para as perguntas restantes.
        if valor and str(valor).upper().strip() in lista_na:
            continue

        # Se é resposta válida (Sim ou Não), o peso entra na base de cálculo
        peso_pergunta = float(pergunta.peso)
        pontuacao_maxima += peso_pergunta

        # Identificar Bloco/Tópico para estatísticas
        bloco_nome = pergunta.topico.nome if pergunta.topico else "Geral"

        if bloco_nome not in detalhes_blocos:
            detalhes_blocos[bloco_nome] = {
                'pontuacao_obtida': 0, 'pontuacao_maxima': 0,
                'perguntas_total': 0, 'perguntas_conformes': 0
            }

        detalhes_blocos[bloco_nome]['pontuacao_maxima'] += peso_pergunta
        detalhes_blocos[bloco_nome]['perguntas_total'] += 1

        # Calcular Pontos da Resposta
        pontos_item = calcular_pontos_resposta(resposta, pergunta)

        if pontos_item > 0:
            pontuacao_obtida += pontos_item
            detalhes_blocos[bloco_nome]['pontuacao_obtida'] += pontos_item
            detalhes_blocos[bloco_nome]['perguntas_conformes'] += 1
        else:
            # Se pontuou 0, verificamos se é uma Não Conformidade (NC)
            lista_negativa = ['NÃO', 'NAO', 'NO', 'IRREGULAR', 'RUIM', 'REPROVADO']
            val_upper = str(valor).upper().strip()

            # É NC se tiver a flag no banco OU se o texto for explicitamente negativo
            eh_nc = getattr(resposta, 'nao_conforme', False) or (val_upper in lista_negativa)

            if eh_nc:
                tipo_nc = 'menor'
                if pergunta.peso >= 15: tipo_nc = 'critica'
                elif pergunta.peso >= 10: tipo_nc = 'maior'

                perguntas_nc.append({
                    'id': pergunta.id,
                    'texto': pergunta.texto,
                    'tipo': tipo_nc,
                    'peso': pergunta.peso,
                    'resposta': valor
                })

    # Cálculo Final do Percentual
    percentual = 0
    if pontuacao_maxima > 0:
        percentual = (pontuacao_obtida / pontuacao_maxima) * 100

    # Determinação do Status
    if percentual >= 90: status, cor = "Excelente", "success"
    elif percentual >= 75: status, cor = "Bom", "info"
    elif percentual >= 60: status, cor = "Regular", "warning"
    else: status, cor = "Insatisfatório", "danger"

    # Percentuais por bloco
    for bloco in detalhes_blocos.values():
        if bloco['pontuacao_maxima'] > 0:
            bloco['percentual'] = (bloco['pontuacao_obtida'] / bloco['pontuacao_maxima']) * 100
        else:
            bloco['percentual'] = 0

    return {
        'pontuacao_obtida': round(pontuacao_obtida, 2),
        'pontuacao_maxima': round(pontuacao_maxima, 2),
        'percentual': round(percentual, 2),
        'status': status,
        'cor': cor,
        'detalhes_blocos': detalhes_blocos,
        'nao_conformidades': perguntas_nc,
        'total_perguntas': len(respostas)
    }

def calcular_pontos_resposta(resposta, pergunta):
    """Calcula pontuação de uma resposta única (Helper)"""
    peso = float(pergunta.peso) if pergunta.peso else 0
    valor = obter_valor_resposta(resposta)

    if not valor:
        return 0

    val_upper = str(valor).upper().strip()
    tipo_upper = str(pergunta.tipo).upper()

    # 1. Sim/Não: SIM = Peso Total, NÃO = 0
    if any(x in tipo_upper for x in ["SIM", "BOOLEAN"]):
        if val_upper == "SIM": return peso
        return 0

    # 2. Nota/Escala: Proporcional (Nota/10 * Peso)
    elif any(x in tipo_upper for x in ["NOTA", "ESCALA", "NUMERICA"]):
        val_num = obter_valor_numerico(resposta)
        if val_num is not None:
            if val_num > 10: val_num = 10
            if val_num < 0: val_num = 0
            return (val_num / 10.0) * peso
        return 0

    # 3. Múltipla Escolha: Valor da opção ou Peso total
    elif "ESCOLHA" in tipo_upper:
        # Tenta pegar valor específico da opção
        opcao = OpcaoPergunta.query.filter_by(pergunta_id=pergunta.id, texto=valor).first()
        if opcao and opcao.valor is not None:
            return float(opcao.valor) * peso
        # Se não tiver valor específico, assume que resposta preenchida vale o peso
        return peso if valor else 0

    # 4. Texto: Se preenchido ganha ponto (informativo obrigatório)
    elif valor:
        return peso

    return 0

def obter_valor_resposta(resposta):
    """Recupera o valor da resposta (string) independente do modelo"""
    # Modelo Novo
    if hasattr(resposta, 'resposta') and resposta.resposta:
        return resposta.resposta
    # Modelo Antigo (Campos legados)
    if hasattr(resposta, 'valor_texto') and resposta.valor_texto:
        return resposta.valor_texto
    if hasattr(resposta, 'valor_boolean') and resposta.valor_boolean is not None:
        return "Sim" if resposta.valor_boolean else "Não"
    return None

def obter_valor_numerico(resposta):
    """Helper para converter resposta em float seguro"""
    valor = obter_valor_resposta(resposta)
    try: return float(valor) if valor else None
    except: return None

def tem_resposta_valida(resposta):
    """Helper para verificar se há resposta"""
    return obter_valor_resposta(resposta) is not None

def gerar_relatorio_pontuacao(auditoria):
    """
    Gera dados detalhados para o relatório (PDF/View).
    Inclui cálculo de tendência comparando com as 3 últimas auditorias.
    """
    resultado = calcular_pontuacao_auditoria(auditoria)
    if not resultado: return None

    resultado['auditoria_id'] = auditoria.id

    # Preenche dados de cabeçalho (Compatível com Novo e Antigo)
    if hasattr(auditoria, 'data_inicio'): # Novo
        resultado['data'] = auditoria.data_inicio.strftime('%d/%m/%Y %H:%M') if auditoria.data_inicio else ''
        resultado['usuario'] = auditoria.aplicador.nome if auditoria.aplicador else 'Sistema'
        resultado['formulario'] = auditoria.questionario.nome if auditoria.questionario else ''

        # --- Cálculo de Tendência (Novo Modelo) ---
        if auditoria.avaliado_id and auditoria.questionario_id:
            anteriores = AplicacaoQuestionario.query.filter(
                AplicacaoQuestionario.avaliado_id == auditoria.avaliado_id,
                AplicacaoQuestionario.questionario_id == auditoria.questionario_id,
                AplicacaoQuestionario.id < auditoria.id,
                AplicacaoQuestionario.status == 'FINALIZADA'
            ).order_by(desc(AplicacaoQuestionario.id)).limit(3).all()

            if anteriores:
                notas = [a.nota_final for a in anteriores if a.nota_final is not None]
                if notas:
                    media = sum(notas) / len(notas)
                    diff = resultado['percentual'] - media

                    if diff > 5:
                        resultado['tendencia'] = 'melhora'
                        resultado['tendencia_icon'] = 'fa-arrow-up'
                        resultado['tendencia_cor'] = 'success'
                    elif diff < -5:
                        resultado['tendencia'] = 'piora'
                        resultado['tendencia_icon'] = 'fa-arrow-down'
                        resultado['tendencia_cor'] = 'danger'
                    else:
                        resultado['tendencia'] = 'estavel'
                        resultado['tendencia_icon'] = 'fa-minus'
                        resultado['tendencia_cor'] = 'warning'

                    resultado['diferenca_percentual'] = round(diff, 2)

    elif hasattr(auditoria, 'data'): # Antigo
        resultado['data'] = auditoria.data.strftime('%d/%m/%Y %H:%M') if auditoria.data else ''
        resultado['usuario'] = auditoria.usuario.nome if hasattr(auditoria,'usuario') and auditoria.usuario else ''
        resultado['formulario'] = auditoria.formulario.nome if hasattr(auditoria,'formulario') and auditoria.formulario else ''

    return resultado

def exportar_pontuacao_csv(auditorias):
    """Exporta CSV com as pontuações (Compatível com ambos os modelos)"""
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Data', 'Questionário', 'Avaliado', 'Usuário', 'Pontos', 'Máximo', '%', 'Status'])

    for aud in auditorias:
        res = calcular_pontuacao_auditoria(aud)
        if res:
            # Dados básicos com verificação de atributos
            d_id = aud.id
            if hasattr(aud, 'data_inicio'): # Novo
                d_data = aud.data_inicio.strftime('%d/%m/%Y') if aud.data_inicio else ''
                d_quest = aud.questionario.nome if aud.questionario else ''
                d_aval = aud.avaliado.nome if aud.avaliado else ''
                d_user = aud.aplicador.nome if aud.aplicador else ''
            else: # Antigo
                d_data = aud.data.strftime('%d/%m/%Y') if hasattr(aud,'data') and aud.data else ''
                d_quest = aud.formulario.nome if hasattr(aud,'formulario') and aud.formulario else ''
                d_aval = aud.avaliado.nome if hasattr(aud,'avaliado') and aud.avaliado else ''
                d_user = aud.usuario.nome if hasattr(aud,'usuario') and aud.usuario else ''

            writer.writerow([
                d_id, d_data, d_quest, d_aval, d_user,
                res['pontuacao_obtida'], res['pontuacao_maxima'],
                f"{res['percentual']}%", res['status']
            ])

    return output.getvalue()
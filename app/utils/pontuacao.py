# app/utils/pontuacao.py
"""
Utilitário para cálculo de pontuação de auditorias/checklists
Sistema compatível com o modelo atual
"""

from app.models import Auditoria, Resposta, Pergunta
import json

def calcular_pontuacao_auditoria(auditoria):
    """
    Calcula a pontuação de uma auditoria baseado nas respostas
    
    Args:
        auditoria: Objeto Auditoria
    
    Returns:
        dict: Dicionário com pontuação obtida, máxima e percentual
    """
    
    if not auditoria:
        return None
    
    pontuacao_obtida = 0
    pontuacao_maxima = 0
    detalhes_blocos = {}
    perguntas_nc = []  # Perguntas com não conformidade
    
    # Buscar todas as respostas da auditoria
    respostas = Resposta.query.filter_by(auditoria_id=auditoria.id).all()
    
    for resposta in respostas:
        pergunta = resposta.pergunta
        
        # Pular perguntas sem peso ou tipo TITULO
        if not pergunta.peso or pergunta.peso == 0:
            continue
            
        if pergunta.tipo_resposta == "TITULO":
            continue
        
        peso_pergunta = float(pergunta.peso)
        pontuacao_maxima += peso_pergunta
        
        # Identificar bloco da pergunta (se houver)
        bloco_nome = "Geral"  # Nome padrão se não houver bloco
        
        if bloco_nome not in detalhes_blocos:
            detalhes_blocos[bloco_nome] = {
                'pontuacao_obtida': 0,
                'pontuacao_maxima': 0,
                'perguntas_total': 0,
                'perguntas_conformes': 0
            }
        
        detalhes_blocos[bloco_nome]['pontuacao_maxima'] += peso_pergunta
        detalhes_blocos[bloco_nome]['perguntas_total'] += 1
        
        # Calcular pontuação baseado no tipo de resposta
        pontos_obtidos = calcular_pontos_resposta(resposta, pergunta)
        
        if pontos_obtidos > 0:
            pontuacao_obtida += pontos_obtidos
            detalhes_blocos[bloco_nome]['pontuacao_obtida'] += pontos_obtidos
            detalhes_blocos[bloco_nome]['perguntas_conformes'] += 1
        else:
            # Registrar não conformidade
            if pergunta.peso >= 15:  # Perguntas críticas (peso >= 15)
                perguntas_nc.append({
                    'id': pergunta.id,
                    'texto': pergunta.texto,
                    'tipo': 'critica',
                    'peso': pergunta.peso
                })
            elif pergunta.peso >= 10:
                perguntas_nc.append({
                    'id': pergunta.id,
                    'texto': pergunta.texto,
                    'tipo': 'maior',
                    'peso': pergunta.peso
                })
    
    # Calcular percentual
    percentual = 0
    if pontuacao_maxima > 0:
        percentual = (pontuacao_obtida / pontuacao_maxima) * 100
    
    # Determinar status baseado no percentual
    if percentual >= 90:
        status = "Excelente"
        cor = "success"
    elif percentual >= 75:
        status = "Bom"
        cor = "info"
    elif percentual >= 60:
        status = "Regular"
        cor = "warning"
    else:
        status = "Insatisfatório"
        cor = "danger"
    
    # Calcular percentual por bloco
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
        'total_perguntas': len(respostas),
        'perguntas_respondidas': len([r for r in respostas if tem_resposta_valida(r)])
    }

def calcular_pontos_resposta(resposta, pergunta):
    """
    Calcula os pontos obtidos em uma resposta específica
    
    Args:
        resposta: Objeto Resposta
        pergunta: Objeto Pergunta
    
    Returns:
        float: Pontos obtidos
    """
    
    peso = float(pergunta.peso) if pergunta.peso else 0
    
    # Resposta Sim/Não
    if pergunta.tipo_resposta in ["Sim/Não", "SIM_NAO", "SIM_NAO_NA"]:
        valor = obter_valor_resposta(resposta)
        
        if valor and valor.upper() == "SIM":
            return peso
        elif valor and valor.upper() == "N/A":
            # N/A não conta nem como positivo nem negativo
            return 0
        else:
            return 0
    
    # Resposta tipo Nota
    elif pergunta.tipo_resposta in ["Nota", "NOTA"]:
        valor = obter_valor_numerico(resposta)
        if valor is not None:
            # Assumir escala de 0-10
            nota_maxima = pergunta.limite_max if hasattr(pergunta, 'limite_max') and pergunta.limite_max else 10
            nota_minima = pergunta.limite_min if hasattr(pergunta, 'limite_min') and pergunta.limite_min else 0
            
            # Normalizar para percentual
            if nota_maxima > nota_minima:
                percentual_nota = (valor - nota_minima) / (nota_maxima - nota_minima)
                return peso * percentual_nota
        return 0
    
    # Resposta tipo Texto ou Número
    elif pergunta.tipo_resposta in ["Texto", "TEXTO", "Numero", "NUMERO"]:
        valor = obter_valor_resposta(resposta)
        # Se preencheu, ganha pontuação total
        if valor and str(valor).strip():
            return peso
        return 0
    
    # Múltipla escolha
    elif pergunta.tipo_resposta in ["Múltipla Escolha", "MULTIPLA_ESCOLHA", "Única Escolha", "UNICA_ESCOLHA"]:
        valor = obter_valor_resposta(resposta)
        if valor:
            # Para simplificar, se selecionou algo, ganha pontuação
            return peso
        return 0
    
    return 0

def obter_valor_resposta(resposta):
    """
    Obtém o valor da resposta independente do formato armazenado
    
    Args:
        resposta: Objeto Resposta
    
    Returns:
        Valor da resposta ou None
    """
    
    # Tentar diferentes campos onde a resposta pode estar
    if hasattr(resposta, 'valor_texto') and resposta.valor_texto:
        return resposta.valor_texto
    
    if hasattr(resposta, 'valor_boolean') and resposta.valor_boolean is not None:
        return "Sim" if resposta.valor_boolean else "Não"
    
    if hasattr(resposta, 'valor_numero') and resposta.valor_numero is not None:
        return resposta.valor_numero
    
    if hasattr(resposta, 'valor_opcoes_selecionadas') and resposta.valor_opcoes_selecionadas:
        try:
            # Tentar fazer parse do JSON
            opcoes = json.loads(resposta.valor_opcoes_selecionadas)
            if isinstance(opcoes, list) and len(opcoes) > 0:
                return opcoes[0]  # Retornar primeira opção
            return opcoes
        except:
            return resposta.valor_opcoes_selecionadas
    
    return None

def obter_valor_numerico(resposta):
    """
    Obtém valor numérico da resposta
    
    Args:
        resposta: Objeto Resposta
    
    Returns:
        float ou None
    """
    
    valor = obter_valor_resposta(resposta)
    
    if valor is None:
        return None
    
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None

def tem_resposta_valida(resposta):
    """
    Verifica se a resposta tem algum valor válido
    
    Args:
        resposta: Objeto Resposta
    
    Returns:
        bool: True se tem resposta válida
    """
    
    valor = obter_valor_resposta(resposta)
    
    if valor is None:
        return False
    
    if isinstance(valor, str):
        return len(valor.strip()) > 0
    
    return True

def gerar_relatorio_pontuacao(auditoria):
    """
    Gera um relatório detalhado da pontuação
    
    Args:
        auditoria: Objeto Auditoria
    
    Returns:
        dict: Relatório completo
    """
    
    resultado = calcular_pontuacao_auditoria(auditoria)
    
    if not resultado:
        return None
    
    # Adicionar informações extras
    resultado['auditoria_id'] = auditoria.id
    resultado['data'] = auditoria.data.strftime('%d/%m/%Y %H:%M') if hasattr(auditoria, 'data') else None
    resultado['usuario'] = auditoria.usuario.nome if auditoria.usuario else None
    resultado['formulario'] = auditoria.formulario.nome if auditoria.formulario else None
    
    # Calcular tendência (se houver auditorias anteriores)
    if hasattr(auditoria, 'avaliado_id'):
        auditorias_anteriores = Auditoria.query.filter(
            Auditoria.avaliado_id == auditoria.avaliado_id,
            Auditoria.formulario_id == auditoria.formulario_id,
            Auditoria.id < auditoria.id
        ).order_by(Auditoria.id.desc()).limit(3).all()
        
        if auditorias_anteriores:
            percentuais_anteriores = []
            for aud_ant in auditorias_anteriores:
                calc_ant = calcular_pontuacao_auditoria(aud_ant)
                if calc_ant:
                    percentuais_anteriores.append(calc_ant['percentual'])
            
            if percentuais_anteriores:
                media_anterior = sum(percentuais_anteriores) / len(percentuais_anteriores)
                diferenca = resultado['percentual'] - media_anterior
                
                if diferenca > 5:
                    resultado['tendencia'] = 'melhora'
                    resultado['tendencia_icon'] = 'fa-arrow-up'
                    resultado['tendencia_cor'] = 'success'
                elif diferenca < -5:
                    resultado['tendencia'] = 'piora'
                    resultado['tendencia_icon'] = 'fa-arrow-down'
                    resultado['tendencia_cor'] = 'danger'
                else:
                    resultado['tendencia'] = 'estavel'
                    resultado['tendencia_icon'] = 'fa-minus'
                    resultado['tendencia_cor'] = 'warning'
                
                resultado['diferenca_percentual'] = round(diferenca, 2)
    
    return resultado

def exportar_pontuacao_csv(auditorias):
    """
    Exporta pontuações de múltiplas auditorias para CSV
    
    Args:
        auditorias: Lista de objetos Auditoria
    
    Returns:
        str: Conteúdo CSV
    """
    
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'Data', 'Formulário', 'Avaliado/Loja', 
        'Usuário', 'Pontuação', 'Máximo', 'Percentual', 'Status'
    ])
    
    for auditoria in auditorias:
        resultado = calcular_pontuacao_auditoria(auditoria)
        
        if resultado:
            writer.writerow([
                auditoria.id,
                auditoria.data.strftime('%d/%m/%Y') if hasattr(auditoria, 'data') else '',
                auditoria.formulario.nome if auditoria.formulario else '',
                auditoria.avaliado.nome if hasattr(auditoria, 'avaliado') and auditoria.avaliado else '',
                auditoria.usuario.nome if auditoria.usuario else '',
                resultado['pontuacao_obtida'],
                resultado['pontuacao_maxima'],
                f"{resultado['percentual']}%",
                resultado['status']
            ])
    
    return output.getvalue()
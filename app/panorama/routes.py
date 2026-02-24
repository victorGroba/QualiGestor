# app/panorama/routes.py - DASHBOARD FUNCIONAL
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_, desc
from datetime import datetime, timedelta
import json

from ..models import (
    db, AplicacaoQuestionario, Avaliado, Questionario, RespostaPergunta,
    Pergunta, StatusAplicacao, TipoResposta, Cliente, Grupo, CategoriaIndicador, Topico
)

def aplicar_filtro_hierarquia(query, model_avaliado=Avaliado):
    query = query.filter(model_avaliado.cliente_id == current_user.cliente_id)
    if current_user.avaliado_id:
        query = query.filter(model_avaliado.id == current_user.avaliado_id)
    elif current_user.grupo_id:
        query = query.filter(model_avaliado.grupo_id == current_user.grupo_id)
    return query

panorama_bp = Blueprint('panorama', __name__, template_folder='templates')

@panorama_bp.route('/')
@login_required
def index():
    return redirect(url_for('panorama.dashboard'))

@panorama_bp.route('/dashboard')
@login_required
def dashboard():
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=30)

    avaliado_id = request.args.get('avaliado_id', type=int)
    questionario_id = request.args.get('questionario_id', type=int)
    grupo_id = request.args.get('grupo_id', type=int) 
    periodo = request.args.get('periodo', '30')
    mes_filtro = request.args.get('mes', '')

    if periodo == '7': data_inicio = data_fim - timedelta(days=7)
    elif periodo == '90': data_inicio = data_fim - timedelta(days=90)
    elif periodo == '365': data_inicio = data_fim - timedelta(days=365)

    query = AplicacaoQuestionario.query.join(Avaliado)
    query = aplicar_filtro_hierarquia(query, Avaliado)
    query = query.filter(AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA)

    if mes_filtro:
        try:
            ano, mes = map(int, mes_filtro.split('-'))
            query = query.filter(
                extract('year', AplicacaoQuestionario.data_inicio) == ano,
                extract('month', AplicacaoQuestionario.data_inicio) == mes
            )
        except ValueError:
            pass
    else:
        query = query.filter(
            AplicacaoQuestionario.data_inicio >= data_inicio,
            AplicacaoQuestionario.data_inicio <= data_fim
        )

    if avaliado_id: query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
    if questionario_id: query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
    if grupo_id: query = query.filter(Avaliado.grupo_id == grupo_id)

    aplicacoes = query.all()
    from ..utils.pontuacao import calcular_pontuacao_auditoria
    for app in aplicacoes:
        # Calcula a pontuação 1 única vez e salva "escondido" no objeto app
        app._cache_resultado = calcular_pontuacao_auditoria(app)
    metricas = calcular_metricas_dashboard(aplicacoes)

    # DICIONÁRIO ATUALIZADO COM O NOVO GRÁFICO
    graficos = {
        'evolucao_pontuacao': gerar_grafico_evolucao_mensal(aplicacoes),
        'evolucao_topicos': gerar_grafico_evolucao_topicos(aplicacoes), # <-- NOVO GRÁFICO AQUI
        'topicos_rancho': gerar_grafico_topicos(aplicacoes),
        'pontuacao_por_avaliado': gerar_grafico_avaliados(aplicacoes),
        'pontuacao_por_questionario': gerar_grafico_questionarios(aplicacoes),
        'distribuicao_notas': gerar_grafico_distribuicao(aplicacoes),
        'ranking_avaliados': gerar_ranking_avaliados(aplicacoes),
        'top_nao_conformidades': gerar_top_nao_conformidades(aplicacoes)
    }

    meses_opcoes = []
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    nomes_meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}

    for i in range(12): 
        m = mes_atual - i
        a = ano_atual
        if m <= 0:
            m += 12
            a -= 1
        meses_opcoes.append({'valor': f"{a}-{m:02d}", 'label': f"{nomes_meses[m]}/{a}"})

    query_avaliados = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
    query_avaliados = aplicar_filtro_hierarquia(query_avaliados)
    
    query_grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
    if current_user.grupo_id:
        query_grupos = query_grupos.filter(Grupo.id == current_user.grupo_id)

    filtros = {
        'meses': meses_opcoes,
        'avaliados': query_avaliados.order_by(Avaliado.nome).all(),
        'questionarios': Questionario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all(),
        'grupos': query_grupos.order_by(Grupo.nome).all()
    }

    return render_template(
        'panorama/dashboard.html',
        metricas=metricas,
        graficos=graficos,
        filtros=filtros,
        filtros_aplicados={
            'mes': mes_filtro,
            'avaliado_id': avaliado_id,
            'questionario_id': questionario_id,
            'grupo_id': grupo_id,
            'periodo': periodo
        }
    )

@panorama_bp.route('/relatorios')
@login_required
def relatorios():
    return render_template('panorama/relatorios.html')

@panorama_bp.route('/filtros')
@login_required
def filtros():
    return redirect(url_for('panorama.dashboard'))

@panorama_bp.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        avaliado_id = request.args.get('avaliado_id', type=int)  
        questionario_id = request.args.get('questionario_id', type=int)
        grupo_id = request.args.get('grupo_id', type=int) 
        mes_filtro = request.args.get('mes', '')

        if data_inicio: data_inicio = datetime.fromisoformat(data_inicio)
        else: data_inicio = datetime.now() - timedelta(days=30)

        if data_fim: data_fim = datetime.fromisoformat(data_fim)
        else: data_fim = datetime.now()

        query = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
        )

        if mes_filtro:
            try:
                ano, mes = map(int, mes_filtro.split('-'))
                query = query.filter(
                    extract('year', AplicacaoQuestionario.data_inicio) == ano,
                    extract('month', AplicacaoQuestionario.data_inicio) == mes
                )
            except ValueError: pass
        else:
            query = query.filter(AplicacaoQuestionario.data_inicio >= data_inicio, AplicacaoQuestionario.data_inicio <= data_fim)

        if avaliado_id: query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
        if questionario_id: query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
        if grupo_id: query = query.filter(Avaliado.grupo_id == grupo_id)

        aplicacoes = query.all()

        data = {
            'metricas': calcular_metricas_dashboard(aplicacoes),
            'evolucao': gerar_grafico_evolucao_mensal(aplicacoes), 
            'evolucao_topicos': gerar_grafico_evolucao_topicos(aplicacoes), # <-- NOVO
            'topicos': gerar_grafico_topicos(aplicacoes),          
            'por_avaliado': gerar_grafico_avaliados(aplicacoes),  
            'distribuicao': gerar_grafico_distribuicao(aplicacoes)
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@panorama_bp.route('/api/export-data')
@login_required
def api_export_data():
    formato = request.args.get('formato', 'json')  
    aplicacoes = AplicacaoQuestionario.query.join(Avaliado).filter(
        Avaliado.cliente_id == current_user.cliente_id,
        AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
    ).all()

    if formato == 'json':
        data = []
        for aplicacao in aplicacoes:
            data.append({
                'id': aplicacao.id, 'data': aplicacao.data_inicio.isoformat(),
                'avaliado': aplicacao.avaliado.nome, 'questionario': aplicacao.questionario.nome,
                'pontuacao': aplicacao.nota_final, 'usuario': aplicacao.aplicador.nome,
                'observacoes': aplicacao.observacoes or ''
            })
        return jsonify(data)
    elif formato == 'csv':
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Data', 'Avaliado', 'Questionário', 'Pontuação (%)', 'Usuário', 'Observações'])
        for aplicacao in aplicacoes:
            writer.writerow([
                aplicacao.id, aplicacao.data_inicio.strftime('%d/%m/%Y'),
                aplicacao.avaliado.nome, aplicacao.questionario.nome,
                f"{aplicacao.nota_final:.1f}%" if aplicacao.nota_final else 'N/A',
                aplicacao.aplicador.nome, aplicacao.observacoes or ''
            ])
        return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=aplicacoes.csv'}
    return jsonify({'error': 'Formato não suportado'}), 400

# ===================== FUNÇÕES DE CÁLCULO =====================

def calcular_metricas_dashboard(aplicacoes):
    if not aplicacoes:
        return {'total_auditorias': 0, 'pontuacao_media': 0, 'lojas_auditadas': 0, 'tendencia_pontuacao': 0, 'auditorias_criticas': 0, 'conformidade_geral': 0}

    total_aplicacoes = len(aplicacoes)
    pontuacoes = [a.nota_final for a in aplicacoes if a.nota_final is not None]
    pontuacao_media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
    avaliados_avaliados = len(set(a.avaliado_id for a in aplicacoes))
    aplicacoes_criticas = len([a for a in aplicacoes if a.nota_final and a.nota_final < 60])
    conformes = len([a for a in aplicacoes if a.nota_final and a.nota_final >= 80])
    conformidade_geral = (conformes / total_aplicacoes * 100) if total_aplicacoes > 0 else 0

    agora = datetime.now()
    duas_semanas_atras = agora - timedelta(days=14)
    quatro_semanas_atras = agora - timedelta(days=28)
    recentes = [a for a in aplicacoes if a.data_inicio >= duas_semanas_atras]
    anteriores = [a for a in aplicacoes if quatro_semanas_atras <= a.data_inicio < duas_semanas_atras]
    media_recente = sum(a.nota_final for a in recentes if a.nota_final) / len(recentes) if recentes else 0
    media_anterior = sum(a.nota_final for a in anteriores if a.nota_final) / len(anteriores) if anteriores else 0

    return {
        'total_auditorias': total_aplicacoes, 'pontuacao_media': round(pontuacao_media, 1),
        'lojas_auditadas': avaliados_avaliados, 'tendencia_pontuacao': round(media_recente - media_anterior, 1),
        'auditorias_criticas': aplicacoes_criticas, 'conformidade_geral': round(conformidade_geral, 1)
    }

def gerar_grafico_avaliados(aplicacoes):
    if not aplicacoes: return {'labels': [], 'datasets': []}
    dados_por_avaliado = {}
    for aplicacao in aplicacoes:
        avaliado_nome = aplicacao.avaliado.nome 
        if avaliado_nome not in dados_por_avaliado: dados_por_avaliado[avaliado_nome] = []
        dados_por_avaliado[avaliado_nome].append(aplicacao.nota_final or 0)

    lista_ordenada = []
    for avaliado, pontuacoes in dados_por_avaliado.items():
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        lista_ordenada.append({'avaliado': avaliado, 'media': round(media, 1)})
    lista_ordenada.sort(key=lambda x: x['media'])

    labels, valores, cores = [], [], []
    for item in lista_ordenada:
        labels.append(item['avaliado'])
        valores.append(item['media'])
        if item['media'] >= 80: cores.append('#28a745')
        elif item['media'] >= 60: cores.append('#ffc107')
        else: cores.append('#dc3545')

    return {'labels': labels, 'datasets': [{'label': 'Pontuação Média (%)', 'data': valores, 'backgroundColor': cores}]}

def gerar_grafico_questionarios(aplicacoes):
    if not aplicacoes: return {'labels': [], 'datasets': []}
    dados_por_questionario = {}
    for aplicacao in aplicacoes:
        quest_nome = aplicacao.questionario.nome
        if quest_nome not in dados_por_questionario: dados_por_questionario[quest_nome] = []
        dados_por_questionario[quest_nome].append(aplicacao.nota_final or 0)

    labels, valores = [], []
    for questionario, pontuacoes in dados_por_questionario.items():
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        labels.append(questionario)
        valores.append(round(media, 1))

    return {'labels': labels, 'datasets': [{'label': 'Pontuação Média (%)', 'data': valores, 'backgroundColor': ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c']}]}

def gerar_grafico_distribuicao(aplicacoes):
    if not aplicacoes: return {'labels': [], 'datasets': []}
    faixas = { '0-20%': 0, '21-40%': 0, '41-60%': 0, '61-80%': 0, '81-100%': 0 }
    for aplicacao in aplicacoes:
        pontuacao = aplicacao.nota_final or 0 
        if pontuacao <= 20: faixas['0-20%'] += 1
        elif pontuacao <= 40: faixas['21-40%'] += 1
        elif pontuacao <= 60: faixas['41-60%'] += 1
        elif pontuacao <= 80: faixas['61-80%'] += 1
        else: faixas['81-100%'] += 1
    return {'labels': list(faixas.keys()), 'datasets': [{'label': 'Quantidade de Aplicações', 'data': list(faixas.values()), 'backgroundColor': ['#dc3545', '#fd7e14', '#ffc107', '#20c997', '#28a745']}]}

def gerar_ranking_avaliados(aplicacoes):
    if not aplicacoes: return []
    dados_por_avaliado = {}
    for aplicacao in aplicacoes:
        avaliado_id = aplicacao.avaliado_id
        if avaliado_id not in dados_por_avaliado:
            dados_por_avaliado[avaliado_id] = {'nome': aplicacao.avaliado.nome, 'pontuacoes': [], 'total_aplicacoes': 0}
        dados_por_avaliado[avaliado_id]['pontuacoes'].append(aplicacao.nota_final or 0)
        dados_por_avaliado[avaliado_id]['total_aplicacoes'] += 1

    ranking = []
    for avaliado_id, dados in dados_por_avaliado.items():
        media = sum(dados['pontuacoes']) / len(dados['pontuacoes']) if dados['pontuacoes'] else 0
        ranking.append({'loja': dados['nome'], 'media': round(media, 1), 'total_auditorias': dados['total_aplicacoes'], 'status': 'success' if media >= 80 else 'warning' if media >= 60 else 'danger'})
    ranking.sort(key=lambda x: x['media'], reverse=True)
    return ranking[:10]

def gerar_top_nao_conformidades(aplicacoes):
    if not aplicacoes: return []
    nao_conformidades = {}
    for aplicacao in aplicacoes:
        for resposta in aplicacao.respostas:
            if resposta.resposta and 'não' in resposta.resposta.lower():
                pergunta_texto = resposta.pergunta.texto
                if pergunta_texto not in nao_conformidades: nao_conformidades[pergunta_texto] = 0
                nao_conformidades[pergunta_texto] += 1
    top_ncs = sorted(nao_conformidades.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{'pergunta': pergunta, 'frequencia': freq} for pergunta, freq in top_ncs]

# ===================== NOVAS FUNÇÕES DOS GRÁFICOS (0 A 10 E BARRAS) =====================

def gerar_grafico_topicos(aplicacoes):
    """Gera notas de 0 a 10 por tópico, cada um sendo um Dataset para gerar a legenda de cor"""
    if not aplicacoes:
        return {'labels': [''], 'datasets': []} # Label vazia para ocultar o Eixo X

    from ..utils.pontuacao import calcular_pontuacao_auditoria
    from ..models import Topico 
    
    dados_topicos = {}
    for app in aplicacoes:
        resultado = getattr(app, '_cache_resultado', calcular_pontuacao_auditoria(app)) 
        if not resultado or not resultado.get('detalhes_blocos'): continue
        
            
        for bloco, detalhes in resultado['detalhes_blocos'].items():
            if bloco not in dados_topicos:
                dados_topicos[bloco] = {'obtido': 0, 'maximo': 0}
            dados_topicos[bloco]['obtido'] += detalhes['pontuacao_obtida']
            dados_topicos[bloco]['maximo'] += detalhes['pontuacao_maxima']

    # ORDENAÇÃO OFICIAL DO BANCO DE DADOS
    topicos_banco = Topico.query.order_by(Topico.id).all()
    ordem_oficial_nomes = [t.nome for t in topicos_banco]

    topicos_ordenados = []
    for nome in ordem_oficial_nomes:
        if nome in dados_topicos:
            topicos_ordenados.append(nome)

    for bloco in dados_topicos.keys():
        if bloco not in topicos_ordenados:
            topicos_ordenados.append(bloco)

    # PALETA DE CORES PARA OS TÓPICOS
    cores_paleta = ['#4e73df', '#1cc88a', '#f6c23e', '#e74a3b', '#36b9cc', '#858796', '#fd7e14', '#20c9a6', '#6610f2', '#e83e8c']
    
    datasets = []
    
    # Cada tópico vira um "dataset" individual. Assim o gráfico cria a legenda colorida!
    for i, topico in enumerate(topicos_ordenados):
        totais = dados_topicos[topico]
        if totais['maximo'] > 0:
            nota = (totais['obtido'] / totais['maximo']) * 10
            nota_arredondada = round(nota, 1)
            
            datasets.append({
                'label': topico, # O nome vai para a legenda
                'data': [nota_arredondada], # O valor cria a barra
                'backgroundColor': cores_paleta[i % len(cores_paleta)],
                'borderColor': cores_paleta[i % len(cores_paleta)],
                'borderWidth': 1
            })

    # Enviamos "labels: ['']" para agrupar todas as barras no mesmo lugar
    return {'labels': [''], 'datasets': datasets}
def gerar_grafico_evolucao_mensal(aplicacoes):
    if not aplicacoes: return {'labels': [], 'datasets': []}
    meses = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

    dados_por_mes = {}
    for aplicacao in aplicacoes:
        chave_mes = aplicacao.data_inicio.strftime('%Y-%m') 
        mes_numero = int(aplicacao.data_inicio.strftime('%m'))
        ano = aplicacao.data_inicio.strftime('%Y')
        label_mes = f"{meses[mes_numero]}/{ano}"

        if label_mes not in dados_por_mes: dados_por_mes[label_mes] = {'ordem': chave_mes, 'notas': []}
        nota = (aplicacao.nota_final / 10) if aplicacao.nota_final is not None else 0
        dados_por_mes[label_mes]['notas'].append(nota)

    meses_ordenados = sorted(dados_por_mes.keys(), key=lambda k: dados_por_mes[k]['ordem'])
    labels, valores = [], []

    for label in meses_ordenados:
        notas = dados_por_mes[label]['notas']
        media = sum(notas) / len(notas) if notas else 0
        labels.append(label)
        valores.append(round(media, 1))

    return {'labels': labels, 'datasets': [{'label': 'Nota Média Mensal (0 a 10)', 'data': valores, 'backgroundColor': '#007bff'}]}

# --- NOVA FUNÇÃO: EVOLUÇÃO MENSAL POR TÓPICO ---
# --- NOVA FUNÇÃO: EVOLUÇÃO MENSAL SEPARADA POR TÓPICO ---
def gerar_grafico_evolucao_topicos(aplicacoes):
    """
    Gera uma LISTA de gráficos, um para cada Tópico.
    O eixo X são os Meses e o eixo Y são as Notas (0-10).
    """
    if not aplicacoes:
        return []

    from ..utils.pontuacao import calcular_pontuacao_auditoria
    from ..models import Topico

    meses = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    
    # Estrutura base: { 'Infraestrutura': { 'Jan/2026': [notas...], 'Fev/2026': [notas...] } }
    dados_por_topico = {}
    meses_encontrados = set()

    for app in aplicacoes:
        chave_mes = app.data_inicio.strftime('%Y-%m') # Usado para ordenar
        mes_numero = int(app.data_inicio.strftime('%m'))
        ano = app.data_inicio.strftime('%Y')
        label_mes = f"{meses[mes_numero]}/{ano}"
        
        meses_encontrados.add((chave_mes, label_mes))

        resultado = getattr(app, '_cache_resultado', calcular_pontuacao_auditoria(app)) 
        if not resultado or not resultado.get('detalhes_blocos'):
            continue
            
        for bloco, detalhes in resultado['detalhes_blocos'].items():
            if detalhes['pontuacao_maxima'] > 0:
                nota = (detalhes['pontuacao_obtida'] / detalhes['pontuacao_maxima']) * 10
                if bloco not in dados_por_topico:
                    dados_por_topico[bloco] = {}
                if label_mes not in dados_por_topico[bloco]:
                    dados_por_topico[bloco][label_mes] = []
                dados_por_topico[bloco][label_mes].append(nota)

    # Ordenar Tópicos
    topicos_banco = Topico.query.order_by(Topico.id).all()
    ordem_oficial = [t.nome for t in topicos_banco]
    topicos_ordenados = [t for t in ordem_oficial if t in dados_por_topico]
    for t in dados_por_topico.keys():
        if t not in topicos_ordenados:
            topicos_ordenados.append(t)

    # Ordenar Meses
    meses_ordenados_tuples = sorted(list(meses_encontrados), key=lambda x: x[0])
    labels_meses = [m[1] for m in meses_ordenados_tuples]

    cores_paleta = ['#4e73df', '#1cc88a', '#f6c23e', '#e74a3b', '#36b9cc', '#858796', '#fd7e14', '#20c9a6', '#6610f2', '#e83e8c']
    
    lista_graficos_separados = []
    
    # Criar um objeto de gráfico COMPLETO para CADA tópico
    for i, topico in enumerate(topicos_ordenados):
        valores_topico = []
        for label_mes in labels_meses:
            notas = dados_por_topico[topico].get(label_mes, [])
            if notas:
                media = sum(notas) / len(notas)
                valores_topico.append(round(media, 1))
            else:
                valores_topico.append(None) # Omitir barra se não houver nota no mês
        
        lista_graficos_separados.append({
            'titulo': topico, # Nome do tópico para usar no título do card
            'id': f"chartEvolucaoTopico_{i}", # ID único para o canvas no HTML
            'cor': cores_paleta[i % len(cores_paleta)], # Cor única para o tópico
            'dados': {
                'labels': labels_meses, # Eixo X são os meses
                'datasets': [{
                    'label': 'Nota',
                    'data': valores_topico, # Eixo Y são as notas
                    'backgroundColor': cores_paleta[i % len(cores_paleta)],
                    'borderColor': cores_paleta[i % len(cores_paleta)],
                    'borderWidth': 1
                }]
            }
        })

    return lista_graficos_separados


# ... Resto das rotas (Pareto, Comparativo, etc) permanecem rigorosamente idênticas ...

@panorama_bp.route('/api/indicadores/comparativo')
@login_required
def api_comparativo_indicadores():
    try:
        categorias = CategoriaIndicador.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(CategoriaIndicador.ordem).all()
        ranchos = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
        dados_painel = []

        for cat in categorias:
            grafico = {'titulo': cat.nome, 'id_grafico': f'grafico_{cat.id}', 'cor': cat.cor, 'labels': [], 'valores': []}
            for rancho in ranchos:
                apps = AplicacaoQuestionario.query.filter_by(avaliado_id=rancho.id, status=StatusAplicacao.FINALIZADA).all()
                total_pontos, total_maximo = 0, 0
                for app in apps:
                    respostas = RespostaPergunta.query.join(Pergunta).join(Topico).filter(
                        RespostaPergunta.aplicacao_id == app.id,
                        Topico.categoria_indicador_id == cat.id
                    ).all()
                    for resp in respostas:
                        if resp.pontos is not None:
                            total_pontos += resp.pontos
                            peso = resp.pergunta.peso or 0
                            total_maximo += peso
                percentual = round((total_pontos / total_maximo) * 100, 1) if total_maximo > 0 else 0
                grafico['labels'].append(rancho.nome)
                grafico['valores'].append(percentual)
            dados_painel.append(grafico)
        return jsonify(dados_painel)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@panorama_bp.route('/pareto')
@login_required
def analise_pareto():
    avaliados = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    questionarios = Questionario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    return render_template('panorama/pareto.html', avaliados=avaliados, questionarios=questionarios)

@panorama_bp.route('/api/pareto-data')
@login_required
def api_pareto_data():
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        avaliado_id = request.args.get('avaliado_id', type=int)
        questionario_id = request.args.get('questionario_id', type=int)

        query = db.session.query(
            Topico.nome, func.count(RespostaPergunta.id).label('total_erros')
        ).join(Pergunta, RespostaPergunta.pergunta_id == Pergunta.id) \
         .join(Topico, Pergunta.topico_id == Topico.id) \
         .join(AplicacaoQuestionario, RespostaPergunta.aplicacao_id == AplicacaoQuestionario.id) \
         .join(Avaliado, AplicacaoQuestionario.avaliado_id == Avaliado.id) \
         .filter(
             Avaliado.cliente_id == current_user.cliente_id,
             RespostaPergunta.nao_conforme == True,
             AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
         )

        if data_inicio: query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        if data_fim:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(AplicacaoQuestionario.data_inicio <= data_fim_dt)
        if avaliado_id: query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
        if questionario_id: query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)

        resultados = query.group_by(Topico.nome).order_by(desc('total_erros')).all()

        labels, data_count, data_percentual = [], [], []
        total_geral = sum([r.total_erros for r in resultados])
        acumulado = 0

        for r in resultados:
            labels.append(r.nome)
            data_count.append(r.total_erros)
            acumulado += r.total_erros
            percentual = (acumulado / total_geral * 100) if total_geral > 0 else 0
            data_percentual.append(round(percentual, 1))

        return jsonify({'labels': labels, 'data': data_count, 'percentual': data_percentual, 'total_erros': total_geral})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@panorama_bp.route('/api/indicadores/quantitativos')
@login_required
def api_indicadores_quantitativos():
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        avaliado_id = request.args.get('avaliado_id', type=int)
        questionario_id = request.args.get('questionario_id', type=int)

        if not questionario_id: return jsonify({'labels': [], 'datasets': []})

        query = db.session.query(
            AplicacaoQuestionario.data_inicio, Pergunta.texto, RespostaPergunta.resposta
        ).join(RespostaPergunta).join(Pergunta)\
         .filter(
             AplicacaoQuestionario.questionario_id == questionario_id,
             AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA,
             Avaliado.cliente_id == current_user.cliente_id,
             Pergunta.tipo == 'numerico'
         )

        if data_inicio: query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        if data_fim:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AplicacaoQuestionario.data_inicio < dt_fim)
        if avaliado_id: query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)

        resultados = query.order_by(AplicacaoQuestionario.data_inicio).all()
        dados_agrupados = {}
        datas = set()

        for data_app, pergunta_texto, valor_resp in resultados:
            try: valor = float(valor_resp.replace(',', '.'))
            except (ValueError, AttributeError): continue

            data_str = data_app.strftime('%d/%m')
            datas.add(data_str)

            if pergunta_texto not in dados_agrupados: dados_agrupados[pergunta_texto] = {}
            if data_str in dados_agrupados[pergunta_texto]: dados_agrupados[pergunta_texto][data_str] += valor
            else: dados_agrupados[pergunta_texto][data_str] = valor

        labels = sorted(list(datas), key=lambda x: datetime.strptime(x + '/' + str(datetime.now().year), '%d/%m/%Y'))
        datasets = []
        cores = ['#e74a3b', '#f6c23e', '#4e73df', '#1cc88a', '#36b9cc']
        i = 0

        for pergunta, valores_dia in dados_agrupados.items():
            data_points = [valores_dia.get(dia, 0) for dia in labels]
            datasets.append({
                'label': pergunta,
                'data': data_points,
                'borderColor': cores[i % len(cores)],
                'backgroundColor': 'transparent',
                'tension': 0.3,
                'fill': False
            })
            i += 1

        return jsonify({'labels': labels, 'datasets': datasets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
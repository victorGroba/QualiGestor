# app/panorama/routes.py - DASHBOARD FUNCIONAL (corrigido para usar modelos corretos)
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_, desc
from datetime import datetime, timedelta
import json

# IMPORTAÇÕES CORRIGIDAS - usando os modelos corretos do models.py
from ..models import (
    db, AplicacaoQuestionario, Avaliado, Questionario, RespostaPergunta,
    Pergunta, StatusAplicacao, TipoResposta, Cliente, Grupo, CategoriaIndicador, Topico
)


panorama_bp = Blueprint('panorama', __name__, template_folder='templates')

@panorama_bp.route('/')
@login_required
def index():
    """Redireciona para o Dashboard completo"""
    # MUDANÇA: Joga o usuário direto para a tela com filtros e gráficos detalhados
    return redirect(url_for('panorama.dashboard'))

@panorama_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal com dados reais"""
    # Período padrão: últimos 30 dias
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=30)

    # Aplicar filtros se fornecidos
    avaliado_id = request.args.get('avaliado_id', type=int)  # Era loja_id
    questionario_id = request.args.get('questionario_id', type=int)  # Era formulario_id
    grupo_id = request.args.get('grupo_id', type=int)
    periodo = request.args.get('periodo', '30')

    # Ajustar período
    if periodo == '7':
        data_inicio = data_fim - timedelta(days=7)
    elif periodo == '90':
        data_inicio = data_fim - timedelta(days=90)
    elif periodo == '365':
        data_inicio = data_fim - timedelta(days=365)

    # Query base para aplicações do cliente (era auditorias)
    query = AplicacaoQuestionario.query.join(Avaliado).filter(
        Avaliado.cliente_id == current_user.cliente_id,
        AplicacaoQuestionario.data_inicio >= data_inicio,
        AplicacaoQuestionario.data_inicio <= data_fim,
        AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA  # Era StatusAuditoria.CONCLUIDA
    )

    # Aplicar filtros
    if avaliado_id:
        query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
    if questionario_id:
        query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
    if grupo_id:
        query = query.filter(Avaliado.grupo_id == grupo_id)

    aplicacoes = query.all()  # Era auditorias

    # Calcular métricas
    metricas = calcular_metricas_dashboard(aplicacoes)

    # Dados para gráficos
    graficos = {
        'evolucao_pontuacao': gerar_grafico_evolucao(aplicacoes),
        'pontuacao_por_avaliado': gerar_grafico_avaliados(aplicacoes),  # Era por_loja
        'pontuacao_por_questionario': gerar_grafico_questionarios(aplicacoes),  # Era por_formulario
        'distribuicao_notas': gerar_grafico_distribuicao(aplicacoes),
        'ranking_avaliados': gerar_ranking_avaliados(aplicacoes),  # Era ranking_lojas
        'top_nao_conformidades': gerar_top_nao_conformidades(aplicacoes)
    }

    # Opções para filtros
    filtros = {
        'avaliados': Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all(),  # Era lojas
        'questionarios': Questionario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all(),  # Era formularios
        'grupos': Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    }

    return render_template(
        'panorama/dashboard.html',
        metricas=metricas,
        graficos=graficos,
        filtros=filtros,
        filtros_aplicados={
            'avaliado_id': avaliado_id,  # Era loja_id
            'questionario_id': questionario_id,  # Era formulario_id
            'grupo_id': grupo_id,
            'periodo': periodo
        }
    )

@panorama_bp.route('/relatorios')
@login_required
def relatorios():
    """Página de relatórios customizáveis"""
    return render_template('panorama/relatorios.html')

@panorama_bp.route('/filtros')
@login_required
def filtros():
    """Página de filtros - redireciona para dashboard"""
    return redirect(url_for('panorama.dashboard'))

@panorama_bp.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API para dados do dashboard (AJAX)"""
    try:
        # Parâmetros da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        avaliado_id = request.args.get('avaliado_id', type=int)  # Era loja_id
        questionario_id = request.args.get('questionario_id', type=int)  # Era formulario_id

        # Converter datas
        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio)
        else:
            data_inicio = datetime.now() - timedelta(days=30)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim)
        else:
            data_fim = datetime.now()

        # Query de aplicações (era auditorias)
        query = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            AplicacaoQuestionario.data_inicio >= data_inicio,
            AplicacaoQuestionario.data_inicio <= data_fim,
            AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
        )

        if avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
        if questionario_id:
            query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)

        aplicacoes = query.all()

        # Gerar dados
        data = {
            'metricas': calcular_metricas_dashboard(aplicacoes),
            'evolucao': gerar_grafico_evolucao(aplicacoes),
            'por_avaliado': gerar_grafico_avaliados(aplicacoes),  # Era por_loja
            'distribuicao': gerar_grafico_distribuicao(aplicacoes)
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@panorama_bp.route('/api/export-data')
@login_required
def api_export_data():
    """API para exportar dados"""
    formato = request.args.get('formato', 'json')  # json, csv, excel

    # Buscar aplicações (era auditorias)
    aplicacoes = AplicacaoQuestionario.query.join(Avaliado).filter(
        Avaliado.cliente_id == current_user.cliente_id,
        AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
    ).all()

    if formato == 'json':
        data = []
        for aplicacao in aplicacoes:
            data.append({
                'id': aplicacao.id,
                'data': aplicacao.data_inicio.isoformat(),
                'avaliado': aplicacao.avaliado.nome,  # Era loja
                'questionario': aplicacao.questionario.nome,  # Era formulario
                'pontuacao': aplicacao.nota_final,  # Era percentual
                'usuario': aplicacao.aplicador.nome,  # Era usuario
                'observacoes': aplicacao.observacoes or ''  # Era observacoes_gerais
            })
        return jsonify(data)

    elif formato == 'csv':
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'ID', 'Data', 'Avaliado', 'Questionário',
            'Pontuação (%)', 'Usuário', 'Observações'
        ])

        # Dados
        for aplicacao in aplicacoes:
            writer.writerow([
                aplicacao.id,
                aplicacao.data_inicio.strftime('%d/%m/%Y'),
                aplicacao.avaliado.nome,
                aplicacao.questionario.nome,
                f"{aplicacao.nota_final:.1f}%" if aplicacao.nota_final else 'N/A',
                aplicacao.aplicador.nome,
                aplicacao.observacoes or ''
            ])

        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=aplicacoes.csv'
        }

    return jsonify({'error': 'Formato não suportado'}), 400

# ===================== FUNÇÕES DE CÁLCULO =====================

def calcular_metricas_dashboard(aplicacoes):
    """Calcula métricas principais do dashboard"""
    if not aplicacoes:
        return {
            'total_auditorias': 0,
            'pontuacao_media': 0,
            'lojas_auditadas': 0,
            'tendencia_pontuacao': 0,
            'auditorias_criticas': 0,
            'conformidade_geral': 0
        }

    # Métricas básicas
    total_aplicacoes = len(aplicacoes)
    pontuacoes = [a.nota_final for a in aplicacoes if a.nota_final is not None]  # Era percentual
    pontuacao_media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0

    # Avaliados únicos (era lojas)
    avaliados_avaliados = len(set(a.avaliado_id for a in aplicacoes))

    # Aplicações críticas (abaixo de 60%) - era auditorias_criticas
    aplicacoes_criticas = len([a for a in aplicacoes if a.nota_final and a.nota_final < 60])

    # Conformidade geral (acima de 80%)
    conformes = len([a for a in aplicacoes if a.nota_final and a.nota_final >= 80])
    conformidade_geral = (conformes / total_aplicacoes * 100) if total_aplicacoes > 0 else 0

    # Tendência (comparar últimas 2 semanas com 2 semanas anteriores)
    agora = datetime.now()
    duas_semanas_atras = agora - timedelta(days=14)
    quatro_semanas_atras = agora - timedelta(days=28)

    recentes = [a for a in aplicacoes if a.data_inicio >= duas_semanas_atras]
    anteriores = [a for a in aplicacoes if quatro_semanas_atras <= a.data_inicio < duas_semanas_atras]

    media_recente = sum(a.nota_final for a in recentes if a.nota_final) / len(recentes) if recentes else 0
    media_anterior = sum(a.nota_final for a in anteriores if a.nota_final) / len(anteriores) if anteriores else 0

    tendencia_pontuacao = media_recente - media_anterior

    return {
        'total_auditorias': total_aplicacoes,  # Manter nome para compatibilidade com template
        'pontuacao_media': round(pontuacao_media, 1),
        'lojas_auditadas': avaliados_avaliados,  # Manter nome para compatibilidade
        'tendencia_pontuacao': round(tendencia_pontuacao, 1),
        'auditorias_criticas': aplicacoes_criticas,  # Manter nome para compatibilidade
        'conformidade_geral': round(conformidade_geral, 1)
    }

def gerar_grafico_evolucao(aplicacoes):
    """Gera dados para gráfico de evolução temporal"""
    if not aplicacoes:
        return {'labels': [], 'datasets': []}

    # Agrupar por dia
    dados_por_dia = {}
    for aplicacao in aplicacoes:
        data_str = aplicacao.data_inicio.strftime('%Y-%m-%d')
        if data_str not in dados_por_dia:
            dados_por_dia[data_str] = []
        dados_por_dia[data_str].append(aplicacao.nota_final or 0)  # Era percentual

    # Calcular média por dia
    labels = sorted(dados_por_dia.keys())
    valores = []

    for data in labels:
        pontuacoes = dados_por_dia[data]
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        valores.append(round(media, 1))

    # Formatar labels para exibição
    labels_formatadas = []
    for label in labels:
        data = datetime.strptime(label, '%Y-%m-%d')
        labels_formatadas.append(data.strftime('%d/%m'))

    return {
        'labels': labels_formatadas,
        'datasets': [{
            'label': 'Pontuação Média (%)',
            'data': valores,
            'borderColor': '#007bff',
            'backgroundColor': 'rgba(0, 123, 255, 0.1)',
            'tension': 0.4
        }]
    }

def gerar_grafico_avaliados(aplicacoes):
    """Gera dados para gráfico por avaliado (era por loja)"""
    if not aplicacoes:
        return {'labels': [], 'datasets': []}

    # Agrupar por avaliado
    dados_por_avaliado = {}
    for aplicacao in aplicacoes:
        avaliado_nome = aplicacao.avaliado.nome  # Era loja.nome
        if avaliado_nome not in dados_por_avaliado:
            dados_por_avaliado[avaliado_nome] = []
        dados_por_avaliado[avaliado_nome].append(aplicacao.nota_final or 0)  # Era percentual

    # Calcular média por avaliado
    labels = []
    valores = []
    cores = []

    for avaliado, pontuacoes in dados_por_avaliado.items():
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        labels.append(avaliado)
        valores.append(round(media, 1))

        # Cor baseada na performance
        if media >= 80:
            cores.append('#28a745')  # Verde
        elif media >= 60:
            cores.append('#ffc107')  # Amarelo
        else:
            cores.append('#dc3545')  # Vermelho

    return {
        'labels': labels,
        'datasets': [{
            'label': 'Pontuação Média (%)',
            'data': valores,
            'backgroundColor': cores,
            'borderColor': cores,
            'borderWidth': 1
        }]
    }

def gerar_grafico_questionarios(aplicacoes):
    """Gera dados para gráfico por questionário (era por formulário)"""
    if not aplicacoes:
        return {'labels': [], 'datasets': []}

    # Agrupar por questionário
    dados_por_questionario = {}
    for aplicacao in aplicacoes:
        quest_nome = aplicacao.questionario.nome  # Era formulario.nome
        if quest_nome not in dados_por_questionario:
            dados_por_questionario[quest_nome] = []
        dados_por_questionario[quest_nome].append(aplicacao.nota_final or 0)  # Era percentual

    # Calcular média por questionário
    labels = []
    valores = []

    for questionario, pontuacoes in dados_por_questionario.items():
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        labels.append(questionario)
        valores.append(round(media, 1))

    return {
        'labels': labels,
        'datasets': [{
            'label': 'Pontuação Média (%)',
            'data': valores,
            'backgroundColor': [
                '#007bff', '#28a745', '#ffc107', '#dc3545',
                '#6f42c1', '#fd7e14', '#20c997', '#e83e8c'
            ]
        }]
    }

def gerar_grafico_distribuicao(aplicacoes):
    """Gera dados para gráfico de distribuição de notas"""
    if not aplicacoes:
        return {'labels': [], 'datasets': []}

    # Faixas de pontuação
    faixas = {
        '0-20%': 0,
        '21-40%': 0,
        '41-60%': 0,
        '61-80%': 0,
        '81-100%': 0
    }

    for aplicacao in aplicacoes:
        pontuacao = aplicacao.nota_final or 0  # Era percentual
        if pontuacao <= 20:
            faixas['0-20%'] += 1
        elif pontuacao <= 40:
            faixas['21-40%'] += 1
        elif pontuacao <= 60:
            faixas['41-60%'] += 1
        elif pontuacao <= 80:
            faixas['61-80%'] += 1
        else:
            faixas['81-100%'] += 1

    return {
        'labels': list(faixas.keys()),
        'datasets': [{
            'label': 'Quantidade de Aplicações',  # Era Auditorias
            'data': list(faixas.values()),
            'backgroundColor': [
                '#dc3545', '#fd7e14', '#ffc107', '#20c997', '#28a745'
            ]
        }]
    }

def gerar_ranking_avaliados(aplicacoes):
    """Gera ranking dos avaliados por performance (era lojas)"""
    if not aplicacoes:
        return []

    # Agrupar por avaliado
    dados_por_avaliado = {}
    for aplicacao in aplicacoes:
        avaliado_id = aplicacao.avaliado_id  # Era loja_id
        avaliado_nome = aplicacao.avaliado.nome  # Era loja.nome

        if avaliado_id not in dados_por_avaliado:
            dados_por_avaliado[avaliado_id] = {
                'nome': avaliado_nome,
                'pontuacoes': [],
                'total_aplicacoes': 0  # Era total_auditorias
            }

        dados_por_avaliado[avaliado_id]['pontuacoes'].append(aplicacao.nota_final or 0)  # Era percentual
        dados_por_avaliado[avaliado_id]['total_aplicacoes'] += 1

    # Calcular ranking
    ranking = []
    for avaliado_id, dados in dados_por_avaliado.items():
        media = sum(dados['pontuacoes']) / len(dados['pontuacoes']) if dados['pontuacoes'] else 0
        ranking.append({
            'loja': dados['nome'],  # Manter nome para compatibilidade com template
            'media': round(media, 1),
            'total_auditorias': dados['total_aplicacoes'],  # Manter nome para compatibilidade
            'status': 'success' if media >= 80 else 'warning' if media >= 60 else 'danger'
        })

    # Ordenar por média decrescente
    ranking.sort(key=lambda x: x['media'], reverse=True)

    return ranking[:10]  # Top 10

def gerar_top_nao_conformidades(aplicacoes):
    """Gera top das não conformidades mais frequentes"""
    if not aplicacoes:
        return []

    # Buscar respostas "Não" mais frequentes
    nao_conformidades = {}

    for aplicacao in aplicacoes:
        for resposta in aplicacao.respostas:
            # Ajustar para o novo modelo RespostaPergunta
            if resposta.resposta and 'não' in resposta.resposta.lower():
                pergunta_texto = resposta.pergunta.texto
                if pergunta_texto not in nao_conformidades:
                    nao_conformidades[pergunta_texto] = 0
                nao_conformidades[pergunta_texto] += 1

    # Ordenar e retornar top 10
    top_ncs = sorted(nao_conformidades.items(), key=lambda x: x[1], reverse=True)[:10]

    return [{'pergunta': pergunta, 'frequencia': freq} for pergunta, freq in top_ncs]

@panorama_bp.route('/api/indicadores/comparativo')
@login_required
def api_comparativo_indicadores():
    """
    API para o Gráfico de Barras Comparativo (Adequação por Categoria).
    """
    try:
        # 1. Buscar Categorias Ativas
        categorias = CategoriaIndicador.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        ).order_by(CategoriaIndicador.ordem).all()
        
        # 2. Buscar Ranchos (Avaliados) Ativos
        ranchos = Avaliado.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        ).all()
        
        dados_painel = []

        for cat in categorias:
            grafico = {
                'titulo': cat.nome,
                'id_grafico': f'grafico_{cat.id}',
                'cor': cat.cor,
                'labels': [],
                'valores': []
            }
            
            for rancho in ranchos:
                # --- CÁLCULO DA NOTA ---
                # Busca aplicações finalizadas deste rancho
                apps = AplicacaoQuestionario.query.filter_by(
                    avaliado_id=rancho.id,
                    status=StatusAplicacao.FINALIZADA
                ).all()
                
                total_pontos = 0
                total_maximo = 0
                
                for app in apps:
                    # Filtra respostas que pertencem a tópicos desta categoria
                    respostas = RespostaPergunta.query.join(Pergunta).join(Topico).filter(
                        RespostaPergunta.aplicacao_id == app.id,
                        Topico.categoria_indicador_id == cat.id
                    ).all()
                    
                    for resp in respostas:
                        if resp.pontos is not None:
                            total_pontos += resp.pontos
                            # Recalcula o máximo da pergunta (peso) para saber o %
                            peso = resp.pergunta.peso or 0
                            total_maximo += peso

                percentual = 0
                if total_maximo > 0:
                    percentual = round((total_pontos / total_maximo) * 100, 1)
                
                grafico['labels'].append(rancho.nome)
                grafico['valores'].append(percentual)
            
            dados_painel.append(grafico)
            
        return jsonify(dados_painel)

    except Exception as e:
        print(f"Erro API Comparativo: {e}")
        return jsonify({'error': str(e)}), 500

@panorama_bp.route('/pareto')
@login_required
def analise_pareto():
    """Renderiza a tela de Análise de Pareto (80/20)"""
    # Carrega filtros básicos para a tela
    avaliados = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    questionarios = Questionario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    
    return render_template('panorama/pareto.html', avaliados=avaliados, questionarios=questionarios)

@panorama_bp.route('/api/pareto-data')
@login_required
def api_pareto_data():
    """
    API que alimenta o Gráfico de Pareto.
    Retorna: Labels (Tópicos), Dados (Frequência) e Linha (Percentual Acumulado).
    """
    try:
        # 1. Filtros da Requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        avaliado_id = request.args.get('avaliado_id', type=int)
        questionario_id = request.args.get('questionario_id', type=int)

        # 2. Query Base: Respostas "Não Conforme" em aplicações FINALIZADAS
        query = db.session.query(
            Topico.nome,
            func.count(RespostaPergunta.id).label('total_erros')
        ).join(Pergunta, RespostaPergunta.pergunta_id == Pergunta.id) \
         .join(Topico, Pergunta.topico_id == Topico.id) \
         .join(AplicacaoQuestionario, RespostaPergunta.aplicacao_id == AplicacaoQuestionario.id) \
         .join(Avaliado, AplicacaoQuestionario.avaliado_id == Avaliado.id) \
         .filter(
             Avaliado.cliente_id == current_user.cliente_id, # Segurança
             RespostaPergunta.nao_conforme == True,          # O erro
             AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
         )

        # 3. Aplicação dos Filtros Dinâmicos
        if data_inicio:
            query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        if data_fim:
            # Ajuste para pegar o dia inteiro (até 23:59:59)
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(AplicacaoQuestionario.data_inicio <= data_fim_dt)
        if avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
        if questionario_id:
            query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)

        # 4. Agrupamento e Ordenação
        resultados = query.group_by(Topico.nome) \
                          .order_by(desc('total_erros')) \
                          .all()

        # 5. Cálculo Matemático do Pareto (Acumulado)
        labels = []
        data_count = []
        data_percentual = []
        
        total_geral = sum([r.total_erros for r in resultados])
        acumulado = 0

        for r in resultados:
            labels.append(r.nome)
            data_count.append(r.total_erros)
            
            acumulado += r.total_erros
            percentual = (acumulado / total_geral * 100) if total_geral > 0 else 0
            data_percentual.append(round(percentual, 1))

        return jsonify({
            'labels': labels,
            'data': data_count,
            'percentual': data_percentual,
            'total_erros': total_geral
        })

    except Exception as e:
        print(f"Erro API Pareto: {e}") # Log no terminal
        return jsonify({'error': str(e)}), 500
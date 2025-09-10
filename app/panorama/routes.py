# app/panorama/routes.py - DASHBOARD FUNCIONAL
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_
from datetime import datetime, timedelta
import json

from ..models import (
    db, Auditoria, Loja, Formulario, Resposta, 
    Pergunta, StatusAuditoria, TipoResposta, Cliente
)

panorama_bp = Blueprint('panorama', __name__, template_folder='templates')

@panorama_bp.route('/')
@login_required
def index():
    """Dashboard principal do Panorama"""
    return render_template('panorama/index.html')

@panorama_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal com dados reais"""
    # Período padrão: últimos 30 dias
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=30)
    
    # Aplicar filtros se fornecidos
    loja_id = request.args.get('loja_id', type=int)
    formulario_id = request.args.get('formulario_id', type=int)
    grupo_id = request.args.get('grupo_id', type=int)
    periodo = request.args.get('periodo', '30')
    
    # Ajustar período
    if periodo == '7':
        data_inicio = data_fim - timedelta(days=7)
    elif periodo == '90':
        data_inicio = data_fim - timedelta(days=90)
    elif periodo == '365':
        data_inicio = data_fim - timedelta(days=365)
    
    # Query base para auditorias do cliente
    query = Auditoria.query.join(Loja).filter(
        Loja.cliente_id == current_user.cliente_id,
        Auditoria.data_inicio >= data_inicio,
        Auditoria.data_inicio <= data_fim,
        Auditoria.status == StatusAuditoria.CONCLUIDA
    )
    
    # Aplicar filtros
    if loja_id:
        query = query.filter(Auditoria.loja_id == loja_id)
    if formulario_id:
        query = query.filter(Auditoria.formulario_id == formulario_id)
    if grupo_id:
        query = query.filter(Loja.grupo_id == grupo_id)
    
    auditorias = query.all()
    
    # Calcular métricas
    metricas = calcular_metricas_dashboard(auditorias)
    
    # Dados para gráficos
    graficos = {
        'evolucao_pontuacao': gerar_grafico_evolucao(auditorias),
        'pontuacao_por_loja': gerar_grafico_lojas(auditorias),
        'pontuacao_por_formulario': gerar_grafico_formularios(auditorias),
        'distribuicao_notas': gerar_grafico_distribuicao(auditorias),
        'ranking_lojas': gerar_ranking_lojas(auditorias),
        'top_nao_conformidades': gerar_top_nao_conformidades(auditorias)
    }
    
    # Opções para filtros
    filtros = {
        'lojas': Loja.query.filter_by(cliente_id=current_user.cliente_id, ativa=True).all(),
        'formularios': Formulario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all(),
        'grupos': db.session.query(Loja.grupo_id, func.max(Loja.grupo.has())).filter(
            Loja.cliente_id == current_user.cliente_id
        ).group_by(Loja.grupo_id).all() if hasattr(Loja, 'grupo') else []
    }
    
    return render_template('panorama/dashboard.html',
                         metricas=metricas,
                         graficos=graficos,
                         filtros=filtros,
                         filtros_aplicados={
                             'loja_id': loja_id,
                             'formulario_id': formulario_id,
                             'grupo_id': grupo_id,
                             'periodo': periodo
                         })

@panorama_bp.route('/relatorios')
@login_required
def relatorios():
    """Página de relatórios customizáveis"""
    return render_template('panorama/relatorios.html')

@panorama_bp.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API para dados do dashboard (AJAX)"""
    try:
        # Parâmetros da requisição
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        loja_id = request.args.get('loja_id', type=int)
        formulario_id = request.args.get('formulario_id', type=int)
        
        # Converter datas
        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio)
        else:
            data_inicio = datetime.now() - timedelta(days=30)
            
        if data_fim:
            data_fim = datetime.fromisoformat(data_fim)
        else:
            data_fim = datetime.now()
        
        # Query de auditorias
        query = Auditoria.query.join(Loja).filter(
            Loja.cliente_id == current_user.cliente_id,
            Auditoria.data_inicio >= data_inicio,
            Auditoria.data_inicio <= data_fim,
            Auditoria.status == StatusAuditoria.CONCLUIDA
        )
        
        if loja_id:
            query = query.filter(Auditoria.loja_id == loja_id)
        if formulario_id:
            query = query.filter(Auditoria.formulario_id == formulario_id)
        
        auditorias = query.all()
        
        # Gerar dados
        data = {
            'metricas': calcular_metricas_dashboard(auditorias),
            'evolucao': gerar_grafico_evolucao(auditorias),
            'por_loja': gerar_grafico_lojas(auditorias),
            'distribuicao': gerar_grafico_distribuicao(auditorias)
        }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@panorama_bp.route('/api/export-data')
@login_required
def api_export_data():
    """API para exportar dados"""
    formato = request.args.get('formato', 'json')  # json, csv, excel
    
    # Buscar auditorias
    auditorias = Auditoria.query.join(Loja).filter(
        Loja.cliente_id == current_user.cliente_id,
        Auditoria.status == StatusAuditoria.CONCLUIDA
    ).all()
    
    if formato == 'json':
        data = []
        for auditoria in auditorias:
            data.append({
                'id': auditoria.id,
                'codigo': auditoria.codigo,
                'data': auditoria.data_inicio.isoformat(),
                'loja': auditoria.loja.nome,
                'formulario': auditoria.formulario.nome,
                'pontuacao': auditoria.percentual,
                'usuario': auditoria.usuario.nome,
                'observacoes': auditoria.observacoes_gerais
            })
        return jsonify(data)
    
    elif formato == 'csv':
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Código', 'Data', 'Loja', 'Formulário', 
            'Pontuação (%)', 'Usuário', 'Observações'
        ])
        
        # Dados
        for auditoria in auditorias:
            writer.writerow([
                auditoria.id,
                auditoria.codigo,
                auditoria.data_inicio.strftime('%d/%m/%Y'),
                auditoria.loja.nome,
                auditoria.formulario.nome,
                f"{auditoria.percentual:.1f}%",
                auditoria.usuario.nome,
                auditoria.observacoes_gerais or ''
            ])
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=auditorias.csv'
        }
    
    return jsonify({'error': 'Formato não suportado'}), 400

# ===================== FUNÇÕES DE CÁLCULO =====================

def calcular_metricas_dashboard(auditorias):
    """Calcula métricas principais do dashboard"""
    if not auditorias:
        return {
            'total_auditorias': 0,
            'pontuacao_media': 0,
            'lojas_auditadas': 0,
            'tendencia_pontuacao': 0,
            'auditorias_criticas': 0,
            'conformidade_geral': 0
        }
    
    # Métricas básicas
    total_auditorias = len(auditorias)
    pontuacoes = [a.percentual for a in auditorias if a.percentual is not None]
    pontuacao_media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
    
    # Lojas únicas auditadas
    lojas_auditadas = len(set(a.loja_id for a in auditorias))
    
    # Auditorias críticas (abaixo de 60%)
    auditorias_criticas = len([a for a in auditorias if a.percentual and a.percentual < 60])
    
    # Conformidade geral (acima de 80%)
    conformes = len([a for a in auditorias if a.percentual and a.percentual >= 80])
    conformidade_geral = (conformes / total_auditorias * 100) if total_auditorias > 0 else 0
    
    # Tendência (comparar últimas 2 semanas com 2 semanas anteriores)
    agora = datetime.now()
    duas_semanas_atras = agora - timedelta(days=14)
    quatro_semanas_atras = agora - timedelta(days=28)
    
    recentes = [a for a in auditorias if a.data_inicio >= duas_semanas_atras]
    anteriores = [a for a in auditorias if quatro_semanas_atras <= a.data_inicio < duas_semanas_atras]
    
    media_recente = sum(a.percentual for a in recentes if a.percentual) / len(recentes) if recentes else 0
    media_anterior = sum(a.percentual for a in anteriores if a.percentual) / len(anteriores) if anteriores else 0
    
    tendencia_pontuacao = media_recente - media_anterior
    
    return {
        'total_auditorias': total_auditorias,
        'pontuacao_media': round(pontuacao_media, 1),
        'lojas_auditadas': lojas_auditadas,
        'tendencia_pontuacao': round(tendencia_pontuacao, 1),
        'auditorias_criticas': auditorias_criticas,
        'conformidade_geral': round(conformidade_geral, 1)
    }

def gerar_grafico_evolucao(auditorias):
    """Gera dados para gráfico de evolução temporal"""
    if not auditorias:
        return {'labels': [], 'datasets': []}
    
    # Agrupar por dia
    dados_por_dia = {}
    for auditoria in auditorias:
        data_str = auditoria.data_inicio.strftime('%Y-%m-%d')
        if data_str not in dados_por_dia:
            dados_por_dia[data_str] = []
        dados_por_dia[data_str].append(auditoria.percentual or 0)
    
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

def gerar_grafico_lojas(auditorias):
    """Gera dados para gráfico por loja"""
    if not auditorias:
        return {'labels': [], 'datasets': []}
    
    # Agrupar por loja
    dados_por_loja = {}
    for auditoria in auditorias:
        loja_nome = auditoria.loja.nome
        if loja_nome not in dados_por_loja:
            dados_por_loja[loja_nome] = []
        dados_por_loja[loja_nome].append(auditoria.percentual or 0)
    
    # Calcular média por loja
    labels = []
    valores = []
    cores = []
    
    for loja, pontuacoes in dados_por_loja.items():
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        labels.append(loja)
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

def gerar_grafico_formularios(auditorias):
    """Gera dados para gráfico por formulário"""
    if not auditorias:
        return {'labels': [], 'datasets': []}
    
    # Agrupar por formulário
    dados_por_formulario = {}
    for auditoria in auditorias:
        form_nome = auditoria.formulario.nome
        if form_nome not in dados_por_formulario:
            dados_por_formulario[form_nome] = []
        dados_por_formulario[form_nome].append(auditoria.percentual or 0)
    
    # Calcular média por formulário
    labels = []
    valores = []
    
    for formulario, pontuacoes in dados_por_formulario.items():
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        labels.append(formulario)
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

def gerar_grafico_distribuicao(auditorias):
    """Gera dados para gráfico de distribuição de notas"""
    if not auditorias:
        return {'labels': [], 'datasets': []}
    
    # Faixas de pontuação
    faixas = {
        '0-20%': 0,
        '21-40%': 0,
        '41-60%': 0,
        '61-80%': 0,
        '81-100%': 0
    }
    
    for auditoria in auditorias:
        pontuacao = auditoria.percentual or 0
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
            'label': 'Quantidade de Auditorias',
            'data': list(faixas.values()),
            'backgroundColor': [
                '#dc3545', '#fd7e14', '#ffc107', '#20c997', '#28a745'
            ]
        }]
    }

def gerar_ranking_lojas(auditorias):
    """Gera ranking das lojas por performance"""
    if not auditorias:
        return []
    
    # Agrupar por loja
    dados_por_loja = {}
    for auditoria in auditorias:
        loja_id = auditoria.loja_id
        loja_nome = auditoria.loja.nome
        
        if loja_id not in dados_por_loja:
            dados_por_loja[loja_id] = {
                'nome': loja_nome,
                'pontuacoes': [],
                'total_auditorias': 0
            }
        
        dados_por_loja[loja_id]['pontuacoes'].append(auditoria.percentual or 0)
        dados_por_loja[loja_id]['total_auditorias'] += 1
    
    # Calcular ranking
    ranking = []
    for loja_id, dados in dados_por_loja.items():
        media = sum(dados['pontuacoes']) / len(dados['pontuacoes']) if dados['pontuacoes'] else 0
        ranking.append({
            'loja': dados['nome'],
            'media': round(media, 1),
            'total_auditorias': dados['total_auditorias'],
            'status': 'success' if media >= 80 else 'warning' if media >= 60 else 'danger'
        })
    
    # Ordenar por média decrescente
    ranking.sort(key=lambda x: x['media'], reverse=True)
    
    return ranking[:10]  # Top 10

def gerar_top_nao_conformidades(auditorias):
    """Gera top das não conformidades mais frequentes"""
    if not auditorias:
        return []
    
    # Buscar respostas "Não" mais frequentes
    nao_conformidades = {}
    
    for auditoria in auditorias:
        for resposta in auditoria.respostas:
            if resposta.valor_opcoes_selecionadas:
                try:
                    opcoes = json.loads(resposta.valor_opcoes_selecionadas)
                    if 'Não' in opcoes:
                        pergunta_texto = resposta.pergunta.texto
                        if pergunta_texto not in nao_conformidades:
                            nao_conformidades[pergunta_texto] = 0
                        nao_conformidades[pergunta_texto] += 1
                except:
                    pass
    
    # Ordenar e retornar top 10
    top_ncs = sorted(nao_conformidades.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return [{'pergunta': pergunta, 'frequencia': freq} for pergunta, freq in top_ncs]
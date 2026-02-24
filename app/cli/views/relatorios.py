# app/cli/views/relatorios.py
import io
import csv
from datetime import datetime
from flask import request, redirect, url_for, flash, jsonify, Response, current_app
from flask_login import current_user, login_required
from sqlalchemy import func, extract

# Importa Blueprint
from .. import cli_bp

# Importa Utilitários
from ..utils import (
    render_template_safe, gerar_pdf_seguro, 
    get_avaliados_usuario, verificar_alertas_atraso
)

# Importa Modelos
from ...models import (
    db, Usuario, Avaliado, Questionario, AplicacaoQuestionario, StatusAplicacao
)

# ===================== DASHBOARD (HOME) =====================

@cli_bp.route('/')
@cli_bp.route('/home')
@login_required
def index():
    """Dashboard principal."""
    
    # 1. Alertas de Atraso (Planos de Ação)
    verificar_alertas_atraso(current_user)

    stats = {
        'total_aplicacoes': 0, 'aplicacoes_mes': 0,
        'questionarios_ativos': 0, 'avaliados_ativos': 0,
        'media_nota_mes': 0, 'aplicacoes_pendentes': 0
    }
    ultimas = []
    populares = []

    try:
        if current_user.cliente_id:
            # Stats Básicos
            stats['total_aplicacoes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id
            ).count()

            stats['aplicacoes_mes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                extract('month', AplicacaoQuestionario.data_inicio) == datetime.now().month,
                extract('year', AplicacaoQuestionario.data_inicio) == datetime.now().year
            ).count()

            stats['questionarios_ativos'] = Questionario.query.filter_by(
                cliente_id=current_user.cliente_id, ativo=True, publicado=True
            ).count()

            stats['avaliados_ativos'] = Avaliado.query.filter_by(
                cliente_id=current_user.cliente_id, ativo=True
            ).count()

            # Média Mensal
            media = db.session.query(func.avg(AplicacaoQuestionario.nota_final)).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None),
                extract('month', AplicacaoQuestionario.data_inicio) == datetime.now().month
            ).scalar()
            stats['media_nota_mes'] = round(float(media or 0), 1)

            # Aplicações em Andamento
           stats['aplicacoes_pendentes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.status == StatusAplicacao.EM_ANDAMENTO
            ).count()

            # Tabelas
            ultimas = AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id
            ).order_by(AplicacaoQuestionario.data_inicio.desc()).limit(5).all()

            populares = db.session.query(
                Questionario.nome, func.count(AplicacaoQuestionario.id).label('total')
            ).join(AplicacaoQuestionario).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id
            ).group_by(Questionario.id, Questionario.nome).order_by(
                func.count(AplicacaoQuestionario.id).desc()
            ).limit(5).all()

    except Exception as e:
        print(f"Erro Dashboard: {e}")

    return render_template_safe('cli/index.html', 
                         stats=stats, 
                         ultimas_aplicacoes=ultimas,
                         questionarios_populares=populares)

# ===================== PÁGINA DE RELATÓRIOS =====================

@cli_bp.route('/relatorios')
@login_required
def relatorios():
    """Tela de filtros e gráficos."""
    try:
        avaliados = get_avaliados_usuario()
        questionarios = Questionario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
        
        # Stats rápidos para o topo da página
        stats = {
            'total_aplicacoes': AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id
            ).count(),
            'media_geral': db.session.query(func.avg(AplicacaoQuestionario.nota_final)).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            ).scalar() or 0,
            'aplicacoes_mes': AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                extract('month', AplicacaoQuestionario.data_inicio) == datetime.now().month
            ).count()
        }
        
        return render_template_safe('cli/relatorios.html',
                             avaliados=avaliados,
                             questionarios=questionarios,
                             stats=stats)
    except Exception as e:
        flash(f"Erro: {str(e)}", "danger")
        return redirect(url_for('cli.index'))

# ===================== API DE DADOS (GRÁFICOS) =====================

@cli_bp.route('/api/relatorio-dados')
@login_required
def api_dados_relatorio():
    """Fornece JSON para os gráficos (Ranking, Evolução, Comparativo)."""
    try:
        tipo = request.args.get('tipo', 'ranking')
        avaliado_id = request.args.get('avaliado_id')
        questionario_id = request.args.get('questionario_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        dados = {}
        
        # Base Query
        query = db.session.query().select_from(AplicacaoQuestionario).join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            AplicacaoQuestionario.nota_final.isnot(None)
        )

        # Filtros Comuns
        if data_inicio: query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        if data_fim: query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        if tipo == 'ranking':
            # Ranking de Avaliados (Melhores notas)
            q = query.add_columns(
                Avaliado.nome, 
                func.avg(AplicacaoQuestionario.nota_final).label('media'),
                func.count(AplicacaoQuestionario.id).label('total')
            ).group_by(Avaliado.id, Avaliado.nome).order_by(func.avg(AplicacaoQuestionario.nota_final).desc())
            
            dados['ranking'] = [
                {'avaliado': r.nome, 'media': round(float(r.media), 2), 'total_aplicacoes': r.total}
                for r in q.all()
            ]
            
        elif tipo == 'evolucao':
            # Evolução Temporal
            if avaliado_id: query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
            if questionario_id: query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
            
            q = query.add_columns(
                func.date(AplicacaoQuestionario.data_inicio).label('data'),
                func.avg(AplicacaoQuestionario.nota_final).label('media')
            ).group_by(func.date(AplicacaoQuestionario.data_inicio)).order_by('data')
            
            dados['evolucao'] = [
                {'data': r.data.strftime('%Y-%m-%d'), 'media': round(float(r.media), 2)}
                for r in q.all()
            ]
            
        elif tipo == 'comparativo':
            # Comparativo entre Questionários
            q = query.join(Questionario).add_columns(
                Questionario.nome,
                func.avg(AplicacaoQuestionario.nota_final).label('media'),
                func.count(AplicacaoQuestionario.id).label('total')
            ).group_by(Questionario.id, Questionario.nome)
            
            dados['comparativo'] = [
                {'questionario': r.nome, 'media': round(float(r.media), 2), 'total_aplicacoes': r.total}
                for r in q.all()
            ]
        
        return jsonify(dados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/api/estatisticas')
@login_required
def api_estatisticas():
    """API para cards do dashboard (AJAX)."""
    try:
        hoje = datetime.now()
        inicio_mes = datetime(hoje.year, hoje.month, 1)
        
        stats = {
            'aplicacoes_hoje': AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                func.date(AplicacaoQuestionario.data_inicio) == hoje.date()
            ).count(),
            'aplicacoes_mes': AplicacaoQuestionario.query.join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.data_inicio >= inicio_mes
            ).count(),
            'media_mensal': db.session.query(func.avg(AplicacaoQuestionario.nota_final)).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.data_inicio >= inicio_mes,
                AplicacaoQuestionario.nota_final.isnot(None)
            ).scalar() or 0
        }
        stats['media_mensal'] = round(float(stats['media_mensal']), 1)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===================== EXPORTAÇÃO =====================

@cli_bp.route('/relatorio/exportar')
@login_required
def exportar_relatorio():
    """Controlador de Exportação (PDF/CSV)."""
    try:
        formato = request.args.get('formato', 'pdf')
        # Reutiliza a lógica da API para pegar os dados
        # (Em produção, ideal extrair para service layer, mas aqui simulamos chamada interna)
        
        # Simulação de query (mesma lógica do Ranking)
        query = db.session.query(
            Avaliado.nome,
            func.avg(AplicacaoQuestionario.nota_final).label('media'),
            func.count(AplicacaoQuestionario.id).label('total')
        ).join(AplicacaoQuestionario).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            AplicacaoQuestionario.nota_final.isnot(None)
        )
        
        di = request.args.get('data_inicio')
        df = request.args.get('data_fim')
        if di: query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(di, '%Y-%m-%d'))
        if df: query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(df + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        resultados = query.group_by(Avaliado.id, Avaliado.nome).order_by(
            func.avg(AplicacaoQuestionario.nota_final).desc()
        ).all()
        
        dados = [{'avaliado': r.nome, 'media': round(float(r.media), 2), 'total': r.total} for r in resultados]
        
        if formato == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Posição', 'Avaliado', 'Nota Média', 'Total Aplicações'])
            for i, item in enumerate(dados, 1):
                writer.writerow([i, item['avaliado'], item['media'], item['total']])
            output.seek(0)
            return Response(output.getvalue(), mimetype='text/csv', 
                           headers={'Content-Disposition': f'attachment; filename=Ranking_{datetime.now().strftime("%Y%m%d")}.csv'})
                           
        elif formato == 'pdf':
            html = f"""
            <h2>Relatório de Ranking - {datetime.now().strftime('%d/%m/%Y')}</h2>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr style="background:#f0f0f0;"><th>Pos</th><th>Avaliado</th><th>Média</th><th>Qtd</th></tr>
            """
            for i, item in enumerate(dados, 1):
                html += f"<tr><td>{i}</td><td>{item['avaliado']}</td><td>{item['media']}%</td><td>{item['total']}</td></tr>"
            html += "</table>"
            
            return gerar_pdf_seguro(html, f"Ranking_{datetime.now().strftime('%Y%m%d')}.pdf")

    except Exception as e:
        flash(f"Erro exportação: {str(e)}", "danger")
        return redirect(url_for('cli.relatorios'))
    
    return redirect(url_for('cli.relatorios'))
# app/panorama/routes.py - DASHBOARD FUNCIONAL
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, flash
from flask_login import login_required, current_user
from sqlalchemy import func, extract, and_, desc
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload, selectinload
import json

from ..models import (
    db, AplicacaoQuestionario, Avaliado, Questionario, RespostaPergunta,
    Pergunta, StatusAplicacao, TipoResposta, Cliente, Grupo, CategoriaIndicador, Topico, DocumentoMensal
)

from ..cli.utils import get_avaliados_usuario

def _obter_ids_primeiras_aplicacoes():
    """Retorna uma lista contendo os IDs da primeira aplicação finalizada para cada rancho"""
    subq = db.session.query(
        AplicacaoQuestionario.avaliado_id, 
        func.min(AplicacaoQuestionario.data_inicio).label('primeira_data')
    ).filter(AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA).group_by(AplicacaoQuestionario.avaliado_id).subquery()
    
    primeiras_aplicacoes = db.session.query(AplicacaoQuestionario.id).join(
        subq,
        (AplicacaoQuestionario.avaliado_id == subq.c.avaliado_id) &
        (AplicacaoQuestionario.data_inicio == subq.c.primeira_data)
    ).all()
    
    return [r[0] for r in primeiras_aplicacoes]

def aplicar_filtro_hierarquia(query, model_avaliado=Avaliado):
    """Aplica o filtro de acessos hierárquicos à query (seja de dashboard, avaliados, etc)"""
    # 1. Busca os ranchos aos quais este usuário tem permissão
    avaliados_permitidos = get_avaliados_usuario()
    ids_permitidos = [a.id for a in avaliados_permitidos]
    
    # 2. Se a lista estiver vazia, retorna ID falso para garantir que nada apareça
    if not ids_permitidos:
        return query.filter(model_avaliado.id == -1)
        
    # 3. Se for Super Admin / Admin, IDs permitidos conteria TODOS os ranchos,
    # então a query .in_() já vai filtrar naturalmente. 
    return query.filter(model_avaliado.id.in_(ids_permitidos))

panorama_bp = Blueprint('panorama', __name__, template_folder='templates')

from flask import flash

@panorama_bp.before_request
def restrict_consultoras():
    """Bloqueia Consultoras de acessarem as rotas do Panorama/Dashboard."""
    if current_user.is_authenticated and current_user.tipo.name == 'AUDITOR':
        flash("Acesso restrito: O seu perfil de Consultora não tem acesso às métricas do Panorama.", "warning")
        return redirect(url_for('main.painel'))

@panorama_bp.route('/')
@login_required
def index():
    return redirect(url_for('panorama.dashboard'))

@panorama_bp.route('/dashboard')
@login_required
def dashboard():
    # Apenas carrega os filtros para a tela abrir instantaneamente (Interface Otimizada)
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
        'grupos': query_grupos.order_by(Grupo.nome).all(),
        'topicos': Topico.query.join(Questionario).filter(Questionario.cliente_id == current_user.cliente_id).order_by(Topico.ordem).all()
    }

    # Enviamos tudo vazio para o HTML montar a casca imediatamente. O JS fará a requisição real.
    return render_template(
        'panorama/dashboard.html',
        metricas={'total_auditorias': 0, 'pontuacao_media': 0, 'lojas_auditadas': 0, 'tendencia_pontuacao': 0, 'auditorias_criticas': 0, 'conformidade_geral': 0},
        graficos={'evolucao_pontuacao': {}, 'evolucao_topicos': [], 'topicos_rancho': {}, 'pontuacao_por_avaliado': {}, 'pontuacao_por_questionario': {}, 'distribuicao_notas': {}, 'ranking_avaliados': [], 'top_nao_conformidades': []},
        filtros=filtros,
        filtros_aplicados={
            'mes': request.args.get('mes', ''),
            'avaliado_id': request.args.get('avaliado_id', type=int),
            'questionario_id': request.args.get('questionario_id', type=int),
            'grupo_id': request.args.get('grupo_id', type=int),
            'periodo': request.args.get('periodo', '30')
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
    
@panorama_bp.route('/laudos')
@login_required
def laudos():
    # Visão SDAB: Todos os GAPs e seus Ranchos
    query_grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
    if current_user.grupo_id:
        # Visão GAP: Apenas o seu GAP
        query_grupos = query_grupos.filter(Grupo.id == current_user.grupo_id)
    
    # Se for um usuário local de Rancho (sem grupo, ou com avaliado_id setado) que pularia o dashboard hierarquico:
    if current_user.avaliado_id:
        return redirect(url_for('panorama.laudos_rancho', avaliado_id=current_user.avaliado_id))

    grupos = query_grupos.order_by(Grupo.nome).all()
    
    # Organizar ranchos por grupo
    dados_hierarquia = {}
    for grupo in grupos:
        dados_hierarquia[grupo.nome] = Avaliado.query.filter_by(grupo_id=grupo.id, ativo=True).order_by(Avaliado.nome).all()
        
    return render_template('panorama/laudos_dashboard.html', hierarquia=dados_hierarquia)

@panorama_bp.route('/laudos/<int:avaliado_id>')
@login_required
def laudos_rancho(avaliado_id):
    # Trava de Segurança
    query_seguranca = Avaliado.query.filter_by(id=avaliado_id, cliente_id=current_user.cliente_id)
    query_seguranca = aplicar_filtro_hierarquia(query_seguranca)
    avaliado = query_seguranca.first_or_404()
    
    aplicacoes = AplicacaoQuestionario.query.filter_by(
        avaliado_id=avaliado_id, 
        status=StatusAplicacao.FINALIZADA
    ).order_by(desc(AplicacaoQuestionario.data_fim)).all()
    
    return render_template('panorama/laudos_rancho.html',
                           avaliado=avaliado,
                           aplicacoes=aplicacoes)

# ======================== MÓDULO PLANILHAS (Hierárquico) ========================

@panorama_bp.route('/planilhas')
@login_required
def planilhas():
    """Atalho gerencial para listar planilhas via GAPs"""
    query_grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
    if current_user.grupo_id:
        query_grupos = query_grupos.filter(Grupo.id == current_user.grupo_id)
    
    if current_user.avaliado_id:
        return redirect(url_for('panorama.planilhas_rancho', avaliado_id=current_user.avaliado_id))

    grupos = query_grupos.order_by(Grupo.nome).all()
    return render_template('panorama/hierarquia_lista.html', 
                           titulo="Central de Planilhas",
                           icone="fa-file-excel",
                           cor="success",
                           grupos=grupos,
                           endpoint_rancho="panorama.planilhas_rancho")

@panorama_bp.route('/planilhas/rancho/<int:avaliado_id>')
@login_required
def planilhas_rancho(avaliado_id):
    """Lista visitas de um rancho que possuam planilhas"""
    avaliado = Avaliado.query.get_or_404(avaliado_id)
    if avaliado.cliente_id != current_user.cliente_id: abort(403)
    
    # Busca aplicações que tenham planilhas vinculadas
    from ..models import PlanilhaVisita
    aplicacoes = AplicacaoQuestionario.query.join(PlanilhaVisita).filter(
        AplicacaoQuestionario.avaliado_id == avaliado_id,
        AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
    ).distinct().order_by(desc(AplicacaoQuestionario.data_fim)).all()

    return render_template('panorama/visitas_lista.html',
                           titulo="Planilhas por Visita",
                           icone="fa-file-excel",
                           cor="success",
                           avaliado=avaliado,
                           aplicacoes=aplicacoes,
                           tipo_anexo="planilhas")

# ======================== MÓDULO RELATÓRIOS (Hierárquico) ========================

@panorama_bp.route('/relatorios-hierarquia')
@login_required
def relatorios_hierarquia():
    """Atalho gerencial para listar relatórios via GAPs"""
    query_grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
    if current_user.grupo_id:
        query_grupos = query_grupos.filter(Grupo.id == current_user.grupo_id)
    
    if current_user.avaliado_id:
        return redirect(url_for('panorama.relatorios_rancho', avaliado_id=current_user.avaliado_id))

    grupos = query_grupos.order_by(Grupo.nome).all()
    return render_template('panorama/hierarquia_lista.html', 
                           titulo="Central de Relatórios",
                           icone="fa-file-pdf",
                           cor="danger",
                           grupos=grupos,
                           endpoint_rancho="panorama.relatorios_rancho")

@panorama_bp.route('/relatorios/rancho/<int:avaliado_id>')
@login_required
def relatorios_rancho(avaliado_id):
    """Lista visitas de um rancho com foco em relatórios"""
    avaliado = Avaliado.query.get_or_404(avaliado_id)
    if avaliado.cliente_id != current_user.cliente_id: abort(403)
    
    aplicacoes = AplicacaoQuestionario.query.filter_by(
        avaliado_id=avaliado_id,
        status=StatusAplicacao.FINALIZADA
    ).order_by(desc(AplicacaoQuestionario.data_fim)).all()

    return render_template('panorama/visitas_lista.html',
                           titulo="Relatórios da Unidade",
                           icone="fa-file-pdf",
                           cor="danger",
                           avaliado=avaliado,
                           aplicacoes=aplicacoes,
                           tipo_anexo="relatorios")

# ======================== MÓDULO TREINAMENTO ========================

@panorama_bp.route('/treinamento')
@login_required
def treinamento():
    """Acesso ao módulo de Treinamento"""
    from ..models import Treinamento
    query = Treinamento.query.filter_by(cliente_id=current_user.cliente_id)
    
    if current_user.avaliado_id:
        query = query.filter(Treinamento.avaliado_id == current_user.avaliado_id)
    elif current_user.grupo_id:
        query = query.filter(Treinamento.grupo_id == current_user.grupo_id)
        
    treinamentos = query.order_by(desc(Treinamento.data)).all()
    
    # Filtros para novo cadastro
    query_grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
    query_avaliados = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
    
    if current_user.grupo_id:
        query_grupos = query_grupos.filter(Grupo.id == current_user.grupo_id)
        query_avaliados = query_avaliados.filter(Avaliado.grupo_id == current_user.grupo_id)
        
    return render_template('panorama/treinamento_dashboard.html',
                           treinamentos=treinamentos,
                           grupos=query_grupos.all(),
                           avaliados=query_avaliados.all())

@panorama_bp.route('/treinamento/novo', methods=['POST'])
@login_required
def treinamento_novo():
    """Salva um novo treinamento"""
    from ..models import Treinamento
    try:
        data_str = request.form.get('data')
        data_obj = datetime.strptime(data_str, '%Y-%m-%d') if data_str else datetime.utcnow()
        
        novo = Treinamento(
            tema=request.form.get('tema'),
            data=data_obj,
            conteudo=request.form.get('conteudo'),
            cliente_id=current_user.cliente_id,
            grupo_id=request.form.get('grupo_id') or None,
            avaliado_id=request.form.get('avaliado_id') or None,
            criado_por_id=current_user.id
        )
        
        # Upload de material se houver
        if 'material' in request.files:
            file = request.files['material']
            if file and file.filename != '':
                import uuid
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"treino_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                novo.materiais_arquivo = filename
                
        db.session.add(novo)
        db.session.commit()
        return redirect(url_for('panorama.treinamento'))
    except Exception as e:
        db.session.rollback()
        return f"Erro ao salvar treinamento: {str(e)}", 500

@panorama_bp.route('/treinamento/<int:treinamento_id>/participantes', methods=['GET', 'POST'])
@login_required
def treinamento_participantes(treinamento_id):
    """Gerenciamento de participantes via AJAX/Modal"""
    from ..models import Treinamento, TreinamentoParticipante
    treino = Treinamento.query.get_or_404(treinamento_id)
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            matricula = request.form.get('matricula')
            if nome:
                novo = TreinamentoParticipante(
                    treinamento_id=treinamento_id,
                    nome=nome,
                    matricula=matricula
                )
                db.session.add(novo)
                db.session.commit()
                return jsonify({'sucesso': True, 'participante': {'id': novo.id, 'nome': novo.nome, 'matricula': novo.matricula}})
        except Exception as e:
            return jsonify({'erro': str(e)}), 500
            
    participantes = [{'id': p.id, 'nome': p.nome, 'matricula': p.matricula} for p in treino.participantes]
    return jsonify({'participantes': participantes})

@panorama_bp.route('/treinamento/participante/<int:id>/excluir', methods=['POST'])
@login_required
def treinamento_participante_excluir(id):
    from ..models import TreinamentoParticipante
    p = TreinamentoParticipante.query.get_or_404(id)
    tid = p.treinamento_id
    db.session.delete(p)
    db.session.commit()
    return jsonify({'sucesso': True})

@panorama_bp.route('/dossie/<int:avaliado_id>')
@login_required
def dossie(avaliado_id):
    # Trava de Segurança
    query_seguranca = Avaliado.query.filter_by(id=avaliado_id, cliente_id=current_user.cliente_id)
    query_seguranca = aplicar_filtro_hierarquia(query_seguranca)
    avaliado = query_seguranca.first_or_404()
    
    # 🚀 NOVO: Ignorar a primeira aplicação de cada rancho
    ids_excluidos = _obter_ids_primeiras_aplicacoes()
    
    aplicacoes = AplicacaoQuestionario.query.filter_by(
        avaliado_id=avaliado_id, 
        status=StatusAplicacao.FINALIZADA
    ).filter(
        ~AplicacaoQuestionario.id.in_(ids_excluidos)
    ).order_by(desc(AplicacaoQuestionario.data_inicio)).all()

    # Buscar treinamentos do Rancho
    from ..models import Treinamento
    treinamentos = Treinamento.query.filter_by(avaliado_id=avaliado_id).order_by(desc(Treinamento.data)).all()

    # --- NOVO: Carregar TODAS as respostas para calcular Tópicos ---
    aplicacao_ids = [app.id for app in aplicacoes]
    if aplicacao_ids:
        todas_respostas = RespostaPergunta.query.options(
            joinedload(RespostaPergunta.pergunta).joinedload(Pergunta.topico)
        ).filter(RespostaPergunta.aplicacao_id.in_(aplicacao_ids)).all()
        
        respostas_agrupadas = {app_id: [] for app_id in aplicacao_ids}
        for resp in todas_respostas:
            respostas_agrupadas[resp.aplicacao_id].append(resp)
            
        for app in aplicacoes:
            app._respostas_carregadas = respostas_agrupadas.get(app.id, [])
    else:
        for app in aplicacoes:
            app._respostas_carregadas = []
    # ---------------------------------------------------------------
    
    # Processa os dados cronológicos para injetar no Chart.js do Dossiê
    grafico_timeline = {
        'datas': [],
        'notas': [],
        'aplicadores': []
    }
    
    topicos_data = {} # Dicionário de Tópicos
    
    # Lendo de baixo pra cima (Ascendente para o gráfico ficar da Esquerda -> Direita)
    
    # --- NOVO: Mapear a ordem oficial dos Tópicos para exibição correta ---
    ordem_topicos_map = {}
    if aplicacao_ids:
        # Pega a ordem de todos os tópicos vinculados aos questionários destas aplicações
        quest_ids = list(set([app.questionario_id for app in aplicacoes if app.questionario_id]))
        topicos_oficiais = Topico.query.join(Questionario).filter(Questionario.id.in_(quest_ids)).all()
        for t in topicos_oficiais:
             ordem_topicos_map[t.nome] = t.ordem
    # -------------------------------------------------------------------------

    for app in reversed(aplicacoes):
        if app.nota_final is not None:
            data_label = app.data_inicio.strftime('%d/%m/%Y')
            grafico_timeline['datas'].append(data_label)
            grafico_timeline['notas'].append(app.nota_final)
            grafico_timeline['aplicadores'].append(app.aplicador.nome if app.aplicador else 'Desconhecido')
            
            # Agrupar respostas por tópico para esta aplicação
            pontos_por_topico = {}
            for resp in getattr(app, '_respostas_carregadas', []):
                if not resp.pergunta or not resp.pergunta.topico: continue
                t_nome = resp.pergunta.topico.nome
                if t_nome not in pontos_por_topico:
                    pontos_por_topico[t_nome] = {'obtido': 0, 'maximo': 0}
                pontos_por_topico[t_nome]['obtido'] += (resp.pontos or 0)
                pontos_por_topico[t_nome]['maximo'] += (resp.pergunta.peso or 0)
                
            # Calcular nota de cada tópico nesta data e registrar na curva evolutiva global daquele tópico
            for t_nome, pts in pontos_por_topico.items():
                if t_nome not in topicos_data:
                    topicos_data[t_nome] = {'labels': [], 'data': [], 'ordem': ordem_topicos_map.get(t_nome, 999)}
                
                nota_pct = (pts['obtido'] / pts['maximo']) * 10 if pts['maximo'] > 0 else 0
                topicos_data[t_nome]['labels'].append(data_label)
                topicos_data[t_nome]['data'].append(round(nota_pct, 1))

    # Ordenar o dicionário topicos_data com base na chave 'ordem' antes de enviar ao template
    topicos_data_ordenado = dict(sorted(topicos_data.items(), key=lambda item: item[1].get('ordem', 999)))
            
    # Média Consolidada Header
    media_geral = round(sum(grafico_timeline['notas']) / len(grafico_timeline['notas']), 2) if grafico_timeline['notas'] else 0
    status_atual = 'success' if media_geral >= 70 else 'danger' # NOVO: CORTE 7.0

    return render_template(
        'panorama/dossie.html', 
        avaliado=avaliado,
        aplicacoes=aplicacoes,
        treinamentos=treinamentos,
        media_geral=media_geral,
        status_atual=status_atual,
        grafico_json=json.dumps(grafico_timeline),
        topicos_json=json.dumps(topicos_data_ordenado)
    )

@panorama_bp.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        periodo = request.args.get('periodo', '30')
        mes_filtro = request.args.get('mes', '')
        avaliado_id = request.args.get('avaliado_id', type=int)  
        questionario_id = request.args.get('questionario_id', type=int)
        grupo_id = request.args.get('grupo_id', type=int) 
        topico_id = request.args.get('topico_id', type=int) 

        agora = datetime.now()
        if not data_fim: data_fim = agora
        
        if not data_inicio and not mes_filtro:
            if periodo == '7': data_inicio = agora - timedelta(days=7)
            elif periodo == '90': data_inicio = agora - timedelta(days=90)
            elif periodo == '365': data_inicio = agora - timedelta(days=365)
            else: data_inicio = agora - timedelta(days=30)

        query = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
        )
        query = aplicar_filtro_hierarquia(query)

        # 1. Carrega apenas os relacionamentos diretos (O selectinload foi removido daqui)
        query = query.options(
            joinedload(AplicacaoQuestionario.avaliado),
            joinedload(AplicacaoQuestionario.questionario),
            joinedload(AplicacaoQuestionario.aplicador)
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

        # 🚀 NOVO: Ignorar a primeira aplicação de cada rancho no dashboard
        ids_excluidos = _obter_ids_primeiras_aplicacoes()
        query = query.filter(~AplicacaoQuestionario.id.in_(ids_excluidos))

        aplicacoes = query.all()
        aplicacao_ids = [app.id for app in aplicacoes]

        # 🚀 SOLUÇÃO DO GARGALO COM POSTGRESQL: Busca TODAS as respostas em lote
        if aplicacao_ids:
            todas_respostas = RespostaPergunta.query.options(
                joinedload(RespostaPergunta.pergunta).joinedload(Pergunta.topico)
            ).filter(RespostaPergunta.aplicacao_id.in_(aplicacao_ids)).all()
            
            respostas_agrupadas = {app_id: [] for app_id in aplicacao_ids}
            for resp in todas_respostas:
                respostas_agrupadas[resp.aplicacao_id].append(resp)
                
            for app in aplicacoes:
                app._respostas_carregadas = respostas_agrupadas.get(app.id, [])
        else:
            for app in aplicacoes:
                app._respostas_carregadas = []

        # Calcula a pontuação com os dados que já vieram da memória (super rápido)
        from ..utils.pontuacao import calcular_pontuacao_auditoria
        for app in aplicacoes:
            app._cache_resultado = calcular_pontuacao_auditoria(app)

        data = {
            'metricas': calcular_metricas_dashboard(aplicacoes),
            'evolucao': gerar_grafico_evolucao_mensal(aplicacoes, topico_id), 
            'evolucao_topicos': gerar_grafico_evolucao_topicos(aplicacoes, topico_id),
            'topicos': gerar_grafico_topicos(aplicacoes, topico_id),          
            'por_avaliado': gerar_grafico_avaliados(aplicacoes, topico_id),  
            'distribuicao': gerar_grafico_distribuicao(aplicacoes, topico_id),
            'questionarios': gerar_grafico_questionarios(aplicacoes, topico_id),
            'ranking_avaliados': gerar_ranking_avaliados(aplicacoes, topico_id),
            'top_nao_conformidades': gerar_top_nao_conformidades(aplicacoes, topico_id),
            'mapa_dados': gerar_dados_mapa(aplicacoes, topico_id),
            'acoes_corretivas': gerar_grafico_acoes_corretivas(aplicacao_ids),
            'ranking_por_topico': gerar_graficos_ranking_topicos(aplicacoes, topico_id)
        }
        return jsonify(data)
    except Exception as e:
        print("ERRO NO DASHBOARD:", str(e))
        return jsonify({'error': str(e)}), 500

def gerar_graficos_ranking_topicos(aplicacoes, topico_id_filtro=None):
    """
    Gera dados para gráficos de barra (um por Tópico) onde o eixo X são as Lojas (Avaliados)
    eixo Y é a nota média da loja naquele tópico, ordenado da pior para a melhor loja.
    """
    if not aplicacoes: return []
    
    # 1. Agrupar dados: { 'Higiene': { loja_id1: {'nome': 'Rancho X', 'obtido': 100, 'maximo': 200}, loja_id2: ...} }
    dados_por_topico = {}
    
    # Extrair todos os tópicos reais diretamente das respostas, garantindo dados reais e com ordem
    topicos_encontrados = {} 
    
    # Se tiver filtro
    t_obj = Topico.query.get(topico_id_filtro) if topico_id_filtro else None
    filtro_nome = t_obj.nome if t_obj else None

    for app in aplicacoes:
        aval_id = app.avaliado_id
        aval_nome = app.avaliado.nome
        
        for resp in getattr(app, '_respostas_carregadas', []):
            if not resp.pergunta or not resp.pergunta.topico: continue
            
            t_nome = resp.pergunta.topico.nome
            
            # Ignora Assinaturas e Conclusão se houver
            if t_nome == 'Assinaturas' or t_nome == 'Conclusão': continue
            
            if filtro_nome and t_nome != filtro_nome: continue # Filtro
            
            if t_nome not in topicos_encontrados:
                topicos_encontrados[t_nome] = resp.pergunta.topico.ordem or 99
            
            if t_nome not in dados_por_topico:
                dados_por_topico[t_nome] = {}
            if aval_id not in dados_por_topico[t_nome]:
                dados_por_topico[t_nome][aval_id] = {'nome': aval_nome, 'obtido': 0, 'maximo': 0}
                
            dados_por_topico[t_nome][aval_id]['obtido'] += (resp.pontos or 0)
            dados_por_topico[t_nome][aval_id]['maximo'] += (resp.pergunta.peso or 0)
            
    # 2. Processar e formatar para o Chart.js
    lista_graficos = []
    
    # Ordena os tópicos pela ordem original do questionário (coletada do db)
    topicos_nomes_ordenados = sorted(topicos_encontrados.keys(), key=lambda k: topicos_encontrados[k])
    
    for t_nome in topicos_nomes_ordenados:
        if t_nome not in dados_por_topico: continue
        
        lojas_pontuacoes = []
        for a_id, dados_loja in dados_por_topico[t_nome].items():
            if dados_loja['maximo'] > 0:
                nota_pct = (dados_loja['obtido'] / dados_loja['maximo']) * 10
                lojas_pontuacoes.append({
                    'id': a_id,
                    'nome': dados_loja['nome'],
                    'nota': round(nota_pct, 1)
                })
                
        if not lojas_pontuacoes: continue
        
        # Ordenar da pior para a melhor loja (ajuda na tomada de decisão)
        lojas_pontuacoes.sort(key=lambda x: x['nota'])
        
        labels_lojas = [lp['nome'] for lp in lojas_pontuacoes]
        notas_lojas = [lp['nota'] for lp in lojas_pontuacoes]
        avaliados_ids = [lp['id'] for lp in lojas_pontuacoes]
        
        # Cores tipo semáforo baseadas na pontuação (Nota corte: 7.0)
        cores_barras = []
        for n in notas_lojas:
            if n >= 7.0: cores_barras.append('rgba(25, 135, 84, 0.85)') # success (Verde)
            else: cores_barras.append('rgba(220, 53, 69, 0.85)') # danger (Vermelho)
            
        lista_graficos.append({
            'titulo': t_nome,
            'id_canvas': f'chartRankingTopic_{abs(hash(t_nome))}',
            'dados': {
                'labels': labels_lojas,
                'avaliados_ids': avaliados_ids,
                'datasets': [{
                    'label': 'Nota Média',
                    'data': notas_lojas,
                    'backgroundColor': cores_barras,
                    'borderRadius': 4
                }]
            }
        })

    return lista_graficos

@panorama_bp.route('/api/export-data')
@login_required
def api_export_data():
    query = AplicacaoQuestionario.query.join(Avaliado).filter(
        Avaliado.cliente_id == current_user.cliente_id,
        AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
    )
    query = aplicar_filtro_hierarquia(query)
    
    # 🚀 NOVO: Ignorar a primeira aplicação de cada rancho
    ids_excluidos = _obter_ids_primeiras_aplicacoes()
    query = query.filter(~AplicacaoQuestionario.id.in_(ids_excluidos))
    
    aplicacoes = query.all()

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
    # Convert 'nota_final' (0-100) to 0-10 base
    pontuacoes = [(a.nota_final / 10) for a in aplicacoes if a.nota_final is not None]
    pontuacao_media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
    avaliados_avaliados = len(set(a.avaliado_id for a in aplicacoes))
    # Criticas are < 7.0 (out of 10)
    aplicacoes_criticas = len([p for p in pontuacoes if p < 7.0])
    # Conformes >= 7.0 (out of 10)
    conformes = len([p for p in pontuacoes if p >= 7.0])
    conformidade_geral = (conformes / total_aplicacoes * 100) if total_aplicacoes > 0 else 0

    agora = datetime.now()
    duas_semanas_atras = agora - timedelta(days=14)
    quatro_semanas_atras = agora - timedelta(days=28)
    recentes = [(a.nota_final / 10) for a in aplicacoes if a.data_inicio >= duas_semanas_atras and a.nota_final is not None]
    anteriores = [(a.nota_final / 10) for a in aplicacoes if quatro_semanas_atras <= a.data_inicio < duas_semanas_atras and a.nota_final is not None]
    media_recente = sum(recentes) / len(recentes) if recentes else 0
    media_anterior = sum(anteriores) / len(anteriores) if anteriores else 0

    return {
        'total_auditorias': total_aplicacoes, 'pontuacao_media': round(pontuacao_media, 1),
        'lojas_auditadas': avaliados_avaliados, 'tendencia_pontuacao': round(media_recente - media_anterior, 1),
        'auditorias_criticas': aplicacoes_criticas, 'conformidade_geral': round(conformidade_geral, 1)
    }

def gerar_grafico_avaliados(aplicacoes, topico_id=None):
    if not aplicacoes: return {'labels': [], 'datasets': []}
    dados_por_avaliado = {}
    for aplicacao in aplicacoes:
        avaliado_id = aplicacao.avaliado_id
        avaliado_nome = aplicacao.avaliado.nome 
        if avaliado_id not in dados_por_avaliado: dados_por_avaliado[avaliado_id] = {'nome': avaliado_nome, 'notas': []}
        
        nota = (aplicacao.nota_final / 10) if aplicacao.nota_final else 0
        if topico_id:
            total_pontos = sum([resp.pontos or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            total_maximo = sum([resp.pergunta.peso or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            nota = (total_pontos / total_maximo) * 10 if total_maximo > 0 else 0

        dados_por_avaliado[avaliado_id]['notas'].append(nota)

    lista_ordenada = []
    for avaliado_id, avalInfo in dados_por_avaliado.items():
        media = sum(avalInfo['notas']) / len(avalInfo['notas']) if avalInfo['notas'] else 0
        lista_ordenada.append({'id': avaliado_id, 'avaliado': avalInfo['nome'], 'media': round(media, 1)})
    lista_ordenada.sort(key=lambda x: x['media'])

    labels, valores, cores, avaliados_ids = [], [], [], []
    for item in lista_ordenada:
        labels.append(item['avaliado'])
        valores.append(item['media'])
        avaliados_ids.append(item['id'])
        if item['media'] >= 7.0: cores.append('#198754') # Verde
        else: cores.append('#dc3545') # Vermelho

    return {'labels': labels, 'avaliados_ids': avaliados_ids, 'datasets': [{'label': 'Pontuação Média', 'data': valores, 'backgroundColor': cores}]}

def gerar_dados_mapa(aplicacoes, topico_id=None):
    """
    Agrupa as aplicações por 'Rancho', calcula a média e constrói a lista para o mapa do Frontend.
    """
    if not aplicacoes: return []

    dados_por_avaliado = {}
    from ..utils.pontuacao import calcular_pontuacao_auditoria
    
    for aplicacao in aplicacoes:
        avaliado = aplicacao.avaliado
        if avaliado.id not in dados_por_avaliado: 
            # Somente exibe ranchos que tenham Lat e Lon (ou o nosso mock temporário)
            if not avaliado.latitude or not avaliado.longitude:
                continue

            dados_por_avaliado[avaliado.id] = {
                'id': avaliado.id,
                'nome': avaliado.nome,
                'cidade': avaliado.cidade or 'Não informada',
                'estado': avaliado.estado or '-',
                'lat': float(avaliado.latitude) if avaliado.latitude else None,
                'lng': float(avaliado.longitude) if avaliado.longitude else None,
                'pontuacoes': []
            }

        # Filtro de Nota global ou do Topico Selecionado
        if topico_id:
            resultado = getattr(aplicacao, '_cache_resultado', calcular_pontuacao_auditoria(aplicacao))
            if resultado and 'detalhes_blocos_id' in resultado:
                # Vamos supor que precisamos pegar  percentual por bloco iterando
                for bloco_nome, pct in resultado.get('percentual_por_bloco', {}).items():
                    # Para simplificar aqui e como a busca e pelo nome no core antigo, pegamos o topico local
                    pass
            # Implementação robusta baseada apenas em respostas para notas especificas
            total_pontos = 0
            total_maximo = 0
            for resp in getattr(aplicacao, '_respostas_carregadas', []):
                if resp.pergunta.topico_id == topico_id:
                    total_pontos += (resp.pontos or 0)
                    total_maximo += (resp.pergunta.peso or 0)
            
            nota_filtrada = round((total_pontos / total_maximo) * 10, 1) if total_maximo > 0 else None
            if nota_filtrada is not None:
                dados_por_avaliado[avaliado.id]['pontuacoes'].append(nota_filtrada)
        else:
            if aplicacao.nota_final is not None:
                dados_por_avaliado[avaliado.id]['pontuacoes'].append(aplicacao.nota_final / 10)

    retorno_mapa = []
    import statistics
    for av_id, av_data in dados_por_avaliado.items():
        if not av_data['pontuacoes']: continue
        
        media_nota = statistics.mean(av_data['pontuacoes'])
        
        status = 'success'
        if media_nota < 60:
            status = 'danger'
        elif media_nota < 80:
            status = 'warning'

        retorno_mapa.append({
            'id': av_data['id'],
            'nome': av_data['nome'],
            'lat': av_data['lat'],
            'lng': av_data['lng'],
            'nota_media': round(media_nota, 1),
            'status': status,
            'total_apps': len(av_data['pontuacoes'])
        })
        
    return retorno_mapa

def gerar_dados_mapa(aplicacoes, topico_id=None):
    """
    Gera dados estruturados para o Mapa Panorâmico (Choropleth/Colorido).
    Agrupa as aplicações por Estado (UF) para alertar visualmente regiões problemáticas.
    """
    if not aplicacoes: return {}

    dados_por_estado = {}
    
    for aplicacao in aplicacoes:
        estado = aplicacao.avaliado.estado
        if not estado or len(estado) != 2: continue # Ignora se não houver UF
        estado = estado.upper()
        
        if estado not in dados_por_estado:
            dados_por_estado[estado] = {'pontuacoes': [], 'ranchos': {}}
            
        r_id = aplicacao.avaliado.id
        if r_id not in dados_por_estado[estado]['ranchos']:
            dados_por_estado[estado]['ranchos'][r_id] = {
                'id': r_id,
                'nome': aplicacao.avaliado.nome,
                'lat': aplicacao.avaliado.latitude,
                'lng': aplicacao.avaliado.longitude,
                'pontuacoes': []
            }
        
        # Filtro Global ou Tópico
        if topico_id:
            total_pontos = 0
            total_maximo = 0
            for resp in getattr(aplicacao, '_respostas_carregadas', []):
                if resp.pergunta.topico_id == topico_id:
                    total_pontos += (resp.pontos or 0)
                    total_maximo += (resp.pergunta.peso or 0)
            
            if total_maximo > 0:
                nota_pct = (total_pontos / total_maximo) * 10
                dados_por_estado[estado]['pontuacoes'].append(nota_pct)
                dados_por_estado[estado]['ranchos'][r_id]['pontuacoes'].append(nota_pct)
        else:
            if aplicacao.nota_final is not None:
                dados_por_estado[estado]['pontuacoes'].append(aplicacao.nota_final / 10)
                dados_por_estado[estado]['ranchos'][r_id]['pontuacoes'].append(aplicacao.nota_final / 10)

    retorno_mapa = {}
    import statistics
    for uf, data in dados_por_estado.items():
        if not data['pontuacoes']: continue
        
        # Média Estadual (ainda util para Tooltip e base)
        media_nota = round(statistics.mean(data['pontuacoes']), 1)
        
        # Processar detalhes dos ranchos desse estado e contar Ruins (< 7.0)
        detalhes_ranchos = []
        ranchos_ruins_count = 0
        
        for r_id, r_info in data['ranchos'].items():
            if not r_info['pontuacoes']: continue
            r_media = statistics.mean(r_info['pontuacoes'])
            r_status = 'success' if r_media >= 7.0 else 'danger'
            
            if r_media < 7.0:
                ranchos_ruins_count += 1
                
            detalhes_ranchos.append({
                'id': r_id,
                'nome': r_info['nome'],
                'lat': r_info['lat'],
                'lng': r_info['lng'],
                'media': round(r_media, 1),
                'status': r_status,
                'qtd_auditorias': len(r_info['pontuacoes'])
            })
            
        total_ranchos = len(detalhes_ranchos)
        if total_ranchos == 0: continue
        
        # Razão de ranchos ruins [0.0 - 1.0] -> Para calcular cor do Gradient Heatmap no frontend
        ratio_ruins = ranchos_ruins_count / total_ranchos

        # Define status semântico retroativo caso frontend use classes baseadas em string
        status = 'success'
        if ratio_ruins > 0.5:
            status = 'danger'
        elif ratio_ruins > 0:
            status = 'warning'
            
        # Ordenar os ranchos do pior pro melhor
        detalhes_ranchos = sorted(detalhes_ranchos, key=lambda x: x['media'])

        # Chave ISO ('BR-RJ', 'BR-SP', etc)
        chave = f"BR-{uf}"
        retorno_mapa[chave] = {
            'nota': media_nota,
            'status': status,
            'ratio_ruins': ratio_ruins,
            'ranchos_ruins': ranchos_ruins_count,
            'qtd_ranchos': total_ranchos,
            'detalhes_ranchos': detalhes_ranchos
        }
        
    return retorno_mapa

def gerar_grafico_questionarios(aplicacoes, topico_id=None):
    if not aplicacoes: return {'labels': [], 'datasets': []}
    dados_por_questionario = {}
    for aplicacao in aplicacoes:
        quest_nome = aplicacao.questionario.nome
        if quest_nome not in dados_por_questionario: dados_por_questionario[quest_nome] = []
        
        nota = aplicacao.nota_final or 0
        if topico_id:
            total_pontos = sum([resp.pontos or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            total_maximo = sum([resp.pergunta.peso or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            nota = (total_pontos / total_maximo) * 10 if total_maximo > 0 else 0

        dados_por_questionario[quest_nome].append(nota)

    labels, valores = [], []
    for questionario, pontuacoes in dados_por_questionario.items():
        media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0
        labels.append(questionario)
        valores.append(round(media, 1))

    return {'labels': labels, 'datasets': [{'label': 'Pontuação Média', 'data': valores, 'backgroundColor': ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c']}]}

def gerar_grafico_distribuicao(aplicacoes, topico_id=None):
    if not aplicacoes: return {'labels': [], 'datasets': []}
    faixas = { '0-2': 0, '2.1-4': 0, '4.1-6': 0, '6.1-8': 0, '8.1-10': 0 }
    for aplicacao in aplicacoes:
        pontuacao = (aplicacao.nota_final / 10) if aplicacao.nota_final is not None else 0 
        
        if topico_id:
            total_pontos = sum([resp.pontos or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            total_maximo = sum([resp.pergunta.peso or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            pontuacao = (total_pontos / total_maximo) * 10 if total_maximo > 0 else 0

        if pontuacao <= 2.0: faixas['0-2'] += 1
        elif pontuacao <= 4.0: faixas['2.1-4'] += 1
        elif pontuacao <= 6.0: faixas['4.1-6'] += 1
        elif pontuacao <= 8.0: faixas['6.1-8'] += 1
        else: faixas['8.1-10'] += 1
    return {'labels': list(faixas.keys()), 'datasets': [{'label': 'Quantidade de Aplicações', 'data': list(faixas.values()), 'backgroundColor': ['#dc3545', '#fd7e14', '#ffc107', '#20c997', '#28a745']}]}

def gerar_ranking_avaliados(aplicacoes, topico_id=None):
    if not aplicacoes: return []
    dados_por_avaliado = {}
    for aplicacao in aplicacoes:
        avaliado_id = aplicacao.avaliado_id
        if avaliado_id not in dados_por_avaliado:
            dados_por_avaliado[avaliado_id] = {'nome': aplicacao.avaliado.nome, 'pontuacoes': [], 'total_aplicacoes': 0}
            
        nota = (aplicacao.nota_final / 10) if aplicacao.nota_final is not None else 0
        if topico_id:
            total_pontos = sum([resp.pontos or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            total_maximo = sum([resp.pergunta.peso or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            nota = (total_pontos / total_maximo) * 10 if total_maximo > 0 else 0

        dados_por_avaliado[avaliado_id]['pontuacoes'].append(nota)
        dados_por_avaliado[avaliado_id]['total_aplicacoes'] += 1

    dados = []
    for avaliado_id, info in dados_por_avaliado.items():
        media = sum(info['pontuacoes']) / len(info['pontuacoes']) if info['pontuacoes'] else 0
        item = {
            'loja': info['nome'], 
            'media': round(media, 1), 
            'total_auditorias': info['total_aplicacoes'], 
            'status': 'success' if media >= 7.0 else 'danger'
        }
        dados.append(item)
    
    return sorted(dados, key=lambda x: x['media'], reverse=True)

def gerar_top_nao_conformidades(aplicacoes, topico_id=None):
    if not aplicacoes: return []
    nao_conformidades = {}
    
    for aplicacao in aplicacoes:
        # Usa a lista pré-carregada na memória ao invés de bater no banco de dados (evita Lazy Load)
        lista_respostas = getattr(aplicacao, '_respostas_carregadas', [])
        
        for resposta in lista_respostas:
            # Pula de acordo com o topico escolhido no dropdown
            if topico_id and resposta.pergunta.topico_id != topico_id:
                continue

            # Segurança extra para garantir que a resposta existe e é uma string antes do .lower()
            if resposta.resposta and 'não' in str(resposta.resposta).lower():
                pergunta_texto = resposta.pergunta.texto
                if pergunta_texto not in nao_conformidades: 
                    nao_conformidades[pergunta_texto] = 0
                nao_conformidades[pergunta_texto] += 1
                
    top_ncs = sorted(nao_conformidades.items(), key=lambda x: x[1], reverse=True)[:10]
    return [{'pergunta': pergunta, 'frequencia': freq} for pergunta, freq in top_ncs]

# ===================== NOVAS FUNÇÕES DOS GRÁFICOS (0 A 10 E BARRAS) =====================

def gerar_grafico_topicos(aplicacoes, topico_id_filtro=None):
    """Gera notas de 0 a 10 por tópico, cada um sendo um Dataset para gerar a legenda de cor"""
    if not aplicacoes:
        return {'labels': [''], 'datasets': []}

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

    topicos_banco = Topico.query.order_by(Topico.id).all()
    if topico_id_filtro:
        topicos_banco = [t for t in topicos_banco if t.id == topico_id_filtro]

    ordem_oficial_nomes = [t.nome for t in topicos_banco]

    topicos_ordenados = []
    for nome in ordem_oficial_nomes:
        if nome in dados_topicos:
            topicos_ordenados.append(nome)

    for bloco in dados_topicos.keys():
        if bloco not in topicos_ordenados:
            topicos_ordenados.append(bloco)

    cores_paleta = ['#4e73df', '#1cc88a', '#f6c23e', '#e74a3b', '#36b9cc', '#858796', '#fd7e14', '#20c9a6', '#6610f2', '#e83e8c']
    
    datasets = []
    for i, topico in enumerate(topicos_ordenados):
        totais = dados_topicos[topico]
        if totais['maximo'] > 0:
            nota = (totais['obtido'] / totais['maximo']) * 10
            nota_arredondada = round(nota, 1)
            
            datasets.append({
                'label': topico, 
                'data': [nota_arredondada], 
                'backgroundColor': cores_paleta[i % len(cores_paleta)],
                'borderColor': cores_paleta[i % len(cores_paleta)],
                'borderWidth': 1
            })

    return {'labels': [''], 'datasets': datasets}

def gerar_grafico_evolucao_mensal(aplicacoes, topico_id=None):
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
        if topico_id:
            total_pontos = sum([resp.pontos or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            total_maximo = sum([resp.pergunta.peso or 0 for resp in getattr(aplicacao, '_respostas_carregadas', []) if resp.pergunta.topico_id == topico_id])
            nota = ((total_pontos / total_maximo) * 10) if total_maximo > 0 else 0

        dados_por_mes[label_mes]['notas'].append(nota)

    meses_ordenados = sorted(dados_por_mes.keys(), key=lambda k: dados_por_mes[k]['ordem'])
    labels, valores = [], []

    for label in meses_ordenados:
        notas = dados_por_mes[label]['notas']
        media = sum(notas) / len(notas) if notas else 0
        labels.append(label)
        valores.append(round(media, 1))

    return {'labels': labels, 'datasets': [{'label': 'Nota Média Mensal (0 a 10)', 'data': valores, 'backgroundColor': '#007bff'}]}

def gerar_grafico_evolucao_topicos(aplicacoes, topico_id_filtro=None):
    if not aplicacoes: return []

    from ..utils.pontuacao import calcular_pontuacao_auditoria
    from ..models import Topico

    meses = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    
    dados_por_topico = {}
    meses_encontrados = set()

    for app in aplicacoes:
        chave_mes = app.data_inicio.strftime('%Y-%m')
        mes_numero = int(app.data_inicio.strftime('%m'))
        ano = app.data_inicio.strftime('%Y')
        label_mes = f"{meses[mes_numero]}/{ano}"
        
        meses_encontrados.add((chave_mes, label_mes))

        resultado = getattr(app, '_cache_resultado', calcular_pontuacao_auditoria(app)) 
        if not resultado or not resultado.get('detalhes_blocos'): continue
            
        for bloco, detalhes in resultado['detalhes_blocos'].items():
            if detalhes['pontuacao_maxima'] > 0:
                nota = (detalhes['pontuacao_obtida'] / detalhes['pontuacao_maxima']) * 10
                if bloco not in dados_por_topico:
                    dados_por_topico[bloco] = {}
                if label_mes not in dados_por_topico[bloco]:
                    dados_por_topico[bloco][label_mes] = []
                dados_por_topico[bloco][label_mes].append(nota)

    topicos_banco = Topico.query.order_by(Topico.id).all()
    if topico_id_filtro:
        topicos_banco = [t for t in topicos_banco if t.id == topico_id_filtro]

    ordem_oficial = [t.nome for t in topicos_banco]
    topicos_ordenados = [t for t in ordem_oficial if t in dados_por_topico]
    for t in dados_por_topico.keys():
        if t not in topicos_ordenados:
            topicos_ordenados.append(t)

    meses_ordenados_tuples = sorted(list(meses_encontrados), key=lambda x: x[0])
    labels_meses = [m[1] for m in meses_ordenados_tuples]

    cores_paleta = ['#4e73df', '#1cc88a', '#f6c23e', '#e74a3b', '#36b9cc', '#858796', '#fd7e14', '#20c9a6', '#6610f2', '#e83e8c']
    lista_graficos_separados = []
    
    for i, topico in enumerate(topicos_ordenados):
        valores_topico = []
        for label_mes in labels_meses:
            notas = dados_por_topico[topico].get(label_mes, [])
            if notas:
                media = sum(notas) / len(notas)
                valores_topico.append(round(media, 1))
            else:
                valores_topico.append(None) 
        
        lista_graficos_separados.append({
            'titulo': topico, 
            'id': f"chartEvolucaoTopico_{i}", 
            'cor': cores_paleta[i % len(cores_paleta)], 
            'dados': {
                'labels': labels_meses, 
                'datasets': [{
                    'label': 'Nota',
                    'data': valores_topico, 
                    'backgroundColor': cores_paleta[i % len(cores_paleta)],
                    'borderColor': cores_paleta[i % len(cores_paleta)],
                    'borderWidth': 1
                }]
            }
        })

    return lista_graficos_separados

@panorama_bp.route('/api/indicadores/comparativo')
@login_required
def api_comparativo_indicadores():
    try:
        categorias = CategoriaIndicador.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(CategoriaIndicador.ordem).all()
        query_ranchos = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
        query_ranchos = aplicar_filtro_hierarquia(query_ranchos)
        ranchos = query_ranchos.all()
        dados_painel = []

        for cat in categorias:
            grafico = {'titulo': cat.nome, 'id_grafico': f'grafico_{cat.id}', 'cor': cat.cor, 'labels': [], 'valores': []}
            for rancho in ranchos:
                # 🚀 NOVO: Ignora a primeira aplicação
                ids_excluidos = _obter_ids_primeiras_aplicacoes()
                apps = AplicacaoQuestionario.query.filter(
                    AplicacaoQuestionario.avaliado_id == rancho.id, 
                    AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA,
                    ~AplicacaoQuestionario.id.in_(ids_excluidos)
                ).all()
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
    query_avaliados = Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True)
    query_avaliados = aplicar_filtro_hierarquia(query_avaliados)
    avaliados = query_avaliados.all()
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
        query = aplicar_filtro_hierarquia(query)
        
        # 🚀 NOVO: Ignora a primeira aplicação
        ids_excluidos = _obter_ids_primeiras_aplicacoes()
        query = query.filter(~AplicacaoQuestionario.id.in_(ids_excluidos))

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
        query = aplicar_filtro_hierarquia(query)
        
        # 🚀 NOVO: Ignora a primeira aplicação
        ids_excluidos = _obter_ids_primeiras_aplicacoes()
        query = query.filter(~AplicacaoQuestionario.id.in_(ids_excluidos))

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

# ==================== GRÁFICO 4: AÇÕES CORRETIVAS POR COR ====================

def gerar_grafico_acoes_corretivas(aplicacao_ids):
    """
    Agrega todas as 'AcaoCorretiva' nas aplicações filtradas
    e as agrupa por Rancho (Nome) e por Gravidade (Baixa, Média, Alta).
    Output: Stacked Bar Chart das Ações Corretivas.
    """
    if not aplicacao_ids:
        return {'labels': [], 'baixa': [], 'media': [], 'alta': []}
        
    from ..models import AcaoCorretiva
    
    # Busca todas as Ações Corretivas filhas destas aplicações puxando também o Nome do Rancho
    acoes = db.session.query(
        Avaliado.nome.label('rancho_nome'),
        AcaoCorretiva.criticidade
    ).join(
        AplicacaoQuestionario, AplicacaoQuestionario.id == AcaoCorretiva.aplicacao_id
    ).join(
        Avaliado, Avaliado.id == AplicacaoQuestionario.avaliado_id
    ).filter(
        AcaoCorretiva.aplicacao_id.in_(aplicacao_ids)
    ).all()
    
    # Agrupador: { 'Rancho A': {'Baixa': 1, 'Média': 3, 'Alta': 0} ... }
    mapa_ranchos = {}
    for acao in acoes:
        r_nome = acao.rancho_nome
        criticidade = str(acao.criticidade).strip().capitalize() if acao.criticidade else 'Média'
        
        if r_nome not in mapa_ranchos:
            mapa_ranchos[r_nome] = {'Baixa': 0, 'Média': 0, 'Alta': 0}
            
        if criticidade not in ['Baixa', 'Média', 'Alta']:
            criticidade = 'Média'
            
        mapa_ranchos[r_nome][criticidade] += 1
        
    # Desmembra pros eixos do Chart.js
    labels = list(mapa_ranchos.keys())
    data_baixa = [mapa_ranchos[r]['Baixa'] for r in labels]
    data_media = [mapa_ranchos[r]['Média'] for r in labels]
    data_alta = [mapa_ranchos[r]['Alta'] for r in labels]
    
    return {
        'labels': labels,
        'baixa': data_baixa,
        'media': data_media,
        'alta': data_alta
    }

# ==========================================
# ROTAS GLOBAIS DE DOCUMENTOS MENSAIS
# ==========================================

@panorama_bp.route('/treinamentos_gerais', methods=['GET', 'POST'])
@login_required
def treinamentos_gerais():
    if request.method == 'POST':
        mes_ano = request.form.get('mes_ano')
        tipo_doc = request.form.get('tipo_documento') # 'treinamento_geral' ou 'prova_geral'
        arq = request.files.get('arquivo')
        
        if arq:
            filename = secure_filename(arq.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'mensais')
            os.makedirs(upload_folder, exist_ok=True)
            caminho_salvo = os.path.join(upload_folder, filename)
            arq.save(caminho_salvo)
            
            novo_doc = DocumentoMensal(
                mes_ano=mes_ano,
                categoria='treinamento',
                tipo_documento=tipo_doc,
                nome_arquivo=filename,
                caminho_arquivo=f"uploads/mensais/{filename}",
                criado_por_id=current_user.id
            )
            db.session.add(novo_doc)
            db.session.commit()
            flash('Documento de Treinamento anexado com sucesso!', 'success')
            return redirect(url_for('panorama.treinamentos_gerais'))
            
    # Listar documentos gerais de treinamento
    docs_gerais = DocumentoMensal.query.filter_by(categoria='treinamento').order_by(DocumentoMensal.data_upload.desc()).all()
    
    # Listar os Planos Locais de todos os ranchos via Aplicação
    planos_locais = AplicacaoQuestionario.query.filter(
        AplicacaoQuestionario.plano_capacitacao_arquivo.isnot(None),
        AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA
    ).order_by(AplicacaoQuestionario.data_inicio.desc()).all()

    return render_template('panorama/treinamentos_dashboard.html', docs_gerais=docs_gerais, planos_locais=planos_locais)


@panorama_bp.route('/planilhas_gerais', methods=['GET', 'POST'])
@login_required
def planilhas_gerais():
    if request.method == 'POST':
        mes_ano = request.form.get('mes_ano')
        tipo_doc = request.form.get('tipo_documento') # 'rankingesta' ou 'ranchos_obra'
        arq = request.files.get('arquivo')
        
        if arq:
            filename = secure_filename(arq.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'mensais')
            os.makedirs(upload_folder, exist_ok=True)
            caminho_salvo = os.path.join(upload_folder, filename)
            arq.save(caminho_salvo)
            
            novo_doc = DocumentoMensal(
                mes_ano=mes_ano,
                categoria='planilha',
                tipo_documento=tipo_doc,
                nome_arquivo=filename,
                caminho_arquivo=f"uploads/mensais/{filename}",
                criado_por_id=current_user.id
            )
            db.session.add(novo_doc)
            db.session.commit()
            flash('Planilha anexada com sucesso!', 'success')
            return redirect(url_for('panorama.planilhas_gerais'))
            
    docs_planilhas = DocumentoMensal.query.filter_by(categoria='planilha').order_by(DocumentoMensal.data_upload.desc()).all()
    return render_template('panorama/planilhas_dashboard.html', docs_planilhas=docs_planilhas)

@panorama_bp.route('/excluir_documento_mensal/<int:id>', methods=['POST'])
@login_required
def excluir_documento_mensal(id):
    if current_user.tipo.name not in ['SUPER_ADMIN', 'ADMIN']:
        flash('Acesso negado', 'danger')
        return redirect(request.referrer or url_for('panorama.index'))
        
    doc = DocumentoMensal.query.get_or_404(id)
    cat = doc.categoria
    
    import os
    file_path = os.path.join(current_app.root_path, 'static', doc.caminho_arquivo)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(doc)
    db.session.commit()
    flash('Documento removido com sucesso.', 'success')
    
    if cat == 'treinamento':
        return redirect(url_for('panorama.treinamentos_gerais'))
    else:
        return redirect(url_for('panorama.planilhas_gerais'))


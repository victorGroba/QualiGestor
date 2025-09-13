# app/cli/routes.py - ROTAS CLIQ COMPLETAS IGUAL PARIPASSU
import json
import os
import base64
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify, make_response, Response
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from weasyprint import HTML
from sqlalchemy import func, extract, and_, or_, desc

# Importações dos modelos
from ..models import (
    db, Usuario, Cliente, Grupo, Avaliado,
    Questionario, Topico, Pergunta, OpcaoPergunta,
    AplicacaoQuestionario, RespostaPergunta, UsuarioAutorizado,
    TipoResposta, StatusQuestionario, StatusAplicacao, 
    TipoPreenchimento, ModoExibicaoNota, CorRelatorio, Integracao,
    TipoUsuario, Notificacao, LogAuditoria, ConfiguracaoCliente
)

cli_bp = Blueprint('cli', __name__, template_folder='templates')

# ===================== DECORATORS E FUNÇÕES AUXILIARES =====================

def admin_required(f):
    """Decorator para exigir permissões de administrador"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Acesso negado. Faça login primeiro.', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.tipo not in [TipoUsuario.ADMIN, TipoUsuario.SUPER_ADMIN]:
            flash('Acesso restrito a administradores.', 'error')
            return redirect(url_for('cli.index'))
        return f(*args, **kwargs)
    return decorated_function

def get_avaliados_usuario():
    """Retorna avaliados disponíveis para o usuário atual"""
    if current_user.tipo == TipoUsuario.ADMIN:
        return Avaliado.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    else:
        # Usuários normais só veem avaliados de seus grupos
        return Avaliado.query.filter_by(
            cliente_id=current_user.cliente_id,
            grupo_id=current_user.grupo_id,
            ativo=True
        ).all()

def log_acao(acao, detalhes=None, entidade_tipo=None, entidade_id=None):
    """Função auxiliar para registrar ações no log"""
    try:
        log = LogAuditoria(
            usuario_id=current_user.id,
            cliente_id=current_user.cliente_id,
            acao=acao,
            detalhes=detalhes,
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            ip=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(log)
        db.session.commit()
    except:
        pass

def criar_notificacao(usuario_id, titulo, mensagem, tipo='info', link=None):
    """Função auxiliar para criar notificações"""
    notificacao = Notificacao(
        usuario_id=usuario_id,
        titulo=titulo,
        mensagem=mensagem,
        tipo=tipo,
        link=link
    )
    db.session.add(notificacao)
    db.session.commit()

# ===================== PÁGINA INICIAL =====================

@cli_bp.route('/')
@cli_bp.route('/home')
@login_required
def index():
    """Dashboard principal do CLIQ"""
    stats = {
        'total_aplicacoes': 0,
        'aplicacoes_mes': 0,
        'questionarios_ativos': 0,
        'avaliados_ativos': 0,
        'media_nota_mes': 0,
        'aplicacoes_pendentes': 0
    }
    
    ultimas_aplicacoes = []
    questionarios_populares = []

    if hasattr(current_user, 'cliente_id') and current_user.cliente_id:
        # Aplicações do cliente
        stats['total_aplicacoes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id
        ).count()

        # Aplicações deste mês
        stats['aplicacoes_mes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            extract('month', AplicacaoQuestionario.data_inicio) == datetime.now().month,
            extract('year', AplicacaoQuestionario.data_inicio) == datetime.now().year
        ).count()

        # Questionários ativos
        stats['questionarios_ativos'] = Questionario.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True,
            publicado=True
        ).count()

        # Avaliados ativos
        stats['avaliados_ativos'] = Avaliado.query.filter_by(
            cliente_id=current_user.cliente_id,
            ativo=True
        ).count()

        # Média de notas do mês
        media_result = db.session.query(func.avg(AplicacaoQuestionario.nota_final)).join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            AplicacaoQuestionario.nota_final.isnot(None),
            extract('month', AplicacaoQuestionario.data_inicio) == datetime.now().month
        ).scalar()
        stats['media_nota_mes'] = round(float(media_result or 0), 1)

        # Aplicações pendentes
        stats['aplicacoes_pendentes'] = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            AplicacaoQuestionario.status == StatusAplicacao.EM_ANDAMENTO
        ).count()

        # Últimas aplicações
        ultimas_aplicacoes = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id
        ).order_by(AplicacaoQuestionario.data_inicio.desc()).limit(5).all()

        # Questionários mais usados
        questionarios_populares = db.session.query(
            Questionario.nome,
            func.count(AplicacaoQuestionario.id).label('total_aplicacoes')
        ).join(AplicacaoQuestionario).join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id
        ).group_by(Questionario.id, Questionario.nome).order_by(
            func.count(AplicacaoQuestionario.id).desc()
        ).limit(5).all()

    return render_template('cli/index.html', 
                         stats=stats, 
                         ultimas_aplicacoes=ultimas_aplicacoes,
                         questionarios_populares=questionarios_populares)

# ===================== QUESTIONÁRIOS =====================

@cli_bp.route('/questionarios')
@cli_bp.route('/listar-questionarios')
@login_required
def listar_questionarios():
    """Lista todos os questionários do cliente"""
    questionarios = Questionario.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativo=True
    ).order_by(Questionario.nome).all()

    # Estatísticas para cada questionário
    for questionario in questionarios:
        questionario.total_aplicacoes = AplicacaoQuestionario.query.filter_by(
            questionario_id=questionario.id
        ).count()
        
        questionario.media_nota = db.session.query(
            func.avg(AplicacaoQuestionario.nota_final)
        ).filter_by(questionario_id=questionario.id).scalar() or 0

    return render_template('cli/listar_questionarios.html', questionarios=questionarios)

@cli_bp.route('/questionario/novo', methods=['GET', 'POST'])
@cli_bp.route('/novo-questionario', methods=['GET', 'POST'])
@login_required
def novo_questionario():
    """Cria um novo questionário - Tela 1: Configurações gerais"""
    if request.method == 'POST':
        return processar_novo_questionario()

    # GET - Mostrar formulário
    usuarios = Usuario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    integracoes = Integracao.query.filter_by(ativa=True).all()

    return render_template('cli/novo_questionario.html',
                           usuarios=usuarios,
                           grupos=grupos,
                           integracoes=integracoes)

def processar_novo_questionario():
    """Processa a criação de novo questionário"""
    try:
        # Dados básicos
        nome = request.form.get('nome', '').strip()
        versao = request.form.get('versao', '1.0').strip()
        descricao = request.form.get('descricao', '').strip()
        modo = request.form.get('modo', 'Avaliado')
        
        if not nome:
            flash("Nome do questionário é obrigatório.", "danger")
            return redirect(url_for('cli.novo_questionario'))

        # Verificar se já existe questionário com mesmo nome
        questionario_existente = Questionario.query.filter_by(
            nome=nome,
            cliente_id=current_user.cliente_id,
            ativo=True
        ).first()
        
        if questionario_existente:
            flash(f"Já existe um questionário com o nome '{nome}'.", "warning")
            return redirect(url_for('cli.novo_questionario'))

        # Criar questionário
        novo_questionario = Questionario(
            nome=nome,
            versao=versao,
            descricao=descricao,
            modo=modo,
            cliente_id=current_user.cliente_id,
            criado_por_id=current_user.id,
            
            # Configurações das notas
            calcular_nota=request.form.get('calcular_nota') == 'on',
            ocultar_nota_aplicacao=request.form.get('ocultar_nota') == 'on',
            base_calculo=int(request.form.get('base_calculo', 100)),
            casas_decimais=int(request.form.get('casas_decimais', 2)),
            modo_configuracao=request.form.get('modo_configuracao', 'percentual'),
            modo_exibicao_nota=ModoExibicaoNota(request.form.get('modo_exibicao_nota', 'PERCENTUAL')),
            
            # Configurações de aplicação
            anexar_documentos=request.form.get('anexar_documentos') == 'on',
            capturar_geolocalizacao=request.form.get('geolocalizacao') == 'on',
            restringir_avaliados=request.form.get('restricao_avaliados') == 'on',
            habilitar_reincidencia=request.form.get('reincidencia') == 'on',
            
            # Configurações visuais
            cor_relatorio=CorRelatorio(request.form.get('cor_relatorio', 'AZUL')),
            incluir_assinatura=request.form.get('incluir_assinatura') == 'on',
            incluir_foto_capa=request.form.get('incluir_foto_capa') == 'on',
            
            # Status
            ativo=True,
            publicado=False,
            status=StatusQuestionario.RASCUNHO
        )

        db.session.add(novo_questionario)
        db.session.flush()  # Para obter o ID

        # Configurar usuários autorizados se especificado
        usuarios_autorizados = request.form.getlist('usuarios_autorizados')
        if usuarios_autorizados:
            for usuario_id in usuarios_autorizados:
                if usuario_id:
                    usuario_auth = UsuarioAutorizado(
                        questionario_id=novo_questionario.id,
                        usuario_id=int(usuario_id)
                    )
                    db.session.add(usuario_auth)

        db.session.commit()
        
        # Log da ação
        log_acao(f"Criou questionário: {nome}", None, "Questionario", novo_questionario.id)
        
        flash(f"Questionário '{nome}' criado com sucesso!", "success")
        return redirect(url_for('cli.gerenciar_topicos', id=novo_questionario.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao criar questionário: {str(e)}", "danger")
        return redirect(url_for('cli.novo_questionario'))

@cli_bp.route('/questionario/<int:id>')
@cli_bp.route('/questionario/<int:id>/visualizar')
@login_required
def visualizar_questionario(id):
    """Visualiza detalhes do questionário"""
    questionario = Questionario.query.get_or_404(id)
    
    if questionario.cliente_id != current_user.cliente_id:
        flash("Questionário não encontrado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    # Estatísticas do questionário
    stats = {
        'total_aplicacoes': AplicacaoQuestionario.query.filter_by(questionario_id=id).count(),
        'total_topicos': Topico.query.filter_by(questionario_id=id, ativo=True).count(),
        'total_perguntas': db.session.query(func.count(Pergunta.id)).join(Topico).filter(
            Topico.questionario_id == id,
            Pergunta.ativo == True
        ).scalar(),
        'media_nota': db.session.query(func.avg(AplicacaoQuestionario.nota_final)).filter_by(
            questionario_id=id
        ).scalar() or 0
    }
    
    # Últimas aplicações
    ultimas_aplicacoes = AplicacaoQuestionario.query.filter_by(
        questionario_id=id
    ).order_by(AplicacaoQuestionario.data_inicio.desc()).limit(10).all()
    
    return render_template('cli/visualizar_questionario.html',
                         questionario=questionario,
                         stats=stats,
                         ultimas_aplicacoes=ultimas_aplicacoes)

@cli_bp.route('/questionario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_questionario(id):
    """Edita questionário existente"""
    questionario = Questionario.query.get_or_404(id)
    
    if questionario.cliente_id != current_user.cliente_id:
        flash("Questionário não encontrado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    if request.method == 'POST':
        try:
            # Atualizar dados básicos
            questionario.nome = request.form.get('nome', '').strip()
            questionario.versao = request.form.get('versao', '1.0').strip()
            questionario.descricao = request.form.get('descricao', '').strip()
            questionario.modo = request.form.get('modo', 'Avaliado')
            
            # Configurações das notas
            questionario.calcular_nota = request.form.get('calcular_nota') == 'on'
            questionario.ocultar_nota_aplicacao = request.form.get('ocultar_nota') == 'on'
            questionario.base_calculo = int(request.form.get('base_calculo', 100))
            questionario.casas_decimais = int(request.form.get('casas_decimais', 2))
            
            # Configurações visuais
            questionario.cor_relatorio = CorRelatorio(request.form.get('cor_relatorio', 'AZUL'))
            questionario.incluir_assinatura = request.form.get('incluir_assinatura') == 'on'
            questionario.incluir_foto_capa = request.form.get('incluir_foto_capa') == 'on'
            
            db.session.commit()
            log_acao(f"Editou questionário: {questionario.nome}", None, "Questionario", id)
            
            flash("Questionário atualizado com sucesso!", "success")
            return redirect(url_for('cli.visualizar_questionario', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar questionário: {str(e)}", "danger")
    
    # GET - Carregar dados
    usuarios = Usuario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    
    return render_template('cli/editar_questionario.html',
                         questionario=questionario,
                         usuarios=usuarios,
                         grupos=grupos)

@cli_bp.route('/questionario/<int:id>/duplicar', methods=['POST'])
@login_required
def duplicar_questionario(id):
    """Duplica um questionário existente"""
    try:
        questionario_original = Questionario.query.get_or_404(id)
        
        if questionario_original.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        # Criar cópia do questionário
        novo_nome = f"{questionario_original.nome} - Cópia"
        contador = 1
        while Questionario.query.filter_by(nome=novo_nome, cliente_id=current_user.cliente_id).first():
            contador += 1
            novo_nome = f"{questionario_original.nome} - Cópia ({contador})"
        
        questionario_copia = Questionario(
            nome=novo_nome,
            versao="1.0",
            descricao=questionario_original.descricao,
            modo=questionario_original.modo,
            cliente_id=current_user.cliente_id,
            criado_por_id=current_user.id,
            calcular_nota=questionario_original.calcular_nota,
            ocultar_nota_aplicacao=questionario_original.ocultar_nota_aplicacao,
            base_calculo=questionario_original.base_calculo,
            casas_decimais=questionario_original.casas_decimais,
            cor_relatorio=questionario_original.cor_relatorio,
            incluir_assinatura=questionario_original.incluir_assinatura,
            incluir_foto_capa=questionario_original.incluir_foto_capa,
            ativo=True,
            publicado=False,
            status=StatusQuestionario.RASCUNHO
        )
        
        db.session.add(questionario_copia)
        db.session.flush()
        
        # Duplicar tópicos e perguntas
        for topico in questionario_original.topicos:
            if topico.ativo:
                topico_copia = Topico(
                    nome=topico.nome,
                    descricao=topico.descricao,
                    ordem=topico.ordem,
                    questionario_id=questionario_copia.id,
                    ativo=True
                )
                db.session.add(topico_copia)
                db.session.flush()
                
                # Duplicar perguntas
                for pergunta in topico.perguntas:
                    if pergunta.ativo:
                        pergunta_copia = Pergunta(
                            texto=pergunta.texto,
                            tipo=pergunta.tipo,
                            obrigatoria=pergunta.obrigatoria,
                            permite_observacao=pergunta.permite_observacao,
                            peso=pergunta.peso,
                            ordem=pergunta.ordem,
                            topico_id=topico_copia.id,
                            ativo=True
                        )
                        db.session.add(pergunta_copia)
                        db.session.flush()
                        
                        # Duplicar opções se existirem
                        for opcao in pergunta.opcoes:
                            opcao_copia = OpcaoPergunta(
                                texto=opcao.texto,
                                valor=opcao.valor,
                                ordem=opcao.ordem,
                                pergunta_id=pergunta_copia.id
                            )
                            db.session.add(opcao_copia)
        
        db.session.commit()
        log_acao(f"Duplicou questionário: {questionario_original.nome}", None, "Questionario", questionario_copia.id)
        
        flash(f"Questionário duplicado como '{novo_nome}'!", "success")
        return redirect(url_for('cli.visualizar_questionario', id=questionario_copia.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao duplicar questionário: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/questionario/<int:id>/publicar', methods=['POST'])
@login_required
def publicar_questionario(id):
    """Publica questionário para uso"""
    try:
        questionario = Questionario.query.get_or_404(id)
        
        if questionario.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        # Validar se tem pelo menos 1 tópico e 1 pergunta
        total_perguntas = db.session.query(func.count(Pergunta.id)).join(Topico).filter(
            Topico.questionario_id == id,
            Topico.ativo == True,
            Pergunta.ativo == True
        ).scalar()
        
        if total_perguntas == 0:
            flash("Não é possível publicar um questionário sem perguntas.", "warning")
            return redirect(url_for('cli.visualizar_questionario', id=id))
        
        questionario.publicado = True
        questionario.status = StatusQuestionario.PUBLICADO
        questionario.data_publicacao = datetime.now()
        
        db.session.commit()
        log_acao(f"Publicou questionário: {questionario.nome}", None, "Questionario", id)
        
        flash("Questionário publicado com sucesso! Agora pode ser usado em aplicações.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao publicar questionário: {str(e)}", "danger")
    
    return redirect(url_for('cli.visualizar_questionario', id=id))

@cli_bp.route('/questionario/<int:id>/desativar', methods=['POST'])
@login_required
def desativar_questionario(id):
    """Desativa um questionário"""
    try:
        questionario = Questionario.query.get_or_404(id)
        
        if questionario.cliente_id != current_user.cliente_id:
            flash("Questionário não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        questionario.ativo = False
        questionario.publicado = False
        questionario.status = StatusQuestionario.INATIVO
        
        db.session.commit()
        log_acao(f"Desativou questionário: {questionario.nome}", None, "Questionario", id)
        
        flash("Questionário desativado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao desativar questionário: {str(e)}", "danger")
    
    return redirect(url_for('cli.listar_questionarios'))

# ===================== TÓPICOS =====================

@cli_bp.route('/questionario/<int:id>/topicos')
@login_required
def gerenciar_topicos(id):
    """Tela 2: Gerenciar tópicos do questionário"""
    questionario = Questionario.query.get_or_404(id)
    
    if questionario.cliente_id != current_user.cliente_id:
        flash("Questionário não encontrado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    topicos = Topico.query.filter_by(
        questionario_id=id,
        ativo=True
    ).order_by(Topico.ordem).all()
    
    # Contar perguntas por tópico
    for topico in topicos:
        topico.total_perguntas = Pergunta.query.filter_by(
            topico_id=topico.id,
            ativo=True
        ).count()
    
    return render_template('cli/gerenciar_topicos.html',
                         questionario=questionario,
                         topicos=topicos)

@cli_bp.route('/questionario/<int:id>/topico/novo', methods=['GET', 'POST'])
@login_required
def novo_topico(id):
    """Criar novo tópico"""
    questionario = Questionario.query.get_or_404(id)
    
    if questionario.cliente_id != current_user.cliente_id:
        flash("Questionário não encontrado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            
            if not nome:
                flash("Nome do tópico é obrigatório.", "danger")
                return render_template('cli/novo_topico.html', questionario=questionario)
            
            # Obter próxima ordem
            ultima_ordem = db.session.query(func.max(Topico.ordem)).filter_by(
                questionario_id=id
            ).scalar() or 0
            
            novo_topico = Topico(
                nome=nome,
                descricao=descricao,
                ordem=ultima_ordem + 1,
                questionario_id=id,
                ativo=True
            )
            
            db.session.add(novo_topico)
            db.session.commit()
            
            log_acao(f"Criou tópico: {nome}", None, "Topico", novo_topico.id)
            flash("Tópico criado com sucesso!", "success")
            
            return redirect(url_for('cli.gerenciar_topicos', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar tópico: {str(e)}", "danger")
    
    return render_template('cli/novo_topico.html', questionario=questionario)

@cli_bp.route('/topico/<int:topico_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_topico(topico_id):
    """Editar tópico existente"""
    topico = Topico.query.get_or_404(topico_id)
    
    if topico.questionario.cliente_id != current_user.cliente_id:
        flash("Tópico não encontrado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    if request.method == 'POST':
        try:
            topico.nome = request.form.get('nome', '').strip()
            topico.descricao = request.form.get('descricao', '').strip()
            
            if not topico.nome:
                flash("Nome do tópico é obrigatório.", "danger")
                return render_template('cli/editar_topico.html', topico=topico)
            
            db.session.commit()
            log_acao(f"Editou tópico: {topico.nome}", None, "Topico", topico_id)
            
            flash("Tópico atualizado com sucesso!", "success")
            return redirect(url_for('cli.gerenciar_topicos', id=topico.questionario_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar tópico: {str(e)}", "danger")
    
    return render_template('cli/editar_topico.html', topico=topico)

@cli_bp.route('/topico/<int:topico_id>/remover', methods=['POST'])
@login_required
def remover_topico(topico_id):
    """Remove um tópico"""
    try:
        topico = Topico.query.get_or_404(topico_id)
        
        if topico.questionario.cliente_id != current_user.cliente_id:
            flash("Tópico não encontrado.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        questionario_id = topico.questionario_id
        
        # Verificar se tem perguntas
        total_perguntas = Pergunta.query.filter_by(topico_id=topico_id, ativo=True).count()
        if total_perguntas > 0:
            flash("Não é possível remover tópico que contém perguntas.", "warning")
        else:
            topico.ativo = False
            db.session.commit()
            log_acao(f"Removeu tópico: {topico.nome}", None, "Topico", topico_id)
            flash("Tópico removido com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover tópico: {str(e)}", "danger")
    
    return redirect(url_for('cli.gerenciar_topicos', id=questionario_id))

# ===================== PERGUNTAS =====================

@cli_bp.route('/topico/<int:topico_id>/perguntas')
@login_required
def gerenciar_perguntas(topico_id):
    """Tela 3: Gerenciar perguntas do tópico"""
    topico = Topico.query.get_or_404(topico_id)
    
    if topico.questionario.cliente_id != current_user.cliente_id:
        flash("Tópico não encontrado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    perguntas = Pergunta.query.filter_by(
        topico_id=topico_id,
        ativo=True
    ).order_by(Pergunta.ordem).all()
    
    return render_template('cli/gerenciar_perguntas.html',
                         topico=topico,
                         perguntas=perguntas)

@cli_bp.route('/topico/<int:topico_id>/pergunta/nova', methods=['GET', 'POST'])
@login_required
def nova_pergunta(topico_id):
    """Criar nova pergunta"""
    topico = Topico.query.get_or_404(topico_id)
    
    if topico.questionario.cliente_id != current_user.cliente_id:
        flash("Tópico não encontrado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    if request.method == 'POST':
        try:
            texto = request.form.get('texto', '').strip()
            tipo = request.form.get('tipo')
            obrigatoria = request.form.get('obrigatoria') == 'on'
            permite_observacao = request.form.get('permite_observacao') == 'on'
            peso = int(request.form.get('peso', 1))
            
            if not texto:
                flash("Texto da pergunta é obrigatório.", "danger")
                return render_template('cli/nova_pergunta.html', topico=topico)
            
            # Obter próxima ordem
            ultima_ordem = db.session.query(func.max(Pergunta.ordem)).filter_by(
                topico_id=topico_id
            ).scalar() or 0
            
            nova_pergunta = Pergunta(
                texto=texto,
                tipo=TipoResposta(tipo),
                obrigatoria=obrigatoria,
                permite_observacao=permite_observacao,
                peso=peso,
                ordem=ultima_ordem + 1,
                topico_id=topico_id,
                ativo=True
            )
            
            db.session.add(nova_pergunta)
            db.session.flush()
            
            # Adicionar opções se for múltipla escolha
            if tipo in ['MULTIPLA_ESCOLHA', 'ESCALA_NUMERICA']:
                opcoes_texto = request.form.getlist('opcao_texto[]')
                opcoes_valor = request.form.getlist('opcao_valor[]')
                
                for i, texto_opcao in enumerate(opcoes_texto):
                    if texto_opcao.strip():
                        opcao = OpcaoPergunta(
                            texto=texto_opcao.strip(),
                            valor=float(opcoes_valor[i]) if i < len(opcoes_valor) and opcoes_valor[i] else 0,
                            ordem=i + 1,
                            pergunta_id=nova_pergunta.id
                        )
                        db.session.add(opcao)
            
            db.session.commit()
            log_acao(f"Criou pergunta: {texto[:50]}...", None, "Pergunta", nova_pergunta.id)
            
            flash("Pergunta criada com sucesso!", "success")
            return redirect(url_for('cli.gerenciar_perguntas', topico_id=topico_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar pergunta: {str(e)}", "danger")
    
    return render_template('cli/nova_pergunta.html', topico=topico)

@cli_bp.route('/pergunta/<int:pergunta_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_pergunta(pergunta_id):
    """Editar pergunta existente"""
    pergunta = Pergunta.query.get_or_404(pergunta_id)
    
    if pergunta.topico.questionario.cliente_id != current_user.cliente_id:
        flash("Pergunta não encontrada.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    if request.method == 'POST':
        try:
            pergunta.texto = request.form.get('texto', '').strip()
            pergunta.tipo = TipoResposta(request.form.get('tipo'))
            pergunta.obrigatoria = request.form.get('obrigatoria') == 'on'
            pergunta.permite_observacao = request.form.get('permite_observacao') == 'on'
            pergunta.peso = int(request.form.get('peso', 1))
            
            # Atualizar opções se necessário
            if pergunta.tipo in [TipoResposta.MULTIPLA_ESCOLHA, TipoResposta.ESCALA_NUMERICA]:
                # Remover opções existentes
                OpcaoPergunta.query.filter_by(pergunta_id=pergunta_id).delete()
                
                # Adicionar novas opções
                opcoes_texto = request.form.getlist('opcao_texto[]')
                opcoes_valor = request.form.getlist('opcao_valor[]')
                
                for i, texto_opcao in enumerate(opcoes_texto):
                    if texto_opcao.strip():
                        opcao = OpcaoPergunta(
                            texto=texto_opcao.strip(),
                            valor=float(opcoes_valor[i]) if i < len(opcoes_valor) and opcoes_valor[i] else 0,
                            ordem=i + 1,
                            pergunta_id=pergunta.id
                        )
                        db.session.add(opcao)
            
            db.session.commit()
            log_acao(f"Editou pergunta: {pergunta.texto[:50]}...", None, "Pergunta", pergunta_id)
            
            flash("Pergunta atualizada com sucesso!", "success")
            return redirect(url_for('cli.gerenciar_perguntas', topico_id=pergunta.topico_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar pergunta: {str(e)}", "danger")
    
    return render_template('cli/editar_pergunta.html', pergunta=pergunta)

@cli_bp.route('/pergunta/<int:pergunta_id>/remover', methods=['POST'])
@login_required
def remover_pergunta(pergunta_id):
    """Remove uma pergunta"""
    try:
        pergunta = Pergunta.query.get_or_404(pergunta_id)
        
        if pergunta.topico.questionario.cliente_id != current_user.cliente_id:
            flash("Pergunta não encontrada.", "error")
            return redirect(url_for('cli.listar_questionarios'))
        
        topico_id = pergunta.topico_id
        
        pergunta.ativo = False
        db.session.commit()
        
        log_acao(f"Removeu pergunta: {pergunta.texto[:50]}...", None, "Pergunta", pergunta_id)
        flash("Pergunta removida com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover pergunta: {str(e)}", "danger")
    
    return redirect(url_for('cli.gerenciar_perguntas', topico_id=topico_id))

# ===================== AVALIADOS =====================

@cli_bp.route('/avaliados')
@cli_bp.route('/listar-avaliados')
@login_required
def listar_avaliados():
    """Lista os avaliados do cliente"""
    avaliados = get_avaliados_usuario()
    
    # Estatísticas para cada avaliado
    for avaliado in avaliados:
        avaliado.total_aplicacoes = AplicacaoQuestionario.query.filter_by(
            avaliado_id=avaliado.id
        ).count()
        
        avaliado.ultima_aplicacao = AplicacaoQuestionario.query.filter_by(
            avaliado_id=avaliado.id
        ).order_by(AplicacaoQuestionario.data_inicio.desc()).first()

    return render_template('cli/listar_avaliados.html', avaliados=avaliados)

@cli_bp.route('/avaliado/novo', methods=['GET', 'POST'])
@cli_bp.route('/cadastrar-avaliado', methods=['GET', 'POST'])
@login_required
def novo_avaliado():
    """Cadastra um novo avaliado"""
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            codigo = request.form.get('codigo', '').strip()
            endereco = request.form.get('endereco', '').strip()
            grupo_id = request.form.get('grupo_id')
            
            if not nome:
                flash("Nome do avaliado é obrigatório.", "danger")
                return redirect(url_for('cli.novo_avaliado'))
            
            # Verificar se código já existe
            if codigo:
                avaliado_existente = Avaliado.query.filter_by(
                    codigo=codigo,
                    cliente_id=current_user.cliente_id
                ).first()
                if avaliado_existente:
                    flash("Já existe um avaliado com este código.", "warning")
                    return redirect(url_for('cli.novo_avaliado'))
            
            novo_avaliado = Avaliado(
                nome=nome,
                codigo=codigo,
                endereco=endereco,
                grupo_id=int(grupo_id) if grupo_id else None,
                cliente_id=current_user.cliente_id,
                ativo=True
            )
            
            db.session.add(novo_avaliado)
            db.session.commit()
            
            log_acao(f"Criou avaliado: {nome}", None, "Avaliado", novo_avaliado.id)
            flash(f"Avaliado '{nome}' criado com sucesso!", "success")
            
            return redirect(url_for('cli.listar_avaliados'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar avaliado: {str(e)}", "danger")

    # GET
    grupos = Grupo.query.filter_by(
        cliente_id=current_user.cliente_id, ativo=True
    ).all()

    return render_template('cli/novo_avaliado.html', grupos=grupos)

@cli_bp.route('/avaliado/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_avaliado(id):
    
    avaliado = Avaliado.query.get_or_404(id)
    
    if avaliado.cliente_id != current_user.cliente_id:
        flash("Avaliado não encontrado.", "error")
        return redirect(url_for('cli.listar_avaliados'))
    
    if request.method == 'POST':
        try:
            avaliado.nome = request.form.get('nome', '').strip()
            avaliado.codigo = request.form.get('codigo', '').strip()
            avaliado.endereco = request.form.get('endereco', '').strip()
            avaliado.grupo_id = int(request.form.get('grupo_id')) if request.form.get('grupo_id') else None
            avaliado.ativo = request.form.get('ativo') == 'on'
            
            db.session.commit()
            log_acao(f"Editou avaliado: {avaliado.nome}", None, "Avaliado", id)
            
            flash("Avaliado atualizado com sucesso!", "success")
            return redirect(url_for('cli.listar_avaliados'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar avaliado: {str(e)}", "danger")
    
    grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    return render_template('cli/editar_avaliado.html', avaliado=avaliado, grupos=grupos)

# ===================== APLICAÇÕES =====================

@cli_bp.route('/aplicacoes')
@cli_bp.route('/listar-aplicacoes')
@login_required
def listar_aplicacoes():
    """Lista todas as aplicações de questionário"""
    # Filtros
    avaliado_id = request.args.get('avaliado_id')
    questionario_id = request.args.get('questionario_id')
    status = request.args.get('status')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Query base
    query = AplicacaoQuestionario.query.join(Avaliado).filter(
        Avaliado.cliente_id == current_user.cliente_id
    )
    
    # Aplicar filtros
    if avaliado_id:
        query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
    
    if questionario_id:
        query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
    
    if status:
        query = query.filter(AplicacaoQuestionario.status == StatusAplicacao(status))
    
    if data_inicio:
        query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
    
    if data_fim:
        query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    
    # Paginação
    page = request.args.get('page', 1, type=int)
    aplicacoes = query.order_by(AplicacaoQuestionario.data_inicio.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Dados para filtros
    avaliados = get_avaliados_usuario()
    questionarios = Questionario.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativo=True,
        publicado=True
    ).all()
    
    return render_template('cli/listar_aplicacoes.html',
                         aplicacoes=aplicacoes,
                         avaliados=avaliados,
                         questionarios=questionarios,
                         filtros={
                             'avaliado_id': int(avaliado_id) if avaliado_id else None,
                             'questionario_id': int(questionario_id) if questionario_id else None,
                             'status': status,
                             'data_inicio': data_inicio,
                             'data_fim': data_fim
                         })

@cli_bp.route('/aplicacao/nova', methods=['GET', 'POST'])
@cli_bp.route('/nova-aplicacao', methods=['GET', 'POST'])
@login_required
def nova_aplicacao():
    """Inicia uma nova aplicação de questionário"""
    if request.method == 'POST':
        try:
            avaliado_id = int(request.form.get('avaliado_id'))
            questionario_id = int(request.form.get('questionario_id'))
            observacoes = request.form.get('observacoes', '').strip()
            
            # Validar permissões
            avaliado = Avaliado.query.get_or_404(avaliado_id)
            if avaliado.cliente_id != current_user.cliente_id:
                flash("Avaliado não encontrado.", "error")
                return redirect(url_for('cli.nova_aplicacao'))
            
            questionario = Questionario.query.get_or_404(questionario_id)
            if questionario.cliente_id != current_user.cliente_id or not questionario.publicado:
                flash("Questionário não disponível.", "error")
                return redirect(url_for('cli.nova_aplicacao'))
            
            # Criar aplicação
            aplicacao = AplicacaoQuestionario(
                avaliado_id=avaliado_id,
                questionario_id=questionario_id,
                aplicador_id=current_user.id,
                data_inicio=datetime.now(),
                observacoes=observacoes,
                status=StatusAplicacao.EM_ANDAMENTO
            )
            
            db.session.add(aplicacao)
            db.session.commit()
            
            log_acao(f"Iniciou aplicação do questionário: {questionario.nome}", None, "AplicacaoQuestionario", aplicacao.id)
            flash("Aplicação iniciada com sucesso!", "success")
            
            return redirect(url_for('cli.responder_aplicacao', id=aplicacao.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao iniciar aplicação: {str(e)}", "danger")
    
    # GET - Mostrar formulário
    avaliados = get_avaliados_usuario()
    questionarios = Questionario.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativo=True,
        publicado=True
    ).all()
    
    return render_template('cli/nova_aplicacao.html',
                         avaliados=avaliados,
                         questionarios=questionarios)

@cli_bp.route('/aplicacao/<int:id>/responder')
@login_required
def responder_aplicacao(id):
    """Interface para responder aplicação"""
    aplicacao = AplicacaoQuestionario.query.get_or_404(id)
    
    # Verificar permissões
    if aplicacao.avaliado.cliente_id != current_user.cliente_id:
        flash("Aplicação não encontrada.", "error")
        return redirect(url_for('cli.listar_aplicacoes'))
    
    if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
        flash("Esta aplicação já foi finalizada.", "warning")
        return redirect(url_for('cli.visualizar_aplicacao', id=id))
    
    # Buscar tópicos e perguntas
    topicos = Topico.query.filter_by(
        questionario_id=aplicacao.questionario_id,
        ativo=True
    ).order_by(Topico.ordem).all()
    
    # Buscar respostas já dadas
    respostas_existentes = {}
    for resposta in aplicacao.respostas:
        respostas_existentes[resposta.pergunta_id] = resposta
    
    return render_template('cli/responder_aplicacao.html',
                         aplicacao=aplicacao,
                         topicos=topicos,
                         respostas_existentes=respostas_existentes)

@cli_bp.route('/aplicacao/<int:id>/salvar-resposta', methods=['POST'])
@login_required
def salvar_resposta(id):
    """Salva uma resposta individual (AJAX)"""
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        
        # Verificar permissões
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            return jsonify({'erro': 'Acesso negado'}), 403
        
        if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
            return jsonify({'erro': 'Aplicação já finalizada'}), 400
        
        data = request.get_json()
        pergunta_id = data.get('pergunta_id')
        resposta_texto = data.get('resposta', '')
        observacao = data.get('observacao', '')
        
        pergunta = Pergunta.query.get_or_404(pergunta_id)
        
        # Buscar resposta existente ou criar nova
        resposta = RespostaPergunta.query.filter_by(
            aplicacao_id=id,
            pergunta_id=pergunta_id
        ).first()
        
        if not resposta:
            resposta = RespostaPergunta(
                aplicacao_id=id,
                pergunta_id=pergunta_id
            )
        
        resposta.resposta = resposta_texto
        resposta.observacao = observacao
        resposta.data_resposta = datetime.now()
        
        # Calcular pontuação se aplicável
        if pergunta.tipo == TipoResposta.SIM_NAO_NA:
            if resposta_texto.lower() == 'sim':
                resposta.pontos = pergunta.peso
            elif resposta_texto.lower() == 'não':
                resposta.pontos = 0
            else:  # N.A.
                resposta.pontos = None
        elif pergunta.tipo in [TipoResposta.MULTIPLA_ESCOLHA, TipoResposta.ESCALA_NUMERICA]:
            opcao = OpcaoPergunta.query.filter_by(
                pergunta_id=pergunta_id,
                texto=resposta_texto
            ).first()
            if opcao:
                resposta.pontos = opcao.valor * pergunta.peso
        elif pergunta.tipo == TipoResposta.NOTA:
            try:
                nota = float(resposta_texto)
                resposta.pontos = nota * pergunta.peso
            except:
                resposta.pontos = 0
        
        db.session.add(resposta)
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Resposta salva com sucesso',
            'pontos': resposta.pontos
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/aplicacao/<int:id>/finalizar', methods=['POST'])
@login_required
def finalizar_aplicacao(id):
    """Finaliza uma aplicação"""
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        
        # Verificar permissões
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Aplicação não encontrada.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))
        
        if aplicacao.status != StatusAplicacao.EM_ANDAMENTO:
            flash("Esta aplicação já foi finalizada.", "warning")
            return redirect(url_for('cli.visualizar_aplicacao', id=id))
        
        # Verificar perguntas obrigatórias
        perguntas_obrigatorias = db.session.query(Pergunta.id).join(Topico).filter(
            Topico.questionario_id == aplicacao.questionario_id,
            Pergunta.obrigatoria == True,
            Pergunta.ativo == True,
            Topico.ativo == True
        ).all()
        
        respostas_dadas = db.session.query(RespostaPergunta.pergunta_id).filter_by(
            aplicacao_id=id
        ).all()
        
        perguntas_obrig_ids = [p.id for p in perguntas_obrigatorias]
        respostas_ids = [r.pergunta_id for r in respostas_dadas]
        
        perguntas_faltando = set(perguntas_obrig_ids) - set(respostas_ids)
        
        if perguntas_faltando:
            flash(f"Existem {len(perguntas_faltando)} pergunta(s) obrigatória(s) sem resposta.", "warning")
            return redirect(url_for('cli.responder_aplicacao', id=id))
        
        # Calcular nota final se configurado
        if aplicacao.questionario.calcular_nota:
            total_pontos = 0
            pontos_obtidos = 0
            
            for resposta in aplicacao.respostas:
                if resposta.pontos is not None:
                    pontos_obtidos += resposta.pontos
                    total_pontos += resposta.pergunta.peso
            
            if total_pontos > 0:
                if aplicacao.questionario.modo_configuracao == 'percentual':
                    aplicacao.nota_final = (pontos_obtidos / total_pontos) * 100
                else:  # pontos
                    aplicacao.nota_final = pontos_obtidos
                    
                aplicacao.nota_final = round(aplicacao.nota_final, aplicacao.questionario.casas_decimais)
        
        # Finalizar aplicação
        aplicacao.data_fim = datetime.now()
        aplicacao.status = StatusAplicacao.FINALIZADA
        aplicacao.observacoes_finais = request.form.get('observacoes_finais', '')
        
        db.session.commit()
        
        log_acao(f"Finalizou aplicação: {aplicacao.questionario.nome}", None, "AplicacaoQuestionario", id)
        flash("Aplicação finalizada com sucesso!", "success")
        
        return redirect(url_for('cli.visualizar_aplicacao', id=id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao finalizar aplicação: {str(e)}", "danger")
        return redirect(url_for('cli.responder_aplicacao', id=id))

@cli_bp.route('/aplicacao/<int:id>')
@cli_bp.route('/aplicacao/<int:id>/visualizar')
@login_required
def visualizar_aplicacao(id):
    """Visualiza uma aplicação finalizada"""
    aplicacao = AplicacaoQuestionario.query.get_or_404(id)
    
    # Verificar permissões
    if aplicacao.avaliado.cliente_id != current_user.cliente_id:
        flash("Aplicação não encontrada.", "error")
        return redirect(url_for('cli.listar_aplicacoes'))
    
    # Buscar estrutura completa
    topicos = Topico.query.filter_by(
        questionario_id=aplicacao.questionario_id,
        ativo=True
    ).order_by(Topico.ordem).all()
    
    # Organizar respostas por pergunta
    respostas_dict = {}
    for resposta in aplicacao.respostas:
        respostas_dict[resposta.pergunta_id] = resposta
    
    # Estatísticas
    stats = {
        'total_perguntas': len(respostas_dict),
        'perguntas_respondidas': len([r for r in respostas_dict.values() if r.resposta.strip()]),
        'tempo_aplicacao': (aplicacao.data_fim - aplicacao.data_inicio).total_seconds() / 60 if aplicacao.data_fim else None
    }
    
    return render_template('cli/visualizar_aplicacao.html',
                         aplicacao=aplicacao,
                         topicos=topicos,
                         respostas_dict=respostas_dict,
                         stats=stats)

@cli_bp.route('/aplicacao/<int:id>/relatorio')
@login_required
def gerar_relatorio_aplicacao(id):
    """Gera relatório em PDF da aplicação"""
    try:
        aplicacao = AplicacaoQuestionario.query.get_or_404(id)
        
        # Verificar permissões
        if aplicacao.avaliado.cliente_id != current_user.cliente_id:
            flash("Aplicação não encontrada.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))
        
        # Buscar dados completos
        topicos = Topico.query.filter_by(
            questionario_id=aplicacao.questionario_id,
            ativo=True
        ).order_by(Topico.ordem).all()
        
        # Organizar respostas
        respostas_dict = {}
        for resposta in aplicacao.respostas:
            respostas_dict[resposta.pergunta_id] = resposta
        
        # Gerar QR Code se necessário
        qr_code_url = None
        if hasattr(current_app, 'config') and current_app.config.get('SITE_URL'):
            qr_url = f"{current_app.config['SITE_URL']}/aplicacao/{id}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        
        # Renderizar template HTML
        html_content = render_template('cli/relatorio_aplicacao.html',
                                     aplicacao=aplicacao,
                                     topicos=topicos,
                                     respostas_dict=respostas_dict,
                                     qr_code_url=qr_code_url,
                                     data_geracao=datetime.now())
        
        # Gerar PDF
        pdf = HTML(string=html_content, base_url=request.url_root).write_pdf()
        
        # Criar resposta
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="aplicacao_{id}_{aplicacao.questionario.nome.replace(" ", "_")}.pdf"'
        
        log_acao(f"Gerou relatório da aplicação: {aplicacao.questionario.nome}", None, "AplicacaoQuestionario", id)
        
        return response
        
    except Exception as e:
        flash(f"Erro ao gerar relatório: {str(e)}", "danger")
        return redirect(url_for('cli.visualizar_aplicacao', id=id))

# ===================== RELATÓRIOS E ANÁLISES =====================

@cli_bp.route('/relatorios')
@login_required
def relatorios():
    """Página de relatórios e análises"""
    # Buscar dados para os filtros
    avaliados = get_avaliados_usuario()
    questionarios = Questionario.query.filter_by(
        cliente_id=current_user.cliente_id,
        ativo=True
    ).all()
    
    # Estatísticas básicas para o dashboard de relatórios
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
    
    return render_template('cli/relatorios.html',
                         avaliados=avaliados,
                         questionarios=questionarios,
                         stats=stats)

@cli_bp.route('/api/relatorio-dados')
@login_required
def api_dados_relatorio():
    """API para dados de relatórios"""
    tipo = request.args.get('tipo', 'ranking')
    avaliado_id = request.args.get('avaliado_id')
    questionario_id = request.args.get('questionario_id')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    try:
        dados = {}
        
        if tipo == 'ranking':
            # Ranking de avaliados por nota média
            query = db.session.query(
                Avaliado.nome,
                func.avg(AplicacaoQuestionario.nota_final).label('media'),
                func.count(AplicacaoQuestionario.id).label('total_aplicacoes')
            ).join(AplicacaoQuestionario).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            )
            
            if data_inicio:
                query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
            if data_fim:
                query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            
            resultados = query.group_by(Avaliado.id, Avaliado.nome).order_by(
                func.avg(AplicacaoQuestionario.nota_final).desc()
            ).all()
            
            dados['ranking'] = [
                {
                    'avaliado': r.nome,
                    'media': round(float(r.media), 2),
                    'total_aplicacoes': r.total_aplicacoes
                }
                for r in resultados
            ]
            
        elif tipo == 'evolucao':
            # Evolução temporal das notas
            query = db.session.query(
                func.date(AplicacaoQuestionario.data_inicio).label('data'),
                func.avg(AplicacaoQuestionario.nota_final).label('media')
            ).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            )
            
            if avaliado_id:
                query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
            if questionario_id:
                query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
            if data_inicio:
                query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
            if data_fim:
                query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            
            resultados = query.group_by(func.date(AplicacaoQuestionario.data_inicio)).order_by('data').all()
            
            dados['evolucao'] = [
                {
                    'data': r.data.strftime('%Y-%m-%d'),
                    'media': round(float(r.media), 2)
                }
                for r in resultados
            ]
            
        elif tipo == 'comparativo':
            # Comparativo entre questionários
            query = db.session.query(
                Questionario.nome,
                func.avg(AplicacaoQuestionario.nota_final).label('media'),
                func.count(AplicacaoQuestionario.id).label('total_aplicacoes')
            ).join(AplicacaoQuestionario).join(Avaliado).filter(
                Avaliado.cliente_id == current_user.cliente_id,
                AplicacaoQuestionario.nota_final.isnot(None)
            )
            
            if data_inicio:
                query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
            if data_fim:
                query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
            
            resultados = query.group_by(Questionario.id, Questionario.nome).all()
            
            dados['comparativo'] = [
                {
                    'questionario': r.nome,
                    'media': round(float(r.media), 2),
                    'total_aplicacoes': r.total_aplicacoes
                }
                for r in resultados
            ]
        
        return jsonify(dados)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/relatorio/exportar')
@login_required
def exportar_relatorio():
    """Exporta relatório em diferentes formatos"""
    formato = request.args.get('formato', 'pdf')
    tipo = request.args.get('tipo', 'ranking')
    
    try:
        # Obter dados do relatório usando a mesma lógica da API
        dados = obter_dados_relatorio_exportacao(tipo, 
                                                request.args.get('avaliado_id'),
                                                request.args.get('questionario_id'),
                                                request.args.get('data_inicio'),
                                                request.args.get('data_fim'))
        
        if formato == 'csv':
            return exportar_csv(dados, tipo)
        elif formato == 'pdf':
            return exportar_pdf(dados, tipo)
        else:
            flash("Formato não suportado.", "error")
            return redirect(url_for('cli.relatorios'))
            
    except Exception as e:
        flash(f"Erro ao exportar relatório: {str(e)}", "danger")
        return redirect(url_for('cli.relatorios'))

# ===================== GESTÃO DE USUÁRIOS =====================

@cli_bp.route('/usuarios')
@login_required
@admin_required
def gerenciar_usuarios():
    """Página de gestão de usuários"""
    usuarios = Usuario.query.filter_by(
        cliente_id=current_user.cliente_id
    ).order_by(Usuario.nome).all()
    
    # Estatísticas de usuários
    stats_usuarios = {
        'total': len(usuarios),
        'ativos': len([u for u in usuarios if u.ativo]),
        'admins': len([u for u in usuarios if u.tipo == TipoUsuario.ADMIN]),
        'usuarios': len([u for u in usuarios if u.tipo == TipoUsuario.USUARIO])
    }
    
    return render_template('cli/usuarios.html',
                         usuarios=usuarios,
                         stats=stats_usuarios)

@cli_bp.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    """Criar novo usuário"""
    if request.method == 'POST':
        try:
            # Validar dados
            nome = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip().lower()
            tipo = request.form.get('tipo')
            grupo_id = request.form.get('grupo_id')
            
            if not all([nome, email, tipo]):
                flash('Todos os campos são obrigatórios.', 'error')
                return render_template('cli/usuario_form.html')
            
            # Verificar se email já existe
            if Usuario.query.filter_by(email=email).first():
                flash('Este e-mail já está em uso.', 'error')
                return render_template('cli/usuario_form.html')
            
            # Criar usuário
            from werkzeug.security import generate_password_hash
            usuario = Usuario(
                nome=nome,
                email=email,
                tipo=TipoUsuario(tipo),
                cliente_id=current_user.cliente_id,
                grupo_id=int(grupo_id) if grupo_id else None,
                senha_hash=generate_password_hash('123456'),  # Senha padrão
                ativo=True
            )
            
            db.session.add(usuario)
            db.session.commit()
            
            log_acao(f"Criou usuário: {nome}", None, "Usuario", usuario.id)
            flash(f'Usuário {nome} criado com sucesso! Senha padrão: 123456', 'success')
            return redirect(url_for('cli.gerenciar_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
    
    grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    return render_template('cli/usuario_form.html', grupos=grupos)

# ===================== CONFIGURAÇÕES =====================

@cli_bp.route('/configuracoes')
@login_required
@admin_required
def configuracoes():
    """Página de configurações do sistema"""
    # Buscar configurações do cliente
    config = ConfiguracaoCliente.query.filter_by(
        cliente_id=current_user.cliente_id
    ).first()
    
    if not config:
        # Criar configuração padrão
        config = ConfiguracaoCliente(
            cliente_id=current_user.cliente_id,
            logo_url='',
            cor_primaria='#007bff',
            cor_secundaria='#6c757d',
            mostrar_notas=True,
            permitir_fotos=True,
            obrigar_plano_acao=True
        )
        db.session.add(config)
        db.session.commit()
    
    return render_template('cli/configuracoes.html', config=config)

@cli_bp.route('/configuracoes/salvar', methods=['POST'])
@login_required
@admin_required
def salvar_configuracoes():
    """Salvar configurações do sistema"""
    try:
        config = ConfiguracaoCliente.query.filter_by(
            cliente_id=current_user.cliente_id
        ).first()
        
        if not config:
            config = ConfiguracaoCliente(cliente_id=current_user.cliente_id)
        
        # Atualizar configurações
        config.cor_primaria = request.form.get('cor_primaria', '#007bff')
        config.cor_secundaria = request.form.get('cor_secundaria', '#6c757d')
        config.mostrar_notas = 'mostrar_notas' in request.form
        config.permitir_fotos = 'permitir_fotos' in request.form
        config.obrigar_plano_acao = 'obrigar_plano_acao' in request.form
        
        # Upload de logo
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename:
                filename = secure_filename(logo.filename)
                logo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logos', filename)
                
                # Criar diretório se não existir
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                logo.save(logo_path)
                config.logo_url = f'/uploads/logos/{filename}'
        
        db.session.add(config)
        db.session.commit()
        
        log_acao("Salvou configurações do sistema", None, "ConfiguracaoCliente", config.id)
        flash('Configurações salvas com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar configurações: {str(e)}', 'error')
    
    return redirect(url_for('cli.configuracoes'))

# ===================== NOTIFICAÇÕES =====================

@cli_bp.route('/notificacoes')
@login_required
def notificacoes():
    """Centro de notificações"""
    # Buscar notificações do usuário
    notificacoes = Notificacao.query.filter_by(
        usuario_id=current_user.id
    ).order_by(Notificacao.data_criacao.desc()).limit(50).all()
    
    # Marcar como visualizadas
    for notif in notificacoes:
        if not notif.visualizada:
            notif.visualizada = True
    
    db.session.commit()
    
    return render_template('cli/notificacoes.html', notificacoes=notificacoes)

@cli_bp.route('/api/notificacoes/count')
@login_required
def api_count_notificacoes():
    """API para contar notificações não lidas"""
    count = Notificacao.query.filter_by(
        usuario_id=current_user.id,
        visualizada=False
    ).count()
    
    return jsonify({'count': count})

# ===================== FUNÇÕES AUXILIARES PARA EXPORTAÇÃO =====================

def obter_dados_relatorio_exportacao(tipo, avaliado_id, questionario_id, data_inicio, data_fim):
    """Obtém dados para exportação de relatórios"""
    dados = {}
    
    if tipo == 'ranking':
        query = db.session.query(
            Avaliado.nome.label('avaliado'),
            func.avg(AplicacaoQuestionario.nota_final).label('media'),
            func.count(AplicacaoQuestionario.id).label('total_aplicacoes')
        ).join(AplicacaoQuestionario).filter(
            Avaliado.cliente_id == current_user.cliente_id,
            AplicacaoQuestionario.nota_final.isnot(None)
        )
        
        if data_inicio:
            query = query.filter(AplicacaoQuestionario.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        if data_fim:
            query = query.filter(AplicacaoQuestionario.data_inicio <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        resultados = query.group_by(Avaliado.id, Avaliado.nome).order_by(
            func.avg(AplicacaoQuestionario.nota_final).desc()
        ).all()
        
        dados['ranking'] = [
            {
                'avaliado': r.avaliado,
                'media': round(float(r.media), 2),
                'total_aplicacoes': r.total_aplicacoes
            }
            for r in resultados
        ]
    
    return dados

def exportar_csv(dados, tipo_relatorio):
    """Exporta relatório em formato CSV"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if tipo_relatorio == 'ranking':
        writer.writerow(['Posição', 'Avaliado', 'Nota Média', 'Total Aplicações'])
        for idx, item in enumerate(dados['ranking'], 1):
            writer.writerow([idx, item['avaliado'], item['media'], item['total_aplicacoes']])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=relatorio_{tipo_relatorio}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'}
    )

def exportar_pdf(dados, tipo_relatorio):
    """Exporta relatório em formato PDF"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relatório QualiGestor - {tipo_relatorio.title()}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; text-align: center; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .data {{ font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Relatório QualiGestor - {tipo_relatorio.title()}</h1>
            <p class="data">Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        {gerar_conteudo_html_relatorio(dados, tipo_relatorio)}
    </body>
    </html>
    """
    
    try:
        pdf = HTML(string=html_content, base_url=request.url_root).write_pdf()
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=relatorio_{tipo_relatorio}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        
        return response
    except Exception as e:
        # Fallback para HTML se PDF falhar
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response

def gerar_conteudo_html_relatorio(dados, tipo_relatorio):
    """Gera conteúdo HTML específico para cada tipo de relatório"""
    if tipo_relatorio == 'ranking' and 'ranking' in dados:
        html = """
        <table>
            <tr>
                <th>Posição</th>
                <th>Avaliado</th>
                <th>Nota Média</th>
                <th>Total Aplicações</th>
            </tr>
        """
        
        for idx, item in enumerate(dados['ranking'], 1):
            html += f"""
            <tr>
                <td>{idx}°</td>
                <td>{item['avaliado']}</td>
                <td>{item['media']}%</td>
                <td>{item['total_aplicacoes']}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    return "<p>Dados do relatório não disponíveis</p>"

# ===================== FIM DAS ROTAS CLI ======================
# ===================== ROTAS DE COMPATIBILIDADE =====================

@cli_bp.route('/checklists')
@cli_bp.route('/listar-checklists')
@login_required
def listar_checklists():
    """Redirecionamento para listar questionários (compatibilidade)"""
    return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/checklist/novo')
@cli_bp.route('/novo-checklist')
@login_required
def novo_checklist():
    """Redirecionamento para novo questionário (compatibilidade)"""
    return redirect(url_for('cli.novo_questionario'))

# Função auxiliar para verificar permissões
def verificar_permissao_admin():
    """Verifica se usuário tem permissão de admin"""
    if not current_user.is_authenticated:
        return False
    return current_user.tipo in [TipoUsuario.ADMIN, TipoUsuario.SUPER_ADMIN]

    
# app/cli/views/questionarios.py
import json
from datetime import datetime
from flask import request, redirect, url_for, flash, make_response, current_app
from flask_login import current_user, login_required
from sqlalchemy import func, or_

# Importa o Blueprint
from .. import cli_bp

# Importa utilitários
from ..utils import (
    admin_required, log_acao, render_template_safe
)

# Importa modelos
from ...models import (
    db, Usuario, Questionario, Topico, Pergunta, 
    OpcaoPergunta, AplicacaoQuestionario, UsuarioAutorizado,
    StatusQuestionario, TipoResposta, ModoExibicaoNota, 
    CorRelatorio, CategoriaIndicador
)

# ===================== LISTAGEM E VISUALIZAÇÃO =====================

@cli_bp.route('/questionarios', endpoint='listar_questionarios', methods=['GET'])
@cli_bp.route('/listar-questionarios', methods=['GET'])
@login_required
def listar_questionarios():
    """Lista questionários com filtros."""
    q_base = Questionario.query
    termo = (request.args.get("q") or "").strip()
    status = request.args.get("status", "publicados") 

    # Filtro por cliente
    q = q_base.filter(Questionario.cliente_id == current_user.cliente_id)

    # Filtro de Status
    if status == "publicados":
        q = q.filter(Questionario.ativo.is_(True), Questionario.publicado.is_(True))
    elif status == "rascunhos":
        q = q.filter(Questionario.ativo.is_(True), Questionario.publicado.is_(False))
    elif status == "inativos":
        q = q.filter(Questionario.ativo.is_(False))
    
    q_base_filtrada = q # Backup para fallback

    # Busca por texto
    if termo:
        like = f"%{termo}%"
        q = q.filter(or_(
            Questionario.nome.ilike(like),
            Questionario.titulo.ilike(like) if hasattr(Questionario, 'titulo') else False,
            Questionario.descricao.ilike(like)
        ))

    questionarios = q.order_by(Questionario.nome.asc()).all()

    # Fallback da busca
    usou_fallback = False
    if not questionarios and termo:
        usou_fallback = True
        questionarios = q_base_filtrada.order_by(Questionario.nome.asc()).all()
        flash(f"Nenhum item encontrado para '{termo}' — exibindo todos os itens do status '{status}'.", "warning")

    # Estatísticas simples
    for item in questionarios:
        item.total_aplicacoes = AplicacaoQuestionario.query.filter_by(questionario_id=item.id).count()
        media = db.session.query(func.avg(AplicacaoQuestionario.nota_final)).filter_by(questionario_id=item.id).scalar()
        item.media_nota = float(media) if media else 0.0

    return render_template_safe(
        'cli/listar_questionarios.html',
        questionarios=questionarios,
        termo=termo,
        status=status,
        usou_fallback=usou_fallback,
    )

@cli_bp.route('/questionario/<int:id>')
@cli_bp.route('/questionario/<int:id>/visualizar')
@login_required
def visualizar_questionario(id):
    """Dashboard do questionário."""
    questionario = Questionario.query.get_or_404(id)
    if questionario.cliente_id != current_user.cliente_id:
        flash("Questionário não encontrado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    stats = {
        'total_aplicacoes': AplicacaoQuestionario.query.filter_by(questionario_id=id).count(),
        'total_topicos': Topico.query.filter_by(questionario_id=id, ativo=True).count(),
        'total_perguntas': db.session.query(func.count(Pergunta.id)).join(Topico).filter(
            Topico.questionario_id == id, Pergunta.ativo == True
        ).scalar(),
        'media_nota': db.session.query(func.avg(AplicacaoQuestionario.nota_final)).filter_by(questionario_id=id).scalar() or 0
    }
    
    ultimas_aplicacoes = AplicacaoQuestionario.query.filter_by(
        questionario_id=id
    ).order_by(AplicacaoQuestionario.data_inicio.desc()).limit(10).all()
    
    return render_template_safe('cli/visualizar_questionario.html',
                         questionario=questionario,
                         stats=stats,
                         ultimas_aplicacoes=ultimas_aplicacoes)

# ===================== CRUD QUESTIONÁRIO =====================

@cli_bp.route('/questionario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_questionario():
    """Cria novo questionário (Restrito a SUPER_ADMIN/Laboratório)."""
    if current_user.tipo.name != 'SUPER_ADMIN':
        flash("Apenas o Laboratório pode criar novos modelos.", "danger")
        return redirect(url_for('cli.listar_questionarios'))

    usuarios_disponiveis = Usuario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Usuario.nome).all()

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            if not nome:
                flash("Nome obrigatório.", "warning")
                return render_template_safe('cli/novo_questionario.html', usuarios=usuarios_disponiveis)

            if Questionario.query.filter_by(nome=nome, cliente_id=current_user.cliente_id, ativo=True).first():
                flash(f"Já existe questionário com nome '{nome}'.", "warning")
                return render_template_safe('cli/novo_questionario.html', usuarios=usuarios_disponiveis)

            novo_q = Questionario(
                nome=nome,
                versao=request.form.get('versao', '1.0'),
                descricao=request.form.get('descricao', ''),
                modo=request.form.get('modo', 'Avaliado'),
                cliente_id=current_user.cliente_id,
                criado_por_id=current_user.id,
                calcular_nota=(request.form.get('calcular_nota') == 'on'),
                ocultar_nota_aplicacao=(request.form.get('ocultar_nota') == 'on'),
                base_calculo=int(request.form.get('base_calculo', 100)),
                casas_decimais=int(request.form.get('casas_decimais', 2)),
                modo_configuracao=request.form.get('modo_configuracao', 'percentual'),
                modo_exibicao_nota=ModoExibicaoNota.PERCENTUAL,
                anexar_documentos=(request.form.get('anexar_documentos') == 'on'),
                capturar_geolocalizacao=(request.form.get('geolocalizacao') == 'on'),
                restringir_avaliados=(request.form.get('restricao_avaliados') == 'on'),
                habilitar_reincidencia=(request.form.get('reincidencia') == 'on'),
                cor_relatorio=CorRelatorio.AZUL,
                incluir_assinatura=(request.form.get('incluir_assinatura') == 'on'),
                incluir_foto_capa=(request.form.get('incluir_foto_capa') == 'on'),
                # Campos extras de relatório
                exibir_nota_anterior=(request.form.get('exibir_nota_anterior') == 'on'),
                exibir_tabela_resumo=(request.form.get('exibir_tabela_de_resumo') == 'on'),
                exibir_limites_aceitaveis=(request.form.get('exibir_limites_aceitáveis') == 'on'),
                exibir_data_hora=(request.form.get('exibir_data/hora_início_e_fim') == 'on'),
                exibir_questoes_omitidas=(request.form.get('exibir_questões_omitidas') == 'on'),
                exibir_nao_conformidade=(request.form.get('exibir_relatório_não_conformidade') == 'on'),
                ativo=True, publicado=False, status=StatusQuestionario.RASCUNHO
            )

            db.session.add(novo_q)
            db.session.flush()

            # Usuários Autorizados
            usuarios_selecionados = request.form.getlist('usuarios_autorizados')
            if not usuarios_selecionados and request.form.get('usuarios_autorizados'):
                 usuarios_selecionados = request.form.get('usuarios_autorizados').split(',')

            if usuarios_selecionados:
                for uid in usuarios_selecionados:
                    if uid and str(uid).strip().isdigit():
                        db.session.add(UsuarioAutorizado(questionario_id=novo_q.id, usuario_id=int(uid)))

            db.session.commit()
            log_acao(f"Criou questionário: {nome}", None, "Questionario", novo_q.id)
            flash(f"Questionário '{nome}' criado!", "success")
            return redirect(url_for('cli.gerenciar_topicos', id=novo_q.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar: {str(e)}", "danger")
            return render_template_safe('cli/novo_questionario.html', usuarios=usuarios_disponiveis)

    return render_template_safe('cli/novo_questionario.html', usuarios=usuarios_disponiveis)

@cli_bp.route('/questionario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_questionario(id):
    """Edita configurações gerais."""
    questionario = Questionario.query.get_or_404(id)
    if questionario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))

    if current_user.tipo.name != 'SUPER_ADMIN':
        flash("Apenas o Laboratório pode editar configurações.", "warning")
        return redirect(url_for('cli.listar_questionarios'))

    usuarios_disponiveis = Usuario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()

    if request.method == 'POST':
        try:
            questionario.nome = request.form.get('nome', '').strip()
            questionario.descricao = request.form.get('descricao', '').strip()
            questionario.versao = request.form.get('versao', '').strip()
            
            # Configurações Bool
            questionario.calcular_nota = (request.form.get('calcular_nota') == 'on')
            questionario.ocultar_nota_aplicacao = (request.form.get('ocultar_nota') == 'on')
            questionario.anexar_documentos = (request.form.get('anexar_documentos') == 'on')
            questionario.capturar_geolocalizacao = (request.form.get('geolocalizacao') == 'on')
            questionario.restringir_avaliados = (request.form.get('restricao_avaliados') == 'on')
            questionario.habilitar_reincidencia = (request.form.get('reincidencia') == 'on')
            questionario.incluir_assinatura = (request.form.get('incluir_assinatura') == 'on')
            questionario.incluir_foto_capa = (request.form.get('incluir_foto_capa') == 'on')
            
            # Flags de Relatório
            if hasattr(questionario, 'exibir_nota_anterior'):
                questionario.exibir_nota_anterior = (request.form.get('exibir_nota_anterior') == 'on')
            if hasattr(questionario, 'exibir_tabela_resumo'):
                questionario.exibir_tabela_resumo = (request.form.get('exibir_tabela_de_resumo') == 'on')
            if hasattr(questionario, 'exibir_limites_aceitaveis'):
                questionario.exibir_limites_aceitaveis = (request.form.get('exibir_limites_aceitáveis') == 'on')
            if hasattr(questionario, 'exibir_data_hora'):
                questionario.exibir_data_hora = (request.form.get('exibir_data/hora_início_e_fim') == 'on')
            if hasattr(questionario, 'exibir_questoes_omitidas'):
                questionario.exibir_questoes_omitidas = (request.form.get('exibir_questões_omitidas') == 'on')
            if hasattr(questionario, 'exibir_nao_conformidade'):
                questionario.exibir_nao_conformidade = (request.form.get('exibir_relatório_não_conformidade') == 'on')

            # Numéricos
            questionario.base_calculo = int(request.form.get('base_calculo', 100))
            questionario.casas_decimais = int(request.form.get('casas_decimais', 2))

            # Usuários
            UsuarioAutorizado.query.filter_by(questionario_id=questionario.id).delete()
            usuarios_selecionados = request.form.getlist('usuarios_autorizados')
            for uid in usuarios_selecionados:
                if uid and str(uid).strip().isdigit():
                    db.session.add(UsuarioAutorizado(questionario_id=questionario.id, usuario_id=int(uid)))

            db.session.commit()
            flash("Configurações atualizadas!", "success")
            return redirect(url_for('cli.listar_questionarios'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar: {str(e)}", "danger")

    autorizados_ids = [u.usuario_id for u in questionario.usuarios_autorizados]
    return render_template_safe('cli/editar_questionario.html', 
                              questionario=questionario, 
                              usuarios=usuarios_disponiveis,
                              autorizados_ids=autorizados_ids)

@cli_bp.route('/questionario/<int:id>/duplicar', methods=['POST'])
@login_required
def duplicar_questionario(id):
    """Duplica questionário e estrutura."""
    try:
        q_original = Questionario.query.get_or_404(id)
        if q_original.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "error")
            return redirect(url_for('cli.listar_questionarios'))

        novo_nome = f"{q_original.nome} - Cópia"
        contador = 1
        while Questionario.query.filter_by(nome=novo_nome, cliente_id=current_user.cliente_id).first():
            contador += 1
            novo_nome = f"{q_original.nome} - Cópia ({contador})"

        q_copia = Questionario(
            nome=novo_nome,
            versao="1.0",
            descricao=q_original.descricao,
            modo=q_original.modo,
            cliente_id=current_user.cliente_id,
            criado_por_id=current_user.id,
            calcular_nota=q_original.calcular_nota,
            ativo=True, publicado=False, status=StatusQuestionario.RASCUNHO
        )
        # Copiar configs restantes...
        q_copia.incluir_assinatura = q_original.incluir_assinatura
        q_copia.incluir_foto_capa = q_original.incluir_foto_capa
        
        db.session.add(q_copia)
        db.session.flush()

        # Duplicar tópicos e perguntas
        for topico in q_original.topicos:
            if topico.ativo:
                t_copia = Topico(
                    nome=topico.nome, descricao=topico.descricao,
                    ordem=topico.ordem, questionario_id=q_copia.id, ativo=True
                )
                db.session.add(t_copia)
                db.session.flush()
                
                for pergunta in topico.perguntas:
                    if pergunta.ativo:
                        p_copia = Pergunta(
                            texto=pergunta.texto, tipo=pergunta.tipo,
                            obrigatoria=pergunta.obrigatoria,
                            permite_observacao=pergunta.permite_observacao,
                            peso=pergunta.peso, ordem=pergunta.ordem,
                            criterio_foto=getattr(pergunta, 'criterio_foto', 'nenhuma'),
                            topico_id=t_copia.id, ativo=True
                        )
                        db.session.add(p_copia)
                        db.session.flush()

                        if hasattr(pergunta, 'opcoes'):
                            for opcao in pergunta.opcoes:
                                db.session.add(OpcaoPergunta(
                                    texto=opcao.texto, valor=opcao.valor,
                                    ordem=opcao.ordem, pergunta_id=p_copia.id, ativo=True
                                ))
        
        db.session.commit()
        log_acao(f"Duplicou questionário: {q_original.nome}", None, "Questionario", q_copia.id)
        flash(f"Cópia criada: '{novo_nome}'", "success")
        return redirect(url_for('cli.visualizar_questionario', id=q_copia.id))

    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao duplicar: {str(e)}", "danger")
        return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/questionario/<int:id>/desativar', methods=['POST'])
@login_required
def desativar_questionario(id):
    """Desativa questionário."""
    q = Questionario.query.get_or_404(id)
    if q.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    q.ativo = False
    q.publicado = False
    q.status = StatusQuestionario.INATIVO
    db.session.commit()
    flash("Questionário desativado.", "success")
    return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/questionario/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_questionario(id):
    """Exclui ou inativa (se já usado) um questionário."""
    q = Questionario.query.get_or_404(id)
    if q.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.listar_questionarios'))

    if current_user.tipo.name != 'SUPER_ADMIN':
        flash("Apenas Laboratório pode excluir.", "danger")
        return redirect(url_for('cli.listar_questionarios'))

    try:
        if AplicacaoQuestionario.query.filter_by(questionario_id=id).first():
            q.ativo = False
            q.publicado = False
            db.session.commit()
            flash("Questionário inativado (possui auditorias vinculadas).", "warning")
        else:
            if 'UsuarioAutorizado' in globals():
                UsuarioAutorizado.query.filter_by(questionario_id=id).delete()
            db.session.delete(q)
            db.session.commit()
            flash("Questionário excluído permanentemente.", "success")
            
    except Exception as e:
        db.session.rollback()
        q.ativo = False
        db.session.commit()
        flash(f"Erro ao excluir (inativado): {str(e)}", "warning")

    return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/questionario/<int:id>/publicar', methods=['POST'])
@login_required
def publicar_questionario(id):
    """Publica questionário."""
    q = Questionario.query.get_or_404(id)
    if q.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    total_perguntas = db.session.query(func.count(Pergunta.id)).join(Topico).filter(
        Topico.questionario_id == id, Topico.ativo == True, Pergunta.ativo == True
    ).scalar()

    if total_perguntas == 0:
        flash("Adicione perguntas antes de publicar.", "warning")
        return redirect(url_for('cli.gerenciar_topicos', id=id))
    
    q.publicado = True
    q.status = StatusQuestionario.PUBLICADO
    q.data_publicacao = datetime.now()
    db.session.commit()
    flash("Questionário publicado com sucesso!", "success")
    return redirect(url_for('cli.gerenciar_topicos', id=id))

# ===================== TÓPICOS =====================

@cli_bp.route('/questionario/<int:id>/topicos')
@login_required
def gerenciar_topicos(id):
    """Lista tópicos."""
    q = Questionario.query.get_or_404(id)
    if q.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    topicos = Topico.query.filter_by(questionario_id=id, ativo=True).order_by(Topico.ordem).all()
    for t in topicos:
        t.total_perguntas = Pergunta.query.filter_by(topico_id=t.id, ativo=True).count()
        
    return render_template_safe('cli/gerenciar_topicos.html', questionario=q, topicos=topicos)

@cli_bp.route('/questionario/<int:id>/topico/novo', methods=['GET', 'POST'])
@cli_bp.route('/questionario/<int:id>/topicos/novo', methods=['GET', 'POST']) # Alias
@login_required
def novo_topico(id):
    """Cria novo tópico."""
    q = Questionario.query.get_or_404(id)
    if q.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            if not nome:
                flash("Nome do tópico é obrigatório.", "danger")
                return render_template_safe('cli/novo_topico.html', questionario=q)

            ultima_ordem = db.session.query(func.max(Topico.ordem)).filter_by(questionario_id=id).scalar() or 0
            
            t = Topico(
                nome=nome, descricao=descricao, ordem=ultima_ordem+1,
                questionario_id=id, ativo=True
            )
            db.session.add(t)
            db.session.commit()
            flash("Tópico criado!", "success")
            return redirect(url_for('cli.gerenciar_topicos', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {str(e)}", "danger")

    return render_template_safe('cli/novo_topico.html', questionario=q)

@cli_bp.route('/topico/<int:topico_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_topico(topico_id):
    """Edita tópico e vincula Categoria SDAB."""
    topico = Topico.query.get_or_404(topico_id)
    if topico.questionario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))

    if request.method == 'POST':
        try:
            topico.nome = request.form.get('nome', '').strip()
            topico.descricao = request.form.get('descricao', '').strip()
            
            cat_id = request.form.get('categoria_id')
            if cat_id and cat_id.isdigit():
                topico.categoria_indicador_id = int(cat_id)
            else:
                topico.categoria_indicador_id = None

            db.session.commit()
            flash("Tópico atualizado.", "success")
            return redirect(url_for('cli.gerenciar_topicos', id=topico.questionario_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {str(e)}", "danger")

    categorias = CategoriaIndicador.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
    return render_template_safe('cli/editar_topico.html', topico=topico, categorias=categorias)

@cli_bp.route('/topico/<int:topico_id>/remover', methods=['POST'])
@login_required
def remover_topico(topico_id):
    """Remove tópico (soft delete) e suas perguntas."""
    topico = Topico.query.get_or_404(topico_id)
    if topico.questionario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    qid = topico.questionario_id
    try:
        perguntas = Pergunta.query.filter_by(topico_id=topico_id, ativo=True).all()
        for p in perguntas: p.ativo = False
        topico.ativo = False
        db.session.commit()
        flash("Tópico removido.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {str(e)}", "danger")
        
    return redirect(url_for('cli.gerenciar_topicos', id=qid))

# ===================== PERGUNTAS =====================

@cli_bp.route('/topico/<int:topico_id>/perguntas')
@login_required
def gerenciar_perguntas(topico_id):
    """Lista perguntas do tópico."""
    topico = Topico.query.get_or_404(topico_id)
    if topico.questionario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    perguntas = Pergunta.query.filter_by(topico_id=topico_id, ativo=True).order_by(Pergunta.ordem).all()
    return render_template_safe('cli/gerenciar_perguntas.html', topico=topico, perguntas=perguntas)

@cli_bp.route('/topico/<int:topico_id>/pergunta/nova', methods=['GET', 'POST'])
@login_required
def nova_pergunta(topico_id):
    """Cria nova pergunta."""
    topico = Topico.query.get_or_404(topico_id)
    if topico.questionario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))

    if request.method == 'POST':
        try:
            texto = request.form.get('texto', '').strip()
            tipo_str = request.form.get('tipo', 'SIM_NAO_NA')
            criterio_foto = request.form.get('criterio_foto', 'nenhuma')

            if not texto:
                flash("Texto obrigatório.", "danger")
                return render_template_safe('cli/nova_pergunta.html', topico=topico)

            # Enum seguro
            tipo_enum = None
            try:
                tipo_enum = TipoResposta[tipo_str]
            except KeyError:
                for item in TipoResposta:
                    if item.value == tipo_str:
                         tipo_enum = item; break
                if not tipo_enum: tipo_enum = TipoResposta.SIM_NAO_NA

            ultima_ordem = db.session.query(func.max(Pergunta.ordem)).filter_by(topico_id=topico_id, ativo=True).scalar() or 0

            p = Pergunta(
                texto=texto, tipo=tipo_enum,
                obrigatoria=(request.form.get('obrigatoria') == 'on'),
                permite_observacao=(request.form.get('permite_observacao') == 'on'),
                peso=int(request.form.get('peso', 1)),
                ordem=ultima_ordem + 1,
                criterio_foto=criterio_foto,
                topico_id=topico_id, ativo=True
            )
            db.session.add(p)
            db.session.flush()

            # Opções
            if tipo_enum in [TipoResposta.MULTIPLA_ESCOLHA, TipoResposta.ESCALA_NUMERICA]:
                opcoes_texto = request.form.getlist('opcao_texto[]')
                opcoes_valor = request.form.getlist('opcao_valor[]')
                for i, txt in enumerate(opcoes_texto):
                    if txt.strip():
                        val = float(opcoes_valor[i]) if i < len(opcoes_valor) and opcoes_valor[i] else 0.0
                        db.session.add(OpcaoPergunta(
                            texto=txt.strip(), valor=val, ordem=i+1, pergunta_id=p.id, ativo=True
                        ))
            elif tipo_enum == TipoResposta.SIM_NAO_NA:
                padrao = [("Sim", 1.0, 1), ("Não", 0.0, 2), ("N.A.", 0.0, 3)]
                for txt, val, ord in padrao:
                    db.session.add(OpcaoPergunta(
                        texto=txt, valor=val, ordem=ord, pergunta_id=p.id, ativo=True
                    ))

            db.session.commit()
            flash("Pergunta criada!", "success")
            return redirect(url_for('cli.gerenciar_perguntas', topico_id=topico_id))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {str(e)}", "danger")

    return render_template_safe('cli/nova_pergunta.html', topico=topico)

@cli_bp.route('/pergunta/<int:pergunta_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_pergunta(pergunta_id):
    """Edita pergunta e suas opções."""
    pergunta = Pergunta.query.get_or_404(pergunta_id)
    if pergunta.topico.questionario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))

    if request.method == 'POST':
        try:
            pergunta.texto = request.form.get('texto', '').strip()
            tipo_str = request.form.get('tipo')
            pergunta.criterio_foto = request.form.get('criterio_foto', 'nenhuma')
            pergunta.obrigatoria = (request.form.get('obrigatoria') == 'on')
            pergunta.permite_observacao = (request.form.get('permite_observacao') == 'on')
            pergunta.peso = int(request.form.get('peso', 1))

            # Atualiza tipo
            try:
                pergunta.tipo = TipoResposta[tipo_str]
            except: pass # Se falhar, mantem o antigo

            # Atualiza opções (Complexo: Remove ausentes, Atualiza existentes, Cria novas)
            if pergunta.tipo in [TipoResposta.MULTIPLA_ESCOLHA, TipoResposta.ESCALA_NUMERICA]:
                ids_form = [int(oid) for oid in request.form.getlist('opcao_id[]') if oid.isdigit()]
                textos = request.form.getlist('opcao_texto[]')
                valores = request.form.getlist('opcao_valor[]')
                
                # Mapa atual
                opcoes_atuais = {op.id: op for op in pergunta.opcoes}
                
                # Processa form
                for i, txt in enumerate(textos):
                    if not txt.strip(): continue
                    oid = ids_form[i] if i < len(ids_form) else None
                    val = float(valores[i]) if i < len(valores) and valores[i] else 0.0
                    
                    if oid and oid in opcoes_atuais:
                        op = opcoes_atuais[oid]
                        op.texto = txt.strip()
                        op.valor = val
                        op.ordem = i + 1
                        op.ativo = True
                        del opcoes_atuais[oid] # Remove do mapa para não deletar depois
                    else:
                        db.session.add(OpcaoPergunta(
                            texto=txt.strip(), valor=val, ordem=i+1, pergunta_id=pergunta.id, ativo=True
                        ))
                
                # Deleta as que sobraram (não vieram no form)
                for op in opcoes_atuais.values():
                    db.session.delete(op)
            
            db.session.commit()
            flash("Pergunta atualizada!", "success")
            return redirect(url_for('cli.gerenciar_perguntas', topico_id=pergunta.topico_id))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro: {str(e)}", "danger")

    # Ordena opções para exibição
    opcoes_ordenadas = sorted(list(pergunta.opcoes), key=lambda o: o.ordem)
    return render_template_safe('cli/editar_pergunta.html', pergunta=pergunta, opcoes=opcoes_ordenadas)

@cli_bp.route('/pergunta/<int:pergunta_id>/remover', methods=['POST'])
@login_required
def remover_pergunta(pergunta_id):
    """Remove pergunta (soft delete)."""
    p = Pergunta.query.get_or_404(pergunta_id)
    if p.topico.questionario.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))
    
    tid = p.topico_id
    p.ativo = False
    db.session.commit()
    flash("Pergunta removida.", "success")
    return redirect(url_for('cli.gerenciar_perguntas', topico_id=tid))

# ===================== IMPORTAR / EXPORTAR =====================

@cli_bp.route('/questionario/<int:id>/exportar')
@login_required
def exportar_questionario(id):
    """Exporta para JSON."""
    q = Questionario.query.get_or_404(id)
    if q.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error")
        return redirect(url_for('cli.listar_questionarios'))

    dados = {
        'questionario': {
            'nome': q.nome, 'versao': q.versao, 'descricao': q.descricao,
            'modo': q.modo, 'calcular_nota': q.calcular_nota,
            'base_calculo': q.base_calculo, 'casas_decimais': q.casas_decimais
        },
        'topicos': []
    }
    
    for t in q.topicos:
        if t.ativo:
            t_data = {'nome': t.nome, 'descricao': t.descricao, 'ordem': t.ordem, 'perguntas': []}
            for p in t.perguntas:
                if p.ativo:
                    p_data = {
                        'texto': p.texto, 'tipo': getattr(p.tipo, 'name', str(p.tipo)),
                        'obrigatoria': p.obrigatoria, 'permite_observacao': p.permite_observacao,
                        'peso': p.peso, 'ordem': p.ordem, 'opcoes': []
                    }
                    if hasattr(p, 'opcoes'):
                        for o in p.opcoes:
                            p_data['opcoes'].append({'texto': o.texto, 'valor': o.valor, 'ordem': o.ordem})
                    t_data['perguntas'].append(p_data)
            dados['topicos'].append(t_data)

    response = make_response(json.dumps(dados, indent=2, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename="questionario_{q.id}.json"'
    return response

@cli_bp.route('/questionarios/importar', methods=['GET', 'POST'])
@login_required
def importar_questionario():
    """Importa JSON."""
    if request.method == 'POST':
        try:
            arquivo = request.files.get('arquivo')
            if not arquivo or not arquivo.filename.endswith('.json'):
                flash("Arquivo JSON inválido.", "error")
                return redirect(request.url)
            
            dados = json.load(arquivo)
            q_data = dados.get('questionario', {})
            
            nome_final = q_data.get('nome', 'Importado')
            contador = 1
            while Questionario.query.filter_by(nome=nome_final, cliente_id=current_user.cliente_id).first():
                contador += 1
                nome_final = f"{q_data.get('nome')} ({contador})"

            q = Questionario(
                nome=nome_final,
                versao=q_data.get('versao', '1.0'),
                descricao=q_data.get('descricao', ''),
                modo=q_data.get('modo', 'Avaliado'),
                cliente_id=current_user.cliente_id,
                criado_por_id=current_user.id,
                ativo=True, publicado=False, status=StatusQuestionario.RASCUNHO
            )
            db.session.add(q)
            db.session.flush()

            for t_data in dados.get('topicos', []):
                t = Topico(nome=t_data['nome'], descricao=t_data.get('descricao'), ordem=t_data.get('ordem', 1), questionario_id=q.id, ativo=True)
                db.session.add(t)
                db.session.flush()
                
                for p_data in t_data.get('perguntas', []):
                    try: tipo = TipoResposta[p_data['tipo']]
                    except: tipo = TipoResposta.SIM_NAO_NA
                    
                    p = Pergunta(
                        texto=p_data['texto'], tipo=tipo,
                        obrigatoria=p_data.get('obrigatoria', False),
                        peso=p_data.get('peso', 1), ordem=p_data.get('ordem', 1),
                        topico_id=t.id, ativo=True
                    )
                    db.session.add(p)
                    db.session.flush()

                    if 'opcoes' in p_data:
                        for o_data in p_data['opcoes']:
                            db.session.add(OpcaoPergunta(
                                texto=o_data['texto'], valor=o_data.get('valor', 0),
                                ordem=o_data.get('ordem', 1), pergunta_id=p.id, ativo=True
                            ))
            
            db.session.commit()
            flash(f"Importado como '{nome_final}'!", "success")
            return redirect(url_for('cli.visualizar_questionario', id=q.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro na importação: {str(e)}", "danger")

    return render_template_safe('cli/importar_questionario.html')
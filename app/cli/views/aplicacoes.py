# app/cli/views/aplicacoes.py
import os
import uuid
import json
import base64
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from flask import request, redirect, url_for, flash, render_template, jsonify, current_app, send_from_directory, abort
from flask_login import current_user, login_required
from sqlalchemy import func, desc, or_, extract
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

# Importa o Blueprint e CSRF
from .. import cli_bp, csrf

# Importa Utilitários
from ..utils import (
    log_acao, render_template_safe, gerar_pdf_seguro, 
    get_avaliados_usuario, verificar_permissao_admin, allowed_file
)

# === IMPORTAÇÃO DA FUNÇÃO DE CÁLCULO ===
from ...utils.pontuacao import calcular_pontuacao_auditoria

# Importa Modelos
from ...models import (
    db, Usuario, Avaliado, Questionario, Topico, Pergunta, 
    AplicacaoQuestionario, RespostaPergunta, OpcaoPergunta,
    StatusAplicacao, TipoResposta, FotoResposta, CategoriaIndicador,
    Grupo, AcaoCorretiva 
)

# ===================== LISTAGEM =====================

@cli_bp.route('/aplicacoes')
@cli_bp.route('/listar-aplicacoes')
@login_required
def listar_aplicacoes():
    """Lista aplicações com Filtro Hierárquico (Multi-GAP) e Paginação."""
    try:
        # Filtros vindos da URL
        avaliado_id = request.args.get('avaliado_id', type=int)
        questionario_id = request.args.get('questionario_id', type=int)
        status = request.args.get('status')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        page = request.args.get('page', 1, type=int)

        # Query Base (Filtra pelo Cliente do Usuário)
        query = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id
        )

        # ================= BLINDAGEM DE HIERARQUIA =================
        if current_user.avaliado_id:
            # 1. Usuário Local: Vê apenas seu Rancho
            query = query.filter(AplicacaoQuestionario.avaliado_id == current_user.avaliado_id)
            avaliado_id = current_user.avaliado_id 
            
        elif hasattr(current_user, 'grupos_acesso'):
            # 2. Lógica Multi-GAP (Gestores e Auditores)
            ids_permitidos = [g.id for g in current_user.grupos_acesso if g.ativo]
            
            # Fallback para grupo_id legado se não tiver lista de GAPs
            if not ids_permitidos and current_user.grupo_id:
                ids_permitidos = [current_user.grupo_id]
            
            if ids_permitidos:
                query = query.filter(Avaliado.grupo_id.in_(ids_permitidos))
            else:
                # Se não é Admin e não tem GAP vinculado, não vê nada
                tipo_nome = getattr(current_user.tipo, 'name', str(current_user.tipo))
                if tipo_nome not in ['SUPER_ADMIN', 'ADMIN']:
                    query = query.filter(Avaliado.id == -1) # Bloqueia tudo

        # ================= APLICA FILTROS DA TELA =================
        if avaliado_id: 
            query = query.filter(AplicacaoQuestionario.avaliado_id == avaliado_id)
        
        if questionario_id: 
            query = query.filter(AplicacaoQuestionario.questionario_id == questionario_id)
        
        if status: 
            # O PostgreSQL exige Maiúsculo (EM_ANDAMENTO)
            query = query.filter(AplicacaoQuestionario.status == status.upper())
        
        # Filtros de Data
        if data_inicio:
            try: 
                dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(AplicacaoQuestionario.data_inicio >= dt_inicio)
            except: pass
            
        if data_fim:
            try:
                # Ajusta para o final do dia (23:59:59)
                dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                query = query.filter(AplicacaoQuestionario.data_inicio <= dt_fim)
            except: pass

        # Paginação e Ordenação (Mais recentes primeiro)
        aplicacoes = query.order_by(AplicacaoQuestionario.data_inicio.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Dados para preencher os dropdowns de filtro na tela
        avaliados = get_avaliados_usuario()
        questionarios = Questionario.query.filter_by(
            cliente_id=current_user.cliente_id, 
            ativo=True
        ).order_by(Questionario.nome).all()
        
        return render_template_safe('cli/listar_aplicacoes.html',
                             aplicacoes=aplicacoes, 
                             avaliados=avaliados, 
                             questionarios=questionarios,
                             filtros={
                                 'avaliado_id': avaliado_id, 
                                 'questionario_id': questionario_id, 
                                 'status': status, 
                                 'data_inicio': data_inicio, 
                                 'data_fim': data_fim
                             })

    except Exception as e:
        print(f"Erro ao carregar lista de aplicações: {e}") # Log no terminal
        flash(f"Erro ao listar: {str(e)}", "danger")
        return render_template_safe('cli/index.html')

# ===================== CRIAÇÃO (WIZARD PASSO A PASSO) =====================

@cli_bp.route('/aplicacao/nova', methods=['GET', 'POST'])
@cli_bp.route('/nova-aplicacao', methods=['GET', 'POST'])
@login_required
def nova_aplicacao():
    return redirect(url_for('cli.selecionar_rancho_auditoria'))

@cli_bp.route('/auditoria/nova/selecao', methods=['GET', 'POST'])
@login_required
def selecionar_rancho_auditoria():
    """Passo 1: Selecionar Rancho (Com verificação Multi-GAP)."""
    if request.method == 'POST':
        rancho_id = request.form.get('avaliado_id')
        if rancho_id: 
            return redirect(url_for('cli.escolher_questionario', avaliado_id=rancho_id))
        else: 
            flash("Selecione um local.", "warning")

    try:
        # Reutiliza lógica de listar avaliados permitidos
        ranchos_disponiveis = get_avaliados_usuario()
        
        # --- BUSCAR OS GRUPOS (GAPs) ---
        grupos = []
        if current_user.tipo.name in ['SUPER_ADMIN', 'ADMIN']:
            # Admin vê todos os grupos do cliente
            grupos = Grupo.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).all()
        elif hasattr(current_user, 'grupos_acesso'):
            # Auditor/Gestor vê apenas os grupos vinculados
            grupos = [g for g in current_user.grupos_acesso if g.ativo]
        
        # Passa 'grupos' para o template preencher o primeiro select
        return render_template_safe(
            'cli/auditoria_selecao.html', 
            avaliados=ranchos_disponiveis,
            grupos=grupos 
        )
    except Exception as e:
        flash(f"Erro: {str(e)}", "danger")
        return redirect(url_for('cli.index'))

@cli_bp.route('/auditoria/passo2/<int:avaliado_id>', methods=['GET', 'POST'])
@login_required
def escolher_questionario(avaliado_id):
    """Passo 2: Escolher Questionário e Criar."""
    rancho = Avaliado.query.get_or_404(avaliado_id)
    
    if request.method == 'POST':
        qid = request.form.get('questionario_id')
        # CAPTURA A DATA MANUAL
        inicio_manual_str = request.form.get('visita_inicio')
        
        if qid:
            # BLOQUEIO DE DUPLICIDADE
            auditoria_existente = AplicacaoQuestionario.query.filter_by(
                avaliado_id=rancho.id,
                questionario_id=int(qid),
                aplicador_id=current_user.id,
                status=StatusAplicacao.EM_ANDAMENTO
            ).first()

            if auditoria_existente:
                flash(f"Você já possui uma auditoria em aberto para {rancho.nome}. Redirecionando para ela...", "info")
                return redirect(url_for('cli.responder_aplicacao', id=auditoria_existente.id))

            try:
                # Tratamento da data manual
                dt_inicio = datetime.now()
                if inicio_manual_str:
                    try:
                        dt_inicio = datetime.strptime(inicio_manual_str, '%Y-%m-%dT%H:%M')
                    except ValueError:
                        pass # Se falhar, usa now()

                nova_app = AplicacaoQuestionario(
                    aplicador_id=current_user.id, 
                    avaliado_id=rancho.id,
                    questionario_id=int(qid), 
                    
                    data_inicio=datetime.now(), # Log de sistema (quando criou no banco)
                    visita_inicio=dt_inicio,    # Dado de Negócio (quando a consultora disse que começou)
                    
                    status=StatusAplicacao.EM_ANDAMENTO 
                )
                db.session.add(nova_app)
                db.session.commit()
                flash(f"Auditoria iniciada! ID: {nova_app.id}", "success")
                return redirect(url_for('cli.responder_aplicacao', id=nova_app.id))
            except Exception as e:
                db.session.rollback()
                flash(f"Erro: {str(e)}", "danger")
        else:
            flash("Selecione um questionário.", "warning")

    questionarios = Questionario.query.filter_by(cliente_id=current_user.cliente_id, ativo=True).order_by(Questionario.nome).all()
    return render_template_safe('cli/auditoria_passo2.html', rancho=rancho, questionarios=questionarios)

# ===================== EXECUÇÃO (CHECKLIST) =====================

@cli_bp.route('/aplicacao/<int:id>/responder', methods=['GET', 'POST'])
@login_required
def responder_aplicacao(id, modo_assinatura=False):
    """
    Interface principal. Permite acesso pós-finalização APENAS para o dono (para anexar fotos).
    """
    try:
        app = AplicacaoQuestionario.query.get_or_404(id)
        if app.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "error"); return redirect(url_for('cli.listar_aplicacoes'))
        
        # Validação de Jurisdição (Auditores/Gestores)
        if current_user.tipo.name in ['AUDITOR', 'GESTOR']:
            permitidos = [r.id for r in get_avaliados_usuario()]
            if app.avaliado_id not in permitidos:
                flash("Acesso negado (Jurisdição).", "danger"); return redirect(url_for('cli.listar_aplicacoes'))

        # LÓGICA DE PERMISSÃO PÓS-FIM
        if app.status != StatusAplicacao.EM_ANDAMENTO and not modo_assinatura:
            if app.aplicador_id != current_user.id:
                 flash("Aplicação já finalizada.", "warning")
                 return redirect(url_for('cli.visualizar_aplicacao', id=id))
            # Se for o dono, deixa passar (o template deve bloquear edição de texto via JS, mas permitir upload)

        topicos = Topico.query.filter_by(questionario_id=app.questionario_id, ativo=True).order_by(Topico.ordem).all()
        perguntas_map = defaultdict(list)
        all_perguntas = Pergunta.query.join(Topico).filter(Topico.questionario_id == app.questionario_id, Topico.ativo == True, Pergunta.ativo == True).order_by(Pergunta.ordem).all()
        for p in all_perguntas: perguntas_map[p.topico_id].append(p)

        respostas = {r.pergunta_id: r for r in app.respostas}
        
        return render_template_safe('cli/responder_aplicacao.html',
                             aplicacao=app, topicos=topicos,
                             perguntas_por_topico=perguntas_map,
                             respostas_existentes=respostas,
                             modo_assinatura=modo_assinatura)
    except Exception as e:
        flash(f"Erro ao carregar: {str(e)}", "danger"); return redirect(url_for('cli.listar_aplicacoes'))

@cli_bp.route('/aplicacao/<int:id>/salvar-resposta', methods=['POST'])
@login_required
@csrf.exempt
def salvar_resposta(id):
    """
    AJAX: Salva respostas. 
    ALTERAÇÃO: Permite salvar (focando em fotos) mesmo se FINALIZADA, se for o dono.
    """
    try:
        app = AplicacaoQuestionario.query.get_or_404(id)
        if app.avaliado.cliente_id != current_user.cliente_id: return jsonify({'erro': 'Acesso negado'}), 403

        data = request.get_json() or {}
        is_closed = app.status != StatusAplicacao.EM_ANDAMENTO
        
        # PERMISSÃO ESPECIAL: Se fechado, só permite salvar se for o dono da auditoria
        if is_closed:
            if app.aplicador_id != current_user.id:
                return jsonify({'erro': 'Aplicação finalizada.'}), 400

        # Edição direta (Gestão de NCs)
        if 'resposta_id' in data:
            resp = RespostaPergunta.query.get(data['resposta_id'])
            if resp and resp.aplicacao_id == id:
                if 'plano_acao' in data: resp.plano_acao = str(data['plano_acao']).strip()
                if 'responsavel_plano_acao' in data: resp.responsavel_plano_acao = str(data['responsavel_plano_acao']).strip()
                if 'setor_atuacao' in data: resp.setor_atuacao = str(data['setor_atuacao']).strip()
                if 'causa_raiz' in data: resp.causa_raiz = str(data['causa_raiz']).strip()
                if 'prazo_plano_acao' in data:
                    try: resp.prazo_plano_acao = datetime.strptime(data['prazo_plano_acao'], '%Y-%m-%d').date()
                    except: resp.prazo_plano_acao = None
                db.session.commit()
                return jsonify({'sucesso': True})

        # Resposta do Checklist
        pid = data.get('pergunta_id')
        txt = (data.get('resposta') or '').strip()
        obs = (data.get('observacao') or '').strip()
        
        pergunta = Pergunta.query.get(pid)
        if not pergunta: return jsonify({'erro': 'Pergunta não encontrada'}), 404

        resp = RespostaPergunta.query.filter_by(aplicacao_id=id, pergunta_id=pid).first()
        if not resp: resp = RespostaPergunta(aplicacao_id=id, pergunta_id=pid)

        # Atualiza dados
        resp.resposta = txt
        resp.observacao = obs
        
        negativas = ['não', 'nao', 'no', 'irregular', 'ruim']
        resp.nao_conforme = (txt.lower() in negativas)
        if data.get('plano_acao'): resp.plano_acao = str(data.get('plano_acao')).strip()

        # Pontos (salva temporariamente, mas o total é recalculado no final)
        resp.pontos = 0
        tipo = str(getattr(pergunta.tipo, 'name', pergunta.tipo)).upper()
        
        # Ajuste simples de ponto por resposta (Lógica completa roda no 'concluir')
        if tipo in ['SIM_NAO_NA', 'MULTIPLA_ESCOLHA']:
            opcao = OpcaoPergunta.query.filter_by(pergunta_id=pid, texto=txt).first()
            if opcao and opcao.valor is not None: 
                resp.pontos = float(opcao.valor) * (pergunta.peso or 1)
        elif tipo in ['ESCALA_NUMERICA', 'NOTA']:
            try: resp.pontos = float(txt) * (pergunta.peso or 1)
            except: pass

        db.session.add(resp)
        db.session.commit()
        return jsonify({'sucesso': True, 'pontos': resp.pontos, 'resposta_id': resp.id})
    except Exception as e:
        db.session.rollback(); return jsonify({'erro': str(e)}), 500

@cli_bp.route('/aplicacao/<int:id>/concluir-coleta', methods=['POST'])
@login_required
def concluir_coleta(id):
    """
    FLUXO ÚNICO V2: Valida -> Lê Horário Manual -> Calcula -> Finaliza -> Visualiza.
    """
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id: 
        return redirect(url_for('cli.listar_aplicacoes'))
    
    # 2. Cálculo da Nota e Atualização do Banco
    resultado = calcular_pontuacao_auditoria(app)
    
    if resultado:
        app.pontos_obtidos = resultado['pontuacao_obtida']
        app.pontos_totais = resultado['pontuacao_maxima']
        app.nota_final = resultado['percentual']
    else:
        app.nota_final = 0.0

    # 3. FINALIZAÇÃO COM HORÁRIO MANUAL
    app.status = StatusAplicacao.FINALIZADA
    app.data_fim = datetime.now() # Hora que chegou no servidor
    
    # Captura o horário preenchido pela consultora
    fim_manual_str = request.form.get('visita_fim_manual')
    
    if fim_manual_str:
        try:
            app.visita_fim = datetime.strptime(fim_manual_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            app.visita_fim = datetime.now()
    else:
        app.visita_fim = datetime.now()

    # Salva observações finais se houver
    obs_finais = request.form.get('observacoes_finais')
    if obs_finais:
        app.observacoes_finais = obs_finais

    db.session.commit()
    
    # 4. Gera NCs e Redireciona
    try:
        gerar_acoes_corretivas_automatico(app.id)
    except Exception as e:
        print(f"Erro background actions: {e}")

    flash("Auditoria finalizada com sucesso!", "success")
    return redirect(url_for('cli.visualizar_aplicacao', id=id))

# ===================== FINALIZAÇÃO =====================

@cli_bp.route('/aplicacao/<int:id>/gestao-ncs', methods=['GET'])
@login_required
def gerenciar_nao_conformidades(id):
    """Tela intermediária para definir Planos de Ação."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    ncs = RespostaPergunta.query.join(Pergunta).join(Topico).filter(
        RespostaPergunta.aplicacao_id == id, RespostaPergunta.nao_conforme == True
    ).order_by(Topico.ordem, Pergunta.ordem).all()
    
    return render_template_safe('cli/definir_planos.html', aplicacao=app, ncs=ncs)

@cli_bp.route('/aplicacao/<int:id>/fase-assinatura')
@login_required
def fase_assinatura(id):
    """Reabre o checklist em modo apenas assinatura."""
    return responder_aplicacao(id, modo_assinatura=True)

@cli_bp.route('/aplicacao/<int:id>/assinar-finalizar', methods=['POST'])
@login_required
def assinar_finalizar(id):
    """
    Recebe a assinatura do form, Finaliza e Preserva o Horário Original.
    """
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger"); return redirect(url_for('cli.index'))

    b64 = request.form.get('assinatura_base64')
    nome_resp = request.form.get('nome_responsavel')
    cargo_resp = request.form.get('cargo_responsavel')
    fim_manual_iso = request.form.get('visita_fim_manual')

    # A assinatura é obrigatória na primeira vez
    if not b64 and not app.assinatura_imagem:
        flash("A assinatura é obrigatória.", "warning")
        return redirect(url_for('cli.responder_aplicacao', id=id))

    try:
        # Salva imagem se enviada
        if b64:
            if ',' in b64: b64 = b64.split(',')[1]
            fname = f"assinatura_app_{id}_{uuid.uuid4().hex[:8]}.png"
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']): os.makedirs(current_app.config['UPLOAD_FOLDER'])
            with open(path, "wb") as f: f.write(base64.b64decode(b64))
            app.assinatura_imagem = fname

        if nome_resp: app.assinatura_responsavel = nome_resp
        if cargo_resp: app.cargo_responsavel = cargo_resp
        
        # === CÁLCULO DE NOTA (GARANTIA) ===
        resultado = calcular_pontuacao_auditoria(app)
        if resultado:
            app.pontos_obtidos = resultado['pontuacao_obtida']
            app.pontos_totais = resultado['pontuacao_maxima']
            app.nota_final = resultado['percentual']
        # ==================================

        # Define como finalizada
        app.status = StatusAplicacao.FINALIZADA
        app.data_fim = datetime.now()
        
        # === PRESERVAÇÃO DE TEMPO ===
        if not app.visita_fim:
            if fim_manual_iso:
                try: app.visita_fim = datetime.fromisoformat(fim_manual_iso.replace('Z', ''))
                except: app.visita_fim = datetime.now()
            else: 
                app.visita_fim = datetime.now()
        
        db.session.commit()
        
        # Gera ações em background
        try:
            gerar_acoes_corretivas_automatico(app.id)
        except Exception as e_gen:
            print(f"Erro ao gerar ações: {e_gen}")

        log_acao(f"Finalizou app {id}", None, "Aplicacao", id)
        flash("Auditoria finalizada com sucesso!", "success")
        
        return redirect(url_for('cli.visualizar_aplicacao', id=id))

    except Exception as e:
        db.session.rollback(); current_app.logger.error(f"Erro finalizar: {e}")
        flash(f"Erro ao finalizar: {str(e)}", "danger")
        return redirect(url_for('cli.responder_aplicacao', id=id))
    
@cli_bp.route('/aplicacao/<int:id>/finalizar-definitivo', methods=['POST'])
@login_required
def finalizar_definitivamente(id):
    """Finalização sem assinatura (opcional) ou pós-revisão."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    
    # Recalcula nota
    resultado = calcular_pontuacao_auditoria(app)
    if resultado:
        app.nota_final = resultado['percentual']
        app.pontos_obtidos = resultado['pontuacao_obtida']
        app.pontos_totais = resultado['pontuacao_maxima']

    app.status = StatusAplicacao.FINALIZADA
    if not app.data_fim: app.data_fim = datetime.now()
    if request.form.get('observacoes_finais'):
        app.observacoes_finais = request.form.get('observacoes_finais')
    
    db.session.commit()
    flash("Finalizada com sucesso.", "success")
    return redirect(url_for('cli.visualizar_aplicacao', id=id))

# ===================== VISUALIZAÇÃO E RELATÓRIO =====================

@cli_bp.route('/aplicacao/<int:id>/visualizar')
@login_required
def visualizar_aplicacao(id):
    """View de somente leitura com segurança."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    
    # Segurança Hierárquica
    if app.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "error"); return redirect(url_for('cli.listar_aplicacoes'))
    
    if current_user.avaliado_id and app.avaliado_id != current_user.avaliado_id:
        flash("Acesso negado.", "danger"); return redirect(url_for('cli.listar_aplicacoes'))

    if current_user.tipo.name not in ['SUPER_ADMIN', 'ADMIN']:
         permitidos = [r.id for r in get_avaliados_usuario()]
         if app.avaliado_id not in permitidos:
             flash("Acesso negado.", "danger"); return redirect(url_for('cli.listar_aplicacoes'))

    # Carrega dados
    topicos_vis = []
    topicos_db = Topico.query.filter_by(questionario_id=app.questionario_id, ativo=True).order_by(Topico.ordem).all()
    
    respostas_dict = {r.pergunta_id: r for r in app.respostas}
    
    for t in topicos_db:
        p_ativas = Pergunta.query.filter_by(topico_id=t.id, ativo=True).order_by(Pergunta.ordem).all()
        if p_ativas:
            t.perguntas_ativas = p_ativas
            topicos_vis.append(t)

    # Stats simples
    stats = {'total_perguntas': sum(len(t.perguntas_ativas) for t in topicos_vis), 'perguntas_respondidas': len(respostas_dict)}
    
    return render_template_safe('cli/visualizar_aplicacao.html',
                         aplicacao=app, topicos=topicos_vis,
                         respostas_dict=respostas_dict, stats=stats)

@cli_bp.route('/aplicacao/<int:id>/relatorio')
@login_required
def gerar_relatorio_aplicacao(id):
    """
    Gera PDF do Relatório com suporte a MÚLTIPLAS FOTOS.
    CORREÇÃO: Implementada lógica de ignorar 'N/A' nos scores por tópico.
    """
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id: abort(403)
    
    # Prepara dados
    topicos = Topico.query.filter_by(questionario_id=app.questionario_id, ativo=True).order_by(Topico.ordem).all()
    respostas = {r.pergunta_id: r for r in app.respostas}
    
    scores = {}
    fotos = defaultdict(list)
    respostas_por_topico = defaultdict(list)
    upload_folder = current_app.config.get('UPLOAD_FOLDER')

    # Cálculos por tópico (para o gráfico de barras)
    for t in topicos:
        obtido, maximo = 0, 0
        for p in t.perguntas:
            if not p.ativo: continue
            r = respostas.get(p.id)
            if r:
                respostas_por_topico[t].append(r)
                
                # Fotos
                caminhos_imagens = []
                if r.caminho_foto: caminhos_imagens.append(r.caminho_foto)
                if hasattr(r, 'fotos'):
                    for f in r.fotos: caminhos_imagens.append(f.caminho)
                
                if caminhos_imagens and upload_folder:
                    uris_validas = []
                    for caminho in caminhos_imagens:
                        uri = None
                        p1 = Path(upload_folder) / caminho
                        p2 = Path(current_app.static_folder) / 'img' / caminho
                        if p1.exists(): uri = p1.as_uri()
                        elif p2.exists(): uri = p2.as_uri()
                        if uri: uris_validas.append(uri)
                    if uris_validas:
                        fotos[t].append({'resposta': r, 'urls': uris_validas})

                # === CORREÇÃO DA LÓGICA DE SCORE NO PDF ===
                # Verifica se é N/A para não somar no Máximo
                valor_resp = (r.resposta or "").upper().strip()
                lista_na = ['N/A', 'NA', 'N.A.', 'NÃO SE APLICA', 'NAO SE APLICA', 'NÃO APLICÁVEL', '-']
                
                if valor_resp in lista_na:
                    continue # Pula N/A (não soma na base)

                # Se não for N/A, soma na base e verifica pontos
                if p.peso:
                    maximo += p.peso
                    if valor_resp in ['SIM', 'CONFORME']:
                        obtido += p.peso
                    elif r.pontos: # Caso numérico
                        obtido += r.pontos

        percent = (obtido/maximo*100) if maximo > 0 else 0
        scores[t.id] = {
            'obtido': obtido, 
            'maximo': maximo, 
            'score_percent': round(percent, 2)
        }

    # Logo
    logo_uri = None
    try:
        lp = Path(current_app.static_folder) / 'img' / 'logo_pdf.png'
        if lp.exists(): logo_uri = lp.as_uri()
    except: pass

    # OBS: Usa app.nota_final (que agora está salva no banco) para o score global
    html = render_template_safe(
        'cli/relatorio_aplicacao.html',
        aplicacao=app, avaliador=Usuario.query.get(app.aplicador_id),
        topicos_ativos=topicos, respostas_por_topico=respostas_por_topico,
        fotos_por_topico=fotos, scores_por_topico=scores,
        nota_final=app.nota_final, logo_pdf_uri=logo_uri, data_geracao=datetime.now()
    )
    
    return gerar_pdf_seguro(html, f"Relatorio_{app.id}.pdf")

# ===================== FLUXOGRAMA E UPLOADS DA APP =====================

@cli_bp.route('/aplicacao/<int:id>/upload-fluxograma', methods=['POST'])
@login_required
def upload_fluxograma(id):
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id: return redirect(url_for('cli.listar_aplicacoes'))
    
    f = request.files.get('fluxograma')
    if f and allowed_file(f.filename, {'pdf', 'png', 'jpg', 'jpeg'}):
        fname = secure_filename(f.filename)
        ext = fname.rsplit('.', 1)[1].lower()
        novo_nome = f"fluxograma_{id}_{uuid.uuid4().hex[:8]}.{ext}"
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], novo_nome)
        f.save(path)
        app.fluxograma_arquivo = novo_nome
        db.session.commit()
        flash("Fluxograma anexado.", "success")
    else:
        flash("Arquivo inválido.", "error")
        
    return redirect(url_for('cli.visualizar_aplicacao', id=id))

@cli_bp.route('/aplicacao/<int:id>/fluxograma/visualizar')
@login_required
def visualizar_fluxograma(id):
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id: abort(403)
    if not app.fluxograma_arquivo: abort(404)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], app.fluxograma_arquivo)

@cli_bp.route('/aplicacao/<int:id>/upload-documento-mensal', methods=['POST'])
@login_required
def upload_documento_mensal(id):
    """Realiza o Upload do Relatório Mensal ou Laudo do Laboratório."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id: return redirect(url_for('cli.visualizar_aplicacao', id=id))
    
    tipo_doc = request.form.get('tipo_documento') # 'relatorio' ou 'laudo'
    f = request.files.get('documento')
    
    if f and allowed_file(f.filename, {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}):
        fname = secure_filename(f.filename)
        ext = fname.rsplit('.', 1)[1].lower()
        novo_nome = f"{tipo_doc}_{id}_{uuid.uuid4().hex[:8]}.{ext}"
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], novo_nome)
        f.save(path)
        
        if tipo_doc == 'relatorio':
            app.relatorio_mensal_arquivo = novo_nome
            flash("Relatório Mensal anexado com sucesso.", "success")
        elif tipo_doc == 'laudo':
            app.laudo_laboratorio_arquivo = novo_nome
            flash("Laudo do Laboratório anexado com sucesso.", "success")
            
        db.session.commit()
    else:
        flash("Arquivo inválido. Formatos aceitos: PDF, Imagens e Word.", "error")
        
    return redirect(url_for('cli.visualizar_aplicacao', id=id))

@cli_bp.route('/aplicacao/<int:id>/documento-mensal/<tipo>', methods=['GET'])
@login_required
def visualizar_documento_mensal(id, tipo):
    """Download/Visualização do documento mensal."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id: abort(403)
    
    arquivo = None
    if tipo == 'relatorio' and app.relatorio_mensal_arquivo:
        arquivo = app.relatorio_mensal_arquivo
    elif tipo == 'laudo' and app.laudo_laboratorio_arquivo:
        arquivo = app.laudo_laboratorio_arquivo
        
    if not arquivo: abort(404)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], arquivo)

# ===================== OPERAÇÕES DE RISCO =====================

@cli_bp.route('/aplicacao/<int:id>/reabrir', methods=['POST'])
@login_required
@csrf.exempt
def reabrir_aplicacao(id):
    try:
        app = AplicacaoQuestionario.query.get_or_404(id)
        if app.avaliado.cliente_id != current_user.cliente_id: return jsonify({'erro': 'Acesso negado'}), 403
        
        app.status = StatusAplicacao.EM_ANDAMENTO
        app.data_fim = None
        db.session.commit()
        log_acao(f"Reabriu app {id}", None, "Aplicacao", id)
        return jsonify({'sucesso': True})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/aplicacao/<int:id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir_aplicacao(id):
    """Exclui aplicação e respostas."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger"); return redirect(url_for('cli.listar_aplicacoes'))
        
    if app.status == StatusAplicacao.FINALIZADA:
        flash("Segurança: Não pode excluir auditoria finalizada.", "warning")
        return redirect(url_for('cli.listar_aplicacoes'))

    try:
        log_acao(f"Excluiu App {id}", {"avaliado": app.avaliado.nome}, "Aplicacao", id)
        RespostaPergunta.query.filter_by(aplicacao_id=id).delete()
        db.session.delete(app)
        db.session.commit()
        flash("Aplicação excluída.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {str(e)}", "danger")
        
    return redirect(url_for('cli.listar_aplicacoes'))

# ===================== FERRAMENTAS AUXILIARES E DIAGNÓSTICO =====================

@cli_bp.route('/aplicacao/<int:id>/forcar-geracao-acoes')
@login_required
def forcar_geracao_acoes(id):
    """Gera as ações corretivas manualmente para uma auditoria já finalizada."""
    if gerar_acoes_corretivas_automatico(id):
        flash("Geração forçada concluída! Verifique a lista abaixo.", "success")
    else:
        flash("Erro ao gerar ações (ou nenhuma NC encontrada).", "warning")
    
    return redirect(url_for('cli.gerenciar_acoes_corretivas', id=id))

@cli_bp.route('/aplicacao/<int:id>/forcar-analise-ncs')
@login_required
def forcar_analise_ncs(id):
    """ROTA DE DIAGNÓSTICO (RAIO-X)."""
    
    app_audit = AplicacaoQuestionario.query.get_or_404(id)
    respostas = RespostaPergunta.query.filter_by(aplicacao_id=id).all()
    
    log = []
    log.append(f"=== RAIO-X DA AUDITORIA #{id} ===")
    log.append(f"Cliente: {app_audit.avaliado.nome}")
    log.append(f"Total de Respostas: {len(respostas)}")
    log.append("-" * 30)
    
    tipos_respostas = {}
    ncs_banco = 0
    
    log.append("AMOSTRA DAS RESPOSTAS (Primeiras 20):")
    for i, r in enumerate(respostas):
        texto = r.resposta
        is_nc = r.nao_conforme
        
        if texto not in tipos_respostas: tipos_respostas[texto] = 0
        tipos_respostas[texto] += 1
        
        if is_nc: ncs_banco += 1
            
        if i < 20:
            status_banco = "[JÁ É NC]" if is_nc else "[OK]"
            log.append(f"Item {r.pergunta_id} | Resposta: '{texto}' | Banco diz: {status_banco}")

    log.append("-" * 30)
    log.append("RESUMO DOS TIPOS DE RESPOSTA ENCONTRADOS:")
    for tipo, qtd in tipos_respostas.items():
        log.append(f" -> '{tipo}': {qtd} vezes")

    log.append("-" * 30)
    log.append(f"Total marcado como NC no banco hoje: {ncs_banco}")

    return f"""<pre style="font-size: 14px; line-height: 1.5;">{chr(10).join(log)}</pre>"""

# ===================== FUNÇÃO HELPER (ESSENCIAL) =====================

def gerar_acoes_corretivas_automatico(aplicacao_id):
    """
    Sincroniza a tabela AcaoCorretiva com as Respostas:
    1. Cria ações para itens Não Conformes.
    2. Remove ações de itens que foram corrigidos para Sim/Conforme/N.A.
    """
    try:
        # Busca todas as respostas da auditoria
        todas_respostas = RespostaPergunta.query.filter_by(aplicacao_id=aplicacao_id).all()
        
        # Definição clara do que é negativo
        respostas_negativas = ['não', 'nao', 'no', 'ruim', 'irregular', 'reprovado', 'crítico']
        respostas_ignorar = ['não se aplica', 'n.a.', 'na', 'n/a', 'não avaliado']

        for resposta in todas_respostas:
            texto_resp = (resposta.resposta or '').lower().strip()
            
            # --- LÓGICA DE DETECÇÃO DE NÃO CONFORMIDADE ---
            eh_nc = False
            
            # 1. Se for explicitamente marcado como NC e NÃO for 'Não se Aplica'
            if resposta.nao_conforme and texto_resp not in respostas_ignorar:
                eh_nc = True
            
            # 2. Se o texto for negativo (safety check)
            elif texto_resp in respostas_negativas:
                eh_nc = True
                resposta.nao_conforme = True # Garante a flag
            
            # --- SINCRONIZAÇÃO (CRIAR ou REMOVER) ---
            acao_existente = AcaoCorretiva.query.filter_by(
                aplicacao_id=aplicacao_id, 
                pergunta_id=resposta.pergunta_id
            ).first()

            if eh_nc:
                # SE É NC: Cria se não existir
                if not acao_existente:
                    nova_acao = AcaoCorretiva(
                        aplicacao_id=aplicacao_id,
                        pergunta_id=resposta.pergunta_id,
                        descricao_nao_conformidade=resposta.observacao or f"Item avaliado como '{resposta.resposta}'",
                        sugestao_correcao=resposta.plano_acao,
                        status='Pendente',
                        criticidade='Média',
                        data_criacao=datetime.now()
                    )
                    db.session.add(nova_acao)
                else:
                    # FALTAVA ISSO: Atualiza a observação se a consultora tiver alterado o texto!
                    texto_atualizado = resposta.observacao or f"Item avaliado como '{resposta.resposta}'"
                    if acao_existente.descricao_nao_conformidade != texto_atualizado:
                        acao_existente.descricao_nao_conformidade = texto_atualizado
            else:
                # SE NÃO É MAIS NC (Virou Sim, N/A, etc): Remove a ação se existir
                if acao_existente:
                    db.session.delete(acao_existente)

        db.session.commit()
        return True

    except Exception as e:
        print(f"Erro ao gerar ações corretivas: {e}")
        db.session.rollback()
        return False
    
@cli_bp.route('/aplicacao/<int:id>/ajustar-horarios', methods=['GET', 'POST'])
@login_required
def ajustar_horarios(id):
    """
    Rota administrativa para corrigir horários de visita incorretos.
    """
    app = AplicacaoQuestionario.query.get_or_404(id)
    
    # 1. Segurança: Apenas Admin ou o próprio aplicador (se a regra permitir)
    # Sugestão: Restringir a Admins para evitar abusos
    if current_user.tipo.name not in ['SUPER_ADMIN', 'ADMIN']:
        flash("Apenas administradores podem corrigir horários.", "danger")
        return redirect(url_for('cli.visualizar_aplicacao', id=id))
        
    if app.avaliado.cliente_id != current_user.cliente_id:
        abort(403)

    if request.method == 'POST':
        inicio_str = request.form.get('visita_inicio')
        fim_str = request.form.get('visita_fim')
        
        try:
            # Converte as strings do input datetime-local para objetos datetime
            if inicio_str:
                app.visita_inicio = datetime.strptime(inicio_str, '%Y-%m-%dT%H:%M')
            
            if fim_str:
                app.visita_fim = datetime.strptime(fim_str, '%Y-%m-%dT%H:%M')
                
            db.session.commit()
            log_acao(f"Ajustou horários App {id}", None, "Aplicacao", id)
            flash("Horários ajustados com sucesso!", "success")
            return redirect(url_for('cli.visualizar_aplicacao', id=id))
            
        except ValueError:
            flash("Formato de data inválido.", "warning")

    return render_template_safe('cli/ajustar_horarios.html', aplicacao=app)
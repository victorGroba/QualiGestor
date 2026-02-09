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

# Importa o Blueprint e CSRF (se necessário para isentar rotas AJAX)
from .. import cli_bp, csrf

# Importa Utilitários
from ..utils import (
    log_acao, render_template_safe, gerar_pdf_seguro, 
    get_avaliados_usuario, verificar_permissao_admin, allowed_file
)

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
        
        # --- CORREÇÃO AQUI: BUSCAR OS GRUPOS (GAPs) ---
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
    
    # ... (mantenha a validação de segurança existente) ...

    if request.method == 'POST':
        qid = request.form.get('questionario_id')
        # CAPTURA A DATA MANUAL
        inicio_manual_str = request.form.get('visita_inicio')
        
        if qid:
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
    """Interface principal do Checklist."""
    try:
        app = AplicacaoQuestionario.query.get_or_404(id)
        if app.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "error")
            return redirect(url_for('cli.listar_aplicacoes'))
        
        # Validação de Permissão (Auditores só veem seus GAPs)
        if current_user.tipo.name in ['AUDITOR', 'GESTOR']:
            permitidos = [r.id for r in get_avaliados_usuario()]
            if app.avaliado_id not in permitidos:
                flash("Acesso negado (Jurisdição).", "danger")
                return redirect(url_for('cli.listar_aplicacoes'))

        if app.status != StatusAplicacao.EM_ANDAMENTO and not modo_assinatura:
            flash("Aplicação já finalizada.", "warning")
            return redirect(url_for('cli.visualizar_aplicacao', id=id))

        topicos = Topico.query.filter_by(questionario_id=app.questionario_id, ativo=True).order_by(Topico.ordem).all()
        perguntas_map = defaultdict(list)
        
        # Carregamento otimizado
        all_perguntas = Pergunta.query.join(Topico).filter(Topico.questionario_id == app.questionario_id, Topico.ativo == True, Pergunta.ativo == True).order_by(Pergunta.ordem).all()
        for p in all_perguntas:
            perguntas_map[p.topico_id].append(p)

        respostas = {r.pergunta_id: r for r in app.respostas}
        
        return render_template_safe('cli/responder_aplicacao.html',
                             aplicacao=app, topicos=topicos,
                             perguntas_por_topico=perguntas_map,
                             respostas_existentes=respostas,
                             modo_assinatura=modo_assinatura)
    except Exception as e:
        flash(f"Erro ao carregar: {str(e)}", "danger")
        return redirect(url_for('cli.listar_aplicacoes'))

@cli_bp.route('/aplicacao/<int:id>/salvar-resposta', methods=['POST'])
@login_required
@csrf.exempt
def salvar_resposta(id):
    """AJAX: Salva resposta individual e calcula nota."""
    try:
        app = AplicacaoQuestionario.query.get_or_404(id)
        if app.avaliado.cliente_id != current_user.cliente_id: return jsonify({'erro': 'Acesso negado'}), 403

        data = request.get_json() or {}
        is_closed = app.status != StatusAplicacao.EM_ANDAMENTO
        
        # Permite edição de plano de ação mesmo fechado
        if is_closed and 'plano_acao' not in data and 'resposta_id' not in data:
            return jsonify({'erro': 'Aplicação finalizada.'}), 400

        # Caso 1: Edição direta (Gestão de NCs)
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

        # Caso 2: Resposta do Checklist
        pid = data.get('pergunta_id')
        txt = (data.get('resposta') or '').strip()
        obs = (data.get('observacao') or '').strip()
        
        pergunta = Pergunta.query.get(pid)
        if not pergunta: return jsonify({'erro': 'Pergunta não encontrada'}), 404

        resp = RespostaPergunta.query.filter_by(aplicacao_id=id, pergunta_id=pid).first()
        if not resp: resp = RespostaPergunta(aplicacao_id=id, pergunta_id=pid)

        resp.resposta = txt
        resp.observacao = obs
        
        # Lógica NC Automática
        negativas = ['não', 'nao', 'no', 'irregular', 'ruim']
        resp.nao_conforme = (txt.lower() in negativas)
        
        if data.get('plano_acao'): resp.plano_acao = str(data.get('plano_acao')).strip()

        # Cálculo de Pontos
        resp.pontos = 0
        tipo = str(getattr(pergunta.tipo, 'name', pergunta.tipo)).upper()
        
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
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/aplicacao/<int:id>/concluir-coleta', methods=['POST'])
@login_required
def concluir_coleta(id):
    """Valida obrigatórias e redireciona para Gestão de NCs."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id: return redirect(url_for('cli.listar_aplicacoes'))
    
    # Validação de Obrigatórias
    perguntas_ativas = Pergunta.query.join(Topico).filter(Topico.questionario_id == app.questionario_id, Pergunta.ativo == True).all()
    respostas = {r.pergunta_id: r for r in app.respostas}
    
    pendencias = []
    sem_foto = []
    sem_obs = []
    
    for p in perguntas_ativas:
        tipo = str(getattr(p.tipo, 'name', p.tipo)).upper()
        if tipo == 'ASSINATURA': continue
        
        resp = respostas.get(p.id)
        
        # 1. Obrigatória não respondida
        if p.obrigatoria and not resp:
            pendencias.append(p.texto)
            continue
            
        if resp:
            # 2. NC sem observação
            if resp.nao_conforme and not (resp.observacao or "").strip():
                sem_obs.append(p.texto)
            
            # 3. Foto Obrigatória
            if resp.nao_conforme and getattr(p, 'criterio_foto', 'nenhuma') == 'obrigatoria':
                tem_foto = bool(resp.caminho_foto) or (hasattr(resp, 'fotos') and resp.fotos.count() > 0)
                if not tem_foto: sem_foto.append(p.texto)

    if pendencias or sem_foto or sem_obs:
        if pendencias: flash(f"Faltam {len(pendencias)} obrigatórias.", "warning")
        if sem_obs: flash(f"{len(sem_obs)} NCs exigem observação.", "warning")
        if sem_foto: flash(f"{len(sem_foto)} NCs exigem foto.", "warning")
        return redirect(url_for('cli.responder_aplicacao', id=id))

    # Cálculo Final
    pontos_totais = 0
    pontos_obtidos = 0
    for p in perguntas_ativas:
        resp = respostas.get(p.id)
        if not resp: continue
        
        # Ignora NA
        if str(resp.resposta).upper() in ['NA', 'N.A.', 'N/A']: continue
        
        peso = p.peso or 0
        pontos_totais += peso
        pontos_obtidos += (resp.pontos or 0)
        
    app.pontos_totais = pontos_totais
    app.pontos_obtidos = pontos_obtidos
    if pontos_totais > 0:
        raw_nota = (pontos_obtidos / pontos_totais) * 100
        casas = app.questionario.casas_decimais or 2
        app.nota_final = round(raw_nota, casas)
    else:
        app.nota_final = 0.0

    db.session.commit()
    flash("Coleta concluída! Revise as NCs.", "info")
    return redirect(url_for('cli.gerenciar_nao_conformidades', id=id))

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
    """Recebe assinatura e finaliza status."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    b64 = request.form.get('assinatura_base64')
    
    # NOVO: Recebe o timestamp manual do fim da visita (enviado pelo JS)
    fim_manual_iso = request.form.get('visita_fim_manual')
    
    if not b64:
        flash("Assinatura obrigatória.", "warning")
        return redirect(url_for('cli.gerenciar_nao_conformidades', id=id))

    try:
        # ... (código existente de salvar imagem) ...
        if ',' in b64: b64 = b64.split(',')[1]
        fname = f"assinatura_app_{id}_{uuid.uuid4().hex[:8]}.png"
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
        with open(path, "wb") as f: f.write(base64.b64decode(b64))
        
        app.assinatura_imagem = fname
        app.assinatura_responsavel = request.form.get('nome_responsavel')
        app.cargo_responsavel = request.form.get('cargo_responsavel')
        app.status = StatusAplicacao.FINALIZADA
        
        # LÓGICA DE FIM DA VISITA
        app.data_fim = datetime.now() # Log do sistema (upload)
        
        # Se o JS mandou a hora da assinatura, usamos ela. Se não, usa agora.
        # Importante: só atualiza visita_fim se ela ainda estiver vazia (proteção contra reabertura)
        if not app.visita_fim:
            if fim_manual_iso:
                try:
                    # O JS manda ISO string (ex: 2026-02-08T15:30:00.000Z)
                    # Cortamos os milissegundos se necessário ou usamos dateutil
                    # Maneira simples de parsear ISO do JS no Python 3.7+:
                    app.visita_fim = datetime.fromisoformat(fim_manual_iso.replace('Z', '+00:00'))
                except:
                    app.visita_fim = datetime.now()
            else:
                app.visita_fim = datetime.now()
        
        db.session.commit()
        log_acao(f"Finalizou app {id}", None, "Aplicacao", id)
        flash("Auditoria finalizada com sucesso!", "success")
        return redirect(url_for('cli.visualizar_aplicacao', id=id))
    except Exception as e:
        db.session.rollback()
       # --- ADICIONE ISTO AQUI ---
        # Gera a lista de pendências para o mês (Ações Corretivas)
        gerar_acoes_corretivas_automatico(id)
        # --------------------------

        log_acao(f"Finalizou app {id}", None, "Aplicacao", id)
        flash("Auditoria finalizada com sucesso! Ações Corretivas geradas.", "success")
        return redirect(url_for('cli.visualizar_aplicacao', id=id))

@cli_bp.route('/aplicacao/<int:id>/finalizar-definitivo', methods=['POST'])
@login_required
def finalizar_definitivamente(id):
    """Finalização sem assinatura (opcional) ou pós-revisão."""
    app = AplicacaoQuestionario.query.get_or_404(id)
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
    """Gera PDF do Relatório com suporte a MÚLTIPLAS FOTOS."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    if app.avaliado.cliente_id != current_user.cliente_id: abort(403)
    
    # Prepara dados
    topicos = Topico.query.filter_by(questionario_id=app.questionario_id, ativo=True).order_by(Topico.ordem).all()
    respostas = {r.pergunta_id: r for r in app.respostas}
    
    scores = {}
    fotos = defaultdict(list)
    respostas_por_topico = defaultdict(list)
    upload_folder = current_app.config.get('UPLOAD_FOLDER')

    # Cálculos por tópico
    for t in topicos:
        obtido, maximo = 0, 0
        for p in t.perguntas:
            if not p.ativo: continue
            r = respostas.get(p.id)
            if r:
                respostas_por_topico[t].append(r)
                
                # === CORREÇÃO 1: LÓGICA DE FOTOS MÚLTIPLAS ===
                caminhos_imagens = []
                
                # 1. Foto Legada
                if r.caminho_foto: 
                    caminhos_imagens.append(r.caminho_foto)
                
                # 2. Fotos Múltiplas (Tabela FotoResposta)
                if hasattr(r, 'fotos'):
                    for f in r.fotos:
                        caminhos_imagens.append(f.caminho)
                
                # Processa URLs
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
                        # Agora enviamos uma LISTA chamada 'urls' para bater com o HTML
                        fotos[t].append({'resposta': r, 'urls': uris_validas})

                # Score
                if str(p.tipo).upper() == 'SIM_NAO_NA' and str(r.resposta).upper() in ['NA', 'N.A.']: continue
                if p.peso:
                    maximo += p.peso
                    obtido += (r.pontos or 0)
        
        percent = (obtido/maximo*100) if maximo > 0 else 0
        
        # === CORREÇÃO 2: NOME DA CHAVE DO SCORE ===
        # Mudamos de 'percent' para 'score_percent' para bater com o HTML
        scores[t.id] = {
            'obtido': obtido, 
            'maximo': maximo, 
            'score_percent': round(percent, 2) # <--- AQUI ESTAVA O ERRO DO CRASH
        }

    # Logo
    logo_uri = None
    try:
        lp = Path(current_app.static_folder) / 'img' / 'logo_pdf.png'
        if lp.exists(): logo_uri = lp.as_uri()
    except: pass

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

# --- ROTA DE EMERGÊNCIA PARA TESTES ---
@cli_bp.route('/aplicacao/<int:id>/forcar-geracao-acoes')
@login_required
def forcar_geracao_acoes(id):
    """Gera as ações corretivas manualmente para uma auditoria já finalizada."""
    if gerar_acoes_corretivas_automatico(id):
        flash("Geração forçada concluída! Verifique a lista abaixo.", "success")
    else:
        flash("Erro ao gerar ações (ou nenhuma NC encontrada).", "warning")
    
    # Redireciona direto para a tela de ações
    return redirect(url_for('cli.gerenciar_acoes_corretivas', id=id))

# --- FUNÇÃO LOGICA (Reutilizável) ---
def gerar_acoes_corretivas_automatico(aplicacao_id):
    """Lê as respostas 'Não Conforme' e cria registros na tabela AcaoCorretiva."""
    try:
        print(f"--- Iniciando Geração para App {aplicacao_id} ---")
        
        # 1. Busca todas as respostas marcadas como 'nao_conforme' no banco
        # Importante: O script JS tem que ter marcado 'nao_conforme=True' no backend
        ncs = RespostaPergunta.query.filter_by(
            aplicacao_id=aplicacao_id, 
            nao_conforme=True
        ).all()

        print(f"Encontradas {len(ncs)} respostas com nao_conforme=True")

        contador = 0
        for resposta in ncs:
            # 2. Evita criar duplicado se você rodar 2 vezes
            existe = AcaoCorretiva.query.filter_by(
                aplicacao_id=aplicacao_id,
                pergunta_id=resposta.pergunta_id
            ).first()

            if not existe:
                # 3. Cria o registro na tabela nova
                nova_acao = AcaoCorretiva(
                    aplicacao_id=aplicacao_id,
                    pergunta_id=resposta.pergunta_id,
                    # Pega a observação que você digitou/script preencheu
                    descricao_nao_conformidade=resposta.observacao or "NC sem observação detalhada",
                    status='Pendente',
                    criticidade='Média',
                    data_criacao=datetime.now()
                )
                db.session.add(nova_acao)
                contador += 1
        
        db.session.commit()
        print(f"--- Sucesso: {contador} Ações Corretivas criadas. ---")
        return True

    except Exception as e:
        print(f"ERRO CRÍTICO AO GERAR AÇÕES: {e}")
        db.session.rollback()
        return False
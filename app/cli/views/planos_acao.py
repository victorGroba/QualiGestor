# app/cli/views/planos_acao.py
import os
import time
import json
import uuid
import base64
from datetime import datetime
from pathlib import Path

from flask import request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import google.generativeai as genai

from .. import cli_bp, csrf
from ..utils import render_template_safe, gerar_pdf_seguro, allowed_file, log_acao
from ...models import (
    db, AplicacaoQuestionario, RespostaPergunta, 
    Avaliado, Pergunta, Topico, FotoResposta, TipoResposta, AcaoCorretiva
)

# ===================== FUNÇÃO AUXILIAR BASE64 =====================
def get_base64_image(file_path):
    """Converte arquivo de imagem local para string Base64."""
    try:
        path_obj = Path(file_path)
        if not path_obj.exists(): return None
        with open(path_obj, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        ext = path_obj.suffix.lower().replace('.', '')
        if ext == 'jpg': ext = 'jpeg'
        return f"data:image/{ext};base64,{encoded_string}"
    except Exception as e:
        print(f"Erro converter img: {e}")
        return None

# ===================== ROTAS DE LISTAGEM E DETALHE (MANTIDAS) =====================
@cli_bp.route('/planos-de-acao')
@login_required
def lista_plano_acao():
    try:
        subquery = db.session.query(RespostaPergunta.aplicacao_id)\
            .filter(RespostaPergunta.plano_acao != None)\
            .filter(RespostaPergunta.plano_acao != "")\
            .distinct()
        query = AplicacaoQuestionario.query.join(Avaliado)\
            .filter(AplicacaoQuestionario.id.in_(subquery))\
            .filter(Avaliado.cliente_id == current_user.cliente_id)
        
        if current_user.avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == current_user.avaliado_id)
        elif current_user.grupo_id:
            query = query.filter(Avaliado.grupo_id == current_user.grupo_id)
        elif hasattr(current_user, 'grupos_acesso') and current_user.grupos_acesso:
            gaps_ids = [g.id for g in current_user.grupos_acesso]
            query = query.filter(Avaliado.grupo_id.in_(gaps_ids))
            
        aplicacoes_pendentes = query.order_by(AplicacaoQuestionario.data_inicio.desc()).all()
        return render_template_safe('cli/plano_acao_lista.html', aplicacoes=aplicacoes_pendentes)
    except Exception as e:
        print(f"Erro: {e}"); return redirect(url_for('cli.index'))

@cli_bp.route('/plano-de-acao/<int:aplicacao_id>')
@login_required
def detalhe_plano_acao(aplicacao_id):
    try:
        app = AplicacaoQuestionario.query.get_or_404(aplicacao_id)
        if app.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "danger"); return redirect(url_for('cli.lista_plano_acao'))
        respostas = RespostaPergunta.query.filter_by(aplicacao_id=app.id)\
            .filter(RespostaPergunta.plano_acao != None).filter(RespostaPergunta.plano_acao != "")\
            .join(Pergunta).order_by(Pergunta.ordem).all()
        return render_template_safe('cli/plano_acao_detalhe.html', app=app, respostas=respostas, datetime=datetime) 
    except Exception: return redirect(url_for('cli.lista_plano_acao'))

@cli_bp.route('/acao-corretiva/registrar/<int:resposta_id>', methods=['POST'])
@login_required
def registrar_acao_corretiva(resposta_id):
    try:
        resp = RespostaPergunta.query.get_or_404(resposta_id)
        app = AplicacaoQuestionario.query.get(resp.aplicacao_id)
        if app.avaliado.cliente_id != current_user.cliente_id: return redirect(url_for('cli.lista_plano_acao'))
        texto = request.form.get('acao_realizada')
        if texto:
            resp.acao_realizada = texto; resp.data_conclusao = datetime.now(); resp.status_acao = 'concluido'
            db.session.commit(); flash("Registrado!", "success")
        else: flash("Informe a ação.", "warning")
    except Exception as e: db.session.rollback(); flash(str(e), "danger")
    return redirect(url_for('cli.detalhe_plano_acao', aplicacao_id=resp.aplicacao_id))

@cli_bp.route('/acao-corretiva/upload-foto/<int:resposta_id>', methods=['POST'])
@login_required
@csrf.exempt 
def upload_foto_correcao(resposta_id):
    try:
        resp = RespostaPergunta.query.get_or_404(resposta_id)
        file = request.files.get('foto')
        if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg'}):
            fname = secure_filename(file.filename)
            ext = fname.rsplit('.', 1)[1].lower()
            unique_name = f"correcao_{resp.id}_{uuid.uuid4().hex[:8]}.{ext}"
            upload_path = current_app.config.get('UPLOAD_FOLDER')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
            file.save(os.path.join(upload_path, unique_name))
            nova_foto = FotoResposta(caminho=unique_name, resposta_id=resp.id, tipo='correcao')
            db.session.add(nova_foto); db.session.commit()
            return jsonify({'sucesso': True})
    except Exception as e: return jsonify({'erro': str(e)}), 500
    return jsonify({'erro': 'Erro upload'}), 400

@cli_bp.route('/api/ia/sugerir-plano', methods=['POST'])
@login_required
def sugerir_plano_acao():
    return jsonify({'erro': 'Feature IA'}), 500

# ===================== PDF DO PLANO DE AÇÃO (LÓGICA CORRIGIDA 18.1 / 18.3) =====================

@cli_bp.route('/plano-de-acao/<int:aplicacao_id>/pdf')
@login_required
def pdf_plano_acao(aplicacao_id):
    """Gera PDF com imagens Base64 e captura Nome (18.1) e Assinatura (18.3)."""
    try:
        app = AplicacaoQuestionario.query.get_or_404(aplicacao_id)
        
        if app.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))

        respostas = RespostaPergunta.query\
            .filter_by(aplicacao_id=app.id)\
            .filter(RespostaPergunta.plano_acao != None)\
            .filter(RespostaPergunta.plano_acao != "")\
            .join(Pergunta).join(Topico)\
            .order_by(Topico.ordem, Pergunta.ordem).all()
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        
        # 1. LOGO (Base64)
        logo_b64 = None
        try:
            p = Path(current_app.static_folder) / 'img' / 'logo_pdf.png'
            if p.exists(): logo_b64 = get_base64_image(p)
        except: pass

        # 2. ASSINATURA E NOME (Lógica Fixa: Tópico 18.1 e 18.3)
        assinatura_b64 = None 
        nome_responsavel_capturado = None

        # A) Busca NOME na pergunta 18.1
        resp_nome = RespostaPergunta.query\
            .join(Pergunta).join(Topico)\
            .filter(RespostaPergunta.aplicacao_id == app.id)\
            .filter(Topico.ordem == 18)\
            .filter(Pergunta.ordem == 1)\
            .first()
        
        if resp_nome and resp_nome.resposta:
            nome_responsavel_capturado = resp_nome.resposta

        # B) Busca ASSINATURA na pergunta 18.3
        resp_assinatura = RespostaPergunta.query\
            .join(Pergunta).join(Topico)\
            .filter(RespostaPergunta.aplicacao_id == app.id)\
            .filter(Topico.ordem == 18)\
            .filter(Pergunta.ordem == 3)\
            .first()
            
        if resp_assinatura and resp_assinatura.resposta:
            # Assinatura digital é salva em Base64 direto no banco ou caminho
            assinatura_b64 = resp_assinatura.resposta

        # Fallback: Se não achou na 18.3, tenta a imagem genérica do app (último recurso)
        if not assinatura_b64 and app.assinatura_imagem and upload_folder:
            try:
                p = Path(upload_folder) / app.assinatura_imagem
                if p.exists(): assinatura_b64 = get_base64_image(p)
            except: pass

        # Define qual nome usar (Prioridade para o 18.1)
        nome_final = nome_responsavel_capturado if nome_responsavel_capturado else app.assinatura_responsavel

        # 3. ITENS E FOTOS
        itens = []
        for r in respostas:
            item = {
                'topico_nome': r.pergunta.topico.nome,
                'topico_ordem': r.pergunta.topico.ordem,
                'pergunta_texto': r.pergunta.texto,
                'pergunta_ordem': r.pergunta.ordem,
                'observacao': r.observacao,
                'plano_acao': r.plano_acao,
                'prazo': r.prazo_plano_acao,
                'responsavel_plano_acao': r.responsavel_plano_acao,
                'setor_atuacao': r.setor_atuacao,
                'causa_raiz': r.causa_raiz,
                'fotos': [] 
            }
            
            def add_foto(caminho_abs):
                b64 = get_base64_image(caminho_abs)
                if b64 and b64 not in item['fotos']: item['fotos'].append(b64)

            # Fotos Legadas
            if r.caminho_foto and upload_folder:
                p1 = Path(upload_folder) / r.caminho_foto
                p2 = Path(current_app.static_folder) / 'img' / r.caminho_foto
                if p1.exists(): add_foto(p1)
                elif p2.exists(): add_foto(p2)

            # Novas Fotos
            if hasattr(r, 'fotos'):
                for foto in r.fotos:
                    if upload_folder and foto.tipo == 'evidencia':
                        p = Path(upload_folder) / foto.caminho
                        if p.exists(): add_foto(p)
            
            itens.append(item)
        
        html = render_template_safe(
            'cli/pdf_plano_acao.html',
            aplicacao=app, 
            itens=itens,
            logo_pdf_uri=logo_b64, 
            assinatura_cliente_uri=assinatura_b64,
            assinatura_responsavel=nome_final, # Nome capturado da 18.1
            cargo_responsavel=app.cargo_responsavel,
            data_geracao=datetime.now()
        )
        
        fname = f"Plano_Acao_{app.id}.pdf"
        return gerar_pdf_seguro(html, filename=fname)
        
    except Exception as e:
        current_app.logger.error(f"Erro PDF Plano: {e}")
        flash(f"Erro ao gerar PDF: {e}", "danger")
        return redirect(url_for('cli.detalhe_plano_acao', aplicacao_id=aplicacao_id))
    
# Em app/cli/views/planos_acao.py

@cli_bp.route('/aplicacao/<int:id>/acoes-corretivas', methods=['GET', 'POST'])
@login_required
def gerenciar_acoes_corretivas(id):
    """
    Painel Mensal de Ações Corretivas.
    Consultora: Preenche Sugestão (pode usar IA).
    Gestor: Preenche 'O que foi feito' e fecha a ação.
    """
    app = AplicacaoQuestionario.query.get_or_404(id)
    
    # Segurança básica (verifique se precisa de mais, igual suas outras rotas)
    if app.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.index'))

    # Processamento do Formulário (Salvar Edições)
    if request.method == 'POST':
        acao_id = request.form.get('acao_id')
        acao = AcaoCorretiva.query.get(acao_id)
        
        if acao and acao.aplicacao_id == app.id:
            # Fluxo da Consultora (Preenchendo Sugestão)
            if 'sugestao' in request.form:
                acao.sugestao_correcao = request.form.get('sugestao')
            
            # Fluxo do Gestor (Respondendo a Ação)
            if 'acao_realizada' in request.form:
                acao.acao_realizada = request.form.get('acao_realizada')
                # Se preencheu o que fez, marca como realizado
                if acao.acao_realizada:
                    acao.status = 'Realizado'
                    acao.data_conclusao = datetime.now()

            db.session.commit()
            flash("Atualizado com sucesso.", "success")
            return redirect(url_for('cli.gerenciar_acoes_corretivas', id=id))

    # Busca as ações geradas
    acoes = AcaoCorretiva.query.filter_by(aplicacao_id=id).all()

    return render_template_safe('cli/acoes_corretivas_lista.html', aplicacao=app, acoes=acoes)
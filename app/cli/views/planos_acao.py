# app/cli/views/planos_acao.py
import os
import time
import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import google.generativeai as genai

# Importa o Blueprint e CSRF
from .. import cli_bp, csrf

# Importa Utilitários
from ..utils import (
    render_template_safe, gerar_pdf_seguro, allowed_file, log_acao
)

# Importa Modelos
from ...models import (
    db, AplicacaoQuestionario, RespostaPergunta, 
    Avaliado, Pergunta, Topico, FotoResposta
)

# ===================== LISTAGEM DE PENDÊNCIAS =====================

@cli_bp.route('/planos-de-acao')
@login_required
def lista_plano_acao():
    """Lista auditorias que possuem planos de ação/NCs pendentes."""
    try:
        # Subquery: IDs de apps com plano de ação definido
        subquery = db.session.query(RespostaPergunta.aplicacao_id)\
            .filter(RespostaPergunta.plano_acao != None)\
            .filter(RespostaPergunta.plano_acao != "")\
            .distinct()

        query = AplicacaoQuestionario.query\
            .join(Avaliado)\
            .filter(AplicacaoQuestionario.id.in_(subquery))\
            .filter(Avaliado.cliente_id == current_user.cliente_id)

        # Filtros de Hierarquia
        if current_user.avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == current_user.avaliado_id)
        elif current_user.grupo_id:
            query = query.filter(Avaliado.grupo_id == current_user.grupo_id)
        elif hasattr(current_user, 'grupos_acesso') and current_user.grupos_acesso:
            # Lógica Multi-GAP
            gaps_ids = [g.id for g in current_user.grupos_acesso]
            query = query.filter(Avaliado.grupo_id.in_(gaps_ids))

        aplicacoes_pendentes = query.order_by(AplicacaoQuestionario.data_inicio.desc()).all()

        return render_template_safe('cli/plano_acao_lista.html', aplicacoes=aplicacoes_pendentes)
    except Exception as e:
        print(f"Erro Plano Lista: {e}")
        return redirect(url_for('cli.index'))

@cli_bp.route('/plano-de-acao/<int:aplicacao_id>')
@login_required
def detalhe_plano_acao(aplicacao_id):
    """Exibe os detalhes das pendências de UMA aplicação."""
    try:
        app = AplicacaoQuestionario.query.get_or_404(aplicacao_id)
        
        # Segurança
        if app.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))

        # Permissão Hierárquica
        if current_user.avaliado_id and app.avaliado_id != current_user.avaliado_id:
            flash("Permissão negada.", "danger"); return redirect(url_for('cli.lista_plano_acao'))
        
        # Busca respostas com plano de ação
        respostas = RespostaPergunta.query\
            .filter_by(aplicacao_id=app.id)\
            .filter(RespostaPergunta.plano_acao != None)\
            .filter(RespostaPergunta.plano_acao != "")\
            .join(Pergunta).order_by(Pergunta.ordem).all()

        return render_template_safe('cli/plano_acao_detalhe.html', 
                               app=app, respostas=respostas, datetime=datetime) 
    except Exception as e:
        print(f"Erro Plano Detalhe: {e}")
        return redirect(url_for('cli.lista_plano_acao'))

# ===================== REGISTRO DE CORREÇÃO (OM) =====================

@cli_bp.route('/acao-corretiva/registrar/<int:resposta_id>', methods=['POST'])
@login_required
def registrar_acao_corretiva(resposta_id):
    """Salva o texto da ação corretiva realizada."""
    try:
        resp = RespostaPergunta.query.get_or_404(resposta_id)
        app = AplicacaoQuestionario.query.get(resp.aplicacao_id)
        
        if app.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "danger")
            return redirect(url_for('cli.lista_plano_acao'))
            
        texto = request.form.get('acao_realizada')
        if texto:
            resp.acao_realizada = texto
            resp.data_conclusao = datetime.now()
            resp.status_acao = 'concluido'
            db.session.commit()
            flash("Ação corretiva registrada!", "success")
        else:
            flash("Descreva a ação realizada.", "warning")

    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {str(e)}", "danger")
        
    return redirect(url_for('cli.detalhe_plano_acao', aplicacao_id=resp.aplicacao_id))

@cli_bp.route('/acao-corretiva/upload-foto/<int:resposta_id>', methods=['POST'])
@login_required
@csrf.exempt 
def upload_foto_correcao(resposta_id):
    """Upload de foto de evidência da correção (Depois)."""
    try:
        resp = RespostaPergunta.query.get_or_404(resposta_id)
        app = AplicacaoQuestionario.query.get(resp.aplicacao_id)
        if app.avaliado.cliente_id != current_user.cliente_id: return jsonify({'erro': 'Acesso negado'}), 403
        
        file = request.files.get('foto')
        if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg'}):
            fname = secure_filename(file.filename)
            ext = fname.rsplit('.', 1)[1].lower()
            unique_name = f"correcao_{resp.id}_{uuid.uuid4().hex[:8]}.{ext}"
            
            upload_path = current_app.config.get('UPLOAD_FOLDER')
            if not os.path.exists(upload_path): os.makedirs(upload_path)
                
            file.save(os.path.join(upload_path, unique_name))
            
            # Salva na tabela FotoResposta com tipo 'correcao'
            nova_foto = FotoResposta(
                caminho=unique_name, resposta_id=resp.id, tipo='correcao'
            )
            db.session.add(nova_foto)
            db.session.commit()
            return jsonify({'sucesso': True})
            
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    
    return jsonify({'erro': 'Erro no upload'}), 400

# ===================== INTEGRAÇÃO IA (GEMINI) =====================

@cli_bp.route('/api/ia/sugerir-plano', methods=['POST'])
@login_required
def sugerir_plano_acao():
    """Gera sugestão de correção com Retry para erro 429."""
    try:
        data = request.get_json()
        if not data.get('pergunta'): return jsonify({'erro': 'Dados insuficientes'}), 400

        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key: return jsonify({'erro': 'IA não configurada'}), 500
            
        genai.configure(api_key=api_key)
        
        prompt = f"""
        Você é um Auditor Especialista em Segurança de Alimentos.
        Analise a Não Conformidade:
        - REQUISITO: "{data.get('pergunta')}"
        - OBSERVAÇÃO: "{data.get('observacao')}"

        CONSULTE: Portaria SVS/MS 326/1997, CVS-5/2013, RDC 275/2002, RDC 216/2004.
        
        RETORNE JSON:
        {{
            "justificativa": "Frase técnica curta citando a norma.",
            "acao": "Ação corretiva direta e imperativa."
        }}
        """
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = None
        
        # Retry Logic
        for tentativa in range(3):
            try:
                response = model.generate_content(prompt)
                break
            except Exception as e:
                if "429" in str(e) or "Resource exhausted" in str(e):
                    time.sleep(2)
                else:
                    raise e

        if not response:
            return jsonify({'sucesso': False, 'erro': "IA ocupada. Tente novamente."}), 429

        texto_limpo = response.text.replace("```json", "").replace("```", "").strip()
        resultado = json.loads(texto_limpo)
        
        return jsonify({
            'sucesso': True, 
            'causa': resultado.get('justificativa', ''),
            'plano': resultado.get('acao', '')
        })

    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

# ===================== PDF DO PLANO DE AÇÃO =====================

@cli_bp.route('/plano-de-acao/<int:aplicacao_id>/pdf')
@login_required
def pdf_plano_acao(aplicacao_id):
    """Gera PDF específico do Plano de Ação (Layout Horizontal)."""
    try:
        app = AplicacaoQuestionario.query.get_or_404(aplicacao_id)
        if app.avaliado.cliente_id != current_user.cliente_id:
            flash("Acesso negado.", "danger"); return redirect(url_for('cli.lista_plano_acao'))

        # Itens com plano
        respostas = RespostaPergunta.query\
            .filter_by(aplicacao_id=app.id)\
            .filter(RespostaPergunta.plano_acao != None)\
            .filter(RespostaPergunta.plano_acao != "")\
            .join(Pergunta).join(Topico)\
            .order_by(Topico.ordem, Pergunta.ordem).all()
        
        # Preparação de imagens
        logo_uri = None
        assinatura_uri = None
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        
        try:
            p = Path(current_app.static_folder) / 'img' / 'logo_pdf.png'
            if p.exists(): logo_uri = p.as_uri()
        except: pass

        if app.assinatura_imagem and upload_folder:
            try:
                p = Path(upload_folder) / app.assinatura_imagem
                if p.exists(): assinatura_uri = p.as_uri()
            except: pass

        # Estrutura de dados para o template
        itens = []
        for r in respostas:
            item = {
                'topico_nome': r.pergunta.topico.nome,
                'pergunta_texto': r.pergunta.texto,
                'observacao': r.observacao,
                'plano_acao': r.plano_acao,
                'prazo': r.prazo_plano_acao,
                'responsavel': getattr(r, 'responsavel_plano_acao', None),
                'setor': getattr(r, 'setor_atuacao', None),
                'causa': getattr(r, 'causa_raiz', None),
                'foto_uri': None
            }
            
            # Foto da NC
            if r.caminho_foto and upload_folder:
                try:
                    p1 = Path(upload_folder) / r.caminho_foto
                    p2 = Path(current_app.static_folder) / 'img' / r.caminho_foto
                    if p1.exists(): item['foto_uri'] = p1.as_uri()
                    elif p2.exists(): item['foto_uri'] = p2.as_uri()
                except: pass
            
            itens.append(item)
        
        html = render_template_safe(
            'cli/pdf_plano_acao.html',
            aplicacao=app, itens=itens,
            logo_pdf_uri=logo_uri, assinatura_cliente_uri=assinatura_uri,
            assinatura_responsavel=app.assinatura_responsavel,
            cargo_responsavel=app.cargo_responsavel,
            data_geracao=datetime.now()
        )
        
        fname = f"Plano_Acao_{app.id}.pdf"
        return gerar_pdf_seguro(html, filename=fname)
        
    except Exception as e:
        current_app.logger.error(f"Erro PDF Plano: {e}")
        flash("Erro ao gerar PDF.", "danger")
        return redirect(url_for('cli.detalhe_plano_acao', aplicacao_id=aplicacao_id))
# app/cli/views/planos_acao.py
import os
import time
import json
import uuid
import base64
from datetime import datetime
from pathlib import Path

from flask import request, redirect, url_for, flash, jsonify, current_app
from flask import render_template
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
    Exibe e gerencia as ações corretivas (Tabela Nova).
    """
    app_audit = AplicacaoQuestionario.query.get_or_404(id)
    
    # Segurança
    if app_audit.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.index'))

    # Lógica de POST (Salvar) - Já tínhamos feito, mas aqui está completa
    if request.method == 'POST':
        acao_id = request.form.get('acao_id')
        acao = AcaoCorretiva.query.get(acao_id)
        
        if acao and acao.aplicacao_id == app_audit.id:
            salvou = False
            
            # 1. Salva Criticidade
            if 'criticidade' in request.form:
                acao.criticidade = request.form.get('criticidade')
                salvou = True

            # 2. Salva Sugestão (Consultora)
            if 'sugestao' in request.form:
                acao.sugestao_correcao = request.form.get('sugestao')
                salvou = True
            
            # 3. Salva Execução (Gestor)
            if 'acao_realizada' in request.form:
                acao.acao_realizada = request.form.get('acao_realizada')
                if acao.acao_realizada:
                    acao.status = 'Realizado'
                    acao.data_conclusao = datetime.now()
                salvou = True

            # Sincronização com Relatório Antigo
            if salvou:
                resp_antiga = RespostaPergunta.query.filter_by(
                    aplicacao_id=app_audit.id, 
                    pergunta_id=acao.pergunta_id
                ).first()
                if resp_antiga:
                    texto = acao.acao_realizada if acao.acao_realizada else acao.sugestao_correcao
                    if texto: 
                        resp_antiga.plano_acao = texto
                        if acao.status == 'Realizado':
                            resp_antiga.status_acao = 'concluido'

            db.session.commit()
            flash("Ação atualizada com sucesso.", "success")
            return redirect(url_for('cli.gerenciar_acoes_corretivas', id=id))

    # --- PARTE IMPORTANTE (GET) ---
    # Busca as ações na tabela NOVA para enviar ao template
    acoes_lista = AcaoCorretiva.query.filter_by(aplicacao_id=id).all()
    
    return render_template(
        'cli/acoes_corretivas_lista.html',
        aplicacao=app_audit,
        acoes=acoes_lista  # <--- O template espera esta variável 'acoes'
    )
# Em app/cli/views/planos_acao.py

@cli_bp.route('/api/ia/sugerir-correcao', methods=['POST'])
@login_required
def sugerir_correcao_ia():
    """Rota AJAX para consultar o Gemini com Contexto Rico e Criticidade"""
    data = request.get_json()
    
    # 1. Extração Segura dos Dados
    item_avaliado = data.get('item_avaliado') or "Item de Checklist"
    observacao_auditor = data.get('observacao') or data.get('problema')
    
    if not observacao_auditor:
        return jsonify({'erro': 'Problema/Observação não informada.'}), 400

    try:
        # 2. Configuração da API Key
        api_key = current_app.config.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        if not api_key:
            return jsonify({'erro': 'Chave da API Google não configurada no servidor.'}), 500
            
        genai.configure(api_key=api_key)
        
        # 3. Definição do Modelo (Use gemini-1.5-flash para velocidade e precisão)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 4. Prompt Otimizado
        prompt = f"""
        Atue como um consultor sênior em Segurança dos Alimentos.
        
        CONTEXTO:
        - Item Avaliado: "{item_avaliado}"
        - Não Conformidade Encontrada: "{observacao_auditor}"

        TAREFA:
        1. Classifique a criticidade deste problema em: Alta, Média ou Baixa.
        2. Elabore uma Ação Corretiva técnica, direta e prática (máximo 3 linhas).

        FORMATO DE RESPOSTA OBRIGATÓRIO:
        CRITICIDADE: [Alta/Média/Baixa]
        ACAO: [Texto da ação corretiva]
        """
        
        # 5. Geração
        response = model.generate_content(prompt)
        
        if response.text:
            texto_bruto = response.text.strip()
            
            # 6. Processamento da Resposta (Separa Ação de Criticidade)
            sugestao_final = texto_bruto
            criticidade_final = "Média" # Valor padrão de segurança
            
            # Tenta fazer o parse se o formato vier correto
            if "CRITICIDADE:" in texto_bruto and "ACAO:" in texto_bruto:
                try:
                    partes = texto_bruto.split("ACAO:")
                    parte_crit = partes[0].replace("CRITICIDADE:", "").strip()
                    parte_acao = partes[1].strip()
                    
                    sugestao_final = parte_acao
                    
                    # Normaliza a criticidade
                    if "Alta" in parte_crit: criticidade_final = "Alta"
                    elif "Baixa" in parte_crit: criticidade_final = "Baixa"
                    else: criticidade_final = "Média"
                except:
                    # Se falhar o split, manda tudo como texto
                    pass

            return jsonify({
                'sugestao': sugestao_final,
                'criticidade': criticidade_final
            })
            
        else:
            return jsonify({'erro': 'IA não retornou texto.'}), 500

    except Exception as e:
        print(f"Erro IA: {e}")
        return jsonify({'erro': f"Falha na IA: {str(e)}"}), 500
    
@cli_bp.route('/aplicacao/<int:id>/pdf-acoes-corretivas')
@login_required
def pdf_acoes_corretivas(id):
    """Gera PDF exclusivo das Ações Corretivas (Vertical, Layout Limpo)."""
    app = AplicacaoQuestionario.query.get_or_404(id)
    
    if app.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.index'))

    # Busca as ações com as perguntas relacionadas para pegar fotos
    acoes = AcaoCorretiva.query.filter_by(aplicacao_id=id).all()
    
    # Prepara estrutura de dados enriquecida para o template
    itens_relatorio = []
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    
    for acao in acoes:
        # Busca a resposta original para pegar as fotos
        resposta = RespostaPergunta.query.filter_by(
            aplicacao_id=app.id, 
            pergunta_id=acao.pergunta_id
        ).first()
        
        fotos_b64 = []
        if resposta:
            # Função auxiliar para pegar B64 (reutiliza a que já existe no arquivo ou cria local)
            def get_img(path_abs):
                try:
                    with open(path_abs, "rb") as image_file:
                        encoded = base64.b64encode(image_file.read()).decode('utf-8')
                        return f"data:image/jpeg;base64,{encoded}"
                except: return None

            # Fotos Novas
            for foto in resposta.fotos:
                p = os.path.join(upload_folder, foto.caminho)
                b64 = get_img(p)
                if b64: fotos_b64.append(b64)
            
            # Foto Legado
            if resposta.caminho_foto:
                p = os.path.join(current_app.static_folder, 'img', resposta.caminho_foto) # ou upload dependendo da versão
                b64 = get_img(p)
                if b64: fotos_b64.append(b64)

        itens_relatorio.append({
            'topico': acao.pergunta.topico.nome,
            'pergunta': acao.pergunta.texto,
            'problema': acao.descricao_nao_conformidade,
            'solucao': acao.acao_realizada if acao.acao_realizada else acao.sugestao_correcao,
            'criticidade': acao.criticidade,
            'status': acao.status,
            'fotos': fotos_b64
        })

    # Logo em B64 para o PDF
    logo_b64 = None
    try:
        p_logo = os.path.join(current_app.static_folder, 'img', 'logo_pdf.png')
        if os.path.exists(p_logo):
            with open(p_logo, "rb") as f:
                logo_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    except: pass

    html = render_template_safe(
        'cli/pdf_acoes_corretivas.html',
        aplicacao=app,
        itens=itens_relatorio,
        logo_pdf=logo_b64,
        data_geracao=datetime.now()
    )
    
    return gerar_pdf_seguro(html, filename=f"Acoes_Corretivas_{id}.pdf")
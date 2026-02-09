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

# ===================== ROTAS DE LISTAGEM E DETALHE (LEGADO) =====================
# Estas rotas mantêm a compatibilidade com o sistema antigo de planos de ação

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

# ===================== PDF DO PLANO DE AÇÃO (LEGADO) =====================

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

        # 2. ASSINATURA E NOME
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
            assinatura_b64 = resp_assinatura.resposta

        # Fallback: Se não achou na 18.3, tenta a imagem genérica do app
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
            assinatura_responsavel=nome_final, 
            cargo_responsavel=app.cargo_responsavel,
            data_geracao=datetime.now()
        )
        
        fname = f"Plano_Acao_{app.id}.pdf"
        return gerar_pdf_seguro(html, filename=fname)
        
    except Exception as e:
        current_app.logger.error(f"Erro PDF Plano: {e}")
        flash(f"Erro ao gerar PDF: {e}", "danger")
        return redirect(url_for('cli.detalhe_plano_acao', aplicacao_id=aplicacao_id))

# ===================== NOVA GESTÃO DE AÇÕES CORRETIVAS =====================

@cli_bp.route('/aplicacao/<int:id>/acoes-corretivas', methods=['GET', 'POST'])
@login_required
def gerenciar_acoes_corretivas(id):
    """
    Exibe e gerencia as ações corretivas (Tabela Nova).
    Inclui Sincronização Robusta: Garante que TODAS as NCs apareçam aqui.
    """
    app_audit = AplicacaoQuestionario.query.get_or_404(id)
    
    if app_audit.avaliado.cliente_id != current_user.cliente_id:
        flash("Acesso negado.", "danger")
        return redirect(url_for('cli.index'))

    # === SINCRONIZAÇÃO ROBUSTA ===
    # 1. Busca TODAS as respostas dessa auditoria
    todas_respostas = RespostaPergunta.query.filter_by(aplicacao_id=id).all()
    
    migrou_algo = False
    
    for resp in todas_respostas:
        # Verifica se é NC (pela flag ou pelo texto negativo)
        eh_nc = resp.nao_conforme
        if not eh_nc and resp.resposta:
            if resp.resposta.lower().strip() in ['não', 'nao', 'ruim', 'irregular', 'não conforme']:
                eh_nc = True
        
        # Se for NC, verifica se já existe na tabela nova
        if eh_nc:
            existe = AcaoCorretiva.query.filter_by(
                aplicacao_id=id,
                pergunta_id=resp.pergunta_id
            ).first()
            
            if not existe:
                # Cria a ação que estava faltando
                nova_acao = AcaoCorretiva(
                    aplicacao_id=app_audit.id,
                    pergunta_id=resp.pergunta_id,
                    # Se não tiver observação, coloca um texto padrão para não ficar vazio
                    descricao_nao_conformidade=resp.observacao or f"Item marcado como {resp.resposta}",
                    sugestao_correcao=resp.plano_acao, # Traz o plano antigo se houver
                    criticidade="Média",
                    status='Pendente',
                    data_criacao=datetime.now()
                )
                
                # Se já tinha sido concluído no sistema antigo, atualiza o status
                if resp.status_acao == 'concluido' or (resp.plano_acao and resp.plano_acao.strip() != ''):
                     nova_acao.status = 'Realizado'
                     if not nova_acao.acao_realizada:
                         nova_acao.acao_realizada = resp.plano_acao

                db.session.add(nova_acao)
                migrou_algo = True
    
    if migrou_algo:
        db.session.commit()
    # =========================================

    # Lógica de POST (Salvar)
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

            # Retro-compatibilidade (Manter tabela antiga atualizada também)
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

    # Busca as ações (agora populadas pela migração se fosse necessário)
    acoes_lista = AcaoCorretiva.query.filter_by(aplicacao_id=id).all()
    
    return render_template(
        'cli/acoes_corretivas_lista.html',
        aplicacao=app_audit,
        acoes=acoes_lista 
    )

@cli_bp.route('/api/ia/sugerir-correcao', methods=['POST'])
@login_required
def sugerir_correcao_ia():
    """Rota AJAX para consultar o Gemini com Lista de Compatibilidade Atualizada (v2.0+)"""
    data = request.get_json()
    
    item_avaliado = data.get('item_avaliado') or "Item de Checklist"
    observacao_auditor = data.get('observacao') or data.get('problema')
    
    if not observacao_auditor:
        return jsonify({'erro': 'Problema/Observação não informada.'}), 400

    try:
        api_key = current_app.config.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return jsonify({'erro': 'Chave da API Google não configurada.'}), 500
            
        genai.configure(api_key=api_key)
        
        prompt = f"""
        Atue como um consultor sênior em Segurança dos Alimentos.
        CONTEXTO:
        - Item Avaliado: "{item_avaliado}"
        - Não Conformidade Encontrada: "{observacao_auditor}"
        TAREFA:
        1. Classifique a criticidade (Alta/Média/Baixa).
        2. Ação Corretiva prática (máx 3 linhas).
        FORMATO:
        CRITICIDADE: [Grau]
        ACAO: [Texto]
        """

        # === LISTA ATUALIZADA COM O SEU LOG ===
        # Prioriza os modelos que apareceram no seu diagnóstico
        modelos_para_tentar = [
            'gemini-2.5-flash',       # Mais novo e rápido
            'gemini-2.0-flash',       # Versão estável anterior
            'gemini-flash-latest',    # Alias genérico
            'gemini-2.5-pro',         # Mais inteligente
            'models/gemini-2.5-flash', # Formato alternativo
            'gemini-1.5-flash',       # Fallback antigo
            'gemini-pro'              # Fallback clássico
        ]
        
        texto_gerado = None
        erro_ultimo = None

        for modelo_nome in modelos_para_tentar:
            try:
                model = genai.GenerativeModel(modelo_nome)
                response = model.generate_content(prompt)
                if response and response.text:
                    texto_gerado = response.text
                    print(f"Sucesso com o modelo: {modelo_nome}") # Log no terminal
                    break 
            except Exception as e:
                erro_ultimo = e
                # print(f"Falha com {modelo_nome}: {e}")
                continue

        if not texto_gerado:
            raise Exception(f"Nenhum modelo compatível. Tentei: {modelos_para_tentar}. Erro: {erro_ultimo}")
        
        # Processamento da resposta
        texto_bruto = texto_gerado.strip()
        sugestao_final = texto_bruto
        criticidade_final = "Média"
        
        if "CRITICIDADE:" in texto_bruto and "ACAO:" in texto_bruto:
            try:
                partes = texto_bruto.split("ACAO:")
                parte_crit = partes[0].replace("CRITICIDADE:", "").strip()
                sugestao_final = partes[1].strip()
                
                if "Alta" in parte_crit: criticidade_final = "Alta"
                elif "Baixa" in parte_crit: criticidade_final = "Baixa"
            except: pass

        return jsonify({
            'sugestao': sugestao_final,
            'criticidade': criticidade_final
        })

    except Exception as e:
        print(f"Erro IA Crítico: {e}")
        return jsonify({'erro': f"Falha na IA: {str(e)}"}), 500
    
@cli_bp.route('/aplicacao/<int:id>/pdf-acoes-corretivas')
@login_required
def pdf_acoes_corretivas(id):
    """Gera PDF exclusivo das Ações Corretivas (Vertical, Layout Limpo) SEM DUPLICAR FOTOS."""
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
        fotos_nomes_processados = set() # SET para evitar duplicatas
        
        if resposta:
            # Função auxiliar para pegar B64
            def get_img(path_abs):
                try:
                    with open(path_abs, "rb") as image_file:
                        encoded = base64.b64encode(image_file.read()).decode('utf-8')
                        return f"data:image/jpeg;base64,{encoded}"
                except: return None

            # 1. Fotos Novas (Tabela FotoResposta)
            if hasattr(resposta, 'fotos'):
                for foto in resposta.fotos:
                    if foto.caminho not in fotos_nomes_processados:
                        p = os.path.join(upload_folder, foto.caminho)
                        b64 = get_img(p)
                        if b64: 
                            fotos_b64.append(b64)
                            fotos_nomes_processados.add(foto.caminho)
            
            # 2. Foto Legado (Coluna caminho_foto)
            if resposta.caminho_foto:
                # Verifica se este arquivo JÁ NÃO FOI processado acima
                if resposta.caminho_foto not in fotos_nomes_processados:
                    p = os.path.join(current_app.static_folder, 'img', resposta.caminho_foto)
                    
                    # Tenta no upload folder também se não achar no static
                    if not os.path.exists(p) and upload_folder:
                        p = os.path.join(upload_folder, resposta.caminho_foto)
                        
                    b64 = get_img(p)
                    if b64: 
                        fotos_b64.append(b64)
                        fotos_nomes_processados.add(resposta.caminho_foto)

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
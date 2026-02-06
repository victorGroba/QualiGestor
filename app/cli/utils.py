# app/cli/utils.py
import json
import os
from functools import wraps
from flask import current_app, request, redirect, url_for, flash, render_template, make_response
from flask_login import current_user
from datetime import datetime, timedelta

# Tenta importar WeasyPrint para PDF
try:
    from weasyprint import HTML
except ImportError:
    HTML = None

# Imports de modelos com tratamento de erro
try:
    from ..models import (
        db, Avaliado, LogAuditoria, Notificacao, 
        RespostaPergunta, AplicacaoQuestionario, StatusAplicacao
    )
except ImportError:
    db = None
    Avaliado = None
    LogAuditoria = None
    Notificacao = None

# ==================== DECORATORS E PERMISSÕES ====================

def admin_required(f):
    """Decorator para exigir permissões de administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Acesso negado. Faça login primeiro.', 'error')
            return redirect(url_for('auth.login'))
        
        if not verificar_permissao_admin():
            flash('Acesso restrito a administradores.', 'error')
            return redirect(url_for('cli.index'))
            
        return f(*args, **kwargs)
    return decorated_function

def verificar_permissao_admin():
    """Retorna True se usuário for ADMIN ou SUPER_ADMIN."""
    if not current_user.is_authenticated:
        return False
    try:
        user_type = getattr(current_user, 'tipo', 'USUARIO')
        # Normalização robusta de Enum/String
        if hasattr(user_type, 'name'): 
            type_name = user_type.name.upper()
        elif hasattr(user_type, 'value'): 
            type_name = str(user_type.value).upper()
        else:
            type_name = str(user_type).upper()
            
        return type_name in ['ADMIN', 'SUPER_ADMIN']
    except:
        return False

# ==================== LOGS E AUDITORIA ====================

def log_acao(acao, detalhes=None, entidade_tipo=None, entidade_id=None):
    """Registra ação no log."""
    try:
        if detalhes is None:
            detalhes_str = None
        elif isinstance(detalhes, (dict, list)):
            detalhes_str = json.dumps(detalhes, ensure_ascii=False)
        else:
            detalhes_str = str(detalhes)

        log = LogAuditoria(
            acao=acao,
            detalhes=detalhes_str,
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            ip=(request.remote_addr if request else None),
            user_agent=(request.headers.get('User-Agent') if request else None),
            usuario_id=getattr(current_user, 'id', None),
            cliente_id=getattr(current_user, 'cliente_id', None),
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar log: {e}")

def registrar_log(acao, detalhes=None, entidade_tipo=None, entidade_id=None):
    return log_acao(acao, detalhes, entidade_tipo, entidade_id)

def criar_notificacao(usuario_id, titulo, mensagem, tipo='info', link=None):
    try:
        if Notificacao:
            notificacao = Notificacao(
                usuario_id=usuario_id, titulo=titulo, mensagem=mensagem, tipo=tipo, link=link
            )
            db.session.add(notificacao)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")

# ==================== UTILITÁRIOS DE DADOS (CORRIGIDO) ====================

def get_avaliados_usuario():
    """
    Retorna a lista de Ranchos (Avaliados) disponíveis.
    [DEBUG ATIVADO] - Verifique o terminal se a lista vier vazia.
    """
    try:
        # 1. Normalização do Tipo de Usuário
        user_type = getattr(current_user, 'tipo', 'USUARIO')
        if hasattr(user_type, 'name'): type_name = user_type.name.upper()
        elif hasattr(user_type, 'value'): type_name = str(user_type.value).upper()
        else: type_name = str(user_type).upper()

        print(f"--- DEBUG AVALIADOS ---")
        print(f"Usuário: {current_user.id} | Tipo Identificado: {type_name}")

        # 2. Lógica Hierárquica
        
        # A) ADMIN vê TUDO do Cliente
        if type_name in ['SUPER_ADMIN', 'ADMIN']:
            print(">> Acesso ADMIN: Buscando todos do cliente.")
            return Avaliado.query.filter_by(
                cliente_id=current_user.cliente_id, 
                ativo=True
            ).order_by(Avaliado.nome).all()
        
        # B) GESTOR/AUDITOR (Multi-GAP)
        elif type_name in ['GESTOR', 'AUDITOR']:
            # Pega lista de grupos da nova relação N:N
            gaps_ids = [g.id for g in current_user.grupos_acesso]
            print(f">> Grupos (Nova Tabela): {gaps_ids}")
            
            # Fallback para sistema antigo (se a lista nova estiver vazia)
            if not gaps_ids and current_user.grupo_id:
                gaps_ids = [current_user.grupo_id]
                print(f">> Fallback Grupo Antigo: {gaps_ids}")

            if gaps_ids:
                # Busca Avaliados que pertencem a esses grupos
                resultado = Avaliado.query.filter(
                    Avaliado.cliente_id == current_user.cliente_id,
                    Avaliado.grupo_id.in_(gaps_ids),
                    Avaliado.ativo == True
                ).order_by(Avaliado.nome).all()
                print(f">> Avaliados Encontrados: {len(resultado)}")
                return resultado
            else:
                print(">> ERRO: Usuário GESTOR/AUDITOR sem nenhum grupo vinculado!")
                return []
            
        # C) USUARIO Local (Vê apenas seu Rancho)
        elif current_user.avaliado_id:
            print(f">> Usuário Local. Avaliado ID: {current_user.avaliado_id}")
            return Avaliado.query.filter_by(
                id=current_user.avaliado_id,
                ativo=True
            ).all()
            
        print(">> Nenhuma regra atendida. Retornando vazio.")
        return []

    except Exception as e:
        print(f"ERRO CRÍTICO ao buscar avaliados: {e}")
        return []

def verificar_alertas_atraso(usuario):
    """Gera flash messages se existirem planos de ação atrasados."""
    try:
        data_limite = datetime.now() - timedelta(days=30)
        query = RespostaPergunta.query.join(AplicacaoQuestionario).join(Avaliado).filter(
            RespostaPergunta.nao_conforme == True,
            (RespostaPergunta.status_acao == 'pendente') | (RespostaPergunta.status_acao == None),
            AplicacaoQuestionario.status == StatusAplicacao.FINALIZADA, 
            AplicacaoQuestionario.data_fim <= data_limite, 
            Avaliado.cliente_id == usuario.cliente_id
        )
        if usuario.avaliado_id:
            query = query.filter(AplicacaoQuestionario.avaliado_id == usuario.avaliado_id)
        elif usuario.grupo_id:
            query = query.filter(Avaliado.grupo_id == usuario.grupo_id)
        
        if query.count() > 0:
            flash(f"⚠️ {query.count()} ações pendentes há mais de 30 dias!", "danger")
    except Exception:
        pass

# ==================== UTILITÁRIOS DE RENDERIZAÇÃO ====================

def render_template_safe(template_name, **kwargs):
    try:
        return render_template(template_name, **kwargs)
    except Exception as e:
        print(f"ERRO TEMPLATE {template_name}: {e}")
        return render_template('cli/index.html', error=str(e), **kwargs)

def gerar_pdf_seguro(html_content, filename="relatorio.pdf"):
    """Gera PDF com WeasyPrint."""
    if not HTML:
        return make_response(html_content)
    try:
        css_path = os.path.join(current_app.static_folder, 'css', 'style.css')
        css_text = ""
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f: css_text = f.read()
            
        html_final = f"<style>{css_text}</style>{html_content}"
        pdf = HTML(string=html_final, base_url=current_app.static_folder).write_pdf()
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        print(f"Erro PDF: {e}")
        return make_response(html_content)

def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
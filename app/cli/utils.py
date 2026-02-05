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

# Imports de modelos
try:
    from ..models import (
        db, Avaliado, LogAuditoria, Notificacao, 
        RespostaPergunta, AplicacaoQuestionario, StatusAplicacao
    )
except ImportError:
    # Fallback para evitar que o editor quebre se os models não forem encontrados no linter
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
        
        try:
            user_type = current_user.tipo
            # Tratamento para Enum ou String
            if hasattr(user_type, 'name'):
                type_name = user_type.name
            elif hasattr(user_type, 'value'):
                type_name = user_type.value
            else:
                type_name = str(user_type)
            
            admin_types = ['ADMIN', 'SUPER_ADMIN', 'admin', 'super_admin']
            
            if type_name not in admin_types:
                flash('Acesso restrito a administradores.', 'error')
                return redirect(url_for('cli.index'))
            
        except AttributeError:
            flash('Erro de autenticação.', 'error')
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function

def verificar_permissao_admin():
    """Função auxiliar que retorna True/False se usuário é admin."""
    if not current_user.is_authenticated:
        return False
    try:
        user_type = current_user.tipo
        if hasattr(user_type, 'name'):
            type_name = user_type.name
        elif hasattr(user_type, 'value'):
            type_name = user_type.value
        else:
            type_name = str(user_type)
        return type_name in ['ADMIN', 'SUPER_ADMIN', 'admin', 'super_admin']
    except:
        return False

# ==================== LOGS E AUDITORIA ====================

def log_acao(acao, detalhes=None, entidade_tipo=None, entidade_id=None):
    """Registra ação no log. Serializa 'detalhes' para JSON."""
    try:
        if detalhes is None:
            detalhes_str = None
        elif isinstance(detalhes, (dict, list)):
            detalhes_str = json.dumps(detalhes, ensure_ascii=False, separators=(',', ':'))
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
        try:
            current_app.logger.exception(f"Erro ao criar log: {e}")
        except Exception:
            print(f"Erro ao criar log: {e}")

def registrar_log(acao, detalhes=None, entidade_tipo=None, entidade_id=None):
    """Alias para manter compatibilidade com código que usa registrar_log."""
    return log_acao(acao, detalhes, entidade_tipo, entidade_id)

def criar_notificacao(usuario_id, titulo, mensagem, tipo='info', link=None):
    """Cria notificação no banco de dados."""
    try:
        if Notificacao:
            notificacao = Notificacao(
                usuario_id=usuario_id,
                titulo=titulo,
                mensagem=mensagem,
                tipo=tipo,
                link=link
            )
            db.session.add(notificacao)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")

# ==================== UTILITÁRIOS DE DADOS ====================

def get_avaliados_usuario():
    """
    Retorna a lista de Ranchos (Avaliados) disponíveis para o usuário.
    Suporta lógica Multi-GAP.
    """
    try:
        user_type = getattr(current_user, 'tipo', 'USUARIO')
        if hasattr(user_type, 'name'): type_name = user_type.name.upper()
        else: type_name = str(user_type).upper()

        # 1. Nível Nacional: Vê TUDO
        if type_name in ['SUPER_ADMIN', 'ADMIN']:
            return Avaliado.query.filter_by(
                cliente_id=current_user.cliente_id, 
                ativo=True
            ).order_by(Avaliado.nome).all()
        
        # 2. Nível Regional (GESTOR/AUDITOR) - MULTI-GAP
        elif type_name in ['GESTOR', 'AUDITOR']:
            gaps_ids = [g.id for g in current_user.grupos_acesso]
            if not gaps_ids and current_user.grupo_id:
                gaps_ids = [current_user.grupo_id]

            if gaps_ids:
                return Avaliado.query.filter(
                    Avaliado.cliente_id == current_user.cliente_id,
                    Avaliado.grupo_id.in_(gaps_ids),
                    Avaliado.ativo == True
                ).order_by(Avaliado.nome).all()
            return []
            
        # 3. Nível Local: Usuário do Rancho
        elif type_name == 'USUARIO' and current_user.avaliado_id:
            return Avaliado.query.filter_by(
                id=current_user.avaliado_id,
                ativo=True
            ).all()
            
        return []

    except Exception as e:
        print(f"Erro ao buscar avaliados: {e}")
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
        
        total_atrasadas = query.count()

        if total_atrasadas > 0:
            msg = f"⚠️ ATENÇÃO: Existem {total_atrasadas} ações corretivas pendentes há mais de 30 dias!"
            flash(msg, "danger")
                
    except Exception as e:
        print(f"Erro ao verificar alertas de atraso: {e}")

# ==================== UTILITÁRIOS DE ARQUIVO E RENDERIZAÇÃO ====================

def render_template_safe(template_name, **kwargs):
    """Render template com tratamento de erro se não existir."""
    try:
        return render_template(template_name, **kwargs)
    except Exception as e:
        print(f"ERRO DETALHADO no template {template_name}: {e}")
        flash(f"Erro no template {template_name}: {str(e)}", "danger")
        return render_template('cli/index.html', 
                             error=f"Template {template_name} erro: {str(e)}", 
                             **kwargs)

def gerar_pdf_seguro(html_content, filename="relatorio.pdf"):
    """Gera PDF com WeasyPrint injetando CSS localmente."""
    if not HTML:
        flash("Sistema de PDF não instalado no servidor. Exibindo HTML.", "warning")
        return make_response(html_content)

    try:
        # Injeção de CSS para garantir carregamento
        css_text = ""
        css_path = os.path.join(current_app.static_folder, 'css', 'style.css')
        if os.path.exists(css_path):
            with open(css_path, 'r', encoding='utf-8') as f:
                css_text = f.read()

        if "</head>" in html_content:
            html_final = html_content.replace("</head>", f"<style>\n{css_text}\n</style>\n</head>")
        else:
            html_final = f"<style>\n{css_text}\n</style>\n" + html_content

        pdf_bytes = HTML(string=html_final, base_url=current_app.static_folder).write_pdf()

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    except Exception as e:
        current_app.logger.error(f"[PDF] ERRO CRÍTICO: {str(e)}")
        flash(f"Erro ao gerar o PDF: {str(e)}", "danger")
        if request.referrer:
            return redirect(request.referrer)
        return make_response(html_content)

def allowed_file(filename, allowed_extensions=None):
    """Verifica extensão de arquivo."""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
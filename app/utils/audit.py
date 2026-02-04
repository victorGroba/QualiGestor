# app/utils/audit.py
from flask import request
from flask_login import current_user
from app.models import db, LogAuditoria

def registrar_log(acao, detalhes=None, entidade_tipo=None, entidade_id=None, commit=False):
    """
    Registra uma ação na tabela de auditoria.
    
    :param acao: Resumo da ação (ex: 'Excluir Aplicação')
    :param detalhes: Texto longo com detalhes (ex: 'ID: 50, Loja: X, Motivo: Y')
    :param entidade_tipo: Nome da tabela afetada (ex: 'AplicacaoQuestionario')
    :param entidade_id: ID do item afetado
    :param commit: Se True, faz commit imediatamente (útil se chamado fora de um fluxo normal)
    """
    try:
        # Pega IP real mesmo se estiver atrás de proxy (Nginx/Cloudflare)
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip = request.remote_addr

        log = LogAuditoria(
            acao=acao,
            detalhes=str(detalhes) if detalhes else None,
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            ip=ip,
            user_agent=str(request.user_agent)[:500], # Limita tamanho
            usuario_id=current_user.id if current_user.is_authenticated else None,
            cliente_id=current_user.cliente_id if current_user.is_authenticated else None
        )

        db.session.add(log)
        
        if commit:
            db.session.commit()
            
    except Exception as e:
        # Falha silenciosa para não travar o sistema se o log der erro
        print(f"ERRO DE AUDITORIA: {e}")
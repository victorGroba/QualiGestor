# app/cli/views/api.py
from flask import request, jsonify, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

# Importa Blueprint e CSRF
from .. import cli_bp, csrf

# Importa Modelos
from ...models import (
    db, Pergunta, Topico, Notificacao, 
    Avaliado, Questionario, AplicacaoQuestionario
)

# ===================== REORDENAÇÃO (DRAG & DROP) =====================

@cli_bp.route('/api/reordenar-perguntas', methods=['POST'])
@login_required
@csrf.exempt
def reordenar_perguntas():
    """Recebe JSON com a nova ordem das perguntas."""
    try:
        data = request.get_json()
        ordem = data.get('ordem', []) # Lista de IDs na nova ordem
        
        if not ordem:
            return jsonify({'erro': 'Ordem vazia'}), 400

        # Verifica segurança do primeiro item para garantir que pertence ao cliente
        primeira = Pergunta.query.get(ordem[0])
        if primeira and primeira.topico.questionario.cliente_id != current_user.cliente_id:
             return jsonify({'erro': 'Acesso negado'}), 403

        # Atualiza em lote
        for index, pid in enumerate(ordem):
            p = Pergunta.query.get(pid)
            if p:
                p.ordem = index + 1
        
        db.session.commit()
        return jsonify({'sucesso': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/api/reordenar-topicos', methods=['POST'])
@login_required
@csrf.exempt
def reordenar_topicos():
    """Recebe JSON com a nova ordem dos tópicos."""
    try:
        data = request.get_json()
        ordem = data.get('ordem', [])
        
        if not ordem: return jsonify({'erro': 'Ordem vazia'}), 400

        primeiro = Topico.query.get(ordem[0])
        if primeiro and primeiro.questionario.cliente_id != current_user.cliente_id:
             return jsonify({'erro': 'Acesso negado'}), 403

        for index, tid in enumerate(ordem):
            t = Topico.query.get(tid)
            if t:
                t.ordem = index + 1
                
        db.session.commit()
        return jsonify({'sucesso': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===================== BUSCA GLOBAL =====================

@cli_bp.route('/buscar')
@login_required
def buscar():
    """Busca global (Barra superior)."""
    termo = request.args.get('q', '').strip()
    if not termo or len(termo) < 2:
        return jsonify([])
    
    resultados = []
    limit = 5
    like = f"%{termo}%"

    try:
        # 1. Avaliados (Ranchos)
        avaliados = Avaliado.query.filter(
            Avaliado.cliente_id == current_user.cliente_id,
            Avaliado.ativo == True,
            Avaliado.nome.ilike(like)
        ).limit(limit).all()
        
        for a in avaliados:
            resultados.append({
                'categoria': 'Local',
                'titulo': a.nome,
                'url': url_for('cli.listar_aplicacoes', avaliado_id=a.id)
            })

        # 2. Questionários
        quest = Questionario.query.filter(
            Questionario.cliente_id == current_user.cliente_id,
            Questionario.ativo == True,
            Questionario.nome.ilike(like)
        ).limit(limit).all()

        for q in quest:
            resultados.append({
                'categoria': 'Modelo',
                'titulo': q.nome,
                'url': url_for('cli.visualizar_questionario', id=q.id)
            })

        # 3. Auditorias (IDs ou Datas)
        apps = AplicacaoQuestionario.query.join(Avaliado).filter(
            Avaliado.cliente_id == current_user.cliente_id
        )
        if termo.isdigit():
            apps = apps.filter(AplicacaoQuestionario.id == int(termo))
        else:
            # Tenta buscar por nome do avaliado dentro da app
            apps = apps.filter(Avaliado.nome.ilike(like))
            
        apps = apps.order_by(AplicacaoQuestionario.data_inicio.desc()).limit(limit).all()

        for app in apps:
            resultados.append({
                'categoria': 'Auditoria',
                'titulo': f"#{app.id} - {app.avaliado.nome}",
                'detalhe': app.data_inicio.strftime('%d/%m/%Y'),
                'url': url_for('cli.visualizar_aplicacao', id=app.id)
            })

    except Exception as e:
        print(f"Erro busca: {e}")

    return jsonify(resultados)

# ===================== NOTIFICAÇÕES =====================

@cli_bp.route('/api/notificacoes/lidas', methods=['POST'])
@login_required
@csrf.exempt
def marcar_notificacoes_lidas():
    """Marca todas como lidas."""
    try:
        Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).update({'lida': True})
        db.session.commit()
        return jsonify({'sucesso': True})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cli_bp.route('/api/count_notificacoes')
@login_required
def api_count_notificacoes():
    """Retorna contador para o badge do sino."""
    try:
        count = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).count()
        return jsonify({'count': count})
    except:
        return jsonify({'count': 0})